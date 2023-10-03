"""
Implements a Thread safe message queue similar to queue.Queue()
It ensures the queue stays below the max capacity, so that producers are not overwhelmed by consumers
"""
import threading
import time
from collections import deque
from random import randrange
from typing import Generic, TypeVar

T = TypeVar("T")
class MessageQueue(Generic[T]):
    def __init__(self, capacity: int = 64) -> None:
        self._capacity = capacity
        self._queue: deque[T] = deque()
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)

    def put(self, item: T) -> None:
        """Put the item into the queue, block if the queue is full"""
        with self._not_full:
            # note: get could be called twice, 
            # notifying 1 thread to do two puts, then notifying another thread to also do a put
            # resulting in 3 items being added to a queue that only had capacity for 2
            # see https://stackoverflow.com/a/7909803
            while len(self._queue) >= self._capacity:
                self._not_full.wait()
            self._queue.append(item)
            self._not_empty.notify()

    def get(self) -> T:
        """Get an item from the queue, block until there is an item"""
        with self._not_empty:
            while not self._queue:
                self._not_empty.wait()
            result = self._queue.popleft()
            self._not_full.notify()
            return result


def producer(queue: MessageQueue[int]) -> None:
    while True:
        item = randrange(1, 100)
        print(f"producer produced {item=}")
        queue.put(item)
        time.sleep(1) # do stress test by removing this and directing stdout to a file


def consumer(queue: MessageQueue[int], id: int) -> None:
    while True:
        print(f"{id} waiting on queue")
        result = queue.get()
        print(f"{id} received {result=}")


def main() -> None:
    queue = MessageQueue[int]()
    prod1 = threading.Thread(target=producer, args=(queue,))
    prod2 = threading.Thread(target=producer, args=(queue,))
    consumer1 = threading.Thread(target=consumer, args=(queue, 1))
    consumer2 = threading.Thread(target=consumer, args=(queue, 2))
    threads = [prod1, prod2, consumer1, consumer2]
    for thread in threads:
        thread.start()


if __name__ == "__main__":
    main()
