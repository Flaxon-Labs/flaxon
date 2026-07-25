"""
WebSocket protocol handler.

This module handles WebSocket connections following the ASGI specification.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from flaxon.websocket import WebSocket, WebSocketDisconnect


class WebSocketHandler:
    """
    Handler for WebSocket connections.

    This class processes WebSocket handshakes, messages, and disconnections.
    """

    def __init__(self) -> None:
        """Initialize the WebSocket handler."""
        self._handlers: list[Callable] = []

    def add_handler(self, handler: Callable) -> None:
        """Add a WebSocket handler."""
        self._handlers.append(handler)

    async def handle(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
        app: Any,
    ) -> None:
        """
        Handle a WebSocket connection.

        Args:
            scope: The ASGI scope dictionary.
            receive: The ASGI receive callable.
            send: The ASGI send callable.
            app: The ASGI application.
        """
        socket = WebSocket(scope, receive, send)

        try:
            await socket.accept()

            for handler in self._handlers:
                result = handler(socket, scope)
                if hasattr(result, "__await__"):
                    await result

            await app(scope, receive, send)

            while True:
                try:
                    message = await socket.receive()
                    if message.get("type") == "websocket.disconnect":
                        break

                    result = app(message, socket)
                    if hasattr(result, "__await__"):
                        await result

                except WebSocketDisconnect:
                    break
                except Exception:
                    continue

        except WebSocketDisconnect:
            pass
        except Exception as exc:
            await socket.close(code=1011, reason=str(exc))
