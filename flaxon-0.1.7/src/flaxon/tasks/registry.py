from __future__ import annotations

from collections.abc import Callable

from .exceptions import TaskNotFoundError


class TaskRegistry:
    def __init__(self) -> None:
        self._tasks: dict[str, Callable] = {}

    def register(self, name: str, func: Callable) -> None:
        self._tasks[name] = func

    def get(self, name: str) -> Callable | None:
        return self._tasks.get(name)

    def get_required(self, name: str) -> Callable:
        func = self._tasks.get(name)
        if func is None:
            raise TaskNotFoundError(f"Task '{name}' not found in registry")
        return func

    def remove(self, name: str) -> None:
        self._tasks.pop(name, None)

    def clear(self) -> None:
        self._tasks.clear()

    def list_tasks(self) -> list[str]:
        return list(self._tasks.keys())

    def count(self) -> int:
        return len(self._tasks)

    def __contains__(self, name: str) -> bool:
        return name in self._tasks

    def __iter__(self):
        return iter(self._tasks)


_default_registry = TaskRegistry()


def register_task(name: str, func: Callable) -> None:
    _default_registry.register(name, func)


def get_task(name: str) -> Callable | None:
    return _default_registry.get(name)
