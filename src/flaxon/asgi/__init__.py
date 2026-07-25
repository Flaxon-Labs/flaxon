"""
ASGI module for Flaxon.

This module contains ASGI protocol implementations, handlers, and utilities
for HTTP, WebSocket, and lifespan events.
"""

from __future__ import annotations

from .application import ASGIApplication
from .http import HTTPHandler
from .lifespan import LifespanHandler
from .protocol import Protocol
from .utils import get_client_ip, get_request_id, parse_headers
from .websocket import WebSocketHandler

__all__ = [
    "ASGIApplication",
    "HTTPHandler",
    "LifespanHandler",
    "Protocol",
    "WebSocketHandler",
    "get_client_ip",
    "get_request_id",
    "parse_headers",
]
