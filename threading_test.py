from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from random import randrange
from typing import Iterator

from hypothesis import given
from hypothesis import strategies as st


class TerminationController:
    def __init__(self, duration: float) -> None:
        self.end_time = time.time() + duration

    def should_terminate(self) -> bool:
        return time.time() > self.end_time


class MessageQueue:
    def __init__(self, use_locks: bool) -> None:
        self._capacity = 8
        self._message_queue: list[int | None] = [None] * self._capacity
        self._read_pos = 0
        self._append_pos = 0

        self._read_lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._use_locks = use_locks

    # NOTE: expand_capacity and shrink_capacity need to acquire both locks
    # (i.e. expand_capacity needs to also acquire read lock, and shrink capacity the write lock)
    # as reads and writes are both affected by changing self._read_pos and self._append_pos

    @property
    def _all_items(self) -> list[int | None]:
        return self._message_queue[self._read_pos : self._append_pos]

    def _shrink_capacity(self) -> None:
        with self._write_lock:
            self._capacity //= 2
            new_message_queue: list[int | None] = [None] * self._capacity
            new_message_queue[: len(self)] = self._all_items
            self._message_queue = new_message_queue
            self._read_pos, self._append_pos = 0, len(self)

    def _popleft(self) -> int:
        """Pop item from the queue, if the queue is mostly empty then shrink it to save space"""
        if self._read_pos == self._append_pos:
            raise IndexError(
                f"The queue is empty as {self._read_pos=} and {self._append_pos=} are the same"
            )
        if self._capacity > 8 and len(self) <= self._capacity // 2:
            self._shrink_capacity()
        result = self._message_queue[self._read_pos]
        assert result is not None
        self._read_pos += 1
        return result

    def _expand_capacity(self) -> None:
        """Double the queue capacity, and remove deleted items"""
        with self._read_lock:
            self._capacity *= 2
            new_message_queue: list[int | None] = [None] * self._capacity
            new_message_queue[: len(self)] = self._all_items
            self._message_queue = new_message_queue
            self._read_pos, self._append_pos = 0, len(self)

    def _append(self, item: int) -> None:
        """Add item, expand the capacity if the maximum capacity is reached"""
        if self._append_pos == self._capacity:
            self._expand_capacity()
        self._message_queue[self._append_pos] = item
        self._append_pos += 1

    @contextmanager
    def check_has_item(self) -> Iterator[bool]:
        if not self._use_locks:
            yield bool(self)
            return
        with self._read_lock:
            yield bool(self)

    def next_item(self) -> int:
        return self._popleft()

    """
    get_next_item is the ideal model, I separated the has_item and next item functions to cause a race condition
    @contextmanager
    def get_next_item(self) -> Iterator[int | None]:
        with self._lock:
            yield None if not self.message_queue else self.message_queue.popleft()
    """

    def add_item(self, item: int) -> None:
        with self._write_lock:
            self._append(item)

    def __len__(self) -> int:
        return self._append_pos - self._read_pos

    def __bool__(self) -> bool:
        return len(self) > 0


def producer(
    queue: MessageQueue,
    termination_controller: TerminationController,
    start_range: int,
    time_scale: float,
) -> None:
    """Produce some messages"""
    messages = iter(range(start_range, 100_000))
    while not termination_controller.should_terminate():
        for _ in range(randrange(1, 20)):
            queue.add_item(next(messages))
        time.sleep(time_scale)


def consumer(
    queue: MessageQueue,
    termination_controller: TerminationController,
    result: list[int],
    processing_time: float,
) -> None:
    """Consume messages immediately"""
    while not termination_controller.should_terminate():
        with queue.check_has_item() as has_item:
            if not has_item:
                continue

            log.info("%s verified queue has an item, now waiting", processing_time)
            if processing_time != 0:
                time.sleep(
                    processing_time
                )  # processing, potentially another thread can interefere and cause a race condition
            try:
                item = queue.next_item()
            except Exception as exception:
                log.error(
                    "%s found an empty queue, after another thread emptied it, which raised Exception=%s",
                    processing_time,
                    exception,
                )
            else:
                log.info("%s Processed: %s", processing_time, item)
                result.append(item)


def run_experiment(
    start_val1: int = 10, start_val2: int = 1, time_scale: float = 1
) -> list[int]:
    message_queue = MessageQueue(use_locks=True)
    termination_controller = TerminationController(time_scale)
    result: list[int] = []
    with ThreadPoolExecutor() as executor:
        executor.submit(
            producer, message_queue, termination_controller, start_val1, time_scale
        )
        executor.submit(
            producer, message_queue, termination_controller, start_val2, time_scale
        )
        executor.submit(
            consumer, message_queue, termination_controller, result, time_scale * 0.01
        )
        executor.submit(
            consumer, message_queue, termination_controller, result, time_scale * 0.005
        )
    return result


@given(st.integers(), st.integers())
def test_race_conditions(start_val1: int, start_val2: int) -> None:
    """Enforce that the messages are consumed sequentially"""
    result = run_experiment(start_val1, start_val2, time_scale=0.001)
    for num in result:
        if num == start_val1:
            start_val1 += 1
        elif num == start_val2:
            start_val2 += 1
        else:
            assert (
                False
            ), f"{num=} not equal to either start values: {start_val1}, {start_val2}"


def fixed_producer(queue: MessageQueue, messages: list[int]) -> None:
    for message in messages:
        queue.add_item(message)


def stress_test(
    messages1: list[int], messages2: list[int], test_time_seconds: float = 5
) -> list[int]:
    """Produce and consume as fast as possible to try to force race conditions"""
    message_queue = MessageQueue(use_locks=True)
    termination_controller = TerminationController(test_time_seconds)
    result: list[int] = []
    with ThreadPoolExecutor() as executor:
        executor.submit(fixed_producer, message_queue, messages1)
        executor.submit(fixed_producer, message_queue, messages2)
        executor.submit(consumer, message_queue, termination_controller, result, 0)
        executor.submit(consumer, message_queue, termination_controller, result, 0)
    return result


@given(st.integers(), st.integers())
def test_race_conditions_stress(start_val1: int, start_val2: int) -> None:
    """Enforce that the messages are consumed sequentially while stress testing"""
    messages1 = list(range(start_val1, start_val1 + 10000))
    messages2 = list(range(start_val2, start_val2 + 10000))
    result = stress_test(messages1, messages2, 0.001)
    for num in result:
        if num == start_val1:
            start_val1 += 1
        elif num == start_val2:
            start_val2 += 1
        else:
            assert (
                False
            ), f"{num=} not equal to either start values: {start_val1}, {start_val2}"


if __name__ == "__main__":
    # set to logging.WARNING for stress testing, to speed up the consumers
    # by removing the logging time
    log = logging.getLogger(name="threading_test")
    logging.basicConfig(level=logging.WARNING)

    run_experiment()
    stress_test(list(range(1, 1_000_000)), list(range(1_000_000, 2_000_000)))
