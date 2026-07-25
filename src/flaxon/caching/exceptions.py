from __future__ import annotations

from flaxon.exceptions import FlaxonError


class CacheError(FlaxonError):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class CacheKeyError(CacheError):
    def __init__(self, message: str = "Invalid cache key") -> None:
        super().__init__(message)


class CacheNotFoundError(CacheError):
    def __init__(self, message: str = "Cache entry not found") -> None:
        super().__init__(message)


class CacheTimeoutError(CacheError):
    def __init__(self, message: str = "Cache operation timed out") -> None:
        super().__init__(message)


class CacheSerializationError(CacheError):
    def __init__(self, message: str = "Cache serialization error") -> None:
        super().__init__(message)
