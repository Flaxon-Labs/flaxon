"""
Protocol definitions for Flaxon.

This module defines protocols (interfaces) that components must implement
to be used with the framework.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable

from .typing import JSONValue, ReceiveType, ScopeType, SendType

# ============================================================
# ASGI Protocol
# ============================================================


@runtime_checkable
class ASGIApplication(Protocol):
    """Protocol for ASGI applications."""

    async def __call__(self, scope: ScopeType, receive: ReceiveType, send: SendType) -> None: ...


# ============================================================
# Middleware Protocol
# ============================================================


@runtime_checkable
class Middleware(Protocol):
    """Protocol for middleware components."""

    def __init__(self, app: ASGIApplication, **options: Any) -> None: ...

    async def __call__(self, scope: ScopeType, receive: ReceiveType, send: SendType) -> None: ...


# ============================================================
# Router Protocol
# ============================================================


@runtime_checkable
class RouterProtocol(Protocol):
    """Protocol for routers."""

    def route(self, path: str, **kwargs: Any) -> Any: ...

    def get(self, path: str, **kwargs: Any) -> Any: ...

    def post(self, path: str, **kwargs: Any) -> Any: ...

    def put(self, path: str, **kwargs: Any) -> Any: ...

    def patch(self, path: str, **kwargs: Any) -> Any: ...

    def delete(self, path: str, **kwargs: Any) -> Any: ...

    def websocket(self, path: str, **kwargs: Any) -> Any: ...

    def include_router(self, router: RouterProtocol, prefix: str | None = None) -> None: ...

    def match(self, path: str, method: str) -> Any: ...

    def match_websocket(self, path: str) -> Any: ...

    def url_for(self, name: str, **params: Any) -> str: ...


# ============================================================
# Request Protocol
# ============================================================


@runtime_checkable
class RequestProtocol(Protocol):
    """Protocol for HTTP requests."""

    method: str
    path: str
    headers: dict[str, str]
    path_params: dict[str, Any]
    query: dict[str, Any]
    cookies: dict[str, str]
    client: tuple[str, int] | None

    async def body(self) -> bytes: ...

    async def json(self) -> JSONValue: ...

    async def text(self) -> str: ...

    async def render(self, template_name: str, context: dict[str, Any] | None = None) -> Any: ...


# ============================================================
# Response Protocol
# ============================================================


@runtime_checkable
class ResponseProtocol(Protocol):
    """Protocol for HTTP responses."""

    status_code: int
    headers: dict[str, str]
    body: bytes

    async def __call__(self, scope: ScopeType, receive: ReceiveType, send: SendType) -> None: ...

    @classmethod
    def from_value(cls, value: Any) -> ResponseProtocol: ...


# ============================================================
# WebSocket Protocol
# ============================================================


@runtime_checkable
class WebSocketProtocol(Protocol):
    """Protocol for WebSocket connections."""

    path_params: dict[str, Any]
    accepted: bool
    closed: bool

    async def accept(self, subprotocol: str | None = None) -> None: ...

    async def receive_text(self) -> str: ...

    async def receive_json(self) -> JSONValue: ...

    async def send_text(self, value: str) -> None: ...

    async def send_json(self, value: Any) -> None: ...

    async def close(self, code: int = 1000) -> None: ...

    async def join(self, room: str) -> None: ...

    async def leave(self, room: str) -> None: ...

    async def broadcast_json(self, room: str, value: Any) -> None: ...

    def iter_json(self) -> AsyncIterator[JSONValue]: ...


# ============================================================
# Validator Protocol
# ============================================================


@runtime_checkable
class ValidatorProtocol(Protocol):
    """Protocol for validation schemas."""

    __fields__: dict[str, Any]

    @classmethod
    def load(cls, data: dict[str, Any]) -> ValidatorProtocol: ...

    def to_dict(self) -> dict[str, Any]: ...


# ============================================================
# Cache Protocol
# ============================================================


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for cache backends."""

    async def get(self, key: str) -> Any: ...

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None: ...

    async def delete(self, key: str) -> None: ...

    async def clear(self) -> None: ...

    async def exists(self, key: str) -> bool: ...


# ============================================================
# Session Protocol
# ============================================================


@runtime_checkable
class SessionProtocol(Protocol):
    """Protocol for session backends."""

    async def get(self, session_id: str, key: str) -> Any: ...

    async def set(self, session_id: str, key: str, value: Any) -> None: ...

    async def delete(self, session_id: str, key: str) -> None: ...

    async def clear(self, session_id: str) -> None: ...

    async def exists(self, session_id: str) -> bool: ...


# ============================================================
# Plugin Protocol
# ============================================================


@runtime_checkable
class PluginProtocol(Protocol):
    """Protocol for plugins."""

    name: str
    version: str

    def setup(self, app: ASGIApplication) -> None: ...

    def startup(self) -> None: ...

    def shutdown(self) -> None: ...


# ============================================================
# Health Check Protocol
# ============================================================


@runtime_checkable
class HealthCheckProtocol(Protocol):
    """Protocol for health checks."""

    async def check(self) -> dict[str, Any]: ...


# ============================================================
# Task Protocol
# ============================================================


@runtime_checkable
class TaskProtocol(Protocol):
    """Protocol for background tasks."""

    async def run(self, *args: Any, **kwargs: Any) -> Any: ...


# ============================================================
# Export
# ============================================================

__all__ = [
    "ASGIApplication",
    "CacheProtocol",
    "HealthCheckProtocol",
    "Middleware",
    "PluginProtocol",
    "RequestProtocol",
    "ResponseProtocol",
    "RouterProtocol",
    "SessionProtocol",
    "TaskProtocol",
    "ValidatorProtocol",
    "WebSocketProtocol",
]
