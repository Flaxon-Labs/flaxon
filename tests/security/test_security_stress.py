"""Adversarial pressure tests for security primitives and middleware."""

import asyncio
from io import BytesIO

import pytest

from flaxon import Flaxon
from flaxon.files import FileStorage
from flaxon.files.upload import UploadedFile
from flaxon.security import (
    CSRF,
    CSRFMiddleware,
    DistributedRateLimiter,
    JWT,
    RateLimitMiddleware,
    RateLimiter,
    Sanitizer,
)
from flaxon.testing import AsyncTestClient, TestClient


pytestmark = pytest.mark.security


def test_csrf_rejects_invalid_token_burst():
    app = Flaxon("csrf-pressure")
    app.add_middleware(CSRFMiddleware, secret_key="stress-secret")

    @app.post("/mutate")
    async def mutate(request):
        return {"ok": True}

    client = TestClient(app)
    responses = [
        client.post("/mutate", json_data={"index": index}, headers={"X-CSRF-Token": "bad"})
        for index in range(250)
    ]
    assert all(response.status_code == 403 for response in responses)
    assert all(response.json()["error"]["code"] == "FX-CSRF-001" for response in responses)
    client.close()


def test_csrf_token_fuzz_does_not_raise():
    csrf = CSRF(secret_key="stress-secret")
    candidates = ["", ".", "a.b.c", "a.0." + ("0" * 64), "\x00" * 100]
    candidates.extend(f"{index}.not-a-token" for index in range(250))
    assert all(csrf.verify_token(candidate) is False for candidate in candidates)


@pytest.mark.asyncio
async def test_rate_limiter_is_atomic_under_concurrency():
    limiter = RateLimiter(requests=100, window_seconds=60)
    scope = {"client": ("stress-client", 443)}
    results = await asyncio.gather(*(limiter.check(scope) for _ in range(500)))
    assert sum(results) == 100
    assert limiter.get_remaining(scope) == 0


@pytest.mark.asyncio
async def test_distributed_rate_limiter_is_atomic_under_concurrency():
    redis = pytest.importorskip("redis.asyncio", reason="Redis client is not installed")
    client = redis.from_url(
        "redis://localhost:6379/1",
        decode_responses=True,
        protocol=2,
        max_connections=500,
    )
    key = "stress-distributed-rate-limit"
    limiter = DistributedRateLimiter(client, prefix="stress")
    await client.delete("stress:" + key)
    try:
        results = await asyncio.gather(
            *(limiter.check(key, requests=100, window_seconds=60) for _ in range(300))
        )
        assert sum(results) == 100
    finally:
        await client.delete("stress:" + key)
        await client.aclose()


@pytest.mark.asyncio
async def test_rate_limit_middleware_rejects_burst_without_server_errors():
    app = Flaxon("rate-pressure")
    app.add_middleware(RateLimitMiddleware, requests=75, window_seconds=60)

    @app.get("/limited")
    async def limited():
        return {"ok": True}

    client = AsyncTestClient(app)
    responses = await asyncio.gather(*(client.get("/limited") for _ in range(300)))
    assert sum(response.status_code == 200 for response in responses) == 75
    assert sum(response.status_code == 429 for response in responses) == 225
    assert all(response.status_code in {200, 429} for response in responses)


def test_allowlist_sanitization_survives_hostile_batch():
    payloads = [
        '<script>alert("x")</script><p>ok</p>',
        '<img src=x onerror="alert(1)"><a href="javascript:alert(1)">link</a>',
        '<svg><a href="data:text/html,x">bad</a></svg>',
    ] * 100
    for payload in payloads:
        clean = Sanitizer.allow_html(payload)
        assert "<script" not in clean.lower()
        assert "onerror" not in clean.lower()
        assert "javascript:" not in clean.lower()
        assert "data:" not in clean.lower()


def test_jwt_tampering_batch_is_rejected():
    jwt = JWT(secret_key="stress-secret")
    token = jwt.encode({"user_id": 7, "role": "editor"})
    header, payload, signature = token.split(".")
    for index in range(250):
        replacement = "A" if signature[0] != "A" else "B"
        tampered = f"{header}.{payload}.{replacement}{signature[1:]}"
        with pytest.raises(Exception):
            jwt.decode(tampered)


def test_storage_rejects_traversal_variants(tmp_path):
    storage = FileStorage(str(tmp_path / "uploads"))
    traversal_paths = ["../outside", "../../outside", "a/../../outside", "..\\outside"]
    for path in traversal_paths:
        upload = UploadedFile("payload.txt", "text/plain", 7, BytesIO(b"payload"))
        with pytest.raises(ValueError):
            storage.save(upload, path=path)
    assert not (tmp_path / "outside.txt").exists()
