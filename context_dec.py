import shutil
import time
from pathlib import Path
from typing import Any, Callable, Generic, Iterator, Protocol, TypeVar

T = TypeVar("T", covariant=True)
class ContextManager(Protocol, Generic[T]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ...

    def __enter__(self) -> T:
        ...

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        ...


def context_manager(func: Callable[..., Iterator[T]]) -> type[ContextManager[T]]:
    class ContextManagerWrapper:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.iterator = func(*args, **kwargs)

        def __enter__(self) -> T:
            try:
                value = next(self.iterator)
            except StopIteration:
                raise ValueError("Iterator must yield one object, but didn't yield anything")
            return value

        def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            try:
                next(self.iterator) # run the cleanup code by going through the rest of the function
            except StopIteration:
                pass # expected that there is no next item
            else:
                raise ValueError("Iterator must yield only one object, yielded multiple")

    return ContextManagerWrapper


@context_manager
def basic_context() -> Iterator[int]:
    print("Starting manager")
    yield 1
    print("Ending manager")


@context_manager
def temporary_directory(name: str) -> Iterator[Path]:
    """Create a temporary directory that can be manipulated, then deleted when the context manager exits"""
    dirpath = Path(name).absolute()
    if dirpath.exists():
        raise ValueError(f"Path {dirpath=} already exists, cannot create temporary directory")
    dirs_to_create = [path for path in reversed(dirpath.parents) if not path.exists()]
    for dir_ in dirs_to_create:
        dir_.mkdir()
    dirpath.mkdir()

    yield dirpath

    shutil.rmtree(dirpath)
    for dir_ in reversed(dirs_to_create):
        dir_.rmdir()


def main() -> None:
    with basic_context() as result:
        print(f"{result=} should be 1")


    with temporary_directory("temp/dir") as dirpath:
        file = dirpath / "hello.txt"
        file.write_text("hello")
        (symlink := dirpath / "link.ln").symlink_to(file)
        print(symlink.read_text())
        time.sleep(5)

    print(dirpath.exists())


if __name__ == "__main__":
    main()
