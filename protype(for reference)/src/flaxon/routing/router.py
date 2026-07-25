from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from flaxon.exceptions import MethodNotAllowed, NotFound

from .route import Route, WebSocketRoute


@dataclass
class RouteMatch:
    route: Route
    params: dict[str, Any]


@dataclass
class WebSocketMatch:
    route: WebSocketRoute
    params: dict[str, Any]


class Router:
    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix.rstrip("/")
        self.routes: list[Route] = []
        self.websocket_routes: list[WebSocketRoute] = []

    def add_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: set[str] | list[str] | tuple[str, ...] = ("GET",),
        name: str | None = None,
    ) -> Route:
        full_path = self._join(path)
        route = Route(full_path, endpoint, set(methods), name)
        self.routes.append(route)
        return route

    def add_websocket(self, path: str, endpoint: Callable[..., Any], *, name: str | None = None) -> WebSocketRoute:
        route = WebSocketRoute(self._join(path), endpoint, name)
        self.websocket_routes.append(route)
        return route

    def route(self, path: str, *, methods: set[str] | list[str] | tuple[str, ...] = ("GET",), name: str | None = None):
        def decorator(endpoint: Callable[..., Any]) -> Callable[..., Any]:
            self.add_route(path, endpoint, methods=methods, name=name)
            return endpoint
        return decorator

    def get(self, path: str, *, name: str | None = None):
        return self.route(path, methods={"GET"}, name=name)

    def post(self, path: str, *, name: str | None = None):
        return self.route(path, methods={"POST"}, name=name)

    def websocket(self, path: str, *, name: str | None = None):
        def decorator(endpoint: Callable[..., Any]) -> Callable[..., Any]:
            self.add_websocket(path, endpoint, name=name)
            return endpoint
        return decorator

    def include_router(self, other: "Router") -> None:
        for route in other.routes:
            self.add_route(route.path, route.endpoint, methods=route.methods, name=route.name)
        for route in other.websocket_routes:
            self.add_websocket(route.path, route.endpoint, name=route.name)

    def match(self, path: str, method: str) -> RouteMatch:
        allowed: set[str] = set()
        for route in self.routes:
            params = route.match_path(path)
            if params is None:
                continue
            if method.upper() in route.methods or (method.upper() == "HEAD" and "GET" in route.methods):
                return RouteMatch(route, params)
            allowed.update(route.methods)
        if allowed:
            raise MethodNotAllowed(allowed)
        raise NotFound()

    def match_websocket(self, path: str) -> WebSocketMatch:
        for route in self.websocket_routes:
            params = route.match_path(path)
            if params is not None:
                return WebSocketMatch(route, params)
        raise NotFound("The requested WebSocket route was not found.")

    def url_for(self, name: str, **params: Any) -> str:
        for route in [*self.routes, *self.websocket_routes]:
            if route.name != name:
                continue
            path = route.path
            for key, value in params.items():
                path = re_sub_parameter(path, key, str(value))
            if "<" in path or "{" in path:
                raise KeyError(f"Missing parameters for route '{name}'.")
            return path
        raise KeyError(f"No route named '{name}'.")

    def _join(self, path: str) -> str:
        path = path if path.startswith("/") else f"/{path}"
        if not self.prefix:
            return path
        return f"{self.prefix}{path}" or "/"


def re_sub_parameter(path: str, name: str, value: str) -> str:
    import re
    path = re.sub(rf"<(?:(?:[a-zA-Z_][a-zA-Z0-9_]*):)?{re.escape(name)}>", value, path)
    path = re.sub(rf"\{{{re.escape(name)}(?::[a-zA-Z_][a-zA-Z0-9_]*)?\}}", value, path)
    return path
