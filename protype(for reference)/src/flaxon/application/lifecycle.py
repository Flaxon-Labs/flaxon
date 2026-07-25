from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any


async def call_maybe_async(callback: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    result = callback(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


class Lifecycle:
    def __init__(self) -> None:
        self.startup_handlers: list[Callable[..., Any]] = []
        self.shutdown_handlers: list[Callable[..., Any]] = []

    def on_startup(self, callback: Callable[..., Any]) -> Callable[..., Any]:
        self.startup_handlers.append(callback)
        return callback

    def on_shutdown(self, callback: Callable[..., Any]) -> Callable[..., Any]:
        self.shutdown_handlers.append(callback)
        return callback

    async def startup(self) -> None:
        for callback in self.startup_handlers:
            await call_maybe_async(callback)

    async def shutdown(self) -> None:
        for callback in reversed(self.shutdown_handlers):
            await call_maybe_async(callback)
