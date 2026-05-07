from collections.abc import Callable
from typing import Any, TypeVar


T = TypeVar("T")


def singleton(class_: type[T]) -> Callable[..., T]:
    instances: dict[type[T], T] = {}

    def getinstance(*args: Any, **kwargs: Any) -> T:
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance
