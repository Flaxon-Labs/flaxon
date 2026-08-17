from flaxon import Flaxon, HTTPException, Router, WebSocket
from flaxon.middleware import CORSMiddleware
from flaxon.security import RateLimitMiddleware
from flaxon.validation import Schema, fields

app = Flaxon("flaxon-hello-api", debug=True)
app.add_middleware(
    CORSMiddleware,
    allowed_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
)
app.add_middleware(RateLimitMiddleware, requests=120, window_seconds=60)


class CreateUser(Schema):
    name = fields.StrField(required=True, min_length=2, max_length=80)
    email = fields.EmailField(required=True)
    age = fields.IntField(required=False, minimum=13, maximum=120)


@app.get("/")
async def home():
    return {
        "framework": "Flaxon",
        "version": "0.1.0",
        "message": "Simple Python. Serious applications.",
    }


@app.get("/health")
async def health():
    return {"success": True, "service": app.name}


@app.get("/api/users/<int:user_id>", name="users.details")
async def get_user(user_id: int):
    if user_id == 404:
        raise HTTPException(404, "User not found.", code="FX-USER-404")
    return {"id": user_id, "name": "Example User"}


@app.post("/api/users")
async def create_user(data: CreateUser):
    return {"success": True, "user": data.to_dict()}


api = Router(prefix="/api/v1")


@api.get("/products")
async def products():
    return [
        {"id": 1, "name": "Keyboard", "price": 79.99},
        {"id": 2, "name": "Monitor", "price": 249.99},
    ]


app.include_router(api)


@app.websocket("/ws/echo")
async def echo(socket: WebSocket):
    await socket.accept()
    async for message in socket.iter_json():
        await socket.send_json({"event": "echo", "data": message})
