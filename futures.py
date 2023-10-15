"""Defines a Future monad that can wrap values as futures and then transform them"""
from __future__ import annotations

import time
from threading import Condition, Thread
from typing import Callable, Generic, TypeVar


class NoResultYet:
    ...

NO_RESULT = NoResultYet()


T = TypeVar("T")
R = TypeVar("R")
class Future(Generic[T]):
    def __init__(self, function: Callable[[], T]) -> None:
        self._result: T | NoResultYet = NO_RESULT
        self._has_result = Condition()

        def set_result_func() -> None:
            result = function()
            with self._has_result:
                self._result = result
                self._has_result.notify_all()

        self._function = set_result_func

    def run(self) -> None:
        """Start the future"""
        Thread(target=self._function).start()

    def result(self) -> T | NoResultYet:
        """Check if there is a result"""
        with self._has_result:
            return self._result
        
    @classmethod
    def from_value(self, value: T) -> Future[T]:
        return Future(lambda: value)
    
    def transform(self, function: Callable[[T], R]) -> Future[R]:
        """Create a new future that computes the result of `function` applied to the result of this future"""
        def run_function() -> R:
            """Function that gets input from this future, then computes its output"""
            self.run()
            with self._has_result:
                self._has_result.wait_for(lambda: self.result() is not NO_RESULT)
                result = self.result()
            assert not isinstance(result, NoResultYet)
            return function(result)
        
        return Future(run_function)
    
    def __or__(self, function: Callable[[T], R]) -> Future[R]:
        return self.transform(function)


def square(num: int) -> int:
    time.sleep(0.5)
    return num**2


def add_one(num: int) -> int:
    time.sleep(0.5)
    return num + 1


def test_wrapping() -> None:
    input_value = Future.from_value(2)
    assert input_value.result() == NO_RESULT
    input_value.run()
    assert input_value.result() == 2


def test_single_future() -> None:
    future = Future(lambda: square(2))
    future.run()
    assert future.result() == NO_RESULT
    time.sleep(0.6)
    assert future.result() == 4


def test_chained_futures() -> None:
    input_value = Future.from_value(2)
    future = input_value | square | square
    future.run()
    assert future.result() == NO_RESULT
    time.sleep(1.1)
    assert future.result() == 16


def test_multiple_dependencies() -> None:
    input_value = Future.from_value(2)
    ancestor = input_value | square
    result1 = ancestor | square
    result2 = ancestor | add_one
    
    result1.run()
    result2.run()

    time.sleep(0.6)
    assert ancestor.result() == 4
    
    time.sleep(0.5)
    assert result1.result() == 16
    assert result2.result() == 5
