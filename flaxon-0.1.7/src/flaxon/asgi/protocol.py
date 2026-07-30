"""
ASGI protocol handling.

This module provides base protocol classes and utilities for handling
ASGI protocol messages.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class Protocol:
    """
    Base protocol handler for ASGI.

    This class provides the foundation for handling specific ASGI protocols
    like HTTP, WebSocket, and lifespan.
    """

    def __init__(self) -> None:
        """Initialize the protocol handler."""
        self._handlers: list[Callable] = []

    def add_handler(self, handler: Callable) -> None:
        """
        Add a protocol handler.

        Args:
            handler: A callable that handles protocol messages.
        """
        self._handlers.append(handler)

    async def handle(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
        app: Any,
    ) -> None:
        """
        Handle protocol messages.

        Args:
            scope: The ASGI scope dictionary.
            receive: The ASGI receive callable.
            send: The ASGI send callable.
            app: The ASGI application.
        """
        raise NotImplementedError("Subclasses must implement handle()")

    def _run_handlers(self, scope: dict[str, Any], *args: Any) -> None:
        """
        Run all registered handlers.

        Args:
            scope: The ASGI scope dictionary.
            *args: Additional arguments to pass to handlers.
        """
        for handler in self._handlers:
            handler(scope, *args)


class HTTPProtocol(Protocol):
    """HTTP protocol handler."""

    async def handle(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
        app: Any,
    ) -> None:
        """Handle HTTP protocol messages."""
        self._run_handlers(scope, receive, send)
        await app(scope, receive, send)


class WebSocketProtocol(Protocol):
    """WebSocket protocol handler."""

    async def handle(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
        app: Any,
    ) -> None:
        """Handle WebSocket protocol messages."""
        self._run_handlers(scope, receive, send)
        await app(scope, receive, send)


class LifespanProtocol(Protocol):
    """Lifespan protocol handler."""

    async def handle(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
        app: Any,
    ) -> None:
        """Handle lifespan protocol messages."""
        self._run_handlers(scope, receive, send)
        await app(scope, receive, send)
