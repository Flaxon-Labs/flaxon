from __future__ import annotations

import asyncio

from flaxon import Flaxon
from flaxon.testing import AsyncTestClient, TestClient


def test_router_handles_specific_routes_before_dynamic_routes_at_scale():
    app = Flaxon("router-extreme", debug=True)

    @app.get("/catalog/<item_id>")
    async def catalog_item(item_id: str):
        return {"route": "dynamic", "item_id": item_id}

    @app.get("/catalog/health")
    async def catalog_health():
        return {"route": "static"}

    for index in range(300):
        route = f"/bulk/{index}/<value>"

        async def bulk(value: str, index=index):
            return {"index": index, "value": value}

        app.router.route(route, methods=["GET"])(bulk)

    client = TestClient(app)
    assert client.get("/catalog/health").json() == {"route": "static"}
    assert client.get("/catalog/42").json() == {"route": "dynamic", "item_id": "42"}
    assert client.get("/bulk/299/ready").json() == {"index": 299, "value": "ready"}


def test_large_json_response_preserves_shape_and_content():
    app = Flaxon("large-response", debug=True)

    @app.get("/large")
    async def large_response():
        return {
            "items": [
                {"id": index, "payload": "x" * 128, "active": index % 2 == 0}
                for index in range(5000)
            ]
        }

    response = TestClient(app).get("/large")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 5000
    assert payload["items"][0]["id"] == 0
    assert payload["items"][-1]["payload"] == "x" * 128


def test_concurrent_requests_complete_without_cross_request_state_leaks():
    app = Flaxon("concurrency-extreme", debug=True)

    @app.get("/echo/<value>")
    async def echo(value: str):
        await asyncio.sleep(0)
        return {"value": value}

    async def exercise():
        client = AsyncTestClient(app)
        responses = await asyncio.gather(
            *(client.get(f"/echo/value-{index}") for index in range(250))
        )
        return responses

    responses = asyncio.run(exercise())
    assert all(response.status_code == 200 for response in responses)
    assert [response.json()["value"] for response in responses] == [
        f"value-{index}" for index in range(250)
    ]
