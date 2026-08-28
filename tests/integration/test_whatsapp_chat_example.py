import pytest

from flaxon.testing import AsyncTestClient, AsyncWebSocketClient


@pytest.mark.asyncio
async def test_whatsapp_chat_example_http_and_websocket():
    from docs.examples.whatsapp_chat.app import app

    http = AsyncTestClient(app)
    assert (await http.get("/")).status_code == 200
    assert (await http.get("/api/health")).json()["ok"] is True

    client = AsyncWebSocketClient(app)
    await client.connect("/ws/chat/general?user=ada")
    ready = await client.receive_json()
    assert ready["type"] == "session.ready"
    joined = await client.receive_json()
    assert joined["type"] == "presence.joined"
    await client.send_json({"type": "message.send", "text": "hello"})
    message = await client.receive_json()
    assert message["type"] == "message.created"
    assert message["text"] == "hello"
    await client.disconnect()
