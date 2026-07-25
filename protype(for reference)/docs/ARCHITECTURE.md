# Architecture

Flaxon is an ASGI application. The core dispatches HTTP, WebSocket, and lifespan scopes. Middleware wraps the dispatcher. HTTP requests are matched by the router, endpoint parameters are resolved, schema annotations are validated, and returned values are converted to Response objects.

Jinax is optional and imports Jinja2 lazily. The core does not require a database, ORM, frontend framework, or mobile technology.

## Intended dependency direction

Client -> HTTP/WebSocket -> Flaxon transport -> application services -> repositories/infrastructure.

Business services should avoid direct dependence on Request where practical so they can be reused by HTTP routes, WebSocket handlers, jobs, and tests.
