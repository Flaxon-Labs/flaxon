from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable
from enum import Enum, StrEnum
from typing import Any


# FIX (UP042): Use StrEnum for string-based Enums
class Signal(StrEnum):
    PRE_RUN = "pre_run"
    POST_RUN = "post_run"
    ON_SUCCESS = "on_success"
    ON_FAILURE = "on_failure"
    ON_RETRY = "on_retry"
    ON_CANCELLED = "on_cancelled"
    ON_TIMEOUT = "on_timeout"


class SignalHandler:

    def __init__(self) -> None:
        self._handlers: dict[Signal, list[Callable]] = {
            signal: [] for signal in Signal
        }

    def connect(self, signal: Signal, handler: Callable) -> None:
        if signal not in self._handlers:
            self._handlers[signal] = []
        self._handlers[signal].append(handler)

    def disconnect(self, signal: Signal, handler: Callable) -> None:
        # FIX (SIM102): Combined nested if statements into a single condition
        if signal in self._handlers and handler in self._handlers[signal]:
            self._handlers[signal].remove(handler)

    async def emit(self, signal: Signal, *args: Any, **kwargs: Any) -> None:
        if signal not in self._handlers:
            return

        for handler in self._handlers[signal]:
            # FIX (SIM105 / S110): Replaced try...except Exception: pass with contextlib.suppress
            with contextlib.suppress(Exception):
                result = handler(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    await result


class SignalManager:

    def __init__(self) -> None:
        self._handlers: dict[str, SignalHandler] = {}

    def get_handler(self, task_id: str) -> SignalHandler:
        if task_id not in self._handlers:
            self._handlers[task_id] = SignalHandler()
        return self._handlers[task_id]

    def remove_handler(self, task_id: str) -> None:
        self._handlers.pop(task_id, None)

    def clear(self) -> None:
        self._handlers.clear()

    def connect(self, task_id: str, signal: Signal, handler: Callable) -> None:
        handler_obj = self.get_handler(task_id)
        handler_obj.connect(signal, handler)

    def disconnect(
        self, task_id: str, signal: Signal, handler: Callable
    ) -> None:
        handler_obj = self.get_handler(task_id)
        handler_obj.disconnect(signal, handler)

    async def emit(
        self, task_id: str, signal: Signal, *args: Any, **kwargs: Any
    ) -> None:
        handler_obj = self.get_handler(task_id)
        await handler_obj.emit(signal, *args, **kwargs)


_default_signal_manager = SignalManager()


def connect_signal(task_id: str, signal: Signal, handler: Callable) -> None:
    _default_signal_manager.connect(task_id, signal, handler)


def disconnect_signal(
    task_id: str, signal: Signal, handler: Callable
) -> None:
    _default_signal_manager.disconnect(task_id, signal, handler)


async def emit_signal(
    task_id: str, signal: Signal, *args: Any, **kwargs: Any
) -> None:
    await _default_signal_manager.emit(task_id, signal, *args, **kwargs)