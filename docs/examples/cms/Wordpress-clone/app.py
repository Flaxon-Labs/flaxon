"""A tiny WordPress-style CMS: a blog feed that updates live for everyone
viewing it, the moment someone publishes a new post — powered by
Flaxon's built-in WebSocket support (app.websocket_manager, rooms, and
broadcast_json). In-memory storage, single page, ~2 files total.
"""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from flaxon import Flaxon, JSONResponse
from flaxon.http import HTMLResponse, Request
from flaxon.websocket import WebSocket, WebSocketDisconnect

app = Flaxon("mini-wordpress", debug=True)

posts: dict[str, dict] = {}


def seed():
    for title, content, author in [
        ("Hello, World!", "This is the first post on this tiny blog.", "Admin"),
        ("Why WebSockets Are Neat", "New posts show up live, no refresh needed.", "Admin"),
    ]:
        post_id = uuid4().hex[:8]
        posts[post_id] = {
            "id": post_id,
            "title": title,
            "content": content,
            "author": author,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }


seed()


@app.get("/")
async def home(request: Request):
    html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.get("/api/posts")
async def list_posts():
    return JSONResponse(sorted(posts.values(), key=lambda p: p["created_at"], reverse=True))


@app.post("/api/posts")
async def create_post(request: Request):
    data = await request.json()
    title = (data or {}).get("title", "").strip()
    content = (data or {}).get("content", "").strip()
    author = (data or {}).get("author", "").strip() or "Anonymous"

    if not title or not content:
        return JSONResponse({"error": "title and content are required"}, status_code=400)

    post_id = uuid4().hex[:8]
    post = {
        "id": post_id,
        "title": title,
        "content": content,
        "author": author,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    posts[post_id] = post

    # Push the new post to every connected browser, live.
    await app.websocket_manager.broadcast_json("blog", {"type": "new_post", "post": post})

    return JSONResponse(post, status_code=201)


@app.delete("/api/posts/<post_id>")
async def delete_post(post_id: str):
    if post_id not in posts:
        return JSONResponse({"error": "not found"}, status_code=404)
    del posts[post_id]
    await app.websocket_manager.broadcast_json("blog", {"type": "delete_post", "id": post_id})
    return JSONResponse({"deleted": True})


@app.websocket("/ws")
async def blog_feed(socket: WebSocket):
    await socket.accept()
    await socket.join("blog")
    try:
        async for _ in socket.iter_json():
            pass  # this demo only pushes server -> client; nothing expected back
    except WebSocketDisconnect:
        pass