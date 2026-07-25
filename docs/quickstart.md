
---

## docs/quickstart.md

```markdown
# Quick Start

This guide will help you build your first Flaxon application in minutes.

## Create a Project

```bash
# Create a new project directory
mkdir my-flaxon-app
cd my-flaxon-app

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Flaxon
pip install flaxon[standard]

Create Your Application
Create a file called app.py:

python
from flaxon import Flaxon

app = Flaxon("hello-world", debug=True)

@app.get("/")
async def home():
    return {"message": "Hello, World!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "hello-world"}
Run Your Application
bash
flaxon run app:app --reload
Visit http://localhost:8000 to see your API.

Add a Route with Parameters
python
@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    return {"id": user_id, "name": f"User {user_id}"}
Visit http://localhost:8000/users/42

Add Validation
python
from flaxon.validation import Schema, fields

class CreateUser(Schema):
    name = fields.String(required=True, min_length=2, max_length=80)
    email = fields.Email(required=True)
    age = fields.Integer(required=False, minimum=13, maximum=120)

@app.post("/users")
async def create_user(data: CreateUser):
    return {"success": True, "user": data.to_dict()}
Add a WebSocket
python
@app.websocket("/ws/echo")
async def echo(socket):
    await socket.accept()
    async for message in socket.iter_json():
        await socket.send_json({"echo": message})
    await socket.close()
Complete Example
python
from flaxon import Flaxon
from flaxon.validation import Schema, fields
from flaxon.websocket import WebSocket

app = Flaxon("my-app", debug=True)

class CreateUser(Schema):
    name = fields.String(required=True, min_length=2)
    email = fields.Email(required=True)

@app.get("/")
async def home():
    return {"message": "Welcome to Flaxon!"}

@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    return {"id": user_id, "name": f"User {user_id}"}

@app.post("/users")
async def create_user(data: CreateUser):
    return {"success": True, "user": data.to_dict()}

@app.websocket("/ws/echo")
async def echo(socket: WebSocket):
    await socket.accept()
    async for message in socket.iter_json():
        await socket.send_json({"echo": message})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
Next Steps
Philosophy — Understand the design principles

Architecture — Learn how Flaxon works

Configuration — Configure your application