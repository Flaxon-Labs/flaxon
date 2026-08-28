"""A production-shaped real-time chat backend using Flaxon WebSockets.

The in-memory repository keeps this example copy-pasteable. Replace the
repository methods with database queries before deploying, and configure a
Redis broadcaster for multi-worker room delivery.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from flaxon import Flaxon
from flaxon.jinax import Jinax
from flaxon.websocket import WebSocket, WebSocketDisconnect


BASE_DIR = Path(__file__).parent
app = Flaxon("whatsapp-chat", debug=True)
app.use_templates(Jinax(BASE_DIR / "templates", auto_reload=True, strict_undefined=True))
app.mount_static("/static", BASE_DIR / "static")

MAX_MESSAGE_LENGTH = 4_000
MAX_HISTORY = 100
messages: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=MAX_HISTORY))
presence: dict[str, set[WebSocket]] = defaultdict(set)
presence_lock = asyncio.Lock()


def message_event(room_id: str, username: str, text: str) -> dict[str, Any]:
    event = {
        "id": uuid.uuid4().hex,
        "type": "message.created",
        "room": room_id,
        "user": username,
        "text": text,
        "created_at": int(time.time()),
    }
    messages[room_id].append(event)
    return event


async def broadcast(room_id: str, event: dict[str, Any]) -> None:
    """Send an event to this worker's room connections.

    For multiple workers, configure ``app.websocket_manager`` with a Redis
    broadcaster; the same room API then fans events across processes.
    """
    await app.websocket_manager.broadcast_json(room_id, event)


@app.get("/")
async def home(request):
    return await request.render(
        "index.html",
        {"title": "Flaxon Chat", "websocket_path": "/ws/chat/general"},
    )


@app.get("/api/health")
async def health():
    return {"ok": True, "rooms": len(presence), "messages": sum(map(len, messages.values()))}


@app.get("/api/rooms/<room_id>/messages")
async def room_history(room_id: str):
    return {"room": room_id, "messages": list(messages[room_id])}


@app.websocket("/ws/chat/<room_id>")
async def chat(socket: WebSocket, room_id: str):
    """JSON event protocol: hello, message.send, typing, and ping."""
    username = (socket.scope.get("query_string", b"").decode() or "guest").split("user=", 1)[-1]
    username = username.split("&", 1)[0][:40] or "guest"
    await socket.accept()
    await socket.join(room_id)
    async with presence_lock:
        presence[room_id].add(socket)
    await socket.send_json({"type": "session.ready", "room": room_id, "user": username, "history": list(messages[room_id])})
    await broadcast(room_id, {"type": "presence.joined", "room": room_id, "user": username})
    try:
        async for payload in socket.iter_json():
            if not isinstance(payload, dict):
                await socket.send_json({"type": "error", "code": "invalid_payload"})
                continue
            event_type = payload.get("type")
            if event_type == "message.send":
                text = str(payload.get("text", "")).strip()
                if not text or len(text) > MAX_MESSAGE_LENGTH:
                    await socket.send_json({"type": "error", "code": "invalid_message"})
                    continue
                await broadcast(room_id, message_event(room_id, username, text))
            elif event_type in {"typing", "ping"}:
                await broadcast(room_id, {"type": event_type, "room": room_id, "user": username})
            else:
                await socket.send_json({"type": "error", "code": "unknown_event"})
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        async with presence_lock:
            presence[room_id].discard(socket)
            if not presence[room_id]:
                presence.pop(room_id, None)
        await socket.leave(room_id)
        await broadcast(room_id, {"type": "presence.left", "room": room_id, "user": username})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("docs.examples.whatsapp_chat.app:app", host="127.0.0.1", port=8000, reload=True)
