from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from .connection import WebSocket


class WebSocketManager:
    """In-memory room manager for a single process.

    Replace this with a Redis-backed plugin when broadcasting across workers.
    """

    def __init__(self) -> None:
        self.rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def join(self, room: str, socket: WebSocket) -> None:
        async with self._lock:
            self.rooms[room].add(socket)

    async def leave(self, room: str, socket: WebSocket) -> None:
        async with self._lock:
            sockets = self.rooms.get(room)
            if sockets is None:
                return
            sockets.discard(socket)
            if not sockets:
                self.rooms.pop(room, None)

    async def broadcast_json(self, room: str, value: Any) -> None:
        sockets = list(self.rooms.get(room, set()))
        failed: list[WebSocket] = []
        for socket in sockets:
            try:
                await socket.send_json(value)
            except Exception:
                failed.append(socket)
        for socket in failed:
            await self.leave(room, socket)
