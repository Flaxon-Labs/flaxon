
---

## docs/guides/requests.md

```markdown
# Requests

## Overview

The `Request` class provides access to all incoming request data including headers, cookies, query parameters, path parameters, and body content.

## Accessing the Request

```python
from flaxon import Request

@app.get("/")
async def home(request: Request):
    return {"method": request.method, "path": request.path}


Request Properties
python
@app.get("/info")
async def info(request: Request):
    return {
        "method": request.method,
        "path": request.path,
        "scheme": request.scheme,
        "host": request.host,
        "url": request.url,
        "client": request.client,
    }
Headers
python
@app.get("/headers")
async def get_headers(request: Request):
    return {
        "user_agent": request.headers.get("user-agent"),
        "content_type": request.headers.get("content-type"),
        "all_headers": dict(request.headers),
    }
Query Parameters
python
@app.get("/search")
async def search(request: Request):
    # Single value
    q = request.query.get("q")
    page = request.query.get("page", 1)

    # Multiple values
    filters = request.query.get_list("filter")

    # Type conversion
    page_int = request.query.get_int("page", 1)
    active = request.query.get_bool("active", False)

    return {
        "query": q,
        "page": page,
        "filters": filters,
    }
Cookies
python
@app.get("/profile")
async def profile(request: Request):
    session_id = request.cookies.get("session_id")
    theme = request.cookies.get("theme", "light")

    return {
        "session_id": session_id,
        "theme": theme,
    }
Reading the Body
JSON Body
python
@app.post("/users")
async def create_user(request: Request):
    data = await request.json()
    return {"received": data}
Text Body
python
@app.post("/text")
async def handle_text(request: Request):
    text = await request.text()
    return {"length": len(text)}
Raw Bytes
python
@app.post("/binary")
async def handle_binary(request: Request):
    data = await request.body()
    return {"size": len(data)}
Form Data
python
@app.post("/form")
async def handle_form(request: Request):
    form = await request.form()
    return {"name": form.get("name"), "email": form.get("email")}
Validation with Schemas
python
from flaxon.validation import Schema, fields

class CreateUser(Schema):
    name = fields.String(required=True, min_length=2)
    email = fields.Email(required=True)
    age = fields.Integer(required=False, minimum=13)

@app.post("/users")
async def create_user(data: CreateUser):
    # data is automatically validated
    return {"user": data.to_dict()}
Path Parameters
python
@app.get("/users/<int:user_id>/posts/<int:post_id>")
async def get_post(user_id: int, post_id: int):
    # Path parameters are injected automatically
    return {"user_id": user_id, "post_id": post_id}
Combining Parameters
python
from flaxon.validation import Schema, fields

class SearchParams(Schema):
    q = fields.String(required=True, min_length=1)
    page = fields.Integer(default=1, minimum=1)
    per_page = fields.Integer(default=20, minimum=1, maximum=100)

@app.get("/api/search")
async def search(request: Request, params: SearchParams):
    # Query parameters are validated
    return {
        "query": params.q,
        "page": params.page,
        "per_page": params.per_page,
    }
Request Context
python
from flaxon.application.context import request_context, get_current_request

@app.get("/context")
async def context_demo(request: Request):
    with request_context(request):
        # Store data in context
        from flaxon.application.context import get_request_context
        ctx = get_request_context()
        ctx.set("user_id", 123)

        # Retrieve current request
        current = get_current_request()
        return {"request_id": id(current)}
Full Example
python
from flaxon import Flaxon, Request
from flaxon.validation import Schema, fields

app = Flaxon("requests-demo")

class CreateUser(Schema):
    name = fields.String(required=True, min_length=2)
    email = fields.Email(required=True)

@app.get("/users/<int:user_id>")
async def get_user(user_id: int, request: Request):
    # Headers
    auth = request.headers.get("authorization")

    # Query parameters
    include_posts = request.query.get_bool("include_posts", False)

    return {
        "user_id": user_id,
        "authenticated": bool(auth),
        "include_posts": include_posts,
    }

@app.post("/users")
async def create_user(request: Request, data: CreateUser):
    # Body is automatically validated
    session_id = request.cookies.get("session_id")

    return {
        "success": True,
        "user": data.to_dict(),
        "session_id": session_id,
    }