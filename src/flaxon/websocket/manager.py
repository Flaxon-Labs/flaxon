"""In-memory WebSocket connection and room manager."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


class WebSocketManager:
    """Track connections and broadcast rooms for an application."""

    def __init__(self) -> None:
        self.connections: set[Any] = set()
        self.rooms: dict[str, set[Any]] = defaultdict(set)

    async def connect(self, socket: Any) -> None:
        self.connections.add(socket)

    async def disconnect(self, socket: Any) -> None:
        self.connections.discard(socket)
        for members in self.rooms.values():
            members.discard(socket)

    async def join(self, room: str, socket: Any) -> None:
        self.rooms[room].add(socket)

    async def leave(self, room: str, socket: Any) -> None:
        self.rooms[room].discard(socket)

    async def broadcast_json(self, room: str, value: Any) -> None:
        for socket in tuple(self.rooms.get(room, ())):
            await socket.send_json(value)
