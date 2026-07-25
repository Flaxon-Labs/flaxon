# Mobile Backends

## Overview

Flaxon is designed to be an excellent backend for mobile applications. It provides stable JSON APIs, WebSocket support for real-time features, and technology neutrality that works with any mobile platform.

## Why Flaxon for Mobile?

- **Technology Neutral** — Works with Android (Kotlin/Java), iOS (Swift), Flutter, React Native, Capacitor
- **Async-First** — Handles multiple concurrent mobile connections efficiently
- **WebSocket Support** — Real-time chat, notifications, and live updates
- **JSON APIs** — First-class JSON support for mobile clients
- **Authentication** — JWT, OAuth2, and session-based auth
- **File Upload** — Handle media uploads from mobile devices
- **Push Notifications** — Firebase Cloud Messaging (FCM) integration

## Android (Kotlin) Backend

### API Endpoints

```python
from flaxon import Flaxon
from flaxon.validation import Schema, fields

app = Flaxon("android-backend")

class DeviceRegistration(Schema):
    device_id = fields.String(required=True, min_length=8)
    platform = fields.Choice(["android", "ios"], required=True)
    notification_token = fields.String(required=True, min_length=16)

@app.post("/api/v1/devices")
async def register_device(data: DeviceRegistration):
    # Store device for push notifications
    await device_service.register(data.device_id, data.platform, data.notification_token)
    return {"success": True, "device": data.to_dict()}

@app.post("/api/v1/auth/login")
async def login(request):
    data = await request.json()
    user = await auth_service.authenticate(data["email"], data["password"])
    token = await jwt_backend.create_token(user)
    return {
        "access_token": token,
        "refresh_token": await create_refresh_token(user),
        "user": user.to_dict(),
    }

@app.post("/api/v1/auth/refresh")
async def refresh_token(request):
    data = await request.json()
    new_token = await refresh_service.refresh(data["refresh_token"])
    return {"access_token": new_token}

    Versioning
python
from flaxon import Router

# Version 1 API
v1 = Router(prefix="/api/v1")

@v1.get("/users")
async def users_v1():
    return {"version": "v1", "users": []}

# Version 2 API (backward compatible)
v2 = Router(prefix="/api/v2")

@v2.get("/users")
async def users_v2():
    return {"version": "v2", "users": [], "pagination": {"page": 1}}

app.include_router(v1)
app.include_router(v2)
iOS (Swift) Backend
python
@app.get("/api/v1/posts")
async def get_posts(request):
    page = request.query.get_int("page", 1)
    per_page = request.query.get_int("per_page", 20)

    posts = await post_service.get_paginated(page, per_page)
    total = await post_service.count()

    return {
        "posts": posts,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
    }
Real-Time Features (WebSocket)
python
@app.websocket("/ws/mobile")
async def mobile_websocket(socket: WebSocket):
    user = getattr(socket.scope, "user", None)
    if not user:
        await socket.close(code=4001)
        return

    await socket.accept()
    await socket.join(f"user_{user.id}")

    try:
        async for message in socket.iter_json():
            event = message.get("event")

            if event == "ping":
                await socket.send_json({"event": "pong"})

            elif event == "message":
                await handle_mobile_message(user, message["data"])

            elif event == "location":
                await update_user_location(user.id, message["data"])

    except WebSocketDisconnect:
        pass
    finally:
        await socket.leave(f"user_{user.id}")
Push Notifications
Firebase Cloud Messaging (FCM)
python
import firebase_admin
from firebase_admin import messaging

# Initialize FCM
firebase_admin.initialize_app()

class NotificationService:
    @staticmethod
    async def send_push_notification(token: str, title: str, body: str, data: dict = None):
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
        )

        response = await messaging.send_async(message)
        return response

@app.post("/api/v1/notifications/send")
async def send_notification(request):
    data = await request.json()
    user_id = data["user_id"]

    # Get user's device tokens
    tokens = await device_service.get_tokens(user_id)

    for token in tokens:
        await NotificationService.send_push_notification(
            token=token,
            title=data["title"],
            body=data["message"],
            data={"type": "notification", "id": data.get("id")},
        )

    return {"sent": len(tokens)}
Offline-First Synchronization
Timestamp-Based Sync
python
@app.post("/api/v1/sync")
async def sync_data(request):
    data = await request.json()
    last_sync = data.get("last_sync", 0)

    # Get changes since last sync
    changes = {
        "users": await user_service.get_changes_since(last_sync),
        "posts": await post_service.get_changes_since(last_sync),
        "messages": await message_service.get_changes_since(last_sync),
    }

    # Update server with local changes
    if data.get("local_changes"):
        await process_local_changes(data["local_changes"])

    return {
        "server_time": time.time(),
        "changes": changes,
        "has_more": False,
    }
Conflict Resolution
python
@app.post("/api/v1/sync/conflict")
async def resolve_conflict(request):
    data = await request.json()

    # Server wins
    if data.get("strategy") == "server_wins":
        await apply_server_changes(data["resource"], data["server_version"])

    # Client wins
    elif data.get("strategy") == "client_wins":
        await apply_client_changes(data["resource"], data["client_version"])

    # Merge
    elif data.get("strategy") == "merge":
        await merge_changes(data["resource"], data["server_version"], data["client_version"])

    return {"resolved": True}
File Uploads
python
from flaxon.files import FileUpload, FileStorage

upload_handler = FileUpload(max_size=50 * 1024 * 1024)
storage = FileStorage("uploads")

@app.post("/api/v1/upload")
async def upload_file(request):
    files = await upload_handler.parse(request)

    uploaded = []
    for file in files:
        path = storage.save(file)
        uploaded.append({
            "filename": file.filename,
            "url": storage.get_url(path),
            "size": file.size,
        })

        # Clean up temporary file
        await upload_handler.cleanup([file])

    return {"files": uploaded}

@app.post("/api/v1/upload/chunk")
async def upload_chunk(request):
    data = await request.json()
    chunk = await request.body()

    # Store chunk
    await chunk_storage.save(data["upload_id"], data["chunk_index"], chunk)

    if data["is_last"]:
        # Assemble chunks
        file_path = await chunk_storage.assemble(data["upload_id"])
        return {"file_url": storage.get_url(file_path)}

    return {"status": "chunk_received"}
Authentication Flows
JWT Authentication
python
from flaxon.security import JWTBackend, login_required

backend = JWTBackend(secret_key="your-secret")

@app.post("/api/v1/auth/login")
async def mobile_login(request):
    data = await request.json()
    user = await authenticate(data["email"], data["password"])

    if not user:
        raise HTTPException(401, "Invalid credentials")

    access_token = await backend.create_token(user, expires_in=900)  # 15 minutes
    refresh_token = await create_refresh_token(user, expires_in=86400 * 7)  # 7 days

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": 900,
        "user": user.to_dict(),
    }

@app.post("/api/v1/auth/refresh")
async def refresh(request):
    data = await request.json()
    user = await validate_refresh_token(data["refresh_token"])

    if not user:
        raise HTTPException(401, "Invalid refresh token")

    access_token = await backend.create_token(user, expires_in=900)

    return {
        "access_token": access_token,
        "expires_in": 900,
    }

@app.get("/api/v1/profile")
@login_required
async def profile(request):
    user = getattr(request, "user")
    return user.to_dict()
Mobile-Specific Middleware
python
class MobileMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        # Detect mobile client
        user_agent = scope.get("headers", {}).get("user-agent", "")
        is_mobile = any(ua in user_agent.lower() for ua in ["android", "iphone", "ipad"])

        if is_mobile:
            scope["is_mobile"] = True

        # Add rate limiting for mobile
        scope["rate_limit"] = 100 if is_mobile else 1000

        await self.app(scope, receive, send)

app.add_middleware(MobileMiddleware)
Complete Mobile Backend Example
python
from flaxon import Flaxon, Router, HTTPException
from flaxon.security import JWTBackend, login_required
from flaxon.validation import Schema, fields
from flaxon.files import FileUpload, FileStorage
from flaxon.websocket import WebSocket

app = Flaxon("mobile-backend", debug=True)

# JWT Authentication
jwt_backend = JWTBackend(secret_key="your-secret-key")

# API Versioning
v1 = Router(prefix="/api/v1")

# Schemas
class LoginRequest(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, min_length=8)

class RegisterRequest(Schema):
    username = fields.String(required=True, min_length=3)
    email = fields.Email(required=True)
    password = fields.String(required=True, min_length=8)

class DeviceRegistration(Schema):
    device_id = fields.String(required=True, min_length=8)
    platform = fields.Choice(["android", "ios", "web"], required=True)
    notification_token = fields.String(required=True, min_length=16)

# Routes
@v1.post("/auth/register")
async def register(data: RegisterRequest):
    user = await user_service.create(data.username, data.email, data.password)
    return {"user": user.to_dict()}

@v1.post("/auth/login")
async def login(data: LoginRequest):
    user = await user_service.authenticate(data.email, data.password)

    if not user:
        raise HTTPException(401, "Invalid credentials")

    token = await jwt_backend.create_token(user)
    return {"token": token, "user": user.to_dict()}

@v1.post("/devices")
async def register_device(data: DeviceRegistration):
    await device_service.register(data.device_id, data.platform, data.notification_token)
    return {"success": True}

@v1.get("/profile")
@login_required
async def get_profile(request):
    user = getattr(request, "user")
    return user.to_dict()

@v1.put("/profile")
@login_required
async def update_profile(request):
    data = await request.json()
    user = getattr(request, "user")
    user = await user_service.update(user.id, data)
    return user.to_dict()

@v1.get("/posts")
async def list_posts(request):
    page = request.query.get_int("page", 1)
    per_page = request.query.get_int("per_page", 20)

    posts = await post_service.get_paginated(page, per_page)
    total = await post_service.count()

    return {
        "data": posts,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
    }

@v1.post("/upload")
async def upload_file(request):
    upload = FileUpload(max_size=50 * 1024 * 1024)
    storage = FileStorage("uploads")

    files = await upload.parse(request)
    uploaded = []

    for file in files:
        path = storage.save(file)
        uploaded.append({
            "filename": file.filename,
            "url": storage.get_url(path),
            "size": file.size,
        })
        await upload.cleanup([file])

    return {"files": uploaded}

@v1.get("/sync")
@login_required
async def sync_data(request):
    user = getattr(request, "user")
    last_sync = request.query.get_int("last_sync", 0)

    changes = await sync_service.get_changes(user.id, last_sync)
    return {
        "server_time": time.time(),
        "changes": changes,
    }

# WebSocket for real-time features
@app.websocket("/ws/mobile")
async def mobile_ws(socket: WebSocket):
    # Authenticate via query parameter
    token = socket.scope.get("query_string", "")
    user = await jwt_backend.validate_token(token)

    if not user:
        await socket.close(code=4001)
        return

    await socket.accept()
    await socket.join(f"user_{user.id}")

    try:
        async for message in socket.iter_json():
            event = message.get("event")

            if event == "ping":
                await socket.send_json({"event": "pong", "timestamp": time.time()})

            elif event == "message":
                await message_service.create(user.id, message["data"])
                await socket.broadcast_json(f"user_{user.id}", {
                    "event": "message",
                    "data": message["data"],
                })

    except WebSocketDisconnect:
        pass
    finally:
        await socket.leave(f"user_{user.id}")

app.include_router(v1)

# Health check
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
    }
Mobile Client Integration Examples
Android (Kotlin) Client
kotlin
// Retrofit interface
interface ApiService {
    @POST("api/v1/auth/login")
    suspend fun login(@Body request: LoginRequest): LoginResponse

    @GET("api/v1/posts")
    suspend fun getPosts(@Query("page") page: Int): PostsResponse

    @Multipart
    @POST("api/v1/upload")
    suspend fun uploadFile(@Part file: MultipartBody.Part): UploadResponse
}

// WebSocket client
val client = OkHttpClient()
val request = Request.Builder()
    .url("ws://yourapp.com/ws/mobile?token=$token")
    .build()

val listener = object : WebSocketListener() {
    override fun onMessage(webSocket: WebSocket, text: String) {
        // Handle message
    }
}

val websocket = client.newWebSocket(request, listener)
iOS (Swift) Client
swift
// URLSession client
struct APIClient {
    func login(email: String, password: String) async throws -> LoginResponse {
        let url = URL(string: "https://yourapp.com/api/v1/auth/login")!
        // ...
    }
}

// WebSocket client
let url = URL(string: "wss://yourapp.com/ws/mobile?token=\(token)")!
let task = URLSession.shared.webSocketTask(with: url)
task.resume()

task.receive { result in
    switch result {
    case .success(let message):
        // Handle message
    case .failure(let error):
        // Handle error
    }
}
Mobile Best Practices
Use JWT with short expiration (15-30 minutes)

Implement refresh token rotation

Use pagination for all list endpoints

Support offline-first synchronization

Handle network errors gracefully

Use WebSocket reconnection with exponential backoff

Implement push notifications for important events

Use chunked uploads for large files

API versioning for backward compatibility

Mobile-specific rate limiting