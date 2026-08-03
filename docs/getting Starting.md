# Flaxon Documentation

Welcome to the official documentation for **Flaxon**, the **async-first, technology-neutral Python backend framework** for building modern APIs, server-rendered websites, WebSocket applications, and scalable backend services.

Flaxon combines the simplicity of Flask with the structure needed for large applications—without forcing you into a specific architecture, database, frontend, or deployment strategy.

---

# Why Flaxon?

Building Python web applications often means choosing between:

- Lightweight frameworks that become difficult to organize as projects grow.
- Large frameworks that require adopting a specific architecture and technology stack.

Flaxon bridges that gap.

You can begin with a single file and gradually add routers, services, middleware, plugins, and other components only when your application needs them.

---

# Core Principles

Flaxon is built around a few simple principles.

### 🚀 Async First

Built on ASGI and Python's `asyncio` for high-performance asynchronous applications.

### 🧩 Technology Neutral

Use the tools you prefer.

- Any frontend
- Any database
- Any ORM
- Any authentication library
- Any deployment platform

### 📦 Start Small

Create a working application in a single file.

### 📈 Scale Naturally

Introduce structure only when your project grows.

### 🔍 Explicit APIs

Minimal magic and predictable behavior make debugging easier.

### ⚡ Developer Friendly

Helpful errors, validation, routing, tooling, and CLI utilities built in.

---

# Features

| Feature | Description |
|---------|-------------|
| 🚀 **Async-first ASGI** | Built for high-concurrency applications |
| 🌐 **Flask-style Routing** | Familiar decorators with async support |
| 📦 **Scalable Architecture** | Start small and grow naturally |
| ✅ **Request Validation** | Declarative schemas with automatic validation |
| 🔌 **WebSocket Support** | Real-time communication with room broadcasting |
| 🧩 **Middleware** | CORS, authentication, logging, rate limiting, and more |
| 🎨 **Jinax Templates** | Optional server-side HTML rendering |
| 🐞 **Readable Debugger** | Clear and informative error pages |
| 🛠 **CLI Tools** | Create, run, inspect, and manage projects |
| 🧪 **Testing Utilities** | Built-in helpers for synchronous and asynchronous testing |
| 🔒 **Security Features** | Middleware, trusted proxies, and security headers |
| ⚙️ **Technology Neutral** | Compatible with your preferred tools and libraries |

---

# Quick Example

```python
from flaxon import Flaxon

app = Flaxon("my-api", debug=True)

@app.get("/")
async def home():
    return {
        "message": "Hello from Flaxon!"
    }


@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    return {
        "id": user_id,
        "name": "Example User"
    }
```

Run the application:

```bash
flaxon run app:app --reload
```

Open your browser or API client:

```
http://localhost:8000
```

---

# Documentation Guide

Whether you're building your first API or deploying a production system, this documentation will guide you through every part of the framework.

---

# Getting Started

If you're new to Flaxon, start here.

| Guide | Description |
|--------|-------------|
| **Installation** | Install Flaxon and create your first project |
| **Quick Start** | Build your first API in minutes |
| **Configuration** | Configure your application |
| **Philosophy** | Learn the ideas behind Flaxon |
| **Architecture** | Understand how the framework works |

---

# User Guide

Learn the core features of Flaxon.

| Topic | Description |
|--------|-------------|
| **Routing** | Register routes and URL parameters |
| **Requests** | Access request data |
| **Responses** | Return JSON, HTML, files, and streams |
| **Middleware** | Process requests and responses |
| **Validation** | Validate incoming data |
| **WebSockets** | Build real-time applications |
| **Jinax** | Render server-side HTML |
| **Authentication** | Secure your application |
| **Database Integration** | Use any ORM or database |
| **Testing** | Test your applications |
| **Configuration** | Manage application settings |
| **Deployment** | Prepare your application for production |

---

# API Reference

Detailed documentation for every major component.

| Module | Description |
|---------|-------------|
| **Application** | `Flaxon` application class |
| **Routing** | Routes, routers, and converters |
| **HTTP** | Requests and responses |
| **Validation** | Schemas and fields |
| **Middleware** | Middleware API |
| **WebSockets** | Real-time communication |
| **Security** | Authentication and security features |
| **Jinax** | Template engine |
| **CLI** | Command-line interface |
| **Utilities** | Helper classes and utilities |

---

# Deployment

Learn how to deploy Flaxon applications.

Topics include:

- Production configuration
- Docker
- Docker Compose
- Reverse proxies
- Health checks
- Scaling
- Cloud deployment
- Performance tuning
- Security recommendations

---

# Learn More

Explore the rest of the documentation to discover advanced features including:

- Middleware
- Background tasks
- Plugins
- Dependency injection
- Validation
- WebSockets
- Performance optimization
- Security
- Monitoring

---

# Community

Need help or want to contribute?

- 🐛 Report bugs through GitHub Issues
- 💬 Join community discussions
- ⭐ Star the project on GitHub
- 🤝 Contribute to the framework

---

# License

Flaxon is open source software released under the **MIT License**.

You are free to use, modify, and distribute Flaxon in personal and commercial projects in accordance with the license terms.

---

## Welcome to Flaxon

Whether you're building a REST API, a real-time WebSocket server, a server-rendered website, or a large enterprise backend, Flaxon provides the flexibility to start simple, scale confidently, and stay in control of your technology choices.

Happy coding! 🚀