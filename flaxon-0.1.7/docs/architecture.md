
---

## docs/architecture.md

```markdown
# Architecture

## Overview

Flaxon is an ASGI application that sits between clients and application services. The core handles protocol dispatch, routing, request/response objects, middleware, validation, errors, lifecycle events, and extension registration. Business logic remains in the developer's application services rather than in controllers or templates.

## Layered Architecture

┌─────────────────────────────────────────────┐
│ Client Layer │
│ Web, Android, iOS, CLI, Third-party │
├─────────────────────────────────────────────┤
│ Flaxon Framework Layer │
│ Protocol → Routing → Middleware → Handler │
├─────────────────────────────────────────────┤
│ Application Layer │
│ Controllers, Services, Schemas, Events │
├─────────────────────────────────────────────┤
│ Infrastructure Layer │
│ Database, Cache, Queue, Storage, Email │
└─────────────────────────────────────────────┘

text

## ASGI Application

Flaxon implements the ASGI 3.0 specification, handling:

- **HTTP** — Requests and responses
- **WebSocket** — Connections and messages
- **Lifespan** — Startup and shutdown events

```python
async def __call__(self, scope, receive, send):
    if scope["type"] == "http":
        await self._handle_http(scope, receive, send)
    elif scope["type"] == "websocket":
        await self._handle_websocket(scope, receive, send)
    elif scope["type"] == "lifespan":
        await self._handle_lifespan(receive, send)
Request Lifecycle
ASGI server creates a scope and forwards protocol messages

Middleware adds cross-cutting behavior (CORS, request ID, security headers)

Router matches path and method, converts parameters

Invoker resolves Request object, path parameters, and Schema annotations

Endpoint performs application logic and returns a response-compatible value

Flaxon converts dictionaries/lists to JSON and sends ASGI response messages

Exceptions are mapped to safe HTTP errors or debug information

Components
Application
The Flaxon class is the central registry and ASGI entry point. It owns configuration, routes, middleware definitions, lifecycle callbacks, application state, Jinax configuration, WebSocket room management, and the debugger.

Router
The router handles route registration, matching, and URL generation. It supports Flask-style and brace-style parameters.

Request and Response
The Request object exposes method, path, URL, headers, cookies, query values, path parameters, and async body methods. Responses are automatically converted from Python objects.

Middleware
Middleware wraps the ASGI application and handles cross-cutting concerns. The stack is built lazily and executed in order.

Validation
Declarative schemas validate request data and inject validated objects into route handlers.

WebSocket
WebSocket connections are managed with room-based broadcasting and a replaceable manager.

Jinax
Optional Jinja2 integration for server-side HTML rendering.

Dependency Direction
text
Client → HTTP/WebSocket → Flaxon transport → Application services → Repositories/Infrastructure
Business services should avoid direct dependence on Request where practical so they can be reused by HTTP routes, WebSocket handlers, jobs, and tests.

Concurrency Model
Flaxon uses Python's asyncio for non-blocking I/O. Async endpoints must avoid blocking calls. A synchronous database driver or long CPU task can block the event loop even when the route is declared with async def.