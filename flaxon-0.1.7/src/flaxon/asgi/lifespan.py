"""
Lifespan protocol handler.

This module handles ASGI lifespan events including startup and shutdown.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class LifespanHandler:
    """
    Handler for ASGI lifespan events.

    This class manages startup and shutdown events for the application.
    """

    def __init__(self) -> None:
        """Initialize the lifespan handler."""
        self.startup_handlers: list[Callable] = []
        self.shutdown_handlers: list[Callable] = []

    def add_handler(self, handler: Callable) -> None:
        """
        Add a lifespan handler.

        Args:
            handler: A callable that handles lifespan events.
        """
        self.startup_handlers.append(handler)

    def on_startup(self, callback: Callable) -> Callable:
        """
        Register a startup callback.

        Args:
            callback: The callback to register.

        Returns:
            The callback function.
        """
        self.startup_handlers.append(callback)
        return callback

    def on_shutdown(self, callback: Callable) -> Callable:
        """
        Register a shutdown callback.

        Args:
            callback: The callback to register.

        Returns:
            The callback function.
        """
        self.shutdown_handlers.append(callback)
        return callback

    async def handle(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
        app: Any,
    ) -> None:
        """
        Handle lifespan events.

        Args:
            scope: The ASGI scope dictionary.
            receive: The ASGI receive callable.
            send: The ASGI send callable.
            app: The ASGI application.
        """
        while True:
            message = await receive()
            message_type = message.get("type")

            if message_type == "lifespan.startup":
                try:
                    for handler in self.startup_handlers:
                        result = handler()
                        if hasattr(result, "__await__"):
                            await result
                    await send({"type": "lifespan.startup.complete"})
                except Exception as exc:
                    await send({
                        "type": "lifespan.startup.failed",
                        "message": str(exc),
                    })
                    return

            elif message_type == "lifespan.shutdown":
                try:
                    for handler in reversed(self.shutdown_handlers):
                        result = handler()
                        if hasattr(result, "__await__"):
                            await result
                    await send({"type": "lifespan.shutdown.complete"})
                except Exception as exc:
                    await send({
                        "type": "lifespan.shutdown.failed",
                        "message": str(exc),
                    })
                    return

            else:
                await send({
                    "type": "lifespan.unknown",
                    "message": f"Unknown lifespan message: {message_type}",
                })
                return
