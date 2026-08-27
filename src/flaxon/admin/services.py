from __future__ import annotations

import secrets
import time
import sqlite3
import json
import uuid
import base64
import hashlib
import hmac
from dataclasses import dataclass, field
from typing import Any

from flaxon.exceptions import Forbidden, Unauthorized
from flaxon.http import Request, Response
from flaxon.security import PasswordHasher, SessionBackend, User
from flaxon.security import RateLimiter


@dataclass
class AdminActivity:
    action: str
    resource: str
    record_id: str | None = None
    username: str = "system"
    timestamp: float = field(default_factory=time.time)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "resource": self.resource,
            "record_id": self.record_id,
            "username": self.username,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class AdminAuth:
    """Small injectable admin auth service backed by Flaxon's token backend."""

    def __init__(self, users: list[dict[str, Any]] | None = None, backend: SessionBackend | None = None) -> None:
        self.backend = backend or SessionBackend()
        self.hasher = PasswordHasher()
        self.users: dict[str, dict[str, Any]] = {}
        for raw in users or []:
            self.add_user(raw)
        self._login_failures: dict[str, list[float]] = {}
        self.role_permissions: dict[str, list[str]] = {}
        self._reset_tokens: dict[str, tuple[str, float]] = {}
        self._verification_tokens: dict[str, tuple[str, float]] = {}

    def add_user(self, raw: dict[str, Any]) -> dict[str, Any]:
        username = str(raw.get("username", "")).strip()
        if not username:
            raise ValueError("Admin users require a username")
        record = dict(raw)
        record["id"] = str(record.get("id") or secrets.token_hex(8))
        record["roles"] = list(record.get("roles") or ["staff"])
        record["permissions"] = list(record.get("permissions") or ["admin:read", "admin:write", "admin:users", "admin:settings", "admin:media"])
        if record.get("password") and not record.get("password_hash"):
            record["password_hash"] = self.hasher.hash(str(record.pop("password")))
        self.users[username] = record
        return record

    def public(self, record: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in record.items() if k not in {"password", "password_hash", "mfa_secret"}}

    def user(self, username: str) -> User | None:
        record = self.users.get(username)
        return User.from_dict(self.public(record)) if record else None

    def verify(self, username: str, password: str) -> User | None:
        record = self.users.get(username)
        if not record or record.get("active", True) is False or not record.get("password_hash"):
            return None
        return self.user(username) if self.hasher.verify(password, record["password_hash"]) else None

    async def login(self, username: str, password: str, otp: str | None = None) -> str | None:
        failures = [stamp for stamp in self._login_failures.get(username, []) if stamp > time.time() - 300]
        if len(failures) >= 10:
            return None
        user = self.verify(username, password)
        if user is None:
            failures.append(time.time())
            self._login_failures[username] = failures
            return None
        record = self.users[username]
        if record.get("mfa_secret") and not self.verify_otp(record["mfa_secret"], otp or ""):
            return None
        self._login_failures.pop(username, None)
        return await self.backend.create_token(user)

    @staticmethod
    def generate_mfa_secret() -> str:
        return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")

    @staticmethod
    def verify_otp(secret: str, code: str, timestamp: int | None = None) -> bool:
        if not code or not secret:
            return False
        try:
            key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
            counter = int((timestamp or int(time.time())) // 30)
            for offset in (-1, 0, 1):
                message = (counter + offset).to_bytes(8, "big")
                digest = hmac.new(key, message, hashlib.sha1).digest()
                position = digest[-1] & 0x0F
                number = (int.from_bytes(digest[position:position + 4], "big") & 0x7FFFFFFF) % 1000000
                if hmac.compare_digest(f"{number:06d}", str(code).strip()):
                    return True
        except (ValueError, TypeError):
            return False
        return False

    def authorize(self, user: User, permission: str) -> None:
        assigned = {item for role in user.roles for item in self.role_permissions.get(role, [])}
        if user.has_permission("admin:superuser") or user.has_permission(permission) or permission in assigned:
            return
        raise Forbidden("Insufficient admin permissions")

    async def current_user(self, request: Request) -> User:
        user = getattr(request, "user", None) or await self.backend.authenticate(request)
        if user is None:
            raise Unauthorized("Authentication required")
        request.user = user
        return user

    async def logout(self, request: Request) -> None:
        token = request.cookies.get("session_id")
        if token:
            await self.backend.revoke_token(token)

    def request_password_reset(self, identifier: str, expires_in: int = 3600) -> str | None:
        value = identifier.strip().lower()
        record = next((item for item in self.users.values() if item.get("username", "").lower() == value or item.get("email", "").lower() == value), None)
        if record is None or record.get("active", True) is False:
            return None
        token = secrets.token_urlsafe(32)
        self._reset_tokens[token] = (record["username"], time.time() + expires_in)
        return token

    def reset_password(self, token: str, password: str) -> bool:
        entry = self._reset_tokens.pop(token, None)
        if entry is None or entry[1] < time.time() or not password:
            return False
        record = self.users.get(entry[0])
        if record is None or record.get("active", True) is False:
            return False
        record["password_hash"] = self.hasher.hash(password)
        return True

    def request_email_verification(self, username: str, expires_in: int = 86400) -> str | None:
        record = self.users.get(username)
        if record is None or not record.get("email") or record.get("email_verified"):
            return None
        token = secrets.token_urlsafe(32)
        self._verification_tokens[token] = (username, time.time() + expires_in)
        return token

    def verify_email(self, token: str) -> bool:
        entry = self._verification_tokens.pop(token, None)
        if entry is None or entry[1] < time.time():
            return False
        record = self.users.get(entry[0])
        if record is None:
            return False
        record["email_verified"] = True
        return True

    def attach_cookie(self, response: Response, token: str, max_age: int = 86400) -> None:
        response.headers.add("set-cookie", f"session_id={token}; Max-Age={max_age}; Path=/; HttpOnly; SameSite=Lax")

    def clear_cookie(self, response: Response) -> None:
        response.headers.add("set-cookie", "session_id=; Max-Age=0; Path=/; HttpOnly; SameSite=Lax")


class AdminStore:
    """SQLite-backed JSON store for admin metadata and CMS records.

    Applications can provide a different repository by implementing the same
    get/set/delete/list methods. SQLite keeps the built-in admin useful across
    restarts without introducing a required database dependency.
    """

    def __init__(self, path: str = "flaxon-admin.sqlite3") -> None:
        self.path = path
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS flaxon_admin_store (namespace TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(namespace, key))")

    def get(self, namespace: str, key: str, default: Any = None) -> Any:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT value FROM flaxon_admin_store WHERE namespace=? AND key=?", (namespace, key)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, namespace: str, key: str, value: Any) -> None:
        encoded = json.dumps(value, default=str)
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO flaxon_admin_store(namespace,key,value) VALUES(?,?,?) ON CONFLICT(namespace,key) DO UPDATE SET value=excluded.value", (namespace, key, encoded))

    def delete(self, namespace: str, key: str) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute("DELETE FROM flaxon_admin_store WHERE namespace=? AND key=?", (namespace, key))

    def list(self, namespace: str) -> dict[str, Any]:
        with sqlite3.connect(self.path) as db:
            rows = db.execute("SELECT key,value FROM flaxon_admin_store WHERE namespace=?", (namespace,)).fetchall()
        return {key: json.loads(value) for key, value in rows}


class AdminRateLimit:
    """Rate-limit mutating requests under an admin prefix."""

    def __init__(self, app: Any, prefix: str = "/admin", requests: int = 120, window_seconds: int = 60) -> None:
        self.app = app
        self.prefix = prefix.rstrip("/")
        self.limiter = RateLimiter(requests=requests, window_seconds=window_seconds)

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        path = str(scope.get("path", ""))
        method = str(scope.get("method", "GET")).upper()
        if scope.get("type") == "http" and path.startswith(self.prefix) and method not in {"GET", "HEAD", "OPTIONS"}:
            if not await self.limiter.check(scope):
                from flaxon.http import JSONResponse
                await JSONResponse({"error": "Too many admin requests"}, status_code=429)(scope, receive, send)
                return
        await self.app(scope, receive, send)


class RedisAdminSessionBackend:
    """Session backend compatible with ``AdminAuth`` for multi-worker deployments."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", prefix: str = "flaxon:admin:session") -> None:
        self.redis_url = redis_url
        self.prefix = prefix
        self.client: Any = None

    async def _client(self) -> Any:
        if self.client is None:
            import redis.asyncio as redis
            self.client = redis.from_url(self.redis_url, decode_responses=True)
        return self.client

    def _key(self, token: str) -> str:
        return f"{self.prefix}:{token}"

    async def create_token(self, user: User, expires_in: int | None = None) -> str:
        token = uuid.uuid4().hex
        await (await self._client()).setex(self._key(token), expires_in or 86400, json.dumps(user.to_dict()))
        return token

    async def authenticate(self, request: Request) -> User | None:
        token = request.cookies.get("session_id")
        return await self.validate_token(token) if token else None

    async def validate_token(self, token: str) -> User | None:
        value = await (await self._client()).get(self._key(token))
        return User.from_dict(json.loads(value)) if value else None

    async def revoke_token(self, token: str) -> None:
        await (await self._client()).delete(self._key(token))
