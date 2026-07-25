from __future__ import annotations

from typing import Any

from .base import Middleware


class SecurityHeadersMiddleware(Middleware):
    DEFAULT_HEADERS = {
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "referrer-policy": "strict-origin-when-cross-origin",
        "permissions-policy": "geolocation=(), microphone=(), camera=()",
    }

    def __init__(self, app: Any, headers: dict[str, str] | None = None) -> None:
        super().__init__(app)
        self.headers = {**self.DEFAULT_HEADERS, **(headers or {})}

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                raw = list(message.get("headers", []))
                existing = {key.decode("latin-1").lower() for key, _ in raw}
                for key, value in self.headers.items():
                    if key not in existing:
                        raw.append((key.encode("latin-1"), value.encode("latin-1")))
                message["headers"] = raw
            await send(message)
        await self.app(scope, receive, send_wrapper)
