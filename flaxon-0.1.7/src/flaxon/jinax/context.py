from __future__ import annotations

from typing import Any


class Context:
    def __init__(self, parent: Context | None = None) -> None:
        self.parent = parent
        self._data: dict[str, Any] = {}

    def get(self, name: str, default: Any = None) -> Any:
        if name in self._data:
            return self._data[name]
        if self.parent:
            return self.parent.get(name, default)
        return default

    def set(self, name: str, value: Any) -> None:
        self._data[name] = value

    def push(self) -> Context:
        return Context(self)

    def pop(self) -> Context | None:
        return self.parent

    def update(self, data: dict[str, Any]) -> None:
        self._data.update(data)

    def to_dict(self) -> dict[str, Any]:
        result = {}
        if self.parent:
            result.update(self.parent.to_dict())
        result.update(self._data)
        return result

    def __getitem__(self, name: str) -> Any:
        return self.get(name)

    def __setitem__(self, name: str, value: Any) -> None:
        self.set(name, value)

    def __contains__(self, name: str) -> bool:
        return name in self._data or (self.parent and name in self.parent)

    def __repr__(self) -> str:
        return f"Context({self.to_dict()})"


class ContextStack:
    def __init__(self) -> None:
        self._stack: list[Context] = [Context()]

    def push(self) -> None:
        self._stack.append(Context(self.current()))

    def pop(self) -> Context | None:
        if len(self._stack) > 1:
            return self._stack.pop()
        return None

    def current(self) -> Context:
        return self._stack[-1]

    def get(self, name: str, default: Any = None) -> Any:
        return self.current().get(name, default)

    def set(self, name: str, value: Any) -> None:
        self.current().set(name, value)

    def update(self, data: dict[str, Any]) -> None:
        self.current().update(data)

    def to_dict(self) -> dict[str, Any]:
        return self.current().to_dict()

    def __getitem__(self, name: str) -> Any:
        return self.current().get(name)

    def __setitem__(self, name: str, value: Any) -> None:
        self.current().set(name, value)
