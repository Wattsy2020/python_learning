from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar

T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")


class Pipeline(Generic[T1, T2]):
    def __init__(self, f: Callable[[T1], T2]) -> None:
        self.f = f

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

    input1 = "5"
    result = input1 | (Pipeline(int) | list_nums | sum_nums | double)
    print(result)


if __name__ == "__main__":
    main()
