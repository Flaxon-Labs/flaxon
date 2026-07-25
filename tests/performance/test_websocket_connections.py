import asyncio
import time

import pytest

from flaxon import Flaxon
from flaxon.websocket import WebSocket


@pytest.fixture
def websocket_app():
    app = Flaxon("test-ws-perf")

    @app.websocket("/ws/echo")
    async def echo(socket: WebSocket):
        await socket.accept()
        try:
            async for message in socket.iter_json():
                await socket.send_json({"echo": message})
        except Exception:
            pass

    @app.websocket("/ws/broadcast/<room_id>")
    async def broadcast(socket: WebSocket, room_id: str):
        await socket.accept()
        await socket.join(room_id)
        try:
            async for message in socket.iter_json():
                await socket.broadcast_json(room_id, message)
        finally:
            await socket.leave(room_id)

    return app


@pytest.mark.asyncio
async def test_websocket_connection_speed(websocket_app):
    from flaxon.testing import AsyncWebSocketClient

    start = time.perf_counter()

    clients = []
    for _ in range(50):
        client = AsyncWebSocketClient(websocket_app)
        await client.connect("/ws/echo")
        clients.append(client)

    elapsed = time.perf_counter() - start
    assert elapsed < 5.0

    for client in clients:
        await client.disconnect()


@pytest.mark.asyncio
async def test_websocket_message_throughput(websocket_app):
    from flaxon.testing import AsyncWebSocketClient

    client = AsyncWebSocketClient(websocket_app)
    await client.connect("/ws/echo")

    start = time.perf_counter()

    for i in range(100):
        await client.send_json({"message": f"Message {i}"})
        response = await client.receive_json()
        assert response["echo"]["message"] == f"Message {i}"

    elapsed = time.perf_counter() - start
    assert elapsed < 5.0

    await client.disconnect()


@pytest.mark.asyncio
async def test_websocket_broadcast_speed(websocket_app):
    from flaxon.testing import AsyncWebSocketClient

    clients = []
    for _ in range(10):
        client = AsyncWebSocketClient(websocket_app)
        await client.connect("/ws/broadcast/room1")
        clients.append(client)

    sender = AsyncWebSocketClient(websocket_app)
    await sender.connect("/ws/broadcast/room1")

    start = time.perf_counter()

    for i in range(50):
        await sender.send_json({"message": f"Broadcast {i}"})

        for client in clients:
            response = await client.receive_json()
            assert response["message"] == f"Broadcast {i}"

    elapsed = time.perf_counter() - start
    assert elapsed < 5.0

    await sender.disconnect()
    for client in clients:
        await client.disconnect()


@pytest.mark.asyncio
async def test_websocket_concurrent_connections(websocket_app):
    from flaxon.testing import AsyncWebSocketClient

    async def connect_client():
        client = AsyncWebSocketClient(websocket_app)
        await client.connect("/ws/echo")
        return client

    start = time.perf_counter()

    tasks = [connect_client() for _ in range(20)]
    clients = await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0

    for client in clients:
        await client.disconnect()


@pytest.mark.asyncio
async def test_websocket_message_size(websocket_app):
    from flaxon.testing import AsyncWebSocketClient

    client = AsyncWebSocketClient(websocket_app)
    await client.connect("/ws/echo")

    large_message = {"data": "x" * 10000}

    start = time.perf_counter()

    for _ in range(10):
        await client.send_json(large_message)
        response = await client.receive_json()
        assert response["echo"]["data"] == large_message["data"]

    elapsed = time.perf_counter() - start
    assert elapsed < 2.0

    await client.disconnect()