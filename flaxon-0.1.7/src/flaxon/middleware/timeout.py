"""
Timeout middleware for Flaxon.

This module provides middleware for setting request timeouts.
"""

from __future__ import annotations

import asyncio
from typing import Any

from flaxon.exceptions import RequestTimeout

from .base import Middleware


class TimeoutMiddleware(Middleware):
    """
    Timeout middleware.

    This middleware sets a timeout for request processing.

    Example:
        ```python
        app.add_middleware(TimeoutMiddleware, timeout=30)
        ```
    """

    def __init__(self, app: Any, timeout: int = 30) -> None:
        """
        Initialize the timeout middleware.

        Args:
            app: The ASGI application.
            timeout: The timeout in seconds.
        """
        super().__init__(app)
        self.timeout = timeout

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """Process the request with a timeout."""
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        try:
            await asyncio.wait_for(
                self.app(scope, receive, send),
                timeout=self.timeout,
            )
        except TimeoutError as exc:
            raise RequestTimeout(f"Request timed out after {self.timeout} seconds") from exc
