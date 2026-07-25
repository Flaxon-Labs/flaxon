"""HTTP and WebSocket route registry."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from flaxon.exceptions import MethodNotAllowed, NotFound

from .route import Route, WebSocketRoute


@dataclass
class RouteMatch:
    """The route and extracted values selected for a request."""

    route: Route | WebSocketRoute
    params: dict[str, Any]


class Router:
    """Register routes and resolve them by request path and method."""

    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix.rstrip("/")
        self.routes: list[Route] = []
        self.websocket_routes: list[WebSocketRoute] = []

    def route(self, path: str, *, methods: set[str] | list[str] | tuple[str, ...] = ("GET",), name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Return a decorator that registers an HTTP endpoint."""
        def decorator(endpoint: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(Route(self._path(path), endpoint, {method.upper() for method in methods}, name or endpoint.__name__))
            return endpoint
        return decorator

    def get(self, path: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.route(path, methods={"GET"}, name=name)

    def post(self, path: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.route(path, methods={"POST"}, name=name)

    def put(self, path: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.route(path, methods={"PUT"}, name=name)

    def patch(self, path: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.route(path, methods={"PATCH"}, name=name)

    def delete(self, path: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.route(path, methods={"DELETE"}, name=name)

    def websocket(self, path: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Return a decorator that registers a WebSocket endpoint."""
        def decorator(endpoint: Callable[..., Any]) -> Callable[..., Any]:
            self.websocket_routes.append(WebSocketRoute(self._path(path), endpoint, name or endpoint.__name__))
            return endpoint
        return decorator

    def match(self, path: str, method: str) -> RouteMatch:
        """Find the HTTP route matching a path and method."""
        method_allowed = False
        for route in self.routes:
            params = route.match(path)
            if params is None:
                continue
            if method.upper() in route.methods:
                return RouteMatch(route, params)
            method_allowed = True
        if method_allowed:
            raise MethodNotAllowed()
        raise NotFound()

    def match_websocket(self, path: str) -> RouteMatch:
        """Find the WebSocket route matching a path."""
        for route in self.websocket_routes:
            params = route.match(path)
            if params is not None:
                return RouteMatch(route, params)
        raise NotFound()

    def include_router(self, router: Router) -> None:
        """Copy routes from another router."""
        self.routes.extend(router.routes)
        self.websocket_routes.extend(router.websocket_routes)

    def url_for(self, name: str, **params: Any) -> str:
        """Build a URL from a named route and its parameters."""
        for route in self.routes:
            if route.name == name:
                path = route.path
                for parameter, _converter in route.parameters:
                    marker = next(match.group(0) for match in __import__("re").finditer(r"<(?:(?:[a-zA-Z_][a-zA-Z0-9_]*):)?" + parameter + r">", path))
                    path = path.replace(marker, str(params[parameter]))
                return path
        raise KeyError(f"No route named {name!r}")

    def _path(self, path: str) -> str:
        return f"{self.prefix}{path}" if self.prefix else path
