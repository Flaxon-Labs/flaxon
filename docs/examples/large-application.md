
---

## docs/examples/large-application.md

```markdown
# Large Application Example

This example demonstrates a structured large application with routers, services, repositories, schemas, and middleware.

## Project Structure

myapp/
├── app.py
├── config.py
├── models/
│ └── user.py
├── schemas/
│ └── user.py
├── services/
│ └── user_service.py
├── repositories/
│ └── user_repository.py
├── routes/
│ ├── init.py
│ ├── users.py
│ └── auth.py
├── middleware/
│ └── auth.py
└── utils/
└── db.py

text

## Application Code

### app.py

```python
from flaxon import Flaxon
from flaxon.middleware import RequestIDMiddleware, SecurityHeadersMiddleware, CORSMiddleware
from flaxon.security import JWTBackend, AuthenticationMiddleware

from config import Config
from routes import users, auth
from middleware.auth import AuthMiddleware

# Create application
app = Flaxon("myapp", debug=Config.DEBUG)

# Configuration
app.config.update(Config.to_dict())

# Middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allowed_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
)
app.add_middleware(AuthMiddleware)

# Authentication
jwt_backend = JWTBackend(secret_key=Config.SECRET_KEY)
app.add_middleware(AuthenticationMiddleware, backend=jwt_backend)

# Routes
app.include_router(auth.router)
app.include_router(users.router)

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def home():
    return {"message": "Welcome to MyApp API", "version": "1.0.0"}
config.py
python
import os
from typing import Any

class Config:
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    JWT_EXPIRATION = int(os.environ.get("JWT_EXPIRATION", 3600))
    MAX_BODY_SIZE = int(os.environ.get("MAX_BODY_SIZE", 10 * 1024 * 1024))

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "DEBUG": cls.DEBUG,
            "SECRET_KEY": cls.SECRET_KEY,
            "DATABASE_URL": cls.DATABASE_URL,
            "ALLOWED_ORIGINS": cls.ALLOWED_ORIGINS,
            "JWT_EXPIRATION": cls.JWT_EXPIRATION,
            "MAX_BODY_SIZE": cls.MAX_BODY_SIZE,
        }
repositories/user_repository.py
python
from typing import Optional
from models.user import User

class UserRepository:
    def __init__(self, db):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        row = await self.db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)
        return User.from_dict(row) if row else None

    async def get_by_email(self, email: str) -> Optional[User]:
        row = await self.db.fetch_one("SELECT * FROM users WHERE email = $1", email)
        return User.from_dict(row) if row else None

    async def create(self, user: User) -> User:
        row = await self.db.fetch_one(
            "INSERT INTO users (name, email, hashed_password) VALUES ($1, $2, $3) RETURNING *",
            user.name,
            user.email,
            user.hashed_password,
        )
        return User.from_dict(row)

    async def update(self, user: User) -> User:
        row = await self.db.fetch_one(
            "UPDATE users SET name = $1, email = $2 WHERE id = $3 RETURNING *",
            user.name,
            user.email,
            user.id,
        )
        return User.from_dict(row)

    async def delete(self, user_id: int) -> bool:
        await self.db.execute("DELETE FROM users WHERE id = $1", user_id)
        return True

    async def list(self, limit: int = 100, offset: int = 0) -> list[User]:
        rows = await self.db.fetch_all(
            "SELECT * FROM users LIMIT $1 OFFSET $2",
            limit,
            offset,
        )
        return [User.from_dict(row) for row in rows]

    async def count(self) -> int:
        return await self.db.fetch_val("SELECT COUNT(*) FROM users")


        services/user_service.py
python
from typing import Optional
from repositories.user_repository import UserRepository
from models.user import User
from flaxon.security import hash_password, verify_password

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def get_user(self, user_id: int) -> Optional[User]:
        return await self.repo.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self.repo.get_by_email(email)

    async def create_user(self, name: str, email: str, password: str) -> User:
        # Validate
        if await self.repo.get_by_email(email):
            raise ValueError("Email already registered")

        user = User(
            name=name,
            email=email,
            hashed_password=hash_password(password),
        )
        return await self.repo.create(user)

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        user = await self.repo.get_by_email(email)
        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    async def update_user(self, user_id: int, data: dict) -> Optional[User]:
        user = await self.repo.get_by_id(user_id)
        if not user:
            return None

        if "name" in data:
            user.name = data["name"]
        if "email" in data:
            user.email = data["email"]

        return await self.repo.update(user)

    async def delete_user(self, user_id: int) -> bool:
        return await self.repo.delete(user_id)

    async def list_users(self, page: int = 1, per_page: int = 20) -> dict:
        offset = (page - 1) * per_page
        users = await self.repo.list(per_page, offset)
        total = await self.repo.count()

        return {
            "items": users,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        }
routes/auth.py
python
from flaxon import Router, HTTPException
from flaxon.security import JWTBackend, login_required
from flaxon.validation import Schema, fields

from services.user_service import UserService
from repositories.user_repository import UserRepository
from utils.db import get_db

router = Router(prefix="/api/v1/auth")

class LoginRequest(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, min_length=8)

class RegisterRequest(Schema):
    name = fields.String(required=True, min_length=2, max_length=80)
    email = fields.Email(required=True)
    password = fields.String(required=True, min_length=8)
    confirm_password = fields.String(required=True, min_length=8)

@router.post("/register")
async def register(data: RegisterRequest):
    if data.password != data.confirm_password:
        raise HTTPException(400, "Passwords do not match")

    db = get_db()
    repo = UserRepository(db)
    service = UserService(repo)

    try:
        user = await service.create_user(data.name, data.email, data.password)
        return {"success": True, "user": user.to_dict()}
    except ValueError as exc:
        raise HTTPException(400, str(exc))

@router.post("/login")
async def login(data: LoginRequest):
    db = get_db()
    repo = UserRepository(db)
    service = UserService(repo)

    user = await service.authenticate(data.email, data.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    jwt_backend = JWTBackend(secret_key="your-secret-key")
    token = await jwt_backend.create_token(user.to_dict())

    return {"token": token, "user": user.to_dict()}

@router.post("/refresh")
@login_required
async def refresh(request):
    user = getattr(request, "user")
    jwt_backend = JWTBackend(secret_key="your-secret-key")
    token = await jwt_backend.create_token(user)

    return {"token": token}
routes/users.py
python
from flaxon import Router, HTTPException
from flaxon.security import login_required, permission_required
from flaxon.validation import Schema, fields

from services.user_service import UserService
from repositories.user_repository import UserRepository
from utils.db import get_db

router = Router(prefix="/api/v1/users")

class UpdateUserRequest(Schema):
    name = fields.String(required=False, min_length=2, max_length=80)
    email = fields.Email(required=False)

@router.get("/")
@login_required
async def list_users(request):
    page = request.query.get_int("page", 1)
    per_page = request.query.get_int("per_page", 20)

    db = get_db()
    repo = UserRepository(db)
    service = UserService(repo)

    result = await service.list_users(page, per_page)
    return result

@router.get("/<int:user_id>")
@login_required
async def get_user(user_id: int):
    db = get_db()
    repo = UserRepository(db)
    service = UserService(repo)

    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    return user.to_dict()

@router.put("/<int:user_id>")
@login_required
async def update_user(user_id: int, data: UpdateUserRequest):
    db = get_db()
    repo = UserRepository(db)
    service = UserService(repo)

    user = await service.update_user(user_id, data.to_dict())
    if not user:
        raise HTTPException(404, "User not found")

    return user.to_dict()

@router.delete("/<int:user_id>")
@login_required
@permission_required("delete_user")
async def delete_user(user_id: int):
    db = get_db()
    repo = UserRepository(db)
    service = UserService(repo)

    result = await service.delete_user(user_id)
    if not result:
        raise HTTPException(404, "User not found")

    return {"deleted": True}

@router.get("/me")
@login_required
async def get_me(request):
    user = getattr(request, "user")
    return user
middleware/auth.py
python
from flaxon.middleware import Middleware

class AuthMiddleware(Middleware):
    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        # Add user to scope for WebSocket authentication
        if "user" not in scope:
            scope["user"] = None

        await self.app(scope, receive, send)
Running the Application
bash
# Install dependencies
pip install flaxon[standard,dev]

# Set environment variables
export SECRET_KEY=your-secret-key
export DATABASE_URL=postgresql://user:pass@localhost/db

# Run the application
flaxon run app:app --reload