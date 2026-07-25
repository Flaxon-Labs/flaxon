
---

## docs/examples/websocket-chat.md

```markdown
# WebSocket Chat Example

This example demonstrates a real-time chat application using WebSockets with room support.

## Application Code

```python
# app.py
import json
from datetime import datetime
from flaxon import Flaxon, WebSocket, WebSocketDisconnect

app = Flaxon("chat-app", debug=True)

# In-memory storage
rooms = {}
users = {}
message_history = {}
max_messages_per_room = 100

@app.websocket("/ws/chat/<room_id>")
async def chat(socket: WebSocket, room_id: str):
    # Get username from query
    username = socket.scope.get("query_string", "").split("=")[1] if "user=" in socket.scope.get("query_string", "") else "Anonymous"
    user_id = f"{username}-{id(socket)}"

    # Accept connection
    await socket.accept()
    await socket.join(room_id)

    # Add user to room
    if room_id not in rooms:
        rooms[room_id] = []
        message_history[room_id] = []

    rooms[room_id].append(user_id)
    users[user_id] = {"username": username, "room": room_id, "socket": socket}

    # Notify others
    await socket.broadcast_json(room_id, {
        "type": "system",
        "event": "user_joined",
        "user": username,
        "users": rooms[room_id],
        "timestamp": datetime.now().isoformat(),
    })

    # Send message history
    await socket.send_json({
        "type": "system",
        "event": "history",
        "messages": message_history[room_id][-max_messages_per_room:],
    })

    try:
        async for message in socket.iter_json():
            if message.get("type") == "message":
                msg = {
                    "type": "message",
                    "user": username,
                    "content": message.get("content"),
                    "timestamp": datetime.now().isoformat(),
                }

                # Store message
                message_history[room_id].append(msg)

                # Broadcast to room
                await socket.broadcast_json(room_id, msg)

            elif message.get("type") == "typing":
                await socket.broadcast_json(room_id, {
                    "type": "typing",
                    "user": username,
                    "is_typing": message.get("is_typing", False),
                })

            elif message.get("type") == "ping":
                await socket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})

    except WebSocketDisconnect:
        pass
    finally:
        # Clean up
        users.pop(user_id, None)
        if room_id in rooms:
            rooms[room_id] = [u for u in rooms[room_id] if u != user_id]

        await socket.leave(room_id)

        # Notify others
        await socket.broadcast_json(room_id, {
            "type": "system",
            "event": "user_left",
            "user": username,
            "users": rooms.get(room_id, []),
        })

@app.get("/rooms")
async def list_rooms():
    return {
        "rooms": [
            {
                "name": room_id,
                "users": len(users_in_room),
                "messages": len(message_history.get(room_id, [])),
            }
            for room_id, users_in_room in rooms.items()
        ]
    }

@app.get("/rooms/<room_id>/messages")
async def get_messages(room_id: str):
    return {"messages": message_history.get(room_id, [])}

@app.get("/rooms/<room_id>/users")
async def get_users(room_id: str):
    if room_id in rooms:
        usernames = [users.get(u_id, {}).get("username", "Unknown") for u_id in rooms[room_id]]
        return {"users": usernames}
    return {"users": []}


    Running the Application
bash
# Install dependencies
pip install flaxon[standard]

# Run the application
flaxon run app:app --reload
HTML Client Example
html
<!-- index.html -->
<!doctype html>
<html>
<head>
    <title>Chat</title>
    <style>
        body { font-family: system-ui; max-width: 800px; margin: 0 auto; padding: 20px; }
        #messages { height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
        .message { margin-bottom: 5px; }
        .system { color: #666; font-style: italic; }
        .username { font-weight: bold; }
        #input { display: flex; gap: 10px; }
        #message-input { flex: 1; padding: 8px; }
        #send-btn { padding: 8px 16px; }
    </style>
</head>
<body>
    <h1>Chat Room: <span id="room">general</span></h1>
    <div id="messages"></div>
    <div id="input">
        <input id="message-input" placeholder="Type a message...">
        <button id="send-btn">Send</button>
    </div>

    <script>
        const room = "general";
        const username = prompt("Enter your username:") || "Anonymous";
        const ws = new WebSocket(`ws://localhost:8000/ws/chat/${room}?user=${username}`);
        const messages = document.getElementById("messages");
        const input = document.getElementById("message-input");
        const sendBtn = document.getElementById("send-btn");

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const div = document.createElement("div");
            div.className = "message";

            if (data.type === "system") {
                div.className = "message system";
                div.textContent = `🔔 ${data.event}: ${data.user || ""}`;
            } else if (data.type === "message") {
                div.innerHTML = `<span class="username">${data.user}:</span> ${data.content}`;
            } else if (data.type === "typing") {
                // Handle typing indicator
            }

            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        };

        sendBtn.onclick = () => {
            const content = input.value.trim();
            if (content) {
                ws.send(JSON.stringify({ type: "message", content }));
                input.value = "";
            }
        };

        input.onkeydown = (e) => {
            if (e.key === "Enter") {
                sendBtn.click();
            }
        };
    </script>
</body>
</html>