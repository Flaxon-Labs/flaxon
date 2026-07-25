import asyncio
import json

import pytest

from flaxon import Flaxon
from flaxon.websocket import WebSocket


@pytest.fixture
def app() -> Flaxon:
    app = Flaxon("test-websocket", debug=True)

    @app.websocket("/ws/echo")
    async def echo(socket: WebSocket):
        await socket.accept()
        try:
            async for message in socket.iter_json():
                await socket.send_json({"echo": message})
        except Exception:
            pass

    @app.websocket("/ws/chat/<room_id>")
    async def chat(socket: WebSocket, room_id: str):
        await socket.accept()
        await socket.join(room_id)
        try:
            async for message in socket.iter_json():
                await socket.broadcast_json(room_id, {
                    "room": room_id,
                    "message": message,
                })
        finally:
            await socket.leave(room_id)

    @app.websocket("/ws/auth")
    async def auth(socket: WebSocket):
        await socket.accept()
        await socket.send_json({"status": "connected"})
        try:
            message = await socket.receive_json()
            if message.get("token") == "valid-token":
                await socket.send_json({"status": "authenticated"})
            else:
                await socket.send_json({"status": "unauthorized"})
                await socket.close()
        except Exception:
            pass

    return app


def test_websocket_echo():
    import asyncio

    app = Flaxon("test")

    @app.websocket("/ws/echo")
    async def echo(socket: WebSocket):
        await socket.accept()
        async for message in socket.iter_json():
            await socket.send_json({"echo": message})

    async def run_test():
        from flaxon.testing import AsyncWebSocketClient

        client = AsyncWebSocketClient(app)
        await client.connect("/ws/echo")

        await client.send_json({"message": "hello"})
        response = await client.receive_json()
        assert response == {"echo": {"message": "hello"}}

        await client.send_json({"message": "world"})
        response = await client.receive_json()
        assert response == {"echo": {"message": "world"}}

        await client.disconnect()

    asyncio.run(run_test())


def test_websocket_chat_room():
    import asyncio

    app = Flaxon("test")

    @app.websocket("/ws/chat/<room_id>")
    async def chat(socket: WebSocket, room_id: str):
        await socket.accept()
        await socket.join(room_id)
        try:
            async for message in socket.iter_json():
                await socket.broadcast_json(room_id, {
                    "room": room_id,
                    "message": message,
                })
        finally:
            await socket.leave(room_id)

    async def run_test():
        from flaxon.testing import AsyncWebSocketClient

        client1 = AsyncWebSocketClient(app)
        client2 = AsyncWebSocketClient(app)

        await client1.connect("/ws/chat/room1")
        await client2.connect("/ws/chat/room1")

        await client1.send_json({"text": "Hello everyone!"})

        response = await client2.receive_json()
        assert response["room"] == "room1"
        assert response["message"]["text"] == "Hello everyone!"

        await client1.disconnect()
        await client2.disconnect()

    asyncio.run(run_test())


def test_websocket_authentication():
    import asyncio

    app = Flaxon("test")

    @app.websocket("/ws/auth")
    async def auth(socket: WebSocket):
        await socket.accept()
        try:
            message = await socket.receive_json()
            if message.get("token") == "valid-token":
                await socket.send_json({"status": "authenticated"})
            else:
                await socket.send_json({"status": "unauthorized"})
                await socket.close()
        except Exception:
            pass

    async def run_test():
        from flaxon.testing import AsyncWebSocketClient

        client = AsyncWebSocketClient(app)
        await client.connect("/ws/auth")

        await client.send_json({"token": "valid-token"})
        response = await client.receive_json()
        assert response["status"] == "authenticated"

        await client.disconnect()

    asyncio.run(run_test())


def test_websocket_invalid_path():
    import asyncio

    app = Flaxon("test")

    @app.websocket("/ws/valid")
    async def valid(socket: WebSocket):
        await socket.accept()

    async def run_test():
        from flaxon.testing import AsyncWebSocketClient

        client = AsyncWebSocketClient(app)

        with pytest.raises(RuntimeError, match="WebSocket connection rejected"):
            await client.connect("/ws/invalid")

    asyncio.run(run_test())