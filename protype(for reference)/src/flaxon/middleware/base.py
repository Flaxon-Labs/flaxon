from __future__ import annotations

from typing import Any


class Middleware:
    def __init__(self, app: Any, **options: Any) -> None:
        self.app = app
        self.options = options

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        await self.app(scope, receive, send)
