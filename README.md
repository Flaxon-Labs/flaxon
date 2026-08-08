# Flaxon

 
 <p align="center">
  <img src="https://raw.githubusercontent.com/aldanedev-create/Flaxon-Backend-Framework/main/assets/flaxon.png" alt="flaxon Logo"
   width="200"/>
</p>


  
  <p align="center">
  <a href="https://pypi.org/project/flaxon/"><img src="https://img.shields.io/pypi/v/flaxon.svg" alt="PyPI version"></a>
  <a href="https://github.com/aldanedev-create/Flaxon-Backend-Framework/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-000000.svg" alt="Code style: ruff"></a>
</p>
 

Flaxon combines Flask-like ease, structured large-application development, async-first networking, readable debugging, optional Jinja2 templates, and complete freedom over your frontend and client technologies.

Author: Aldane Hutchinson

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

### 🚀 Installation

Install the published package via `pip`:

```bash
pip install flaxon
```

Or with just the core:

```bash
pip install flaxon

```
Or clone the repository locally:

Bash
git clone [https://github.com/aldanedev-create/Flaxon-Backend-Framework.git](https://github.com/aldanedev-create/Flaxon-Backend-Framework.git)

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


## 💡 Quick Start Example

Small example Flaxon application: a server-rendered HTML Todo list.

Uses Jinax (Flaxon's Jinja2 integration) to render `templates/todos.html`, plain HTML `<form>` elements for adding/toggling/deleting todos, and redirect-after-post so refreshing the page never resubmits a form.

### Run the App

```bash
flaxon run todo_html:app --reload
# or
uvicorn todo_html:app --reload

Then open http://localhost:8000/ in your browser

todo_html.py See Below: ⬇️⬇️
```python

from __future__ import annotations

from urllib.parse import parse_qs

from flaxon import Flaxon
from flaxon.exceptions import NotFound
from flaxon.http.response import RedirectResponse
from flaxon.jinax import Jinax

app = Flaxon("todo-html", debug=True)
app.use_templates(Jinax("templates", auto_reload=True))

todos: list[dict] = []
next_id = 1


@app.get("/")
async def home(request):
    return await request.render("todos.html", {"todos": todos})


@app.post("/todos")
async def create_todo(request):
    global next_id
    body = (await request.body()).decode("utf-8")
    form = parse_qs(body, keep_blank_values=True)
    title = form.get("title", [""])[0].strip()
    if title:
        todos.append({"id": next_id, "title": title, "done": False})
        next_id += 1
    return RedirectResponse("/", status_code=303)


@app.post("/todos/<int:todo_id>/toggle")
async def toggle_todo(todo_id: int):
    for todo in todos:
        if todo["id"] == todo_id:
            todo["done"] = not todo["done"]
            return RedirectResponse("/", status_code=303)
    raise NotFound(f"No todo with id {todo_id}")


@app.post("/todos/<int:todo_id>/delete")
async def delete_todo(todo_id: int):
    for i, todo in enumerate(todos):
        if todo["id"] == todo_id:
            todos.pop(i)
            return RedirectResponse("/", status_code=303)
    raise NotFound(f"No todo with id {todo_id}")


```



### `templates/todos.html` : See Below ⬇️⬇️💡

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Flaxon Todos</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 480px; margin: 3rem auto; color: #222; }
    h1 { font-size: 1.4rem; }
    form.add { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
    form.add input[type=text] { flex: 1; padding: 0.5rem; font-size: 1rem; }
    form.add button { padding: 0.5rem 1rem; }
    ul { list-style: none; padding: 0; }
    li { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0; border-bottom: 1px solid #eee; }
    li form { display: inline; margin: 0; }
    li .title { flex: 1; }
    li .done .title { text-decoration: line-through; color: #999; }
    button.link { background: none; border: none; color: #666; cursor: pointer; padding: 0.2rem 0.4rem; }
    button.link:hover { color: #000; }
    .empty { color: #888; }
  </style>
</head>
<body>
  <h1>Flaxon Todos</h1>

  <form class="add" method="post" action="/todos">
    <input type="text" name="title" placeholder="What needs doing?" required>
    <button type="submit">Add</button>
  </form>

  {% if todos %}
  <ul>
    {% for todo in todos %}
    <li class="{{ 'done' if todo.done else '' }}">
      <form method="post" action="/todos/{{ todo.id }}/toggle">
        <button type="submit" class="link">{{ "☑" if todo.done else "☐" }}</button>
      </form>
      <span class="title">{{ todo.title }}</span>
      <form method="post" action="/todos/{{ todo.id }}/delete">
        <button type="submit" class="link">✕</button>
      </form>
    </li>
    {% endfor %}
  </ul>
  {% else %}
  <p class="empty">No todos yet — add one above.</p>
  {% endif %}
</body>
</html>

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

Flaxon is currently in beta. It is suitable for evaluation, experimentation, and learning. Production use is possible with careful testing and monitoring.



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
