# Testing

## Overview

Flaxon provides comprehensive testing utilities including synchronous and asynchronous test clients, WebSocket testing, fixtures, and assertions.

## Installation

```bash
pip install flaxon[dev]

Basic Test Client
python
from flaxon import Flaxon
from flaxon.testing import TestClient

def test_basic_route():
    app = Flaxon("test-app")

    @app.get("/")
    async def home():
        return {"message": "Hello"}

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}
Async Test Client
python
import pytest
from flaxon.testing import AsyncTestClient

@pytest.mark.asyncio
async def test_async_route():
    app = Flaxon("test-app")

    @app.get("/")
    async def home():
        return {"message": "Hello"}

    client = AsyncTestClient(app)
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}
Testing Different HTTP Methods
python
def test_all_methods():
    app = Flaxon("test-app")

    @app.get("/get")
    async def get_route():
        return {"method": "GET"}

    @app.post("/post")
    async def post_route():
        return {"method": "POST"}

    @app.put("/put")
    async def put_route():
        return {"method": "PUT"}

    @app.delete("/delete")
    async def delete_route():
        return {"method": "DELETE"}

    client = TestClient(app)

    assert client.get("/get").json()["method"] == "GET"
    assert client.post("/post").json()["method"] == "POST"
    assert client.put("/put").json()["method"] == "PUT"
    assert client.delete("/delete").json()["method"] == "DELETE"
Testing Request Body
python
def test_request_body():
    app = Flaxon("test-app")

    @app.post("/users")
    async def create_user(request):
        data = await request.json()
        return {"received": data}

    client = TestClient(app)
    response = client.post("/users", json_data={"name": "Alice", "age": 30})

    assert response.status_code == 200
    assert response.json()["received"] == {"name": "Alice", "age": 30}
Testing Query Parameters
python
def test_query_params():
    app = Flaxon("test-app")

    @app.get("/search")
    async def search(request):
        q = request.query.get("q")
        page = request.query.get("page", 1)
        return {"q": q, "page": page}

    client = TestClient(app)
    response = client.get("/search", query={"q": "test", "page": 2})

    assert response.json()["q"] == "test"
    assert response.json()["page"] == 2
Testing Headers
python
def test_headers():
    app = Flaxon("test-app")

    @app.get("/headers")
    async def get_headers(request):
        return {"user_agent": request.headers.get("user-agent")}

    client = TestClient(app)
    response = client.get("/headers", headers={"User-Agent": "TestClient/1.0"})

    assert response.json()["user_agent"] == "TestClient/1.0"
Testing Cookies
python
def test_cookies():
    app = Flaxon("test-app")

    @app.get("/cookies")
    async def get_cookies(request):
        return {"session": request.cookies.get("session")}

    client = TestClient(app)
    response = client.get("/cookies", headers={"Cookie": "session=abc123"})

    assert response.json()["session"] == "abc123"
Testing Validation
python
from flaxon.validation import Schema, fields

class CreateUser(Schema):
    name = fields.String(required=True, min_length=2)
    email = fields.Email(required=True)

def test_validation():
    app = Flaxon("test-app")

    @app.post("/users")
    async def create_user(data: CreateUser):
        return {"user": data.to_dict()}

    client = TestClient(app)

    # Valid data
    response = client.post("/users", json_data={"name": "Alice", "email": "alice@example.com"})
    assert response.status_code == 200

    # Invalid data
    response = client.post("/users", json_data={"name": "A", "email": "invalid"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "FX-VAL-001"
Testing WebSockets
python
import pytest
from flaxon.testing import AsyncWebSocketClient

@pytest.mark.asyncio
async def test_websocket():
    app = Flaxon("test-app")

    @app.websocket("/ws/echo")
    async def echo(socket):
        await socket.accept()
        async for message in socket.iter_json():
            await socket.send_json({"echo": message})

    client = AsyncWebSocketClient(app)
    await client.connect("/ws/echo")

    await client.send_json({"message": "Hello"})
    response = await client.receive_json()

    assert response == {"echo": {"message": "Hello"}}

    await client.disconnect()
Testing with Fixtures
python
import pytest
from flaxon import Flaxon
from flaxon.testing import TestClient

@pytest.fixture
def app():
    app = Flaxon("test-app")

    @app.get("/")
    async def home():
        return {"message": "Hello"}

    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_with_fixtures(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}
Testing Database
python
import pytest
from flaxon.database import DatabaseManager
from flaxon.database.adapters.sqlite import SQLiteAdapter

@pytest.fixture
async def db():
    adapter = SQLiteAdapter(database=":memory:")
    manager = DatabaseManager(adapter)
    await manager.initialize()

    await manager.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)

    yield manager

    await manager.close()

@pytest.mark.asyncio
async def test_database(db):
    await db.execute("INSERT INTO users (name) VALUES (?)", "Alice")
    row = await db.fetch_one("SELECT * FROM users WHERE name = ?", "Alice")

    assert row["name"] == "Alice"
Testing Authentication
python
from flaxon.security import JWTBackend, login_required

def test_authentication():
    app = Flaxon("test-app")
    backend = JWTBackend(secret_key="test-secret")

    @app.post("/login")
    async def login(request):
        data = await request.json()
        token = await backend.create_token({"username": data["username"]})
        return {"token": token}

    @app.get("/protected")
    @login_required
    async def protected(request):
        return {"ok": True}

    client = TestClient(app)

    # Login
    response = client.post("/login", json_data={"username": "alice"})
    token = response.json()["token"]

    # Access protected route
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    # Unauthorized access
    response = client.get("/protected")
    assert response.status_code == 401
Using Assertions
python
from flaxon.testing import Assertions

def test_assertions():
    app = Flaxon("test-app")

    @app.get("/users")
    async def get_users():
        return [{"id": 1, "name": "Alice"}]

    @app.get("/error")
    async def error():
        return {"error": {"code": "FX-ERROR"}}, 400

    client = TestClient(app)

    # Assert status
    response = client.get("/users")
    Assertions.assert_status(response, 200)

    # Assert JSON
    data = Assertions.assert_json(response)
    assert data[0]["name"] == "Alice"

    # Assert JSON array
    data = Assertions.assert_json_array(response)
    assert len(data) == 1

    # Assert error
    response = client.get("/error")
    Assertions.assert_error_code(response.json(), "FX-ERROR")
Mocking
python
from flaxon.testing import MockRegistry

def test_mocking():
    registry = MockRegistry()

    mock_db = registry.register("db")
    mock_db.return_value = [{"id": 1, "name": "Alice"}]

    app = Flaxon("test-app")

    @app.get("/users")
    async def get_users():
        return mock_db()

    client = TestClient(app)
    response = client.get("/users")

    mock_db.assert_called_once()
    assert response.json() == [{"id": 1, "name": "Alice"}]
Factory Pattern
python
from flaxon.testing import Factory

class UserFactory(Factory):
    def build(self, **kwargs):
        return {
            "id": self.sequence("user_id"),
            "name": kwargs.get("name", self.random_string()),
            "email": kwargs.get("email", self.random_email()),
            "age": kwargs.get("age", self.random_int(13, 120)),
        }

def test_factory():
    factory = UserFactory()
    user = factory.build(name="Alice")

    assert user["name"] == "Alice"
    assert user["email"].endswith("@example.com")
    assert 13 <= user["age"] <= 120
Complete Test Example
python
import pytest
from flaxon import Flaxon, HTTPException
from flaxon.testing import TestClient, AsyncTestClient
from flaxon.validation import Schema, fields

app = Flaxon("test-app")

class CreateUser(Schema):
    name = fields.String(required=True, min_length=2)
    email = fields.Email(required=True)

users = []

@app.get("/")
async def home():
    return {"message": "Welcome"}

@app.get("/users")
async def list_users():
    return users

@app.post("/users")
async def create_user(data: CreateUser):
    user = data.to_dict()
    user["id"] = len(users) + 1
    users.append(user)
    return {"created": True, "user": user}

@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    for user in users:
        if user["id"] == user_id:
            return user
    raise HTTPException(404, "User not found")

@pytest.fixture
def client():
    return TestClient(app)

def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome"

def test_list_users_empty(client):
    response = client.get("/users")
    assert response.status_code == 200
    assert response.json() == []

def test_create_user(client):
    response = client.post("/users", json_data={"name": "Alice", "email": "alice@example.com"})
    assert response.status_code == 200
    assert response.json()["created"] is True
    assert response.json()["user"]["name"] == "Alice"

def test_create_user_validation_error(client):
    response = client.post("/users", json_data={"name": "A", "email": "invalid"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "FX-VAL-001"

def test_get_user(client):
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Alice"

def test_get_user_not_found(client):
    response = client.get("/users/999")
    assert response.status_code == 404