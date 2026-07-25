"""
Route resolver for Flaxon.

This module provides route resolution for matching incoming requests
to registered routes.
"""

from __future__ import annotations

from typing import Any

from .router import Router


class RouteResolver:
    """
    Resolves routes for incoming requests.

    This class handles matching HTTP and WebSocket requests to
    registered routes.
    """

    def __init__(self, router: Router) -> None:
        """
        Initialize the route resolver.

        Args:
            router: The router to resolve routes from.
        """
        self.router = router

    def resolve_http(self, path: str, method: str) -> tuple[Any, dict[str, Any]]:
        """
        Resolve an HTTP request to a route.

        Args:
            path: The request path.
            method: The HTTP method.

        Returns:
            A tuple of (endpoint, parameters).

        Raises:
            NotFound: If no route matches the path.
            MethodNotAllowed: If the path matches but the method is not allowed.
        """
        match = self.router.match(path, method)
        return match.route.endpoint, match.params

    def resolve_websocket(self, path: str) -> tuple[Any, dict[str, Any]]:
        """
        Resolve a WebSocket request to a route.

        Args:
            path: The WebSocket path.

        Returns:
            A tuple of (endpoint, parameters).

        Raises:
            NotFound: If no WebSocket route matches the path.
        """
        match = self.router.match_websocket(path)
        return match.route.endpoint, match.params

    def resolve_route(self, path: str) -> Any | None:
        """
        Resolve a route by path only (for static file serving, etc.).

        Args:
            path: The path to resolve.

        Returns:
            The matched route or None.
        """
        for route in self.router.routes:
            if route.match_path(path) is not None:
                return route
        return None

    def resolve_websocket_route(self, path: str) -> Any | None:
        """
        Resolve a WebSocket route by path.

        Args:
            path: The path to resolve.

        Returns:
            The matched WebSocket route or None.
        """
        for route in self.router.websocket_routes:
            if route.match_path(path) is not None:
                return route
        return None

    def get_all_http_routes(self) -> list[tuple[str, str, str]]:
        """
        Get all HTTP routes.

        Returns:
            A list of tuples (method, path, name).
        """
        routes = []
        for route in self.router.routes:
            for method in route.methods:
                routes.append((method, route.path, route.name or ""))
        return routes

    def get_all_websocket_routes(self) -> list[tuple[str, str]]:
        """
        Get all WebSocket routes.

        Returns:
            A list of tuples (path, name).
        """
        return [(route.path, route.name or "") for route in self.router.websocket_routes]
