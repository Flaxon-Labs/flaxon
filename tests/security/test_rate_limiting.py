import asyncio

import pytest

from flaxon import Flaxon
from flaxon.security import DistributedRateLimiter, RateLimitMiddleware, RateLimiter
from flaxon.testing import TestClient


def test_rate_limiter_basic():
    limiter = RateLimiter(requests=3, window_seconds=10)

    scope = {"client": ("127.0.0.1", 12345)}

    import asyncio

    async def run_test():
        assert await limiter.check(scope) is True
        assert await limiter.check(scope) is True
        assert await limiter.check(scope) is True
        assert await limiter.check(scope) is False

    asyncio.run(run_test())


def test_rate_limiter_key_func():
    def key_func(scope):
        return scope.get("user_id", "anonymous")

    limiter = RateLimiter(requests=2, window_seconds=10, key_func=key_func)

    import asyncio

    async def run_test():
        scope1 = {"user_id": "user1"}
        scope2 = {"user_id": "user2"}

        assert await limiter.check(scope1) is True
        assert await limiter.check(scope1) is True
        assert await limiter.check(scope1) is False

        assert await limiter.check(scope2) is True
        assert await limiter.check(scope2) is True
        assert await limiter.check(scope2) is False

    asyncio.run(run_test())


def test_rate_limiter_remaining():
    limiter = RateLimiter(requests=5, window_seconds=10)

    scope = {"client": ("127.0.0.1", 12345)}

    import asyncio

    async def run_test():
        assert limiter.get_remaining(scope) == 5

        for _ in range(3):
            await limiter.check(scope)

        assert limiter.get_remaining(scope) == 2

    asyncio.run(run_test())


def test_rate_limit_middleware():
    app = Flaxon("test-rate-limit")
    app.add_middleware(RateLimitMiddleware, requests=3, window_seconds=10)

    @app.get("/")
    async def home():
        return {"ok": True}

    client = TestClient(app)

    for _ in range(3):
        response = client.get("/")
        assert response.status_code == 200

    response = client.get("/")
    assert response.status_code == 429
    result = response.json()
    assert result["error"]["code"] == "FX-RATE-001"


def test_rate_limit_middleware_with_retry_after():
    app = Flaxon("test-rate-limit-retry")
    app.add_middleware(RateLimitMiddleware, requests=2, window_seconds=60)

    @app.get("/")
    async def home():
        return {"ok": True}

    client = TestClient(app)

    for _ in range(2):
        client.get("/")

    response = client.get("/")
    assert "retry-after" in response.headers
    assert int(response.headers["retry-after"]) > 0


def test_distributed_rate_limiter():
    redis = pytest.importorskip("redis.asyncio", reason="Redis client is not installed")

    redis_client = redis.from_url("redis://localhost:6379/1", decode_responses=True)

    try:
        limiter = DistributedRateLimiter(redis_client, prefix="test_rate")

        import asyncio

        async def run_test():
            key = "test_key"

            for i in range(3):
                result = await limiter.check(key, requests=3, window_seconds=10)
                assert result is True

            result = await limiter.check(key, requests=3, window_seconds=10)
            assert result is False

            remaining = await limiter.get_remaining(key, requests=3, window_seconds=10)
            assert remaining == 0

            await redis_client.flushdb()

        asyncio.run(run_test())

    except redis.ConnectionError:
        pytest.skip("Redis not available")
