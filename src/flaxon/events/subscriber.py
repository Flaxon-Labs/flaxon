from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .event import Event
from .listener import Listener


class EventSubscriber:
    def __init__(self, name: str | None = None) -> None:
        self.name = name or self.__class__.__name__
        self._listeners: dict[str, list[Listener]] = {}

    def subscribe(self, event_name: str, callback: Callable, priority: int = 0) -> None:
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(Listener(callback, priority))

    def get_listeners(self) -> dict[str, list[Listener]]:
        return self._listeners

    def get_listeners_for_event(self, event_name: str) -> list[Listener]:
        return self._listeners.get(event_name, [])

    def get_subscribed_events(self) -> list[str]:
        return list(self._listeners.keys())

    def clear(self) -> None:
        self._listeners.clear()


def subscriber(name: str | None = None) -> Callable:
    def decorator(cls: type) -> type:
        if not hasattr(cls, "get_subscribed_events"):
            cls.get_subscribed_events = lambda self: list(self._listeners.keys())
        return cls
    return decorator


class EventSubscriberMixin:
    def get_subscribed_events(self) -> list[str]:
        events = []
        for attr_name in dir(self):
            if attr_name.startswith("on_"):
                events.append(attr_name[3:])
        return events

    def handle_event(self, event: Event) -> Any:
        method_name = f"on_{event.name}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(event)
        return None
