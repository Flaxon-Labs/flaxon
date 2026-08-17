
# Quick Start

Welcome to Flaxon.

This guide will help you create and run your first Flaxon application in just a few minutes.

---

# Create a Project

Create a new project directory:

```bash
mkdir my-flaxon-app
cd my-flaxon-app
````

---

## Create a Virtual Environment

Create and activate a Python virtual environment:

### Linux / macOS

```bash
python -m venv .venv

source .venv/bin/activate
```

### Windows

```bash
python -m venv .venv

.venv\Scripts\activate
```

---

## Install Flaxon

Install Flaxon with the standard dependencies:

```bash
pip install flaxon[standard]
```

---

# Create Your Application

Create a file called:

```
app.py
```

Add the following code:

```python
from flaxon import Flaxon


app = Flaxon(
    "hello-world",
    debug=True
)


@app.get("/")
async def home():
    return {
        "message": "Hello, World!"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "hello-world"
    }
```

---

# Run Your Application

Start the development server:

```bash
flaxon run app:app --reload
```

Your application will be available at:

```
http://localhost:8000
```

---

# Add a Route with Parameters

Flaxon supports typed route parameters.

Example:

```python
@app.get("/users/<int:user_id>")
async def get_user(user_id: int):

    return {
        "id": user_id,
        "name": f"User {user_id}"
    }
```

Visit:

```
http://localhost:8000/users/42
```

Response:

```json
{
    "id": 42,
    "name": "User 42"
}
```

---

# Add Validation

Flaxon provides schema-based request validation.

Example:

```python
from flaxon.validation import Schema, fields


class CreateUser(Schema):

    name = fields.StrField(
        required=True,
        min_length=2,
        max_length=80
    )

    email = fields.EmailField(
        required=True
    )

    age = fields.IntField(
        required=False,
        minimum=13,
        maximum=120
    )


@app.post("/users")
async def create_user(data: CreateUser):

    return {
        "success": True,
        "user": data.to_dict()
    }
```

---

# Add a WebSocket

Flaxon includes asynchronous WebSocket support.

Example:

```python
@app.websocket("/ws/echo")
async def echo(socket):

    await socket.accept()

    async for message in socket.iter_json():

        await socket.send_json({
            "echo": message
        })

    await socket.close()
```

---

# Complete Example

A complete Flaxon application:

```python
from flaxon import Flaxon
from flaxon.validation import Schema, fields
from flaxon.websocket import WebSocket


app = Flaxon(
    "my-app",
    debug=True
)


class CreateUser(Schema):

    name = fields.StrField(
        required=True,
        min_length=2
    )

    email = fields.EmailField(
        required=True
    )


@app.get("/")
async def home():

    return {
        "message": "Welcome to Flaxon!"
    }


@app.get("/users/<int:user_id>")
async def get_user(user_id: int):

    return {
        "id": user_id,
        "name": f"User {user_id}"
    }


@app.post("/users")
async def create_user(data: CreateUser):

    return {
        "success": True,
        "user": data.to_dict()
    }


@app.websocket("/ws/echo")
async def echo(socket: WebSocket):

    await socket.accept()

    async for message in socket.iter_json():

        await socket.send_json({
            "echo": message
        })

```

Run this application with `flaxon run app:app --reload` during development, or
with Uvicorn in production.

---

# Next Steps

Continue learning Flaxon:

* **Philosophy** — Understand Flaxon's design principles
* **Architecture** — Learn how Flaxon works internally
* **Configuration** — Configure your application
* **Migration Guide** — Move from Flask, Django, or FastAPI

---

# Need Help?

If you run into problems:

* Check the documentation
* Search existing GitHub issues
* Start a GitHub discussion
* Report bugs and feature requests
