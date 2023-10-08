"""Defines a Pipeline class that supports creating pipelines with functions"""
from __future__ import annotations

from typing import Callable, Generic, TypeVar

T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")


class Pipeline(Generic[T1, T2]):
    def __init__(self, f: Callable[[T1], T2]) -> None:
        self.f = f

    def __call__(self, arg: T1) -> T2:
        return self.f(arg)

    def __ror__(self, other: T1) -> T2:
        return self.f(other)
    
    def __or__(self, other: Callable[[T2], T3]) -> Pipeline[T1, T3]:
        return Pipeline(lambda x: other(self.f(x)))


def main() -> None:
    def list_nums(n: int) -> list[int]:
        return list(range(n))
    
    def sum_nums(nums: list[int]) -> int:
        return sum(nums)
    
    def double(x: int) -> int:
        return 2*x
    
    def filter_even(nums: list[int]) -> list[int]:
        return list(filter(lambda x: x % 2 == 0, nums))
    
    def filter_positive(x: int) -> int:
        return x >= 0

    input1 = "5"
    pipeline = Pipeline(int) | double | list_nums | filter_even | sum_nums
    result = input1 | pipeline
    print(result)

    inputs = [1, 2, 3, 4]
    result2 = list(map(pipeline, inputs))
    print(result2)


if __name__ == "__main__":
    main()
