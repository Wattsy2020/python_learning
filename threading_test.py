from __future__ import annotations

import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor


class TerminationController:
    def __init__(self, duration: int) -> None:
        self.end_time = time.time() + duration

    def should_terminate(self) -> bool:
        return time.time() > self.end_time


def producer(queue: deque[int], termination_controller: TerminationController) -> None:
    """Produce some messages"""
    messages = iter(range(100_000_000_000))
    while not termination_controller.should_terminate():
        queue.append(next(messages))
        time.sleep(1)


def consumer(queue: deque[int], termination_controller: TerminationController, processing_time: float) -> None:
    """Consume messages immediately"""
    while not termination_controller.should_terminate():
        if queue:
            print(f"{processing_time=} checked queue, now waiting")
            time.sleep(processing_time) # processing, potentially another thread can interefere and cause a race condition
            print(f"{processing_time=} done, {len(queue)=}")
            try:
                next_message = queue.popleft()
            except IndexError as exception:
                print(f"{processing_time=} tried to read from empty queue, received {exception=}")
            else:
                print(f"Processed: {next_message} -> {next_message**2}")


def main() -> None:
    message_queue: deque[int] = deque()
    termination_controller = TerminationController(10)
    with ThreadPoolExecutor() as executor:
        executor.submit(producer, message_queue, termination_controller)
        executor.submit(consumer, message_queue, termination_controller, 0.1)
        executor.submit(consumer, message_queue, termination_controller, 0.01)

if __name__ == "__main__":
    main()
