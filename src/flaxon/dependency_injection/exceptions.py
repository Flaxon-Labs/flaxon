from __future__ import annotations

from flaxon.exceptions import FlaxonError


class DependencyError(FlaxonError):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class DependencyNotFoundError(DependencyError):
    def __init__(self, message: str = "Dependency not found") -> None:
        super().__init__(message)


class CircularDependencyError(DependencyError):
    def __init__(self, message: str = "Circular dependency detected") -> None:
        super().__init__(message)


class ProviderError(DependencyError):
    def __init__(self, message: str = "Provider error") -> None:
        super().__init__(message)


class ScopeError(DependencyError):
    def __init__(self, message: str = "Scope error") -> None:
        super().__init__(message)


class InjectionError(DependencyError):
    def __init__(self, message: str = "Injection error") -> None:
        super().__init__(message)
