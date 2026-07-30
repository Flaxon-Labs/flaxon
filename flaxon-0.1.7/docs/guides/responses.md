
---

## docs/guides/responses.md

```markdown
# Responses

## Overview

Flaxon automatically converts return values to appropriate HTTP responses. You can return dictionaries, lists, strings, or explicit Response objects.

## Automatic Conversion

```python
@app.get("/")
async def home():
    # Dictionary → JSON
    return {"message": "Hello"}

@app.get("/users")
async def list_users():
    # List → JSON
    return [{"id": 1, "name": "Alice"}]

@app.get("/text")
async def text():
    # String → Text
    return "Hello, World!"

@app.get("/empty")
async def empty():
    # None → 204 No Content
    return None

@app.get("/file")
async def file():
    # Bytes → Octet-Stream
    return b"file content"

    Response Classes
JSONResponse
python
from flaxon import JSONResponse

@app.get("/json")
async def json_response():
    return JSONResponse(
        {"status": "ok", "data": [1, 2, 3]},
        status_code=201,
        headers={"X-Custom": "value"},
    )
HTMLResponse
python
from flaxon import HTMLResponse

@app.get("/html")
async def html_response():
    return HTMLResponse("<h1>Hello</h1>", status_code=200)
TextResponse
python
from flaxon import TextResponse

@app.get("/text")
async def text_response():
    return TextResponse("Plain text", status_code=200)
RedirectResponse
python
from flaxon import RedirectResponse

@app.get("/old")
async def redirect():
    return RedirectResponse("/new", status_code=301)

# Or use the Redirect helper
from flaxon.http.redirects import Redirect

@app.get("/temp")
async def temp_redirect():
    return Redirect.temporary("/new")
StreamingResponse
python
from flaxon import StreamingResponse

async def generate_data():
    for i in range(10):
        yield f"Data {i}\n".encode()

@app.get("/stream")
async def stream():
    return StreamingResponse(
        generate_data(),
        media_type="text/plain",
    )
Status Codes
python
from flaxon.http.status import OK, CREATED, NO_CONTENT, BAD_REQUEST, NOT_FOUND

@app.get("/ok")
async def ok_response():
    return {"status": "ok"}, OK

@app.post("/users")
async def create_user():
    return {"created": True}, CREATED

@app.delete("/users/<int:user_id>")
async def delete_user(user_id: int):
    return None, NO_CONTENT
Custom Headers
python
@app.get("/headers")
async def custom_headers():
    return JSONResponse(
        {"data": "value"},
        headers={
            "X-Custom-Header": "custom-value",
            "X-Rate-Limit": "100",
        },
    )
Cookies
python
@app.post("/login")
async def login():
    response = JSONResponse({"success": True})
    response.headers["set-cookie"] = "session_id=abc123; Path=/; HttpOnly"
    return response
Streaming Large Files
python
import aiofiles

async def stream_file(path: str):
    async with aiofiles.open(path, "rb") as f:
        while chunk := await f.read(8192):
            yield chunk

@app.get("/download/<path:file_path>")
async def download(file_path: str):
    return StreamingResponse(
        stream_file(file_path),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{file_path}"',
        },
    )
Custom Response Class
python
from flaxon import Response

class CSVResponse(Response):
    media_type = "text/csv; charset=utf-8"

    def __init__(self, data: list[list[str]], **kwargs):
        content = "\n".join(",".join(row) for row in data)
        super().__init__(content, **kwargs)

@app.get("/export")
async def export():
    data = [["Name", "Email"], ["Alice", "alice@example.com"]]
    return CSVResponse(data, status_code=200)
Full Example
python
from flaxon import Flaxon, JSONResponse, HTMLResponse, RedirectResponse, StreamingResponse
from flaxon.http.redirects import Redirect
from flaxon.http.status import CREATED

app = Flaxon("responses-demo")

@app.get("/")
async def home():
    return {"message": "Welcome to Flaxon"}

@app.get("/users")
async def list_users():
    return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

@app.post("/users", status_code=CREATED)
async def create_user(request):
    data = await request.json()
    return {"created": True, "user": data}

@app.get("/redirect")
async def redirect():
    return Redirect.permanent("/")

@app.get("/stream")
async def stream_data():
    async def generate():
        for i in range(100):
            yield f"{i}\n".encode()
    return StreamingResponse(generate(), media_type="text/plain")

@app.get("/custom")
async def custom():
    return JSONResponse(
        {"data": "custom"},
        status_code=202,
        headers={"X-Custom": "value"},
    )