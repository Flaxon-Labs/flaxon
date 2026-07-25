import pytest

from flaxon import Flaxon
from flaxon.middleware import CORSMiddleware, Middleware, RequestIDMiddleware, SecurityHeadersMiddleware
from flaxon.security import RateLimitMiddleware
from flaxon.testing import TestClient


class CustomMiddleware(Middleware):
    def __init__(self, app, header_name="x-custom"):
        super().__init__(app)
        self.header_name = header_name

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((self.header_name.encode(), b"custom-value"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


@pytest.fixture
def app_with_middleware():
    app = Flaxon("test-middleware", debug=True)

    app.add_middleware(RequestIDMiddleware, header_name="x-request-id")
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allowed_origins=["https://example.com"],
        allow_credentials=True,
    )
    app.add_middleware(CustomMiddleware, header_name="x-custom")
    app.add_middleware(RateLimitMiddleware, requests=10, window_seconds=60)

    @app.get("/")
    async def home():
        return {"message": "Hello"}

    @app.get("/rate-limit")
    async def rate_limit():
        return {"status": "ok"}

    return app


def test_middleware_order(app_with_middleware):
    client = TestClient(app_with_middleware)
    response = client.get("/")

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert "x-custom" in response.headers
    assert response.headers["x-custom"] == "custom-value"
    assert "x-content-type-options" in response.headers
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "https://example.com"


def test_cors_preflight(app_with_middleware):
    client = TestClient(app_with_middleware)

    headers = {"Origin": "https://example.com"}
    response = client.options("/", headers=headers)

    assert response.status_code == 204
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-credentials" in response.headers


def test_cors_preflight_unauthorized_origin(app_with_middleware):
    client = TestClient(app_with_middleware)

    headers = {"Origin": "https://unauthorized.com"}
    response = client.options("/", headers=headers)

    assert response.status_code == 204
    assert "access-control-allow-origin" not in response.headers


def test_rate_limit(app_with_middleware):
    client = TestClient(app_with_middleware)

    for _ in range(10):
        response = client.get("/rate-limit")
        assert response.status_code == 200

    response = client.get("/rate-limit")
    assert response.status_code == 429
    result = response.json()
    assert result["error"]["code"] == "FX-RATE-001"


def test_middleware_removal():
    app = Flaxon("test")

    app.add_middleware(CustomMiddleware, header_name="x-custom")
    app.add_middleware(RequestIDMiddleware)

    @app.get("/")
    async def home():
        return {"message": "Hello"}

    client = TestClient(app)
    response = client.get("/")
    assert "x-request-id" in response.headers
    assert "x-custom" in response.headers


def test_middleware_with_custom_headers():
    app = Flaxon("test")

    app.add_middleware(
        SecurityHeadersMiddleware,
        headers={
            "x-custom-header": "custom-value",
            "x-another-header": "another-value",
        },
    )

    @app.get("/")
    async def home():
        return {"message": "Hello"}

    client = TestClient(app)
    response = client.get("/")

    assert response.headers.get("x-custom-header") == "custom-value"
    assert response.headers.get("x-another-header") == "another-value"