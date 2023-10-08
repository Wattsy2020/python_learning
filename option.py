from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Generic, TypeAlias, TypeVar, overload

T = TypeVar("T")
T1 = TypeVar("T1")
Option: TypeAlias = "Some[T] | Empty[T]"


class Optional(ABC, Generic[T]):
    def __init__(self, *value: T) -> None:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        ...

    @abstractmethod
    def __bool__(self) -> bool:
        ...

    @abstractmethod
    def unwrap(self) -> T:
        ...

    @abstractmethod
    def or_else(self, other: T) -> T:
        ...

    @abstractmethod
    def transform(self, f: Callable[[T], T1]) -> Option[T1]:
        ...

    @overload
    def __or__(self, other: Callable[[T], T1]) -> Option[T1]:  # type: ignore[misc]
        ...

    @overload
    def __or__(self, other: T) -> T:
        ...

    def __or__(self, other: T | Callable[[T], T1]) -> T | Option[T1]:  # type: ignore[misc]
        if callable(other):
            return self.transform(other)
        return self.or_else(other)


class Some(Optional[T]):
    def __init__(self, *value: T) -> None:
        try:
            first, *remaining = value
        except ValueError:
            raise ValueError("A value must be provided to a Some object")
        if remaining:
            raise ValueError("Only one value should be provided to a Some object")
        self.value = first

    def __repr__(self) -> str:
        return f"Some({self.value})"

    def __bool__(self) -> bool:
        return True
    
    def unwrap(self) -> T:
        return self.value
    
    def or_else(self, other: T) -> T:
        return self.value

    def transform(self, f: Callable[[T], T1]) -> Option[T1]:
        return Some(f(self.value))


class Empty(Optional[T]):
    def __init__(self, *value: T) -> None:
        if value:
            raise ValueError(f"Cannot assign the value {value} to an Empty object")

    def __repr__(self) -> str:
        return "Empty"

    def __bool__(self) -> bool:
        return False

    def unwrap(self) -> T:
        raise ValueError("Empty object has no value to unwrap")
    
    def or_else(self, other: T) -> T:
        return other

    def transform(self, f: Callable[[T], T1]) -> Option[T1]:
        return Empty[T1]()


def make_option(*value: T) -> Option[T]:
    if not value:
        return Empty()
    return Some(value[0])


def main() -> None:
    opt1: Option[int] = make_option()
    opt2 = make_option(2)
    opt3 = make_option(5)

    opts: list[Option[int]] = [opt1, opt2, opt3]
    for opt in opts:
        match opt:
            case Some(value=value):
                print(f"{opt=} {value=}")
            case Empty():
                print(f"{opt=}")

    for opt in opts:
        print(f"{opt=} {bool(opt)=}")

    def range_f(x: int) -> list[int]:
        return list(range(x))

    def sum_typed(x: list[int]) -> int:
        return sum(x)

    for opt in opts:
        result = opt | range_f | sum_typed
        print(f"piped: {result}")
        or_else_result = opt | 1000
        print(f"or_else: {or_else_result}")


if __name__ == "__main__":
    main()
