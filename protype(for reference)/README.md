# Flaxon Framework Prototype

Flaxon is an async-first Python backend framework prototype designed around four ideas:

1. **Easy to learn:** Flask-style decorators and small applications.
2. **Ready to grow:** ASGI lifecycle, middleware, validation, WebSockets, testing, and a CLI.
3. **Technology freedom:** React, Vue, Android/Kotlin, Flutter, Java, C#, Rust, plain HTML, or any HTTP/WebSocket client can use the backend.
4. **Readable failures:** development errors include an error code, request ID, route context, and a cleaned traceback.

**Jinax is optional.** It is a Flaxon integration layer powered by Jinja2. API-only projects never import or load it.

## Install locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[standard,dev]"
```

Linux/macOS activation:

```bash
source .venv/bin/activate
python -m pip install -e '.[standard,dev]'
```

## Run the hello API

```powershell
flaxon run examples.hello_api.app:app --reload
```

Open:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/api/users/7`
- `http://127.0.0.1:8000/health`

## Run the Jinax website

```powershell
flaxon run examples.jinax_site.app:app --reload
```

## Run tests

```powershell
pytest
```

## Minimal application

```python
from flaxon import Flaxon

app = Flaxon("my-app")

@app.get("/")
async def home():
    return {"message": "Hello from Flaxon"}
```

## Validated endpoint

```python
from flaxon import Flaxon
from flaxon.validation import Schema, fields

app = Flaxon("users")

class CreateUser(Schema):
    name = fields.String(required=True, min_length=2)
    email = fields.Email(required=True)

@app.post("/users")
async def create_user(data: CreateUser):
    return {"name": data.name, "email": data.email}
```

## Important scope note

This repository is a serious working prototype, not a claim that every production concern is finished. Before a 1.0 release, Flaxon would need broader protocol conformance tests, security review, load testing, stable public APIs, database plugins, observability integrations, and complete documentation.
