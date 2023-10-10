"""Defines a Pipeline class that supports creating pipelines with functions"""
from __future__ import annotations

import collections
from typing import Callable, Generic, Iterable, TypeVar, overload

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")


class Pipeline(Generic[T1, T2]):
    def __init__(self, f: Callable[[T1], T2]) -> None:
        self.f = f

    def __call__(self, arg: T1) -> T2:
        return self.f(arg)

    @overload
    def __ror__(self, other: Iterable[T1]) -> Iterable[T2]:  # type: ignore[misc]
        ...

    @overload
    def __ror__(self, other: T1) -> T2:
        ...

    def __ror__(self, other: Iterable[T1] | T1) -> Iterable[T2] | T2:
        if isinstance(other, collections.abc.Iterable) and not isinstance(other, str):
            return map(self.f, other)
        else:
            return self.f(other) # type: ignore[arg-type]

    def __or__(self, other: Callable[[T2], T3]) -> Pipeline[T1, T3]:
        return Pipeline(lambda x: other(self.f(x)))


class Filter(Generic[T]):
    def __init__(self, f: Callable[[T], bool]) -> None:
        self.f = f

    def __call__(self, arg: T) -> bool:
        return self.f(arg)

    def __ror__(self, other: Iterable[T]) -> Iterable[T]:
        yield from (x for x in other if self.f(x))

    def __or__(self, other: Callable[[T], bool]) -> Filter[T]:
        return Filter(lambda x: self.f(x) and other(x))


def main() -> None:
    def list_nums(n: int) -> list[int]:
        return list(range(n))

    def sum_nums(nums: list[int]) -> int:
        return sum(nums)

    def double(x: int) -> int:
        return 2 * x

    def is_even(x: int) -> bool:
        return x % 2 == 0

    def is_positive(x: int) -> bool:
        return x >= 0

    input1 = "5"
    pipeline = Pipeline(int) | double | list_nums | sum_nums
    result = input1 | pipeline
    print(result)

    inputs = [1, 2, 3, 4]
    result2 = list(map(pipeline, inputs))
    print(result2)

    filters = Filter(is_even) | is_positive
    inputs2 = [-4, -2, -1, 0, 2, 3, 4]
    result3 = list(inputs2 | filters)
    print(result3)
 
    for num in inputs2 | pipeline:
        print(num)


if __name__ == "__main__":
    main()
