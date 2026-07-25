from __future__ import annotations

from collections.abc import Callable

from .listener import Listener
from .subscriber import EventSubscriber


class EventRegistry:
    def __init__(self) -> None:
        self._listeners: dict[str, list[Listener]] = {}

    def register(self, event_name: str, callback: Callable, priority: int = 0) -> None:
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(Listener(callback, priority))
        self._listeners[event_name].sort()

    def register_subscriber(self, subscriber: EventSubscriber) -> None:
        for event_name, listeners in subscriber.get_listeners().items():
            for listener in listeners:
                self.register(event_name, listener.callback, listener.priority)

    def get_listeners(self, event_name: str) -> list[Listener]:
        return self._listeners.get(event_name, [])

    def remove(self, event_name: str, callback: Callable) -> None:
        if event_name in self._listeners:
            self._listeners[event_name] = [
                l for l in self._listeners[event_name]
                if l.callback != callback
            ]
            if not self._listeners[event_name]:
                del self._listeners[event_name]

    def remove_all(self, event_name: str) -> None:
        self._listeners.pop(event_name, None)

    def has_listeners(self, event_name: str) -> bool:
        return event_name in self._listeners and bool(self._listeners[event_name])

    def clear(self) -> None:
        self._listeners.clear()

    def get_event_names(self) -> list[str]:
        return list(self._listeners.keys())

    def get_listener_count(self, event_name: str) -> int:
        return len(self._listeners.get(event_name, []))

    def get_total_listener_count(self) -> int:
        return sum(len(listeners) for listeners in self._listeners.values())
