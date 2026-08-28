"""Repeatable performance pressure tests for the public Flaxon APIs.

These tests intentionally avoid machine-specific latency assertions.  The
benchmark fixture records comparable numbers while the assertions verify that
pressure does not corrupt responses or route resolution.
"""

import asyncio

import pytest

from flaxon import Flaxon, Router
from flaxon.http import JSONResponse
from flaxon.testing import AsyncTestClient, TestClient


pytestmark = pytest.mark.performance


@pytest.fixture
def pressure_app():
    app = Flaxon("performance-pressure")

    @app.get("/health")
    async def health():
        return {"ok": True, "service": "flaxon"}

    @app.get("/records")
    async def records():
        return {
            "items": [
                {"id": index, "name": f"record-{index}", "active": index % 2 == 0}
                for index in range(250)
            ],
            "total": 250,
        }

    return app


def test_request_throughput_benchmark(pressure_app, benchmark):
    client = TestClient(pressure_app)

    def request_batch():
        responses = [client.get("/health") for _ in range(100)]
        assert all(response.status_code == 200 for response in responses)

    benchmark(request_batch)
    client.close()


def test_large_json_response_benchmark(pressure_app, benchmark):
    client = TestClient(pressure_app)

    def request_large_response():
        response = client.get("/records")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 250

    benchmark(request_large_response)
    client.close()


def test_json_serialization_benchmark(benchmark):
    payload = {
        "items": [{"id": index, "values": list(range(10))} for index in range(1000)]
    }

    def serialize():
        response = JSONResponse(payload)
        assert response is not None

    benchmark(serialize)


def test_route_matching_pressure_benchmark(benchmark):
    router = Router()
    for index in range(500):
        @router.get(f"/api/items/{index}")
        async def item(request, item_id=index):
            return {"id": item_id}

    @router.get("/api/items/<int:item_id>/events")
    async def events(request):
        return {"ok": True}

    def match_batch():
        for index in range(500):
            assert router.match(f"/api/items/{index}", "GET") is not None
        assert router.match("/api/items/42/events", "GET") is not None

    benchmark(match_batch)


@pytest.mark.asyncio
async def test_concurrent_request_pressure(pressure_app):
    client = AsyncTestClient(pressure_app)

    async def request(index):
        path = "/health" if index % 4 else "/records"
        response = await client.get(path)
        return response.status_code, response.json()

    results = await asyncio.gather(*(request(index) for index in range(500)))
    assert all(status == 200 for status, _ in results)
    assert sum("items" in body for _, body in results) == 125
