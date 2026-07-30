from __future__ import annotations

import contextvars
from typing import Any


class Scope:
    _current_scope: contextvars.ContextVar[str] = contextvars.ContextVar("di_scope", default="global")
    _scope_data: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("di_scope_data", default={})

    def __init__(self, name: str = "global") -> None:
        self.name = name

    def __enter__(self) -> Scope:
        self._token = Scope._current_scope.set(self.name)
        self._data_token = Scope._scope_data.set({})
        return self

    def __exit__(self, *args: Any) -> None:
        Scope._current_scope.reset(self._token)
        Scope._scope_data.reset(self._data_token)

    @classmethod
    def get_current(cls) -> str:
        return cls._current_scope.get()

    @classmethod
    def set_data(cls, key: str, value: Any) -> None:
        data = dict(cls._scope_data.get())
        data[key] = value
        cls._scope_data.set(data)

    @classmethod
    def get_data(cls, key: str, default: Any = None) -> Any:
        return cls._scope_data.get().get(key, default)

    @classmethod
    def clear_data(cls) -> None:
        cls._scope_data.set({})


class ScopedContainer:
    def __init__(self, parent_container: Any, name: str) -> None:
        self.parent = parent_container
        self.name = name
        self._instances: dict[str, Any] = {}

    def get(self, name: str) -> Any:
        if name in self._instances:
            return self._instances[name]
        return self.parent.get(name)

    def set(self, name: str, value: Any) -> None:
        self._instances[name] = value

    def clear(self) -> None:
        self._instances.clear()


class ScopeManager:
    def __init__(self) -> None:
        self._scopes: dict[str, Scope] = {}
        self._active_scope: str = "global"

    def create_scope(self, name: str) -> None:
        self._scopes[name] = Scope(name)

    def enter_scope(self, name: str) -> Scope:
        scope = self._scopes.get(name)
        if scope is None:
            scope = Scope(name)
            self._scopes[name] = scope
        self._active_scope = name
        return scope

    def exit_scope(self) -> None:
        self._active_scope = "global"

    def get_active_scope(self) -> str:
        return self._active_scope

    def get_scope(self, name: str) -> Scope | None:
        return self._scopes.get(name)

    def remove_scope(self, name: str) -> None:
        self._scopes.pop(name, None)

    def clear(self) -> None:
        self._scopes.clear()
        self._active_scope = "global"
