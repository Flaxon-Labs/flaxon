"""
ASGI application wrapper.

This module provides the base ASGI application class that handles
protocol dispatch and middleware management.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .http import HTTPHandler
from .lifespan import LifespanHandler
from .websocket import WebSocketHandler


class ASGIApplication:
    """
    Base ASGI application wrapper.

    This class wraps an ASGI application and provides protocol-specific
    handling for HTTP, WebSocket, and lifespan events.
    """

    def __init__(self, app: Any) -> None:
        """
        Initialize the ASGI application wrapper.

        Args:
            app: The ASGI application to wrap.
        """
        self.app = app
        self.http_handler = HTTPHandler()
        self.websocket_handler = WebSocketHandler()
        self.lifespan_handler = LifespanHandler()

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """
        ASGI entry point.

        Args:
            scope: The ASGI scope dictionary.
            receive: The ASGI receive callable.
            send: The ASGI send callable.
        """
        scope_type = scope.get("type")

        if scope_type == "lifespan":
            await self.lifespan_handler.handle(scope, receive, send, self.app)
        elif scope_type == "http":
            await self.http_handler.handle(scope, receive, send, self.app)
        elif scope_type == "websocket":
            await self.websocket_handler.handle(scope, receive, send, self.app)
        else:
            raise RuntimeError(f"Unsupported ASGI scope type: {scope_type}")

    def add_middleware(self, middleware: Callable[[Any], Any]) -> None:
        """
        Add middleware to the application.

        Args:
            middleware: A middleware factory that takes an app and returns a wrapped app.
        """
        self.app = middleware(self.app)

    def add_lifespan_handler(self, handler: Callable) -> None:
        """Add a lifespan handler."""
        self.lifespan_handler.add_handler(handler)

    def add_http_handler(self, handler: Callable) -> None:
        """Add an HTTP handler."""
        self.http_handler.add_handler(handler)

    def add_websocket_handler(self, handler: Callable) -> None:
        """Add a WebSocket handler."""
        self.websocket_handler.add_handler(handler)
