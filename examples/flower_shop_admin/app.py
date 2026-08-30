"""Editable flower-shop application using Flaxon Admin, CMS, and WebSockets.

Run from the repository root with::

    python -m flaxon run examples.flower_shop_admin.app:app --reload --port 8000

The example uses the AdminStore for persistent Admin/CMS data. The catalog
model is intentionally small and in-memory so developers can replace it with
their own database model without learning extra framework machinery.
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from flaxon import Flaxon
from flaxon.admin import AdminConfig, AdminDashboard, admin_model
from flaxon.admin.cms import CMS, CMSField, ContentType
from flaxon.jinax import Jinax
from flaxon.websocket import WebSocket, WebSocketDisconnect


ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

app = Flaxon("petal-and-stem", debug=True)
app.use_templates(Jinax(ROOT / "templates", auto_reload=True, strict_undefined=True))
app.mount_static("/shop-static", str(ROOT / "static"))

admin = AdminDashboard(
    app,
    config=AdminConfig(
        site_title="Petal & Stem",
        site_header="Petal & Stem Operations",
        index_title="Flower shop operations",
        timezone="UTC",
        settings={"environment": "development", "public_site": "http://127.0.0.1:8000"},
    ),
    storage_path=str(DATA / "admin.sqlite3"),
    upload_dir=str(DATA / "uploads"),
    url_prefix="/admin",
    users=[
        {
            "username": "owner",
            "password": os.getenv("FLORAL_ADMIN_PASSWORD", "Owner123!"),
            "email": "owner@petal-stem.test",
            "roles": ["administrator"],
            # Set FLORAL_MFA_SECRET to a base32 TOTP secret to require MFA
            # immediately. Otherwise enroll it at /admin/profile after login.
            **({"mfa_secret": os.environ["FLORAL_MFA_SECRET"]} if os.getenv("FLORAL_MFA_SECRET") else {}),
        },
        {
            "username": "florist",
            "password": os.getenv("FLORAL_EDITOR_PASSWORD", "Florist123!"),
            "email": "florist@petal-stem.test",
            "roles": ["editor"],
        },
    ],
)


@admin_model(
    list_display=["id", "name", "category", "price", "stock", "active"],
    search_fields=["name", "sku", "category"],
    list_filter=["category", "active"],
    fields=["name", "sku", "category", "price", "stock", "active"],
)
class Flower:
    """Editable catalog model exposed at ``/admin/flower``."""

    _data: dict[str, dict[str, Any]] = {}
    _id_counter = 1

    @classmethod
    async def get_instances(cls) -> list[dict[str, Any]]:
        return list(cls._data.values())

    @classmethod
    async def get_instance(cls, id: str) -> dict[str, Any] | None:
        return cls._data.get(id)

    @classmethod
    async def create_instance(cls, data: dict[str, Any]) -> dict[str, Any]:
        flower_id = str(cls._id_counter)
        cls._id_counter += 1
        record = {"id": flower_id, "active": True, "stock": 0, **data}
        cls._data[flower_id] = record
        return record

    @classmethod
    async def update_instance(cls, id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        if id not in cls._data:
            return None
        cls._data[id].update(data)
        return cls._data[id]

    @classmethod
    async def delete_instance(cls, id: str) -> bool:
        return cls._data.pop(id, None) is not None


async def restock(flowers: list[str]) -> None:
    """Bulk action used to exercise Admin action permissions and workflows."""
    for flower_id in flowers:
        record = await Flower.get_instance(flower_id)
        if record:
            await Flower.update_instance(flower_id, {"stock": int(record.get("stock", 0)) + 10})


admin.registry.get("flower").add_action("restock", restock)
admin.register_widget(lambda: {"title": "Today", "value": "Fresh flowers, fast delivery"})


cms = CMS(app, url_prefix="/admin/cms", title="Petal & Stem Content", auth=admin.auth)
cms.register(
    ContentType(
        name="story",
        label="Story",
        label_plural="Stories",
        fields=[
            CMSField("title", "Title", required=True),
            CMSField("body", "Body", type="richtext"),
            CMSField("hero_image", "Hero image", type="image"),
            CMSField("published_on", "Published on", type="datetime"),
            CMSField("status", "Status", type="select", choices=["draft", "review", "published", "archived"]),
        ],
        list_display=["title", "status", "updated_at"],
        list_filter=["status"],
        search_fields=["title", "body"],
    )
)


def seed() -> None:
    if not Flower._data:
        for item in (
            {"name": "Spring Peony", "sku": "PEO-001", "category": "Bouquets", "price": 48, "stock": 12, "active": True},
            {"name": "Sunlit Tulips", "sku": "TUL-002", "category": "Seasonal", "price": 32, "stock": 24, "active": True},
            {"name": "Garden Rose Box", "sku": "ROS-003", "category": "Gifts", "price": 72, "stock": 8, "active": True},
        ):
            # The example's seed data is synchronous at import time; the Admin
            # model remains async for normal request handling.
            flower_id = str(Flower._id_counter)
            Flower._id_counter += 1
            Flower._data[flower_id] = {"id": flower_id, **item}
    stories = cms.content_types["story"]
    if not stories.items:
        stories.create({
            "title": "How to keep cut flowers fresh",
            "body": "<p>Trim stems, refresh the water, and keep the arrangement cool.</p>",
            "status": "published",
        })
        cms._save(stories)


seed()

MAX_HISTORY = 100
room_messages: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=MAX_HISTORY))
room_members: dict[str, set[WebSocket]] = defaultdict(set)
room_lock = asyncio.Lock()


def create_message(room_id: str, user: str, text: str) -> dict[str, Any]:
    message = {"id": uuid.uuid4().hex, "room": room_id, "user": user, "text": text, "created_at": int(time.time())}
    room_messages[room_id].append(message)
    return message


@app.get("/")
async def home(request):
    return await request.render("index.html", {"title": "Petal & Stem", "admin_url": "/admin/login", "cms_url": "/admin/cms/", "chat_url": "/chat"})


@app.get("/chat")
async def chat_page(request):
    return await request.render("chat.html", {"title": "Petal & Stem team chat", "room": "shop-floor"})


@app.get("/api/chat/<room_id>/messages")
async def chat_history(room_id: str):
    return {"room": room_id, "messages": list(room_messages[room_id])}


@app.websocket("/ws/chat/<room_id>")
async def chat(socket: WebSocket, room_id: str):
    query = socket.scope.get("query_string", b"").decode()
    user = next((part.split("=", 1)[1] for part in query.split("&") if part.startswith("user=")), "guest")[:40] or "guest"
    await socket.accept()
    await socket.join(room_id)
    async with room_lock:
        room_members[room_id].add(socket)
    await socket.send_json({"type": "ready", "room": room_id, "user": user, "messages": list(room_messages[room_id])})
    await app.websocket_manager.broadcast_json(room_id, {"type": "presence.joined", "user": user})
    try:
        async for payload in socket.iter_json():
            if not isinstance(payload, dict):
                continue
            if payload.get("type") == "message.send":
                text = str(payload.get("text", "")).strip()
                if text and len(text) <= 4000:
                    await app.websocket_manager.broadcast_json(room_id, {"type": "message", "message": create_message(room_id, user, text)})
            elif payload.get("type") in {"typing", "ping"}:
                await app.websocket_manager.broadcast_json(room_id, {"type": payload["type"], "user": user})
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        async with room_lock:
            room_members[room_id].discard(socket)
        await socket.leave(room_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("examples.flower_shop_admin.app:app", host="127.0.0.1", port=8000, reload=True)
