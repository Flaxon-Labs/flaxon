from __future__ import annotations

from flaxon.exceptions import FlaxonError


class EventError(FlaxonError):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class EventNotFoundError(EventError):
    def __init__(self, message: str = "Event not found") -> None:
        super().__init__(message)


class EventHandlerError(EventError):
    def __init__(self, message: str = "Event handler error") -> None:
        super().__init__(message)


class EventSubscriptionError(EventError):
    def __init__(self, message: str = "Event subscription error") -> None:
        super().__init__(message)


class EventDispatcherError(EventError):
    def __init__(self, message: str = "Event dispatcher error") -> None:
        super().__init__(message)
