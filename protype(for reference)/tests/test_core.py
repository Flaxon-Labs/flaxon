from flaxon import Flaxon, Router
from flaxon.testing import TestClient


def test_basic_json_route():
    app = Flaxon("test")

    @app.get("/")
    async def home():
        return {"message": "hello"}

    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "hello"}
    assert "x-request-id" in response.headers


def test_typed_route_and_url_for():
    app = Flaxon("test")

    @app.get("/users/<int:user_id>", name="users.detail")
    async def user(user_id: int):
        return {"id": user_id}

    response = TestClient(app).get("/users/42")
    assert response.json() == {"id": 42}
    assert app.url_for("users.detail", user_id=9) == "/users/9"


def test_router_prefix():
    app = Flaxon("test")
    router = Router(prefix="/api/v1")

    @router.get("/status")
    async def status():
        return {"ok": True}

    app.include_router(router)
    assert TestClient(app).get("/api/v1/status").json() == {"ok": True}
