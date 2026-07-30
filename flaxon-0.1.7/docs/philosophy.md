
---

## docs/philosophy.md

```markdown
# Philosophy

## Core Principles

Flaxon is built on a set of core principles that guide its design and development.

### 1. Simple Applications Remain Simple

Small applications should start in one file without generators or mandatory architecture. Flaxon provides a minimal entry point that lets you get started quickly.

```python
from flaxon import Flaxon

app = Flaxon("my-app")

@app.get("/")
async def home():
    return {"message": "Hello"}

    2. Large Applications Gain Structure
As your application grows, Flaxon provides optional structure without requiring a complete rewrite. You can introduce routers, services, middleware, and plugins incrementally.

python
from flaxon import Router

api = Router(prefix="/api/v1")

@api.get("/users")
async def list_users():
    return [{"id": 1, "name": "Alice"}]

app.include_router(api)
3. HTML Rendering is Optional
Flaxon treats JSON APIs as a first-class default. HTML rendering through Jinax is optional and lazily loaded.

python
# API-only - no template dependencies
@app.get("/api/users")
async def get_users():
    return [{"id": 1, "name": "Alice"}]

# With templates (optional)
from flaxon.jinax import Jinax
app.use_templates(Jinax("templates"))
4. Technology Neutrality
Flaxon does not care about your frontend, database, ORM, or client technology. Use React, Vue, Angular, Kotlin, Java, Flutter, or plain API clients. Use PostgreSQL, MongoDB, Redis, or custom storage.

5. Explicit and Debuggable
Framework APIs should be explicit enough to debug and profile without hidden magic. Flaxon's debugger explains failures in plain language with request context.

python
# Clear error messages
raise HTTPException(404, "User not found.", code="FX-USER-404")
Design Decisions
Why ASGI?
ASGI (Asynchronous Server Gateway Interface) is the modern standard for Python web servers. It supports HTTP, WebSocket, and lifespan events in a single interface, making it ideal for async-first applications.

Why Flask-Style Routes?
Flask-style route decorators are familiar to Python developers. They are intuitive, readable, and easy to learn.

Why Async-First?
Async I/O allows Flaxon to handle high-concurrency workloads efficiently. This is essential for real-time applications, chat services, and mobile backends.

Why No Built-in ORM?
Flaxon is technology neutral. Teams should be free to choose SQLAlchemy, SQLModel, Tortoise ORM, PyMongo, or custom solutions.

What Flaxon is Not
Not a full-stack framework — Flaxon handles the backend only

Not a replacement for Node.js — Flaxon is for Python teams

Not faster than Go or Rust — Flaxon optimizes for developer productivity

Not a compiled language — Flaxon is Python, with all the benefits and tradeoffs

When to Use Flaxon
Building APIs for React, Vue, or Angular applications

Developing mobile backends for Android or iOS

Creating real-time applications with WebSockets

Building microservices with Python

When you want technology freedom

When you want clear debugging and error messages

When you want to start simple and scale up

When Not to Use Flaxon
You need a full-stack framework with built-in admin or try do it if you want

You are building a simple static website or do as you please

You need a compiled language for performance-critical workloads

You want a framework with a very large ecosystem