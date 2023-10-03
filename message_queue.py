"""
Implements a Thread safe message queue similar to queue.Queue()
It ensures the queue stays below the max capacity, so that producers are not overwhelmed by consumers
It also allows for tasks to be marked as done, so the queue can be joined and wait for all threads to complete
"""
import threading
from collections import deque
from random import randrange
from typing import Generic, TypeVar

T = TypeVar("T")
class MessageQueue(Generic[T]):
    def __init__(self, capacity: int = 64) -> None:
        self._capacity = capacity
        self._queue: deque[T] = deque()
        self._unfinished_tasks = 0

        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
        self._all_tasks_done = threading.Condition(self._lock)

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
            self._unfinished_tasks += 1
            self._not_empty.notify()

    def get(self) -> T:
        """Get an item from the queue, block until there is an item"""
        with self._not_empty:
            while not self._queue:
                self._not_empty.wait()
            result = self._queue.popleft()
            self._not_full.notify()
            return result
        
    def task_done(self) -> None:
        with self._all_tasks_done:
            self._unfinished_tasks -= 1
            self._all_tasks_done.notify()

    def join(self) -> None:
        """Wait until all tasks are done"""
        with self._all_tasks_done:
            # release the lock until all tasks are done
            while self._unfinished_tasks != 0:
                self._all_tasks_done.wait()
            # now all tasks are done it will stop blocking, and the join function will end
            # allowing the program to end


def producer(queue: MessageQueue[int], num_items: int = 5) -> None:
    while num_items > 0:
        item = randrange(1, 100)
        print(f"producer produced {item=}")
        queue.put(item)
        num_items -= 1


def consumer(queue: MessageQueue[int], id: int) -> None:
    while True:
        print(f"{id} waiting on queue")
        result = queue.get()
        print(f"{id} received {result=}")
        queue.task_done()


def main() -> None:
    queue = MessageQueue[int]()
    # Python doesn't wait for daemon threads to complete
    # it will terminate them upon reaching the end of the program
    # so we need to use queue.join() to wait for the threads to complete
    prod1 = threading.Thread(target=producer, args=(queue,), daemon=True)
    prod2 = threading.Thread(target=producer, args=(queue,), daemon=True)
    consumer1 = threading.Thread(target=consumer, args=(queue, 1), daemon=True)
    consumer2 = threading.Thread(target=consumer, args=(queue, 2), daemon=True)
    threads = [prod1, prod2, consumer1, consumer2]
    for thread in threads:
        thread.start()
    print("queue join start")
    queue.join()
    print("queue join finished")


if __name__ == "__main__":
    main()
