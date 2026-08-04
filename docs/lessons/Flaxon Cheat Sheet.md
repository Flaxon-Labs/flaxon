# Flaxon Cheat Sheet

Quick reference for everything the framework offers. For explanations, see [`features.md`](features.md).

## App & routes

```python
from flaxon import Flaxon
app = Flaxon("name", debug=True)

@app.get("/")            # also: .post .put .patch .delete
async def home(): return {"ok": True}

@app.get("/x/<int:id>")  # converters: int float str uuid path
async def x(id: int): return {"id": id}
```
Run: `flaxon run app:app --reload` or `uvicorn app:app`

## Params auto-resolved in handlers

`request` / `socket` · path params by name · `app.container` entries · `Schema`-typed body params

## Responses

`dict`/`list` → JSON · `str` → text · or explicit: `JSONResponse` `HTMLResponse` `TextResponse` `RedirectResponse(url, status_code=303)` `StreamingResponse`

## Middleware

```python
app.add_middleware(CORSMiddleware, allowed_origins=[...])
```
`RequestIDMiddleware` `SecurityHeadersMiddleware` (on by default) · `CORSMiddleware` `CompressionMiddleware` `TimeoutMiddleware` `TrustedHostsMiddleware` `BodyLimitMiddleware` `ProxyHeadersMiddleware` `RecoveryMiddleware` `MetricsMiddleware` — all in `flaxon.middleware.*` · `RateLimitMiddleware` `CSRFMiddleware` in `flaxon.security.*`

## Validation

```python
from flaxon.validation import Schema, fields
class In(Schema):
    name = fields.StrField(required=True, min_length=2)
    age  = fields.IntField(minimum=0)

@app.post("/x")
async def x(data: In): return data.to_dict()  # auto 422 on invalid
```
Fields: `StrField IntField FloatField BoolField EmailField DateField DateTimeField DecimalField UUIDField ListField ChoiceField NestedField`

## Sessions

```python
request.session["k"] = "v"   # dict-like, always available, cookie-backed
request.session.get("k")
```

## Dependency injection

```python
app.container.register_instance("name", value)
app.container.register_factory("Type", lambda: Type(), singleton=True)

async def handler(dep: Type): ...   # resolved by name, then by type
```

## Security

```python
from flaxon.security.password import PasswordHasher
h = PasswordHasher(); hashed = h.hash(pw); h.verify(pw, hashed)

from flaxon.security.jwt import JWT, jwt_required
app.jwt = JWT("real-secret")               # no default secret -- must set your own
token = app.jwt.encode({"user_id": "1"})

@app.get("/x")
@jwt_required
async def x(request): return request.user
```
Also: `role_required("x")` `permission_required("x")` `api_key_required()` + `APIKeyManager` — all in `flaxon.security.*`

## WebSockets

```python
@app.websocket("/ws/<room>")
async def ws(socket, room: str):
    await socket.accept()
    await socket.join(room)
    async for msg in socket.iter_json():
        await socket.broadcast_json(room, msg)
```
`.accept()` `.join(room)` `.leave(room)` `.receive_json()` `.send_json()` `.iter_json()` `.broadcast_json(room, data)` `.close(code, reason)`

## GraphQL

```python
from flaxon.graphql import GraphQLSchema, ObjectType, Field, Scalar
q = ObjectType("Query", {"hi": Field(Scalar("String"), resolver=lambda p,a,c,i: "hi")})
app.enable_graphql(GraphQLSchema(query=q))   # needs GraphQLSchema, NOT bare ObjectType
```
Routes: `POST /graphql` · playgrounds: `/graphql` `/graphql/graphiql` `/graphql/altair` · both `{ x }` and `query { x }` syntax work

## Admin panel

```python
admin = app.enable_admin()
admin.register(Model, list_display=["a","b"], fields=["a","b"])
```
Model needs (all optional, sync or async): `get_instances()` `get_instance(id)` `create_instance(data)` `update_instance(id,data)` `delete_instance(id)`

## OpenAPI docs

```python
app.enable_openapi(title="My API")   # -> /openapi.json /docs /redoc
```
CLI: `flaxon docs app:app -o openapi.json [--include-internal]` — pulls summary/description from docstrings, request schema from `Schema` classes, automatically

## Database

```python
from flaxon.database.adapters.sqlite import SQLiteAdapter   # + .redis .postgresql .mysql .mongodb .sqlalchemy
db = SQLiteAdapter(":memory:"); await db.connect()
await db.execute("...", *args)
await db.fetch_one/fetch_all/fetch_val("...", *args)
await db.begin(); await db.commit()  # or .rollback()
```

## Caching

```python
from flaxon.caching import Cache, cached_async
c = Cache(); await c.set("k","v",ttl=60); await c.get("k"); await c.increment("k")

@cached_async(ttl=60)
async def fn(x): ...
```

## Tasks

```python
from flaxon.tasks import TaskRegistry, TaskQueue, Worker, Task
registry.register("name", fn)
await queue.push(Task("name", fn, args=(...), kwargs={...}))
```
Run: `flaxon worker app:app --concurrency 4` / `flaxon schedule app:app`

## Events

```python
from flaxon.events import EventDispatcher, EventRegistry
registry.register("evt.name", callback)          # sync or async
await dispatcher.dispatch_async("evt.name", data) # fires all listeners
```
`dispatch_sync()` exists but silently skips async listeners

## Mail

```python
from flaxon.mail import Mailer, Email, Attachment
from flaxon.mail.adapters.console import ConsoleAdapter  # or .smtp
await Mailer(ConsoleAdapter()).send(Email(from_address=..., to=[...], subject=..., body=...))
```

## Templates (Jinax)

```python
app.use_templates(Jinax("templates", auto_reload=True))
return await request.render("page.html", {"key": "value"})
```
Real Jinja2, autoescaped.

## Testing

```python
from flaxon.testing import TestClient
c = TestClient(app)
c.get("/x"); c.post("/x", json_data={...})
c.request("POST", "/x", content="a=1", headers={"content-type": "application/x-www-form-urlencoded"})
```
No dedicated WebSocket test client — use a real connection for those.

## Debugging

`debug=True` → rich HTML traceback in browser, JSON+traceback for API clients, history at `/__debug__`. No setup needed.

## Health & metrics

`/health` `/health/live` `/health/ready` `/metrics` — all automatic. Register checks: `app.health.register(HealthCheck("name", fn))`. Populate metrics: `app.add_middleware(MetricsMiddleware, collector=app.metrics)`.

## Plugins

```python
from flaxon.plugins import SimplePlugin
await app.plugins.load_plugin(SimplePlugin(name="x", setup_func=lambda app: ...))
```
See [`plugins.md`](plugins.md) before building a real one — common mistakes documented there.

## Mounting other apps

```python
app.mount_asgi("/fastapi", real_fastapi_app)          # any real ASGI app, unmodified
app.mount_asgi("/flask", WSGIMiddleware(flask_app))   # WSGI needs a2wsgi
app.include_router(Mount("/sub", other_flaxon_app).as_router())  # Flaxon-to-Flaxon only
```

## CLI

| Command | Does |
|---|---|
| `run app:app --reload` | start dev server |
| `routes app:app` | list routes |
| `doctor app:app` | health check the app itself |
| `new NAME` | scaffold a project |
| `generate model NAME` | scaffold one component |
| `docs app:app` | export OpenAPI spec |
| `inspect app:app --middleware --config` | show app details |
| `build` | build wheel/sdist |
| `test` | run pytest |
| `shell app:app` | REPL with app loaded |
| `migrate --direction up` | run db migrations |
| `schedule app:app` | run due scheduled tasks |
| `worker app:app` | consume the task queue |
| `--version` | show installed version |

Full reference: [`cli.md`](cli.md).