from __future__ import annotations

from typing import Generic, TypeVar, cast

T = TypeVar("T")


class Option(Generic[T]):
    def __new__(cls, *value: T) -> Option[T]:
        """Create a new option given a single value, or no value"""
        if not value:
            return cast(Empty[T], object.__new__(Empty))
        return cast(Some[T], object.__new__(Some))
    

class Some(Option[T]):
    def __init__(self, *value: T) -> None:
        self.value = value[0]

    def __repr__(self) -> str:
        return f"Some({self.value})"


class Empty(Option[T]):
    def __repr__(self) -> str:
        return "Empty"


def main() -> None:
    opt1 = Option[int]()
    opt2 = Option(2)
    opt3 = Option(5)

    opts: list[Option[int]] = [opt1, opt2, opt3]
    for opt in opts:
        match opt:
            case Some(value=value):
                print(f"{opt=} {value=}")
            case Empty():
                print(f"{opt=}")
 

if __name__ == "__main__":
    main()
