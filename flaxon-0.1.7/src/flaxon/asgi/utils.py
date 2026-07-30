"""
ASGI utility functions.

This module provides utility functions for working with ASGI scopes
and messages.
"""

from __future__ import annotations

import uuid
from typing import Any


def parse_headers(scope: dict[str, Any]) -> dict[str, str]:
    """
    Parse ASGI headers into a dictionary.

    Args:
        scope: The ASGI scope dictionary.

    Returns:
        A dictionary of header names to values.
    """
    headers = {}
    for key, value in scope.get("headers", []):
        headers[key.decode("latin-1").lower()] = value.decode("latin-1")
    return headers


def get_client_ip(scope: dict[str, Any]) -> str | None:
    """
    Get the client IP address from the ASGI scope.

    Args:
        scope: The ASGI scope dictionary.

    Returns:
        The client IP address or None.
    """
    client = scope.get("client")
    if client:
        return client[0]

    headers = parse_headers(scope)
    forwarded = headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    return None


def get_request_id(scope: dict[str, Any]) -> str:
    """
    Get or generate a request ID.

    Args:
        scope: The ASGI scope dictionary.

    Returns:
        A request ID string.
    """
    request_id = scope.get("flaxon.request_id")
    if request_id:
        return request_id

    headers = parse_headers(scope)
    request_id = headers.get("x-request-id")

    if not request_id:
        request_id = uuid.uuid4().hex[:16]

    scope["flaxon.request_id"] = request_id
    return request_id


def get_scope_type(scope: dict[str, Any]) -> str:
    """
    Get the scope type from the ASGI scope.

    Args:
        scope: The ASGI scope dictionary.

    Returns:
        The scope type string.
    """
    return scope.get("type", "unknown")


def is_http_scope(scope: dict[str, Any]) -> bool:
    """Check if the scope is an HTTP scope."""
    return get_scope_type(scope) == "http"


def is_websocket_scope(scope: dict[str, Any]) -> bool:
    """Check if the scope is a WebSocket scope."""
    return get_scope_type(scope) == "websocket"


def is_lifespan_scope(scope: dict[str, Any]) -> bool:
    """Check if the scope is a lifespan scope."""
    return get_scope_type(scope) == "lifespan"


def get_path(scope: dict[str, Any]) -> str:
    """
    Get the path from the ASGI scope.

    Args:
        scope: The ASGI scope dictionary.

    Returns:
        The path string.
    """
    return scope.get("path", "/")


def get_method(scope: dict[str, Any]) -> str:
    """
    Get the HTTP method from the ASGI scope.

    Args:
        scope: The ASGI scope dictionary.

    Returns:
        The HTTP method string.
    """
    return scope.get("method", "GET").upper()


def get_query_string(scope: dict[str, Any]) -> str:
    """
    Get the query string from the ASGI scope.

    Args:
        scope: The ASGI scope dictionary.

    Returns:
        The query string.
    """
    qs = scope.get("query_string", b"").decode("utf-8")
    return f"?{qs}" if qs else ""


def get_full_path(scope: dict[str, Any]) -> str:
    """
    Get the full path including query string.

    Args:
        scope: The ASGI scope dictionary.

    Returns:
        The full path with query string.
    """
    return f"{get_path(scope)}{get_query_string(scope)}"


def get_scheme(scope: dict[str, Any]) -> str:
    """
    Get the scheme from the ASGI scope.

    Args:
        scope: The ASGI scope dictionary.

    Returns:
        The scheme string.
    """
    return scope.get("scheme", "http")


def get_server(scope: dict[str, Any]) -> tuple[str, int] | None:
    """
    Get the server address from the ASGI scope.

    Args:
        scope: The ASGI scope dictionary.

    Returns:
        A tuple of (host, port) or None.
    """
    server = scope.get("server")
    if server:
        return (server[0], server[1])
    return None


def get_client(scope: dict[str, Any]) -> tuple[str, int] | None:
    """
    Get the client address from the ASGI scope.

    Args:
        scope: The ASGI scope dictionary.

    Returns:
        A tuple of (host, port) or None.
    """
    client = scope.get("client")
    if client:
        return (client[0], client[1])
    return None


def get_root_path(scope: dict[str, Any]) -> str:
    """
    Get the root path from the ASGI scope.

    Args:
        scope: The ASGI scope dictionary.

    Returns:
        The root path string.
    """
    return scope.get("root_path", "")


def get_subprotocols(scope: dict[str, Any]) -> list[str]:
    """
    Get the WebSocket subprotocols from the ASGI scope.

    Args:
        scope: The ASGI scope dictionary.

    Returns:
        A list of subprotocols.
    """
    return scope.get("subprotocols", [])
