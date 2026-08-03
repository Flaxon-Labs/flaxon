# Application API

# Flaxon

The main application class.

---

## Constructor

```python
Flaxon(
    name: str,
    *,
    debug: bool | None = None,
    config: dict[str, Any] | None = None
)
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | Application name |
| `debug` | `bool \| None` | Enable debug mode |
| `config` | `dict[str, Any] \| None` | Configuration dictionary |

---

# Routing Methods

## route

```python
route(
    path: str,
    *,
    methods: set[str] | list[str] | tuple[str, ...] = ("GET",),
    name: str | None = None
) -> Callable
```

Register a route with custom HTTP methods.

---

## get

```python
get(
    path: str,
    *,
    name: str | None = None
) -> Callable
```

Register a GET route.

---

## post

```python
post(
    path: str,
    *,
    name: str | None = None
) -> Callable
```

Register a POST route.

---

## put

```python
put(
    path: str,
    *,
    name: str | None = None
) -> Callable
```

Register a PUT route.

---

## patch

```python
patch(
    path: str,
    *,
    name: str | None = None
) -> Callable
```

Register a PATCH route.

---

## delete

```python
delete(
    path: str,
    *,
    name: str | None = None
) -> Callable
```

Register a DELETE route.

---

## head

```python
head(
    path: str,
    *,
    name: str | None = None
) -> Callable
```

Register a HEAD route.

---

## options

```python
options(
    path: str,
    *,
    name: str | None = None
) -> Callable
```

Register an OPTIONS route.

---

## websocket

```python
websocket(
    path: str,
    *,
    name: str | None = None
) -> Callable
```

Register a WebSocket route.

---

## include_router

```python
include_router(router: Router) -> None
```

Include routes from another router.

---

## url_for

```python
url_for(
    name: str,
    **params: Any
) -> str
```

Generate a URL for a named route.

---

# Middleware Methods

## add_middleware

```python
add_middleware(
    middleware_class: type[Any],
    **options: Any
) -> None
```

Add middleware to the application.

---

# Template Methods

## use_templates

```python
use_templates(engine: Any) -> None
```

Configure Jinax template engine.

---

# Lifecycle Methods

## on_startup

```python
on_startup(
    callback: Callable[..., Any]
) -> Callable[..., Any]
```

Register a startup callback.

---

## on_shutdown

```python
on_shutdown(
    callback: Callable[..., Any]
) -> Callable[..., Any]
```

Register a shutdown callback.

---

# Server Methods

## run

```python
run(
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    reload: bool = False,
    workers: int = 1
) -> None
```

Run the application using Uvicorn.

---

# Properties

## routes

```python
@property
def routes(self) -> list[Any]
```

Get all registered HTTP routes.

---

## websocket_routes

```python
@property
def websocket_routes(self) -> list[Any]
```

Get all registered WebSocket routes.

---

## state

```python
@property
def state(self) -> State
```

Get the application state container.

---

## config

```python
@property
def config(self) -> Config
```

Get the application configuration.

---

## debug

```python
@property
def debug(self) -> bool
```

Check if debug mode is enabled.

---

## name

```python
@property
def name(self) -> str
```

Get the application name.

---

# Config

Configuration container.

---

## Constructor

```python
Config(
    values: Mapping[str, Any] | None = None,
    *,
    prefix: str = "FLAXON_"
)
```

---

# Config Methods

## get_env

```python
get_env() -> str
```

Get the current environment name.

---

## is_development

```python
is_development() -> bool
```

Check if the environment is development.

---

## is_testing

```python
is_testing() -> bool
```

Check if the environment is testing.

---

## is_staging

```python
is_staging() -> bool
```

Check if the environment is staging.

---

## is_production

```python
is_production() -> bool
```

Check if the environment is production.

---

## is_debug

```python
is_debug() -> bool
```

Check if debug mode is enabled.

---

## get_secret_key

```python
get_secret_key() -> str | None
```

Get the secret key.

---

## get_allowed_hosts

```python
get_allowed_hosts() -> list[str]
```

Get the list of allowed hosts.

---

## get_max_body_size

```python
get_max_body_size() -> int
```

Get the maximum body size in bytes.

---

## to_dict

```python
to_dict() -> dict[str, Any]
```

Convert configuration to a plain dictionary.

---

# State

Application state container.

---

# State Methods

## get

```python
get(
    name: str,
    default: Any = None
) -> Any
```

Get a state attribute with a default value.

---

## setdefault

```python
setdefault(
    name: str,
    default: Any
) -> Any
```

Set a state attribute if it does not already exist.

---

## update

```python
update(
    **kwargs: Any
) -> None
```

Update state with multiple attributes.

---

## to_dict

```python
to_dict() -> dict[str, Any]
```

Convert state to a dictionary.

---

## clear

```python
clear() -> None
```

Clear all state attributes.