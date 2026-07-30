
---

## docs/api/routing.md

```markdown
# Routing API

## Router

The main router class.

### Constructor

```python
Router(prefix: str = "")

Parameter	Type	Description
prefix	str	Optional URL prefix
Methods
add_route
python
add_route(path: str, endpoint: Callable, *, methods: set[str] | list[str] | tuple[str, ...] = ("GET",), name: str | None = None) -> Route
Add an HTTP route.

add_websocket
python
add_websocket(path: str, endpoint: Callable, *, name: str | None = None) -> WebSocketRoute
Add a WebSocket route.

route
python
route(path: str, *, methods: set[str] | list[str] | tuple[str, ...] = ("GET",), name: str | None = None) -> Callable
Decorator for registering an HTTP route.

get
python
get(path: str, *, name: str | None = None) -> Callable
Register a GET route.

post
python
post(path: str, *, name: str | None = None) -> Callable
Register a POST route.

put
python
put(path: str, *, name: str | None = None) -> Callable
Register a PUT route.

patch
python
patch(path: str, *, name: str | None = None) -> Callable
Register a PATCH route.

delete
python
delete(path: str, *, name: str | None = None) -> Callable
Register a DELETE route.

head
python
head(path: str, *, name: str | None = None) -> Callable
Register a HEAD route.

options
python
options(path: str, *, name: str | None = None) -> Callable
Register an OPTIONS route.

websocket
python
websocket(path: str, *, name: str | None = None) -> Callable
Register a WebSocket route.

include_router
python
include_router(other: Router) -> None
Include routes from another router.

match
python
match(path: str, method: str) -> RouteMatch
Match an HTTP request to a route.

match_websocket
python
match_websocket(path: str) -> WebSocketMatch
Match a WebSocket connection to a route.

url_for
python
url_for(name: str, **params: Any) -> str
Generate a URL for a named route.

Properties
routes
python
@property
def routes(self) -> list[Route]
Get all HTTP routes.

websocket_routes
python
@property
def websocket_routes(self) -> list[WebSocketRoute]
Get all WebSocket routes.

route_count
python
@property
def route_count(self) -> int
Get the number of HTTP routes.

websocket_count
python
@property
def websocket_count(self) -> int
Get the number of WebSocket routes.

total_count
python
@property
def total_count(self) -> int
Get the total number of routes.

Route
HTTP route definition.

Attributes
Attribute	Type	Description
path	str	The URL path pattern
endpoint	Callable	The endpoint function
methods	set[str]	HTTP methods allowed
name	str | None	Route name
regex	re.Pattern	Compiled regex
parameters	list[str]	Parameter names
Methods
match_path
python
match_path(path: str) -> dict[str, Any] | None
Match a path against this route.

WebSocketRoute
WebSocket route definition.

Attributes
Attribute	Type	Description
path	str	The WebSocket URL path pattern
endpoint	Callable	The endpoint function
name	str | None	Route name
regex	re.Pattern	Compiled regex
parameters	list[str]	Parameter names
Methods
match_path
python
match_path(path: str) -> dict[str, Any] | None
Match a path against this route.

RouteMatch
Result of a route match.

Attributes
Attribute	Type	Description
route	Route	The matched route
params	dict[str, Any]	Path parameters
WebSocketMatch
Result of a WebSocket route match.

Attributes
Attribute	Type	Description
route	WebSocketRoute	The matched route
params	dict[str, Any]	Path parameters