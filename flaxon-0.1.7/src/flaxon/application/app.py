"""The main Flaxon ASGI application."""

from __future__ import annotations

import inspect
import logging
import sys
import time
import traceback
import uuid
from collections.abc import Callable
from typing import Any

from flaxon.debugging import Dashboard, Debugger, ErrorStore
from flaxon.exceptions import HTTPException
from flaxon.http import HTMLResponse, JSONResponse, Request, Response
from flaxon.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from flaxon.routing import Router
from flaxon.websocket import WebSocket, WebSocketManager

from .configuration import Config
from .lifecycle import Lifecycle
from .state import State

logger = logging.getLogger("flaxon")


class Flaxon:
    """An async-first ASGI application with route and middleware support."""

    def __init__(self, name: str = "FlaxonApp", *, debug: bool | None = None, config: dict[str, Any] | None = None) -> None:
        self.name = name
        self.config = Config(config)
        if debug is not None:
            self.config["DEBUG"] = debug
        self.debug = bool(self.config["DEBUG"])
        self.router = Router()
        self.state = State()
        self.lifecycle = Lifecycle()
        self.jinax: Any = None
        self.websocket_manager = WebSocketManager()
        self.error_store = ErrorStore()
        self.debugger = Debugger(debug=self.debug)
        self._middleware: list[tuple[type[Any], dict[str, Any]]] = [(RequestIDMiddleware, {}), (SecurityHeadersMiddleware, {})]
        self._middleware_stack: Any = None

        if self.debug:
            self.router.route("/__debug__", methods=("GET",), name="flaxon_debug_dashboard")(self._debug_dashboard)

    async def _debug_dashboard(self) -> HTMLResponse:
        """Render the debug dashboard showing recent errors (debug mode only)."""
        return Dashboard(self.error_store, debug=self.debug).render()

    def route(self, path: str, *, methods: set[str] | list[str] | tuple[str, ...] = ("GET",), name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a route with an explicit set of HTTP methods."""
        return self.router.route(path, methods=methods, name=name)

    def get(self, path: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a GET route."""
        return self.router.get(path, name=name)

    def post(self, path: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a POST route."""
        return self.router.post(path, name=name)

    def put(self, path: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a PUT route."""
        return self.router.put(path, name=name)

    def patch(self, path: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a PATCH route."""
        return self.router.patch(path, name=name)

    def delete(self, path: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a DELETE route."""
        return self.router.delete(path, name=name)

    def websocket(self, path: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a WebSocket route."""
        return self.router.websocket(path, name=name)

    def add_middleware(self, middleware_class: type[Any], **options: Any) -> None:
        """Add middleware, with first-added middleware executing outermost."""
        self._middleware.append((middleware_class, options))
        self._middleware_stack = None

    def include_router(self, router: Router) -> None:
        """Include routes registered on another router."""
        self.router.include_router(router)

    def url_for(self, name: str, **params: Any) -> str:
        """Build a URL for a named route."""
        return self.router.url_for(name, **params)

    def use_templates(self, engine: Any) -> None:
        """Set the template engine used by request rendering."""
        self.jinax = engine

    def on_startup(self, callback: Callable[..., Any]) -> Callable[..., Any]:
        """Register a startup callback."""
        return self.lifecycle.on_startup(callback)

    def on_shutdown(self, callback: Callable[..., Any]) -> Callable[..., Any]:
        """Register a shutdown callback."""
        return self.lifecycle.on_shutdown(callback)

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """Handle one ASGI connection."""
        if self._middleware_stack is None:
            app: Any = self._dispatch
            for middleware, options in reversed(self._middleware):
                app = middleware(app, **options)
            self._middleware_stack = app
        await self._middleware_stack(scope, receive, send)

    async def _dispatch(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        scope["app"] = self
        match scope.get("type"):
            case "http":
                await self._handle_http(scope, receive, send)
            case "websocket":
                await self._handle_websocket(scope, receive, send)
            case "lifespan":
                await self._handle_lifespan(receive, send)
            case value:
                raise RuntimeError(f"Unsupported ASGI scope type: {value!r}")

    async def _handle_http(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        request = Request(scope, receive, self)
        try:
            matched = self.router.match(request.path, request.method)
            request.path_params = matched.params
            result = await self._invoke(matched.route.endpoint, request, matched.params)
            response = Response.from_value(result)
        except HTTPException as exc:
            response = JSONResponse(exc.to_dict(), status_code=exc.status_code)
        except Exception as exc:
            # Print unhandled stack trace to terminal so errors are visible in stdout/stderr
            sys.stderr.write(f"ERROR processing request [{request.method} {request.path}]:\n")
            traceback.print_exc(file=sys.stderr)

            response = await self.debugger.response_for(exc, request, scope)
            if self.debug:
                self.error_store.store(
                    {
                        "error_id": str(scope.get("flaxon.request_id") or uuid.uuid4()),
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "path": request.path,
                        "timestamp": time.time(),
                    }
                )
        if request.method == "HEAD":
            response.body = b""
            response.headers["content-length"] = "0"
        await response(scope, receive, send)

    async def _invoke(self, endpoint: Callable[..., Any], request: Request | WebSocket, params: dict[str, Any]) -> Any:
        signature = inspect.signature(endpoint)
        kwargs: dict[str, Any] = {}
        for name, parameter in signature.parameters.items():
            if name in params:
                kwargs[name] = params[name]
            elif name in {"request", "socket", "websocket"}:
                kwargs[name] = request
            elif parameter.default is not inspect.Parameter.empty:
                continue
            else:
                raise TypeError(f"Cannot resolve endpoint parameter {name!r}")
        result = endpoint(**kwargs)
        return await result if inspect.isawaitable(result) else result

    async def _handle_websocket(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        socket = WebSocket(scope, receive, send, self.websocket_manager)
        try:
            matched = self.router.match_websocket(str(scope.get("path", "/")))
            socket.path_params = matched.params
            await self._invoke(matched.route.endpoint, socket, matched.params)
        except HTTPException:
            await socket.close(code=4404, reason="WebSocket route not found")
        except Exception as exc:
            sys.stderr.write(f"ERROR processing WebSocket connection:\n")
            traceback.print_exc(file=sys.stderr)
            await socket.close(code=1011, reason="Internal server error")

    async def _handle_lifespan(self, receive: Any, send: Any) -> None:
        while True:
            message = await receive()
            if message.get("type") == "lifespan.startup":
                try:
                    await self.lifecycle.startup()
                except Exception as exc:
                    await send({"type": "lifespan.startup.failed", "message": str(exc)})
                else:
                    await send({"type": "lifespan.startup.complete"})
            elif message.get("type") == "lifespan.shutdown":
                try:
                    await self.lifecycle.shutdown()
                except Exception as exc:
                    await send({"type": "lifespan.shutdown.failed", "message": str(exc)})
                else:
                    await send({"type": "lifespan.shutdown.complete"})
                return