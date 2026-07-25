import pytest

from flaxon import Flaxon
from flaxon.http import Request
from flaxon.security import CSRF, CSRFMiddleware
from flaxon.testing import TestClient


def test_csrf_token_generation():
    csrf = CSRF(secret_key="test-secret")

    token = csrf.generate_token()
    assert token is not None
    assert len(token.split(".")) == 3


def test_csrf_token_verification():
    csrf = CSRF(secret_key="test-secret")

    token = csrf.generate_token()
    assert csrf.verify_token(token) is True


def test_csrf_token_invalid():
    csrf = CSRF(secret_key="test-secret")

    assert csrf.verify_token("invalid.token.format") is False
    assert csrf.verify_token("") is False


def test_csrf_token_expired():
    import time

    csrf = CSRF(secret_key="test-secret")

    token = csrf.generate_token()

    original_time = time.time

    class MockTime:
        @staticmethod
        def time():
            return original_time() + 4000

    time.time = MockTime.time

    try:
        assert csrf.verify_token(token) is False
    finally:
        time.time = original_time


def test_csrf_middleware_get_request():
    app = Flaxon("test-csrf")
    app.add_middleware(CSRFMiddleware, secret_key="test-secret")

    @app.get("/")
    async def home():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_csrf_middleware_post_without_token():
    app = Flaxon("test-csrf")
    app.add_middleware(CSRFMiddleware, secret_key="test-secret")

    @app.post("/submit")
    async def submit(request):
        data = await request.json()
        return {"ok": True}

    client = TestClient(app)
    response = client.post("/submit", json_data={"data": "test"})
    assert response.status_code == 403
    result = response.json()
    assert result["error"]["code"] == "FX-CSRF-001"


def test_csrf_middleware_post_with_valid_token():
    app = Flaxon("test-csrf")
    csrf = CSRF(secret_key="test-secret")
    app.add_middleware(CSRFMiddleware, secret_key="test-secret")

    @app.post("/submit")
    async def submit(request):
        data = await request.json()
        return {"ok": True, "data": data}

    token = csrf.generate_token()

    client = TestClient(app)
    response = client.post(
        "/submit",
        json_data={"data": "test"},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["ok"] is True


def test_csrf_middleware_post_with_invalid_token():
    app = Flaxon("test-csrf")
    app.add_middleware(CSRFMiddleware, secret_key="test-secret")

    @app.post("/submit")
    async def submit(request):
        return {"ok": True}

    client = TestClient(app)
    response = client.post(
        "/submit",
        json_data={"data": "test"},
        headers={"X-CSRF-Token": "invalid-token"},
    )
    assert response.status_code == 403


def test_csrf_middleware_post_with_cookie_token():
    app = Flaxon("test-csrf")
    app.add_middleware(CSRFMiddleware, secret_key="test-secret", cookie_name="_csrf")

    @app.post("/submit")
    async def submit(request):
        return {"ok": True}

    csrf = CSRF(secret_key="test-secret")
    token = csrf.generate_token()

    client = TestClient(app)
    response = client.post(
        "/submit",
        json_data={"data": "test"},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 200
