
---

## docs/examples/android-backend.md

```markdown
# Android Backend Example

This example demonstrates a backend for Android applications with authentication, device registration, and data synchronization.

## Application Code

```python
# app.py
import time
from flaxon import Flaxon, HTTPException
from flaxon.security import JWTBackend, login_required
from flaxon.validation import Schema, fields

app = Flaxon("android-backend")

# JWT Authentication
jwt_backend = JWTBackend(secret_key="your-secret-key")

# Schemas
class LoginRequest(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, min_length=8)

class RegisterRequest(Schema):
    username = fields.String(required=True, min_length=3, max_length=30)
    email = fields.Email(required=True)
    password = fields.String(required=True, min_length=8)

class DeviceRegistration(Schema):
    device_id = fields.String(required=True, min_length=8)
    platform = fields.Choice(["android", "ios"], required=True)
    notification_token = fields.String(required=True, min_length=16)
    app_version = fields.String(required=False)

class SyncRequest(Schema):
    last_sync = fields.IntField(required=False, default=0)
    local_changes = fields.ListField(required=False)

# In-memory storage
users = {}
devices = {}
posts = []
user_id_counter = 1
post_id_counter = 1

@app.post("/api/v1/auth/register")
async def register(data: RegisterRequest):
    if data.email in users:
        raise HTTPException(400, "Email already registered")

    user = data.to_dict()
    user["id"] = user_id_counter
    user_id_counter += 1
    user["created_at"] = int(time.time())
    users[data.email] = user

    token = await jwt_backend.create_token({"id": user["id"], "email": user["email"]})
    return {"user": user, "token": token}

@app.post("/api/v1/auth/login")
async def login(data: LoginRequest):
    user = users.get(data.email)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    # In production, use proper password hashing
    if user["password"] != data.password:
        raise HTTPException(401, "Invalid credentials")

    token = await jwt_backend.create_token({"id": user["id"], "email": user["email"]})
    return {"user": user, "token": token}

@app.post("/api/v1/devices")
@login_required
async def register_device(request, data: DeviceRegistration):
    user = getattr(request, "user")
    device = data.to_dict()
    device["user_id"] = user["id"]
    device["registered_at"] = int(time.time())

    devices[data.device_id] = device
    return {"success": True, "device": device}

@app.get("/api/v1/profile")
@login_required
async def get_profile(request):
    user = getattr(request, "user")
    return {"user": users.get(user["email"])}

@app.put("/api/v1/profile")
@login_required
async def update_profile(request):
    user = getattr(request, "user")
    data = await request.json()

    stored_user = users.get(user["email"])
    if stored_user:
        stored_user.update(data)
        return {"updated": True, "user": stored_user}

    raise HTTPException(404, "User not found")

@app.post("/api/v1/posts")
@login_required
async def create_post(request):
    user = getattr(request, "user")
    data = await request.json()

    post = {
        "id": post_id_counter,
        "user_id": user["id"],
        "user_name": user.get("username", "Unknown"),
        "content": data.get("content"),
        "created_at": int(time.time()),
    }
    post_id_counter += 1
    posts.append(post)

    return {"created": True, "post": post}

@app.get("/api/v1/posts")
async def list_posts(request):
    page = request.query.get_int("page", 1)
    per_page = request.query.get_int("per_page", 20)

    start = (page - 1) * per_page
    end = start + per_page

    return {
        "data": posts[start:end],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": len(posts),
            "total_pages": (len(posts) + per_page - 1) // per_page,
        },
    }

@app.post("/api/v1/sync")
@login_required
async def sync_data(request, data: SyncRequest):
    user = getattr(request, "user")
    last_sync = data.last_sync or 0

    # Get changes since last sync
    changes = {
        "posts": [
            p for p in posts
            if p.get("created_at", 0) > last_sync
        ],
    }

    # Process local changes
    if data.local_changes:
        for change in data.local_changes:
            if change.get("type") == "post":
                posts.append({
                    "id": post_id_counter,
                    "user_id": user["id"],
                    "content": change.get("content"),
                    "created_at": int(time.time()),
                })
                post_id_counter += 1

    return {
        "server_time": int(time.time()),
        "changes": changes,
        "has_more": False,
    }

@app.get("/api/v1/notifications")
@login_required
async def get_notifications(request):
    user = getattr(request, "user")
    # Return notifications for the user
    return {"notifications": []}

@app.get("/api/v1/search")
async def search(request):
    q = request.query.get("q", "")
    if not q:
        return {"results": []}

    # Search in posts
    results = [p for p in posts if q.lower() in p.get("content", "").lower()]
    return {"results": results, "total": len(results)}


    Android Client Example (Kotlin)
kotlin
// ApiService.kt
interface ApiService {
    @POST("api/v1/auth/login")
    suspend fun login(@Body request: LoginRequest): LoginResponse

    @POST("api/v1/auth/register")
    suspend fun register(@Body request: RegisterRequest): RegisterResponse

    @POST("api/v1/devices")
    suspend fun registerDevice(@Header("Authorization") token: String, @Body request: DeviceRegistration): DeviceResponse

    @GET("api/v1/profile")
    suspend fun getProfile(@Header("Authorization") token: String): UserResponse

    @GET("api/v1/posts")
    suspend fun getPosts(@Query("page") page: Int): PostsResponse

    @POST("api/v1/posts")
    suspend fun createPost(@Header("Authorization") token: String, @Body request: CreatePostRequest): CreatePostResponse

    @POST("api/v1/sync")
    suspend fun sync(@Header("Authorization") token: String, @Body request: SyncRequest): SyncResponse
}