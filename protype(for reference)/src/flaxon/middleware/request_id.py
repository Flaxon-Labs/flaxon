from __future__ import annotations

import uuid
from typing import Any

from .base import Middleware


class RequestIDMiddleware(Middleware):
    def __init__(self, app: Any, header_name: str = "x-request-id") -> None:
        super().__init__(app)
        self.header_name = header_name.lower()

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        request_id = uuid.uuid4().hex[:16]
        scope["flaxon.request_id"] = request_id

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((self.header_name.encode("latin-1"), request_id.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
