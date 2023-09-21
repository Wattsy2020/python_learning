from __future__ import annotations

import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import Iterator


class TerminationController:
    def __init__(self, duration: int) -> None:
        self.end_time = time.time() + duration

    def should_terminate(self) -> bool:
        return time.time() > self.end_time

class MessageQueue:
    def __init__(self, use_locks: bool) -> None:
        self.message_queue: deque[int] = deque()
        self._lock = threading.RLock()
        self.use_locks = use_locks

    @contextmanager
    def check_has_item(self) -> Iterator[bool]:
        if not self.use_locks:
            yield bool(self.message_queue)
            return
        with self._lock:
            yield bool(self.message_queue)

    def next_item(self) -> int:
        return self.message_queue.popleft()

    """
    get_next_item is the ideal model, I separated the has_item and next item functions to cause a race condition
    @contextmanager
    def get_next_item(self) -> Iterator[int | None]:
        with self._lock:
            yield None if not self.message_queue else self.message_queue.popleft()
    """
            
    def _add_item(self, item: int) -> None:
        self.message_queue.append(item)

    def add_item(self, item: int) -> None:
        if not self.use_locks:
            return self._add_item(item)
        with self._lock:
            self._add_item(item)


def producer(queue: MessageQueue, termination_controller: TerminationController) -> None:
    """Produce some messages"""
    messages = iter(range(100_000_000_000))
    while not termination_controller.should_terminate():
        queue.add_item(next(messages))
        time.sleep(1)


def consumer(queue: MessageQueue, termination_controller: TerminationController, processing_time: float) -> None:
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
                print(f"{processing_time=} found an empty queue, after another thread emptied it, raising {exception=}")
            else:
                print(f"{processing_time=} Processed: {item} -> {item**2}")


def main() -> None:
    message_queue = MessageQueue(use_locks=False)
    termination_controller = TerminationController(10)
    with ThreadPoolExecutor() as executor:
        executor.submit(producer, message_queue, termination_controller)
        executor.submit(consumer, message_queue, termination_controller, 0.1)
        executor.submit(consumer, message_queue, termination_controller, 0.01)

if __name__ == "__main__":
    main()
