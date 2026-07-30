
---

## docs/migration-guide.md

```markdown
# Migration Guide

## Overview

This guide helps you migrate from other frameworks to Flaxon.

## Migrating from Flask

### Route Decorators

Flask:
```python
@app.route("/users/<int:user_id>")
def get_user(user_id):
    return jsonify({"id": user_id})

Flaxon:

python
@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    return {"id": user_id}
Request and Response
Flask:

python
data = request.get_json()
return jsonify({"status": "ok"})
Flaxon:

python
data = await request.json()
return {"status": "ok"}
Validation
Flask:

python
# Manual validation
Flaxon:

python
class CreateUser(Schema):
    name = fields.String(required=True)
WebSockets
Flask:

python
# Requires Flask-SocketIO
Flaxon:

python
@app.websocket("/ws/chat")
async def chat(socket):
    await socket.accept()
Migrating from Django
Views
Django:

python
def get_user(request, user_id):
    return JsonResponse({"id": user_id})
Flaxon:

python
@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    return {"id": user_id}
Serializers
Django REST Framework:

python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name"]
Flaxon:

python
class UserSchema(Schema):
    id = fields.Integer()
    name = fields.String()
Migrating from FastAPI
Path Parameters
FastAPI:

python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id}
Flaxon:

python
@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    return {"id": user_id}
Validation
FastAPI:

python
class User(BaseModel):
    name: str
    email: EmailStr
Flaxon:

python
class User(Schema):
    name = fields.String(required=True)
    email = fields.Email(required=True)
Common Patterns
Database Connection
python
@app.on_startup
async def startup():
    app.state.db = await create_pool()

@app.on_shutdown
async def shutdown():
    await app.state.db.close()
Dependency Injection
python
from flaxon.dependency_injection import Container, inject

container = Container()
container.register_instance("db", db_pool)

@inject(container)
async def get_users(db):
    return await db.fetch_all("SELECT * FROM users")
Testing
python
from flaxon.testing import TestClient

def test_get_users():
    client = TestClient(app)
    response = client.get("/users")
    assert response.status_code == 200
Breaking Changes
0.1.0 to Future Versions
API may change before 1.0

Check CHANGELOG.md for updates

Use semantic versioning

Getting Help
GitHub Issues

Discussions