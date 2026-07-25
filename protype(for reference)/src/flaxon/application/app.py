from __future__ import annotations

import inspect
from typing import Any, Callable

from flaxon.debugging import Debugger
from flaxon.exceptions import HTTPException
from flaxon.http import Request, Response
from flaxon.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from flaxon.routing import Router
from flaxon.validation import Schema
from flaxon.websocket import WebSocket, WebSocketManager

from .configuration import Config
from .lifecycle import Lifecycle, call_maybe_async
from .state import State


class Flaxon:
    """ASGI application and public framework entry point."""

    def __init__(
        self,
        name: str,
        *,
        debug: bool | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.config = Config(config)
        if debug is not None:
            self.config["DEBUG"] = debug
        self.debug = bool(self.config["DEBUG"])
        self.router = Router()
        self.state = State()
        self.lifecycle = Lifecycle()
        self.debugger = Debugger(debug=self.debug)
        self.jinax: Any = None
        self.websocket_manager = WebSocketManager()
        self._middleware: list[tuple[type[Any], dict[str, Any]]] = [
            (RequestIDMiddleware, {}),
            (SecurityHeadersMiddleware, {}),
        ]
        self._middleware_stack: Any = None

    def route(
        self,
        path: str,
        *,
        methods: set[str] | list[str] | tuple[str, ...] = ("GET",),
        name: str | None = None,
    ):
        return self.router.route(path, methods=methods, name=name)

    def get(self, path: str, *, name: str | None = None):
        return self.route(path, methods={"GET"}, name=name)

    def post(self, path: str, *, name: str | None = None):
        return self.route(path, methods={"POST"}, name=name)

    def put(self, path: str, *, name: str | None = None):
        return self.route(path, methods={"PUT"}, name=name)

    def patch(self, path: str, *, name: str | None = None):
        return self.route(path, methods={"PATCH"}, name=name)

    def delete(self, path: str, *, name: str | None = None):
        return self.route(path, methods={"DELETE"}, name=name)

    def websocket(self, path: str, *, name: str | None = None):
        return self.router.websocket(path, name=name)

    def include_router(self, router: Router) -> None:
        self.router.include_router(router)

    def add_middleware(self, middleware_class: type[Any], **options: Any) -> None:
        self._middleware.append((middleware_class, options))
        self._middleware_stack = None

    def use_templates(self, engine: Any) -> None:
        self.jinax = engine

    def on_startup(self, callback: Callable[..., Any]) -> Callable[..., Any]:
        return self.lifecycle.on_startup(callback)

    def on_shutdown(self, callback: Callable[..., Any]) -> Callable[..., Any]:
        return self.lifecycle.on_shutdown(callback)

    def url_for(self, name: str, **params: Any) -> str:
        return self.router.url_for(name, **params)

    @property
    def routes(self) -> list[Any]:
        return self.router.routes

    def _build_middleware_stack(self) -> Any:
        app: Any = self._dispatch
        for middleware_class, options in reversed(self._middleware):
            app = middleware_class(app, **options)
        return app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if self._middleware_stack is None:
            self._middleware_stack = self._build_middleware_stack()
        await self._middleware_stack(scope, receive, send)

    async def _dispatch(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        scope.setdefault("app", self)
        scope_type = scope.get("type")
        if scope_type == "lifespan":
            await self._handle_lifespan(receive, send)
            return
        if scope_type == "http":
            await self._handle_http(scope, receive, send)
            return
        if scope_type == "websocket":
            await self._handle_websocket(scope, receive, send)
            return
        raise RuntimeError(f"Unsupported ASGI scope type: {scope_type}")

    async def _handle_lifespan(self, receive: Any, send: Any) -> None:
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                try:
                    await self.lifecycle.startup()
                    await send({"type": "lifespan.startup.complete"})
                except Exception as exc:
                    await send({"type": "lifespan.startup.failed", "message": str(exc)})
            elif message["type"] == "lifespan.shutdown":
                try:
                    await self.lifecycle.shutdown()
                    await send({"type": "lifespan.shutdown.complete"})
                except Exception as exc:
                    await send({"type": "lifespan.shutdown.failed", "message": str(exc)})
                return

    async def _handle_http(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        request = Request(scope, receive, self)
        try:
            match = self.router.match(request.path, request.method)
            scope["path_params"] = match.params
            request.path_params = match.params
            value = await self._invoke_http(match.route.endpoint, request, match.params)
            response = Response.from_value(value)
        except Exception as exc:
            response = await self.debugger.response_for(exc, request, scope)
        if request.method == "HEAD":
            response.body = b""
            response.headers["content-length"] = "0"
        await response(scope, receive, send)

    async def _invoke_http(self, endpoint: Callable[..., Any], request: Request, params: dict[str, Any]) -> Any:
        signature = inspect.signature(endpoint)
        kwargs: dict[str, Any] = {}
        json_body: Any = None
        for name, parameter in signature.parameters.items():
            annotation = parameter.annotation
            if name in params:
                kwargs[name] = params[name]
            elif name == "request" or annotation is Request:
                kwargs[name] = request
            elif inspect.isclass(annotation) and issubclass(annotation, Schema):
                if json_body is None:
                    json_body = await request.json()
                kwargs[name] = annotation.load(json_body)
            elif parameter.default is not inspect.Parameter.empty:
                continue
            else:
                raise TypeError(f"Cannot resolve endpoint parameter '{name}'.")
        return await call_maybe_async(endpoint, **kwargs)

    async def _handle_websocket(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        socket = WebSocket(scope, receive, send, self.websocket_manager)
        try:
            match = self.router.match_websocket(scope.get("path", "/"))
            scope["path_params"] = match.params
            socket.path_params = match.params
            await self._invoke_websocket(match.route.endpoint, socket, match.params)
        except HTTPException:
            await socket.close(code=4404, reason="WebSocket route not found")
        except Exception:
            await socket.close(code=1011, reason="Internal server error")

    async def _invoke_websocket(self, endpoint: Callable[..., Any], socket: WebSocket, params: dict[str, Any]) -> Any:
        signature = inspect.signature(endpoint)
        kwargs: dict[str, Any] = {}
        for name, parameter in signature.parameters.items():
            annotation = parameter.annotation
            if name in params:
                kwargs[name] = params[name]
            elif name in {"socket", "websocket"} or annotation is WebSocket:
                kwargs[name] = socket
            elif parameter.default is not inspect.Parameter.empty:
                continue
            else:
                raise TypeError(f"Cannot resolve WebSocket endpoint parameter '{name}'.")
        return await call_maybe_async(endpoint, **kwargs)

    def run(self, host: str = "127.0.0.1", port: int = 8000, *, reload: bool = False) -> None:
        try:
            import uvicorn
        except ImportError as exc:
            raise RuntimeError("Install the server extra: pip install 'flaxon-framework[server]'") from exc
        uvicorn.run(self, host=host, port=port, reload=reload)
