from __future__ import annotations

from typing import Generic, TypeAlias, TypeVar

T = TypeVar("T")


class Some(Generic[T]):
    def __init__(self, *value: T) -> None:
        self.value = value[0]

    def __repr__(self) -> str:
        return f"Some({self.value})"


class Empty():
    def __repr__(self) -> str:
        return "Empty"


Option: TypeAlias = Some[T] | Empty
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
 

if __name__ == "__main__":
    main()
