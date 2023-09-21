from __future__ import annotations

import threading
import time
from collections import deque
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
        self._message_queue: deque[int] = deque()
        self._read_lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._use_locks = use_locks

    @contextmanager
    def check_has_item(self) -> Iterator[bool]:
        if not self._use_locks:
            yield bool(self._message_queue)
            return
        with self._read_lock:
            yield bool(self._message_queue)

    def next_item(self) -> int:
        return self._message_queue.popleft()

    """
    get_next_item is the ideal model, I separated the has_item and next item functions to cause a race condition
    @contextmanager
    def get_next_item(self) -> Iterator[int | None]:
        with self._lock:
            yield None if not self.message_queue else self.message_queue.popleft()
    """

    def add_item(self, item: int) -> None:
        with self._write_lock:
            self._message_queue.append(item)


def producer(queue: MessageQueue, termination_controller: TerminationController, start_range: int, time_scale: float) -> None:
    """Produce some messages"""
    messages = iter(range(start_range, 100_000))
    while not termination_controller.should_terminate():
        for _ in range(randrange(1, 20)):
            queue.add_item(next(messages))
        time.sleep(time_scale)


def consumer(queue: MessageQueue, termination_controller: TerminationController, result: list[int], processing_time: float) -> None:
    """Consume messages immediately"""
    while not termination_controller.should_terminate():
        with queue.check_has_item() as has_item:
            if not has_item:
                continue

            print(f"{processing_time=} verified queue has an item, now waiting")
            time.sleep(processing_time) # processing, potentially another thread can interefere and cause a race condition
            try:
                item = queue.next_item()
            except Exception as exception:
                print(f"{processing_time=} found an empty queue, after another thread emptied it, which raised {exception=}")
            else:
                print(f"{processing_time=} Processed: {item} -> {item**2}")
                result.append(item)


def run_experiment(start_val1: int = 10, start_val2: int = 1, time_scale: float = 1) -> list[int]:
    message_queue = MessageQueue(use_locks=True)
    termination_controller = TerminationController(time_scale)
    result: list[int] = []
    with ThreadPoolExecutor() as executor:
        executor.submit(producer, message_queue, termination_controller, start_val1, time_scale)
        executor.submit(producer, message_queue, termination_controller, start_val2, time_scale)
        executor.submit(consumer, message_queue, termination_controller, result, time_scale*0.01)
        executor.submit(consumer, message_queue, termination_controller, result, time_scale*0.005)
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
            assert False, f"{num=} not equal to either start values: {start_val1}, {start_val2}"


if __name__ == "__main__":
    run_experiment()
