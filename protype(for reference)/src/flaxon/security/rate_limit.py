from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from typing import Any, Callable

from flaxon.http import JSONResponse


class RateLimitMiddleware:
    """Simple in-memory fixed-window limiter for development and single-process use."""

    def __init__(
        self,
        app: Any,
        *,
        requests: int = 60,
        window_seconds: int = 60,
        key_func: Callable[[dict[str, Any]], str] | None = None,
    ) -> None:
        self.app = app
        self.requests = requests
        self.window_seconds = window_seconds
        self.key_func = key_func or self._default_key
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.lock = asyncio.Lock()

    def _default_key(self, scope: dict[str, Any]) -> str:
        client = scope.get("client") or ("unknown", 0)
        return str(client[0])

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        key = self.key_func(scope)
        now = time.monotonic()
        async with self.lock:
            bucket = self.hits[key]
            cutoff = now - self.window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.requests:
                response = JSONResponse(
                    {"success": False, "error": {"code": "FX-RATE-001", "message": "Too many requests."}},
                    status_code=429,
                    headers={"retry-after": str(self.window_seconds)},
                )
                await response(scope, receive, send)
                return
            bucket.append(now)
        await self.app(scope, receive, send)
