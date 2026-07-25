from __future__ import annotations

import json
from typing import Any, AsyncIterator


class WebSocketDisconnect(Exception):
    def __init__(self, code: int = 1000) -> None:
        super().__init__(f"WebSocket disconnected with code {code}")
        self.code = code


class WebSocket:
    def __init__(self, scope: dict[str, Any], receive: Any, send: Any, manager: Any = None) -> None:
        self.scope = scope
        self._receive = receive
        self._send = send
        self.manager = manager
        self.path_params = scope.setdefault("path_params", {})
        self.accepted = False
        self.closed = False

    async def accept(self, subprotocol: str | None = None, headers: list[tuple[bytes, bytes]] | None = None) -> None:
        message: dict[str, Any] = {"type": "websocket.accept"}
        if subprotocol:
            message["subprotocol"] = subprotocol
        if headers:
            message["headers"] = headers
        await self._send(message)
        self.accepted = True

    async def receive(self) -> dict[str, Any]:
        message = await self._receive()
        if message["type"] == "websocket.disconnect":
            raise WebSocketDisconnect(message.get("code", 1000))
        return message

    async def receive_text(self) -> str:
        message = await self.receive()
        if "text" in message and message["text"] is not None:
            return message["text"]
        return message.get("bytes", b"").decode("utf-8")

    async def receive_json(self) -> Any:
        return json.loads(await self.receive_text())

    async def send_text(self, value: str) -> None:
        await self._send({"type": "websocket.send", "text": value})

    async def send_bytes(self, value: bytes) -> None:
        await self._send({"type": "websocket.send", "bytes": value})

    async def send_json(self, value: Any) -> None:
        await self.send_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")))

    async def close(self, code: int = 1000, reason: str = "") -> None:
        if not self.closed:
            await self._send({"type": "websocket.close", "code": code, "reason": reason})
            self.closed = True

    async def join(self, room: str) -> None:
        if self.manager is None:
            raise RuntimeError("No WebSocket manager is configured.")
        await self.manager.join(room, self)

    async def leave(self, room: str) -> None:
        if self.manager is not None:
            await self.manager.leave(room, self)

    async def broadcast_json(self, room: str, value: Any) -> None:
        if self.manager is None:
            raise RuntimeError("No WebSocket manager is configured.")
        await self.manager.broadcast_json(room, value)

    async def iter_json(self) -> AsyncIterator[Any]:
        while True:
            try:
                yield await self.receive_json()
            except WebSocketDisconnect:
                return
