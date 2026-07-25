"""
HTTP protocol handler.

This module handles HTTP requests and responses following the ASGI specification.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from flaxon.http import Request, Response


class HTTPHandler:
    """
    Handler for HTTP requests.

    This class processes HTTP requests and generates appropriate responses.
    """

    def __init__(self) -> None:
        """Initialize the HTTP handler."""
        self._handlers: list[Callable] = []

    def add_handler(self, handler: Callable) -> None:
        """Add an HTTP handler."""
        self._handlers.append(handler)

    async def handle(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
        app: Any,
    ) -> None:
        """
        Handle an HTTP request.

        Args:
            scope: The ASGI scope dictionary.
            receive: The ASGI receive callable.
            send: The ASGI send callable.
            app: The ASGI application.
        """
        request = Request(scope, receive, app)

        try:
            for handler in self._handlers:
                result = handler(request, scope)
                if hasattr(result, "__await__"):
                    await result

            response = await self._get_response(app, request, scope)
            await response(scope, receive, send)

        except Exception as exc:
            response = await self._handle_error(exc, request, scope)
            await response(scope, receive, send)

    async def _get_response(
        self,
        app: Any,
        request: Request,
        scope: dict[str, Any],
    ) -> Response:
        """Get the response from the application."""
        try:
            result = app(scope, request)
            if hasattr(result, "__await__"):
                result = await result

            if isinstance(result, Response):
                return result

            if isinstance(result, (dict, list, tuple)):
                return Response.from_value(result)

            return Response.from_value(result)

        except Exception as exc:
            return await self._handle_error(exc, request, scope)

    async def _handle_error(
        self,
        exc: Exception,
        request: Request,
        scope: dict[str, Any],
    ) -> Response:
        """Handle errors during request processing."""
        from flaxon.debugging import Debugger

        debugger = Debugger(debug=scope.get("app", {}).debug if hasattr(scope.get("app", {}), "debug") else False)
        return await debugger.response_for(exc, request, scope)
