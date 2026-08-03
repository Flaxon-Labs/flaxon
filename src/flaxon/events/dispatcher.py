from __future__ import annotations

import asyncio
from typing import Any

from .event import Event
from .listener import Listener
from .registry import EventRegistry


class EventDispatcher:
    def __init__(self, registry: EventRegistry | None = None) -> None:
        self.registry = registry or EventRegistry()

    def dispatch(self, event: Event | str, data: Any = None) -> None:
        if isinstance(event, str):
            event = Event(event, data)

        listeners = self.registry.get_listeners(event.name)

        for listener in listeners:
            try:
                result = listener.handle(event)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception:
                pass

    async def dispatch_async(self, event: Event | str, data: Any = None) -> None:
        if isinstance(event, str):
            event = Event(event, data)

        listeners = self.registry.get_listeners(event.name)

        tasks = []
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener.callback):
                    tasks.append(asyncio.create_task(listener.handle(event)))
                else:
                    tasks.append(asyncio.create_task(self._run_sync(listener, event)))
            except Exception:
                pass

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_sync(self, listener: Listener, event: Event) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, listener.handle, event)

    def dispatch_sync(self, event: Event | str, data: Any = None) -> None:
        if isinstance(event, str):
            event = Event(event, data)

        listeners = self.registry.get_listeners(event.name)

        for listener in listeners:
            try:
                listener.handle(event)
            except Exception:
                pass

    async def dispatch_with_response(self, event: Event | str, data: Any = None) -> list[Any]:
        if isinstance(event, str):
            event = Event(event, data)

        listeners = self.registry.get_listeners(event.name)
        results = []

        for listener in listeners:
            try:
                result = listener.handle(event)
                if asyncio.iscoroutine(result):
                    result = await result
                results.append(result)
            except Exception:
                pass

        return results

    def has_listeners(self, event_name: str) -> bool:
        return len(self.registry.get_listeners(event_name)) > 0

    def get_listener_count(self, event_name: str) -> int:
        return len(self.registry.get_listeners(event_name))

    def clear(self) -> None:
        self.registry.clear()