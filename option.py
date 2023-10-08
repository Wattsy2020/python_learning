from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, TypeAlias, TypeVar

T = TypeVar("T")
T1 = TypeVar("T1")
Option: TypeAlias = 'Some[T] | Empty[T]'


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
    def __or__(self, other: Callable[[T], T1] | Any) -> Option[T1]:
        ...


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
    
    def __or__(self, other: Callable[[T], T1] | Any) -> Option[T1]:
        if not callable(other):
            raise NotImplementedError(f"| operator is only defined for callables, not {other=}")
        return Some[T1](other(self.value))


class Empty(Optional[T]):
    def __init__(self, *value: Any) -> None:
        if value:
            raise ValueError(f"Cannot assign the value {value} to an Empty object")

    def __repr__(self) -> str:
        return "Empty"
    
    def __bool__(self) -> bool:
        return False
    
    def __or__(self, other: Callable[[T], T1] | Any) -> Option[T1]:
        if not callable(other):
            raise NotImplementedError(f"| operator is only defined for callables, not {other=}")
        return Empty[T1]()


def make_option(*value: T) -> Option[T]:
    if not value:
        return Empty()
    return Some(value[0])


def flatmap(option: Option[T], f: Callable[[T], T1]) -> Option[T1]:
    match option:
        case Some(value=value):
            return Some(f(value))
        case Empty():
            return Empty()


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

    for opt in opts:
        result = opt | range_f | sum
        print(result)
 

if __name__ == "__main__":
    main()
