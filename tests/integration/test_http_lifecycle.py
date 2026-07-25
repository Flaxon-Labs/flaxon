import pytest

from flaxon import Flaxon
from flaxon.http import Request, Response
from flaxon.testing import TestClient


@pytest.fixture
def app() -> Flaxon:
    app = Flaxon("test-http-lifecycle", debug=True)

    @app.get("/")
    async def home():
        return {"message": "Hello, World!"}

    @app.get("/users/<int:user_id>")
    async def get_user(user_id: int):
        return {"id": user_id, "name": f"User {user_id}"}

    @app.post("/users")
    async def create_user(request: Request):
        data = await request.json()
        return {"created": True, "user": data}

    @app.put("/users/<int:user_id>")
    async def update_user(user_id: int, request: Request):
        data = await request.json()
        return {"updated": True, "id": user_id, "data": data}

    @app.delete("/users/<int:user_id>")
    async def delete_user(user_id: int):
        return {"deleted": True, "id": user_id}

    @app.get("/error")
    async def error():
        raise ValueError("Something went wrong")

    @app.get("/stream")
    async def stream():
        async def generate():
            yield b"chunk1"
            yield b"chunk2"
            yield b"chunk3"
        return StreamingResponse(generate())

    return app


def test_get_request(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


def test_get_with_path_params(client):
    response = client.get("/users/42")
    assert response.status_code == 200
    assert response.json() == {"id": 42, "name": "User 42"}


def test_post_request(client):
    data = {"name": "Alice", "email": "alice@example.com"}
    response = client.post("/users", json_data=data)
    assert response.status_code == 200
    result = response.json()
    assert result["created"] is True
    assert result["user"] == data


def test_put_request(client):
    data = {"name": "Updated Alice"}
    response = client.put("/users/42", json_data=data)
    assert response.status_code == 200
    result = response.json()
    assert result["updated"] is True
    assert result["id"] == 42
    assert result["data"] == data


def test_delete_request(client):
    response = client.delete("/users/42")
    assert response.status_code == 200
    result = response.json()
    assert result["deleted"] is True
    assert result["id"] == 42


def test_not_found(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404
    result = response.json()
    assert result["error"]["code"] == "FX-HTTP-404"


def test_method_not_allowed(client):
    response = client.post("/")
    assert response.status_code == 405
    result = response.json()
    assert result["error"]["code"] == "FX-HTTP-405"


def test_error_handling(client):
    response = client.get("/error")
    assert response.status_code == 500
    result = response.json()
    assert result["error"]["code"] == "FX-DEV-500"
    assert "debug" in result["error"]


def test_request_id_header(client):
    response = client.get("/")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) == 16


def test_security_headers(client):
    response = client.get("/")
    assert "x-content-type-options" in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "x-frame-options" in response.headers
    assert response.headers["x-frame-options"] == "DENY"


def test_lifecycle_startup_shutdown():
    startup_called = False
    shutdown_called = False

    app = Flaxon("test-lifecycle")

    @app.on_startup
    async def startup():
        nonlocal startup_called
        startup_called = True
        app.state.startup_value = "started"

    @app.on_shutdown
    async def shutdown():
        nonlocal shutdown_called
        shutdown_called = True
        app.state.shutdown_value = "stopped"

    import asyncio

    async def exercise_lifespan() -> None:
        messages = iter([
            {"type": "lifespan.startup"},
            {"type": "lifespan.shutdown"},
        ])
        sent = []

        async def receive():
            return next(messages)

        async def send(message):
            sent.append(message)

        await app({"type": "lifespan"}, receive, send)
        assert [message["type"] for message in sent] == [
            "lifespan.startup.complete",
            "lifespan.shutdown.complete",
        ]

    asyncio.run(exercise_lifespan())

    assert startup_called
    assert shutdown_called
