# Routing

## Overview

Routing in Flaxon is designed to be intuitive and familiar. Routes are defined using decorators on your Flaxon application instance or on routers.

## Basic Routes

```python
from flaxon import Flaxon

app = Flaxon("my-app")

@app.get("/")
async def home():
    return {"message": "Hello"}

@app.post("/users")
async def create_user():
    return {"created": True}

@app.put("/users/<int:user_id>")
async def update_user(user_id: int):
    return {"updated": True, "id": user_id}

@app.delete("/users/<int:user_id>")
async def delete_user(user_id: int):
    return {"deleted": True, "id": user_id}

    Route Methods
Flaxon supports all standard HTTP methods:

python
@app.get("/")
@app.post("/")
@app.put("/")
@app.patch("/")
@app.delete("/")
@app.head("/")
@app.options("/")
Path Parameters
Flask-Style Parameters
python
@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    return {"id": user_id}

@app.get("/posts/<slug:post_slug>")
async def get_post(post_slug: str):
    return {"slug": post_slug}

@app.get("/files/<path:file_path>")
async def get_file(file_path: str):
    return {"path": file_path}
Brace-Style Parameters
python
@app.get("/users/{user_id:int}")
async def get_user(user_id: int):
    return {"id": user_id}

@app.get("/posts/{post_slug:slug}")
async def get_post(post_slug: str):
    return {"slug": post_slug}
Supported Converters
Converter	Description	Example
str	String (default)	<name>
int	Integer	<int:user_id>
float	Float	<float:price>
path	Path with slashes	<path:file_path>
uuid	UUID	<uuid:token>
slug	Slug (a-z, 0-9, -, _)	<slug:post_slug>
Route Groups
Using Router
python
from flaxon import Router

api = Router(prefix="/api/v1")

@api.get("/users")
async def list_users():
    return [{"id": 1, "name": "Alice"}]

@api.post("/users")
async def create_user():
    return {"created": True}

app.include_router(api)
Using RouteGroup
python
from flaxon.routing import RouteGroup

group = RouteGroup(prefix="/admin")

@group.get("/dashboard")
async def dashboard():
    return {"admin": True}

@group.get("/users")
async def admin_users():
    return {"users": []}

app.include_router(group.as_router())
Nested Routers
python
v1 = Router(prefix="/v1")
v2 = Router(prefix="/v2")

@v1.get("/users")
async def users_v1():
    return {"version": "v1", "users": []}

@v2.get("/users")
async def users_v2():
    return {"version": "v2", "users": []}

api = Router(prefix="/api")
api.include_router(v1)
api.include_router(v2)

app.include_router(api)
Named Routes
python
@app.get("/users/<int:user_id>", name="users.detail")
async def get_user(user_id: int):
    return {"id": user_id}

# Generate URL
url = app.url_for("users.detail", user_id=42)
# url == "/users/42"
Route Matching Order
Routes are matched in the order they are registered. More specific routes should be registered before more general routes.

python
# Specific route first
@app.get("/users/me")
async def get_current_user():
    return {"user": "current"}

# General route second
@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    return {"id": user_id}
Error Handling
python
from flaxon import HTTPException

@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    if user_id == 0:
        raise HTTPException(400, "Invalid user ID", code="FX-INVALID-ID")
    if user_id == 404:
        raise HTTPException(404, "User not found", code="FX-USER-404")
    return {"id": user_id, "name": f"User {user_id}"}
Mounting Sub-Applications
python
from flaxon.routing import Mount

admin_app = Flaxon("admin")

@admin_app.get("/")
async def admin_home():
    return {"admin": True}

app.include_router(Mount("/admin", admin_app))
Full Example
python
from flaxon import Flaxon, Router
from flaxon.routing import RouteGroup

app = Flaxon("routing-demo")

# Basic routes
@app.get("/")
async def home():
    return {"message": "Welcome"}

# Path parameters
@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    return {"id": user_id, "name": f"User {user_id}"}

# API router
api = Router(prefix="/api/v1")

@api.get("/products")
async def list_products():
    return [{"id": 1, "name": "Product A"}]

app.include_router(api)

# Admin group
admin = RouteGroup(prefix="/admin")

@admin.get("/dashboard")
async def admin_dashboard():
    return {"stats": {"users": 100, "orders": 50}}

app.include_router(admin.as_router())

# Named route
@app.get("/about", name="about")
async def about():
    return {"version": "1.0.0"}

# Generate URL
about_url = app.url_for("about")
Route Inspection
bash
# List all routes
flaxon routes app:app

# Output:
# Method      Path                      Name
# GET         /                         home
# GET         /users/<int:user_id>      get_user
# GET         /api/v1/products          list_products
# GET         /admin/dashboard          admin_dashboard
# GET         /about                    about