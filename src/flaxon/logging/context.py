from __future__ import annotations

import contextvars
from typing import Any


class LogContext:
    _context: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("log_context", default={})

    def __init__(self) -> None:
        self._data = self._context.get()

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._context.set(self._data)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def update(self, data: dict[str, Any]) -> None:
        self._data.update(data)
        self._context.set(self._data)

    def remove(self, key: str) -> None:
        self._data.pop(key, None)
        self._context.set(self._data)

    def clear(self) -> None:
        self._data.clear()
        self._context.set(self._data)

    def get_all(self) -> dict[str, Any]:
        return dict(self._data)

    def __enter__(self) -> LogContext:
        self._token = self._context.set(self._data)
        return self

    def __exit__(self, *args: Any) -> None:
        if hasattr(self, "_token"):
            self._context.reset(self._token)

    def bind(self, **kwargs: Any) -> LogContext:
        new_context = LogContext()
        new_context.update(self._data)
        new_context.update(kwargs)
        return new_context


_default_context = LogContext()


def set_log_context(key: str, value: Any) -> None:
    _default_context.set(key, value)


def get_log_context(key: str, default: Any = None) -> Any:
    return _default_context.get(key, default)


def update_log_context(data: dict[str, Any]) -> None:
    _default_context.update(data)


def clear_log_context() -> None:
    _default_context.clear()


class LogContextMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        request_id = scope.get("flaxon.request_id", "unknown")
        with LogContext():
            set_log_context("request_id", request_id)
            await self.app(scope, receive, send)
