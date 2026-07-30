"""
Routing exceptions for Flaxon.

This module provides exceptions for routing errors.
"""

from __future__ import annotations

from flaxon.exceptions import FlaxonError


class RoutingError(FlaxonError):
    """Base exception for routing errors."""

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class RouteNotFound(RoutingError):
    """Raised when a route is not found."""

    def __init__(self, path: str, method: str | None = None) -> None:
        """
        Initialize the exception.

        Args:
            path: The path that was not found.
            method: The HTTP method that was used.
        """
        if method:
            message = f"Route not found: {method} {path}"
        else:
            message = f"Route not found: {path}"
        super().__init__(message)
        self.path = path
        self.method = method


class MethodNotAllowed(RoutingError):
    """Raised when an HTTP method is not allowed for a route."""

    def __init__(self, path: str, method: str, allowed: list[str]) -> None:
        """
        Initialize the exception.

        Args:
            path: The path that was requested.
            method: The HTTP method that was used.
            allowed: The allowed methods.
        """
        message = f"Method '{method}' not allowed for '{path}'. Allowed: {', '.join(allowed)}"
        super().__init__(message)
        self.path = path
        self.method = method
        self.allowed = allowed


class InvalidPathParameter(RoutingError):
    """Raised when a path parameter is invalid."""

    def __init__(self, name: str, value: str, expected_type: str) -> None:
        """
        Initialize the exception.

        Args:
            name: The parameter name.
            value: The parameter value.
            expected_type: The expected type.
        """
        message = f"Invalid parameter '{name}': expected {expected_type}, got '{value}'"
        super().__init__(message)
        self.name = name
        self.value = value
        self.expected_type = expected_type


class MissingPathParameter(RoutingError):
    """Raised when a path parameter is missing."""

    def __init__(self, name: str) -> None:
        """
        Initialize the exception.

        Args:
            name: The parameter name.
        """
        message = f"Missing path parameter: '{name}'"
        super().__init__(message)
        self.name = name


class DuplicateRoute(RoutingError):
    """Raised when a duplicate route is registered."""

    def __init__(self, path: str, methods: list[str]) -> None:
        """
        Initialize the exception.

        Args:
            path: The path that was duplicated.
            methods: The methods that were duplicated.
        """
        message = f"Duplicate route: {', '.join(methods)} {path}"
        super().__init__(message)
        self.path = path
        self.methods = methods


class InvalidRouteName(RoutingError):
    """Raised when a route name is invalid."""

    def __init__(self, name: str, reason: str) -> None:
        """
        Initialize the exception.

        Args:
            name: The route name.
            reason: The reason why it's invalid.
        """
        message = f"Invalid route name '{name}': {reason}"
        super().__init__(message)
        self.name = name
        self.reason = reason


class RouteAlreadyExists(RoutingError):
    """Raised when a route with the same name already exists."""

    def __init__(self, name: str) -> None:
        """
        Initialize the exception.

        Args:
            name: The route name.
        """
        message = f"Route with name '{name}' already exists"
        super().__init__(message)
        self.name = name
