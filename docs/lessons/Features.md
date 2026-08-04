# Everything Flaxon Can Do

A complete map of the framework's features. Each section is runnable, minimal, and enough to get started — see the linked guide or API reference for full depth on anything.

## Core application & routing

```python
from flaxon import Flaxon

app = Flaxon("my-api", debug=True)

@app.get("/")
async def home():
    return {"message": "Hello"}

@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    return {"id": user_id}
```

`@app.get/post/put/patch/delete(path)` register routes. Path converters: `<int:x>`, `<float:x>`, `<str:x>` (default if untyped), `<uuid:x>`, `<path:x>` (matches slashes). Return a `dict`/`list` for automatic JSON, a `str` for text, or a `Response` subclass (`JSONResponse`, `HTMLResponse`, `TextResponse`, `RedirectResponse`, `StreamingResponse`) for full control.

Route handlers can declare any of these parameter types and Flaxon resolves them automatically: path parameters by name, `request` (or `socket`/`websocket` for WebSocket routes), anything registered on `app.container` (see Dependency Injection below), and `Schema`-typed parameters (see Validation below).

## Middleware

```python
from flaxon.middleware.cors import CORSMiddleware
from flaxon.middleware.compression import CompressionMiddleware
from flaxon.middleware.rate_limit import RateLimitMiddleware  # from flaxon.security.rate_limit

app.add_middleware(CORSMiddleware, allowed_origins=["https://example.com"])
app.add_middleware(CompressionMiddleware)
```

Built in and ready to add: `RequestIDMiddleware` and `SecurityHeadersMiddleware` (on by default), `CORSMiddleware`, `CompressionMiddleware`, `TimeoutMiddleware`, `TrustedHostsMiddleware`, `BodyLimitMiddleware`, `ProxyHeadersMiddleware`, `RecoveryMiddleware`, `RateLimitMiddleware`, `MetricsMiddleware`, `CSRFMiddleware`. First-added middleware runs outermost. Any exception a middleware raises (not just ones from your route handlers) is caught and converted into a clean error response automatically.

## Request validation

```python
from flaxon.validation import Schema, fields

class CreateUser(Schema):
    name = fields.StrField(required=True, min_length=2)
    email = fields.EmailField(required=True)
    age = fields.IntField(minimum=13, maximum=120)

@app.post("/users")
async def create_user(data: CreateUser):
    return {"success": True, "user": data.to_dict()}
```

Type a parameter as a `Schema` subclass and Flaxon parses the JSON body and validates it automatically — invalid data returns a `422` with field-level error messages, no manual checking needed. Available field types: `StrField`, `IntField`, `FloatField`, `BoolField`, `EmailField`, `DateField`, `DateTimeField`, `DecimalField`, `UUIDField`, `ListField`, `ChoiceField`, `NestedField`.

## Sessions

```python
@app.get("/visit")
async def visit(request):
    count = request.session.get("visits", 0) + 1
    request.session["visits"] = count
    return {"visits": count}
```

`request.session` is always available on every request — no setup required. Backed by a signed cookie by default; values persist across requests for the same client automatically.

## Dependency injection

```python
class EmailService:
    def send(self, to: str) -> str:
        return f"sent to {to}"

app.container.register_factory("EmailService", lambda: EmailService(), singleton=True)

@app.get("/notify")
async def notify(mailer: EmailService):  # resolved automatically by type
    return {"result": mailer.send("user@example.com")}
```

Register with `app.container.register_instance(name, value)` or `register_factory(name, factory, singleton=...)`. Parameters resolve by matching name first, then by type annotation.

## Security

```python
from flaxon.security.password import PasswordHasher
from flaxon.security.jwt import JWT, jwt_required
from flaxon.security.csrf import CSRFMiddleware
from flaxon.security.roles import role_required
from flaxon.security.permissions import permission_required
from flaxon.security.api_keys import api_key_required, APIKeyManager

# Password hashing
hasher = PasswordHasher()
hashed = hasher.hash("a password")
hasher.verify("a password", hashed)  # True

# JWT -- secret_key is required, no insecure default
app.jwt = JWT("your-app-specific-secret")
token = app.jwt.encode({"user_id": "7"})

@app.get("/protected")
@jwt_required
async def protected(request):
    return {"user": request.user}
```

Also available: `role_required("admin")`, `permission_required("edit")`, `api_key_required()` (with `APIKeyManager` for issuing/validating keys), `CSRFMiddleware` for form protection, `RateLimitMiddleware`. All the `*_required` decorators work correctly with Flaxon's parameter resolution — protected routes can still declare `request`, path params, etc. normally.

## WebSockets

```python
@app.websocket("/ws/chat/<room_id>")
async def chat(socket, room_id: str):
    await socket.accept()
    await socket.join(room_id)

    async for message in socket.iter_json():
        await socket.broadcast_json(room_id, {
            "event": "chat.message",
            "data": message,
            "room": room_id,
        })
```

`socket.accept()`, `.join(room)`/`.leave(room)`, `.receive_json()`/`.send_json()`, `.iter_json()` for a message loop, `.broadcast_json(room, data)` to fan out to everyone in a room, `.close(code, reason)`.

## GraphQL

```python
from flaxon.graphql import GraphQLSchema, ObjectType, Field, Scalar

def resolve_hello(parent, args, context, info):
    return "world"

query_type = ObjectType("Query", {"hello": Field(Scalar("String"), resolver=resolve_hello)})
app.enable_graphql(GraphQLSchema(query=query_type))
```

Registers `POST /graphql` for queries/mutations plus interactive playgrounds at `/graphql` (default), `/graphql/graphiql`, and `/graphql/altair`. Supports both `{ hello }` shorthand and named `query { ... }` syntax. **Note:** `enable_graphql()` takes a `GraphQLSchema`, not a bare `ObjectType` — wrap it.

## Admin panel

```python
admin = app.enable_admin()
admin.register(Product, list_display=["name", "price"], fields=["name", "price"])
```

A full list/detail/add/edit/delete dashboard at `/admin`, generated from your registered models. See the [Admin guide](admin.md) for the complete CRUD hook protocol.

## OpenAPI docs

```python
app.enable_openapi(title="My API")
```

Registers `/openapi.json`, `/docs` (Swagger UI), and `/redoc`. The spec is generated from your actual routes, endpoint docstrings, and `Schema` field definitions — see [`flaxon docs`](cli.md#flaxon-docs) for exporting it as a file you can also hand-edit.

## Database adapters

```python
from flaxon.database.adapters.sqlite import SQLiteAdapter
from flaxon.database.adapters.redis import RedisAdapter
from flaxon.database.adapters.postgresql import PostgreSQLAdapter
from flaxon.database.adapters.mysql import MySQLAdapter
from flaxon.database.adapters.mongodb import MongoDBAdapter
from flaxon.database.adapters.sqlalchemy import SQLAlchemyAdapter

db = SQLiteAdapter(":memory:")
await db.connect()
await db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
row = await db.fetch_one("SELECT * FROM users WHERE id = ?", 1)
```

Every adapter shares the same interface: `connect()`/`disconnect()`, `execute()`, `fetch_one()`/`fetch_all()`/`fetch_val()`, `begin()`/`commit()`/`rollback()` for transactions, `ping()`. `RedisAdapter` additionally supports `get`/`set`/`incr`/`hset`/`hgetall`/`lpush`/`lrange`/`sadd`/`smembers` and more for Redis's native data types.

## Caching

```python
from flaxon.caching import Cache, cached_async

cache = Cache()
await cache.set("key", "value", ttl=60)
await cache.get("key")
await cache.increment("counter")

@cached_async(ttl=60)
async def expensive(x):
    return x * 2  # only actually runs once per distinct argument, within the ttl
```

`Cache()` is in-memory by default. `caching/backends/` also has `MemoryBackend`, `FilesystemBackend`, and `RedisBackend` for standalone use, though note they aren't currently pluggable into `Cache` itself — they're independent implementations you'd use directly if you need them.

## Task queues

```python
from flaxon.tasks import TaskRegistry, TaskQueue, Worker, Task

async def send_email(to, subject):
    ...

registry = TaskRegistry()
registry.register("send_email", send_email)

queue = TaskQueue()
worker = Worker(registry, queue=queue, concurrency=2)

await queue.push(Task("send_email", send_email, args=("user@example.com",), kwargs={"subject": "hi"}))
```

Backends for `memory`, `database`, and `redis` in `tasks/backends/`. Run tasks continuously with `flaxon worker app:app`, or on a schedule with `flaxon schedule app:app`.

## Events

```python
from flaxon.events import EventDispatcher, EventRegistry

def on_user_created(event):
    print(f"new user: {event.data}")

registry = EventRegistry()
registry.register("user.created", on_user_created)

dispatcher = EventDispatcher(registry)
await dispatcher.dispatch_async("user.created", {"id": 1})
```

`dispatch_async()` fires all listeners (sync or async) concurrently. `dispatch_sync()` exists for non-async contexts but can't run async listeners — only sync ones fire.

## Mail

```python
from flaxon.mail import Mailer, Email, Attachment
from flaxon.mail.adapters.smtp import SMTPAdapter
from flaxon.mail.adapters.console import ConsoleAdapter  # prints instead of sending -- useful in dev

mailer = Mailer(ConsoleAdapter())
await mailer.send(Email(
    from_address="noreply@example.com",
    to=["user@example.com"],
    subject="Welcome",
    body="Thanks for signing up.",
    attachments=[Attachment(filename="receipt.txt", content=b"...")],
))
```

Also: `mailer.create_message()` for a fluent builder (`.from_address(...).to(...).subject(...).body(...)`), `mailer.send_many([...])`, and `mailer.send_template(...)` with `EmailTemplate`.

## Templating (Jinax)

```python
from flaxon.jinax import Jinax

app.use_templates(Jinax("templates", auto_reload=True))

@app.get("/")
async def home(request):
    return await request.render("home.html", {"title": "Welcome"})
```

Real Jinja2 under the hood (autoescaping included) — `Jinax("templates")` points at a folder of `.html` files, `request.render(name, context)` renders one.

## Testing utilities

```python
from flaxon.testing import TestClient

client = TestClient(app)
response = client.get("/users/1")
response = client.post("/users", json_data={"name": "Ada"})
response = client.request("POST", "/form", content="a=1&b=2", headers={"content-type": "application/x-www-form-urlencoded"})
```

Both `TestClient` (sync) and `AsyncTestClient` are available. There's currently no dedicated WebSocket test client — WebSocket routes need a real ASGI connection (e.g. the `websockets` library against a running server) to exercise fully.

## Debugging

In `debug=True` mode, unhandled errors render a full interactive traceback page in the browser (`Accept: text/html`) or structured JSON with a traceback for API clients, instead of a bare 500. A running history of errors is available at `/__debug__`.

## Health checks & metrics

```python
# both are already registered automatically -- no setup needed
```

`GET /health`, `/health/live`, `/health/ready` — the readiness check correctly reports unhealthy until your app finishes startup, and not-ready again during shutdown. Register your own checks with `app.health.register(HealthCheck("database", check_fn))`. `GET /metrics` exposes Prometheus-format metrics from `app.metrics`; add `MetricsMiddleware(collector=app.metrics)` to actually populate request counts and latency.

## Plugins

```python
from flaxon.plugins import SimplePlugin

def setup_hello(app):
    @app.get("/hello-plugin")
    async def hello_plugin():
        return {"from": "plugin"}

await app.plugins.load_plugin(SimplePlugin(name="hello", setup_func=setup_hello))
```

`Plugin` is the base class for building distributable, installable packages that extend a Flaxon app — see `flaxon-ffd` (bridging FastAPI/Flask/Django apps into Flaxon) as a real example of one.

## Mounting other apps

```python
from fastapi import FastAPI

fastapi_app = FastAPI()
app.mount_asgi("/fastapi", fastapi_app)  # a real, unmodified FastAPI app, running as-is
```

`mount_asgi(path, app)` delegates everything under that prefix straight to any ASGI-compatible app — FastAPI, Django (`get_asgi_application()`), or Flask wrapped with `a2wsgi.WSGIMiddleware`. For modularizing a large Flaxon app into sub-apps of your own, use `Mount`/`app.include_router(Mount(path, sub_app).as_router())` instead, which properly namespaces the routes under your own routing table.

## CLI

Full command reference: [`cli.md`](cli.md). Covers `run`, `routes`, `doctor`, `new`, `generate`, `docs`, `inspect`, `build`, `test`, `shell`, `migrate`, `schedule`, and `worker`.