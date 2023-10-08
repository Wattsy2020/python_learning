from __future__ import annotations

from typing import Callable, Generic, TypeAlias, TypeVar

T = TypeVar("T")
T1 = TypeVar("T1")


class Some(Generic[T]):
    def __init__(self, *value: T) -> None:
        self.value = value[0]

    def __repr__(self) -> str:
        return f"Some({self.value})"
    
    def __bool__(self) -> bool:
        return True


class Empty():
    def __repr__(self) -> str:
        return "Empty"
    
    def __bool__(self) -> bool:
        return False


Option: TypeAlias = Some[T] | Empty
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
    
    for opt in opts:
        print(flatmap(opt, lambda x: list(range(x))))
 

if __name__ == "__main__":
    main()
