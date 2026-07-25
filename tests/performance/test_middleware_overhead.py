import time

import pytest

from flaxon import Flaxon
from flaxon.middleware import CORSMiddleware, RequestIDMiddleware, SecurityHeadersMiddleware
from flaxon.security import RateLimitMiddleware
from flaxon.testing import TestClient


@pytest.fixture
def app_no_middleware():
    app = Flaxon("test-no-mw")

    @app.get("/")
    async def home():
        return {"ok": True}

    return app


@pytest.fixture
def app_with_middleware():
    app = Flaxon("test-with-mw")

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allowed_origins=["https://example.com"],
        allow_credentials=True,
    )
    app.add_middleware(RateLimitMiddleware, requests=1000, window_seconds=60)

    @app.get("/")
    async def home():
        return {"ok": True}

    return app


def test_no_middleware_overhead(app_no_middleware):
    client = TestClient(app_no_middleware)

    start = time.perf_counter()

    for _ in range(100):
        client.get("/")

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_middleware_overhead(app_with_middleware):
    client = TestClient(app_with_middleware)

    start = time.perf_counter()

    for _ in range(100):
        client.get("/")

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_cors_middleware_overhead():
    app = Flaxon("test-cors")
    app.add_middleware(CORSMiddleware, allowed_origins=["*"])

    @app.get("/")
    async def home():
        return {"ok": True}

    client = TestClient(app)

    start = time.perf_counter()

    for _ in range(100):
        client.get("/")

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_middleware_stack_with_10_middleware():
    app = Flaxon("test-stack")

    for i in range(10):
        class CustomMiddleware:
            def __init__(self, app):
                self.app = app

            async def __call__(self, scope, receive, send):
                await self.app(scope, receive, send)

        app.add_middleware(CustomMiddleware)

    @app.get("/")
    async def home():
        return {"ok": True}

    client = TestClient(app)

    start = time.perf_counter()

    for _ in range(100):
        client.get("/")

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_middleware_with_request_modification():
    app = Flaxon("test-modify")

    class ModifyMiddleware:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            scope["modified"] = True
            await self.app(scope, receive, send)

    app.add_middleware(ModifyMiddleware)

    @app.get("/")
    async def home(request):
        return {"modified": request.scope.get("modified", False)}

    client = TestClient(app)

    start = time.perf_counter()

    for _ in range(100):
        response = client.get("/")
        assert response.json()["modified"] is True

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0