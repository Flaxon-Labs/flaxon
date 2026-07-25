# Flaxon Documentation

Welcome to the Flaxon documentation. Flaxon is a **technology-neutral, async-first Python backend framework** that combines Flask-like ease with structured large-application development.

## What is Flaxon?

Flaxon is a Python backend framework for APIs, server-rendered websites, real-time applications, mobile backends, and structured enterprise systems. It addresses a recurring problem in Python web development: simple frameworks are easy to start but require significant manual architecture as applications grow, while larger frameworks provide structure by controlling more technical decisions.

### Core Principles

- **Simple applications remain simple** — Start in one file without generators or mandatory architecture
- **Large applications gain structure** — Introduce routers, services, middleware, and plugins as needed
- **HTML rendering is optional** — JSON APIs are a first-class default
- **Technology neutral** — Use any frontend, database, ORM, or client
- **Explicit APIs** — Debug and profile without hidden magic

## Key Features

| Feature | Description |
|---------|-------------|
| **Async-first ASGI** | Built for high-concurrency I/O workloads |
| **Flask-style routes** | Familiar and intuitive decorators |
| **Optional structure** | Start simple, scale to large applications |
| **Request validation** | Declarative schemas with automatic 422 responses |
| **WebSocket support** | Real-time communication with room broadcasting |
| **Jinax templates** | Optional Jinja2 integration (lazy-loaded) |
| **Middleware stack** | CORS, request IDs, security headers, rate limiting |
| **Readable debugger** | Explains failures in plain language |
| **CLI tools** | Run, inspect, doctor, and generate projects |
| **Testing utilities** | Sync and async test clients |

## Quick Example

```python
from flaxon import Flaxon

app = Flaxon("my-api", debug=True)

@app.get("/")
async def home():
    return {"message": "Hello from Flaxon"}

@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    return {"id": user_id, "name": "Example User"}
Getting Started
Installation — Install Flaxon

Quick Start — Build your first application

Philosophy — Understand the design principles

Architecture — Learn how Flaxon works

Documentation Sections
User Guide
Routing — Define routes and handle requests

Requests — Access request data

Responses — Return responses

Middleware — Add cross-cutting concerns

Validation — Validate request data

WebSockets — Real-time communication

Jinax — Optional HTML templates

Databases — Use any database

Authentication — Secure your application

Testing — Test your application

API Reference
Application — Flaxon class

Routing — Router, Route, converters

HTTP — Request, Response

WebSocket — WebSocket, Manager

Validation — Schema, fields

Security — Auth, JWT, CSRF

Jinax — Template engine

Deployment
Overview — Deploy Flaxon applications

Docker — Containerized deployment

Kubernetes — Kubernetes deployment

Cloud Platforms — AWS, GCP, Azure

Community
GitHub Issues

GitHub Discussions

License
Flaxon is released under the MIT License.