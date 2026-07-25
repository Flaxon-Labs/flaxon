"""
Recovery middleware for Flaxon.

This module provides middleware for recovering from errors and returning
safe responses.
"""

from __future__ import annotations

import traceback
from typing import Any

from flaxon.exceptions import HTTPException
from flaxon.http import JSONResponse, Response

from .base import Middleware


class RecoveryMiddleware(Middleware):
    """
    Recovery middleware.

    This middleware catches exceptions and returns safe error responses.

    Example:
        ```python
        app.add_middleware(
            RecoveryMiddleware,
            debug=False,
            error_response=lambda: {"error": "Something went wrong"},
        )
        ```
    """

    def __init__(
        self,
        app: Any,
        debug: bool = False,
        error_response: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the recovery middleware.

        Args:
            app: The ASGI application.
            debug: Whether to include debug information in responses.
            error_response: Custom error response for 500 errors.
        """
        super().__init__(app)
        self.debug = debug
        self.error_response = error_response or {
            "success": False,
            "error": {
                "code": "FX-SRV-500",
                "message": "The request could not be completed.",
            },
        }

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """Process the request with error recovery."""
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
        except HTTPException as exc:
            response = self._create_http_error_response(exc)
            await response(scope, receive, send)
        except Exception as exc:
            if self.debug:
                response = self._create_debug_response(exc, scope)
            else:
                response = self._create_production_response()
            await response(scope, receive, send)

    def _create_http_error_response(self, exc: HTTPException) -> Response:
        payload: dict[str, Any] = {
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.detail,
            },
        }
        if exc.extra:
            payload["error"].update(exc.extra)

        return JSONResponse(payload, status_code=exc.status_code, headers=exc.headers)

    def _create_debug_response(self, exc: Exception, scope: dict[str, Any]) -> Response:
        request_id = scope.get("flaxon.request_id", "unknown")

        payload = {
            "success": False,
            "error": {
                "code": "FX-DEV-500",
                "message": str(exc),
                "request_id": request_id,
                "debug": {
                    "type": exc.__class__.__name__,
                    "traceback": traceback.format_exc(),
                    "path": scope.get("path", "/"),
                    "method": scope.get("method", "GET"),
                },
            },
        }

        return JSONResponse(payload, status_code=500)

    def _create_production_response(self) -> Response:
        return JSONResponse(self.error_response, status_code=500)
