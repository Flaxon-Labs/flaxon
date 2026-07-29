# Flaxon

<p align="center">
  <img src="assets/flaxon.png" alt="Flaxon Logo" width="200"/>
</p>





# Flaxon
**A technology-neutral, async-first Python backend framework**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/aldanedev-create/Flaxon-Backend-Framework/blob/main/LICENSE) [![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Flaxon combines Flask-like ease, structured large-application development, async-first networking, readable debugging, optional Jinja2 templates, and complete freedom over your frontend and client technologies.

check out the docs on website below ⬇️⬇️⬇️⬇️

[Visit Flaxon Website](https://flaxon-website.vercel.app/)

```python
from flaxon import Flaxon

app = Flaxon("my-api", debug=True)

@app.get("/")
async def home():
    return {"message": "Hello from Flaxon"}

@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    return {"id": user_id, "name": "Example User"}
```

## Features

- **Async-first ASGI architecture** — Built for high-concurrency I/O workloads
- **Flask-style route decorators** — Familiar and intuitive
- **Optional modular structure** — Start simple, scale to large applications
- **Request validation** — Declarative schemas with automatic 422 responses
- **WebSocket support** — Real-time communication with room broadcasting
- **Jinax templates** — Optional Jinja2 integration (lazy-loaded)
- **Middleware stack** — CORS, request IDs, security headers, rate limiting
- **Readable debugger** — Explains failures in plain language
- **Technology neutral** — Use any frontend, database, ORM, or client
- **CLI tools** — Run, inspect, doctor, and generate projects
- **Testing utilities** — Sync and async test clients

## Quick Start

### Installation

```bash
pip install flaxon
```

Or with just the core:

```bash
pip install flaxon
```

### Create an application

```python
# app.py
from flaxon import Flaxon

app = Flaxon("hello-world", debug=True)

@app.get("/")
async def home():
    return {"message": "Hello, World!"}
```

### Run it

```bash
flaxon run app:app --reload
```

Visit http://localhost:8000 to see your API.

## Documentation

- [Full Documentation](docs/index.md)
- [Quick Start Guide](docs/quickstart.md)
- [API Reference](docs/api/)
- [Examples](docs/examples/)

### Example: Validation

```python
from flaxon import Flaxon
from flaxon.validation import Schema, fields

app = Flaxon("user-api")

class CreateUser(Schema):
    name = fields.String(required=True, min_length=2)
    email = fields.Email(required=True)
    age = fields.Integer(minimum=13, maximum=120)

@app.post("/users")
async def create_user(data: CreateUser):
    return {"success": True, "user": data.to_dict()}
```

### Example: WebSocket Chat

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

### Example: Optional Templates (Jinax)

```python
from flaxon import Flaxon
from flaxon.jinax import Jinax

app = Flaxon("website", debug=True)
app.use_templates(Jinax("templates", auto_reload=True))

@app.get("/")
async def home(request):
    return await request.render("home.html", {
        "title": "Welcome",
        "products": await product_service.list()
    })
```

## Philosophy

Simple applications remain simple; large applications gain structure without losing technology choice.

- Small applications start in one file without generators or mandatory architecture
- Large applications can introduce routers, services, middleware, and plugins
- HTML rendering is optional; JSON APIs are a first-class default
- Framework APIs are explicit enough to debug and profile without hidden magic

## Comparative Overview

| Feature | Flask | Django | Node.js | Flaxon |
|---|---|---|---|---|
| Async core | ❌ | ⚠️ | ✅ | ✅ |
| Flask-style routing | ✅ | ❌ | ⚠️ | ✅ |
| Optional structure | ❌ | ❌ | ⚠️ | ✅ |
| WebSocket support | ⚠️ | ❌ | ✅ | ✅ |
| Technology neutral | ✅ | ❌ | ✅ | ✅ |
| Readable debugging | ⚠️ | ⚠️ | ⚠️ | ✅ |
| Mobile backend ready | ⚠️ | ❌ | ✅ | ✅ |

## Production Readiness

Flaxon is currently in alpha. It is suitable for evaluation, experimentation, and learning. Production use is possible with careful testing and monitoring, but the API is not yet stable.

## Roadmap

- **0.2** — Protocol hardening, multipart uploads, ASGI conformance
- **0.3** — Sessions, OpenAPI, health checks, logging
- **0.4** — Plugin system, SQLAlchemy, Redis, authentication
- **0.5** — Distributed tasks, queues, Redis broadcast
- **1.0** — Stable API, security audit, production-ready

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).

```bash
git clone https://github.com/aldanedev-create/Flaxon-Backend-Framework.git
cd Flaxon-Backend-Framework
python -m venv .venv
source .venv/bin/activate
pip install -e ".[standard,dev]"
pytest
```

## License

MIT License — see [LICENSE](LICENSE) for details.

## Community

- [GitHub Issues](https://github.com/aldanedev-create/Flaxon-Backend-Framework/issues)
