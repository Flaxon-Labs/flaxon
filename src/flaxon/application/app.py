"""The main Flaxon ASGI application."""

from __future__ import annotations

import inspect
import time
import uuid
from collections.abc import Callable
from typing import Any
from pathlib import Path

from flaxon.debugging import Dashboard, Debugger, ErrorStore
from flaxon.exceptions import HTTPException
from flaxon.http import HTMLResponse, JSONResponse, Request, Response
from flaxon.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from flaxon.plugins import PluginManager
from flaxon.routing import Router
from flaxon.websocket import WebSocket, WebSocketManager

from flaxon.admin import AdminDashboard, AdminConfig
from flaxon.graphql import GraphQLSchema
from flaxon.graphql.playground import AltairPlayground, GraphiQLPlayground
from flaxon.graphql.middleware import GraphQLMiddleware

from .configuration import Config
from .lifecycle import Lifecycle
from .state import State


class Flaxon:
    """An async-first ASGI application with route and middleware support."""

    def __init__(self, name: str, *, debug: bool | None = None, config: dict[str, Any] | None = None) -> None:
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
        self.plugins = PluginManager(self)
        self._middleware: list[tuple[type[Any], dict[str, Any]]] = [(RequestIDMiddleware, {}), (SecurityHeadersMiddleware, {})]
        self._middleware_stack: Any = None

        # ============================================================
        # NEW: ADMIN & GRAPHQL PROPERTIES
        # ============================================================
        self._admin: AdminDashboard | None = None
        self._graphql_schema: GraphQLSchema | None = None
        self._graphql_middleware: GraphQLMiddleware | None = None


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



            # ============================================================
    # ADMIN METHODS
    # ============================================================

    def enable_admin(
        self,
        url_prefix: str = "/admin",
        config: AdminConfig | None = None,
        template_dir: str = "templates/admin",
    ) -> Any:
        """
        Enable the admin dashboard.

        Args:
            url_prefix: URL prefix for admin routes (default: "/admin")
            config: Admin configuration
            template_dir: Template directory path

        Returns:
            AdminDashboard instance
        """
        from flaxon.admin import AdminDashboard

        self._admin = AdminDashboard(self, config, url_prefix, template_dir)
        return self._admin

    @property
    def admin(self) -> Any:
        """Get the admin dashboard instance."""
        return self._admin

    # ============================================================
    # GRAPHQL METHODS
    # ============================================================

    def enable_graphql(
        self,
        schema: GraphQLSchema | None = None,
        url: str = "/graphql",
        enable_playground: bool = True,
    ) -> GraphQLSchema:
        """
        Enable GraphQL support.

        Args:
            schema: GraphQL schema (creates new if None)
            url: GraphQL endpoint URL (default: "/graphql")
            enable_playground: Enable GraphiQL and Altair playgrounds

        Returns:
            GraphQLSchema instance
        """
        from flaxon.graphql import GraphQLSchema
        from flaxon.graphql.middleware import GraphQLMiddleware

        self._graphql_schema = schema or GraphQLSchema()
        self._graphql_middleware = GraphQLMiddleware(self)

        @self.router.post(url)
        async def graphql_endpoint(request):
            return await self._handle_graphql(request)

        if enable_playground:
            self._register_graphql_playground(url)

        self.add_middleware(GraphQLMiddleware)

        return self._graphql_schema

    async def _handle_graphql(self, request):
        """Handle GraphQL requests."""
        if self._graphql_schema is None:
            return JSONResponse(
                {"errors": [{"message": "GraphQL not configured"}]},
                status_code=500,
            )

        try:
            data = await request.json()
            query = data.get("query", "")
            variables = data.get("variables", {})
            operation_name = data.get("operationName")

            result = await self._graphql_schema.execute(
                query=query,
                variables=variables,
                context={"request": request},
                operation_name=operation_name,
            )

            return JSONResponse(result)

        except Exception as exc:
            return JSONResponse(
                {"errors": [{"message": str(exc)}]},
                status_code=500,
            )

    def _register_graphql_playground(self, url: str) -> None:
        """Register GraphQL playground routes."""
        from flaxon.graphql.playground import AltairPlayground, GraphiQLPlayground

        graphiql = GraphiQLPlayground(endpoint=url)
        altair = AltairPlayground(endpoint=url)

        @self.router.get(f"{url}/graphiql")
        async def graphiql_route(request):
            return await graphiql.render(request)

        @self.router.get(f"{url}/altair")
        async def altair_route(request):
            return await altair.render(request)

        @self.router.get(url)
        async def playground_index(request):
            from flaxon.http import HTMLResponse
            from jinja2 import Template

            html_path = Path(__file__).parent.parent / "graphql" / "playground" / "index.html"
            html_content = html_path.read_text()
        
        # Simple template replacement
            html = html_content.replace("{{ url }}", url)

            return HTMLResponse(html)

    @property
    def graphql(self) -> GraphQLSchema | None:
        """Get the GraphQL schema instance."""
        return self._graphql_schema

    # ============================================================
    # LIFECYCLE METHODS
    # ============================================================

    def on_startup(self, callback: Callable[..., Any]) -> Callable[..., Any]:
        """Register a startup callback."""
        return self.lifecycle.on_startup(callback)

    def on_shutdown(self, callback: Callable[..., Any]) -> Callable[..., Any]:
        """Register a shutdown callback."""
        return self.lifecycle.on_shutdown(callback)

    # ============================================================
    # ASGI INTERFACE
    # ============================================================

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
        except Exception:
            await socket.close(code=1011, reason="Internal server error")

    async def _handle_lifespan(self, receive: Any, send: Any) -> None:
        while True:
            message = await receive()
            if message.get("type") == "lifespan.startup":
                try:
                    await self.lifecycle.startup()
                    await self.plugins.startup()
                except Exception as exc:
                    await send({"type": "lifespan.startup.failed", "message": str(exc)})
                else:
                    await send({"type": "lifespan.startup.complete"})
            elif message.get("type") == "lifespan.shutdown":
                try:
                    await self.plugins.shutdown()
                    await self.lifecycle.shutdown()
                except Exception as exc:
                    await send({"type": "lifespan.shutdown.failed", "message": str(exc)})
                else:
                    await send({"type": "lifespan.shutdown.complete"})
                return
            

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
        except Exception:
            await socket.close(code=1011, reason="Internal server error")

    async def _handle_lifespan(self, receive: Any, send: Any) -> None:
        while True:
            message = await receive()
            if message.get("type") == "lifespan.startup":
                try:
                    await self.lifecycle.startup()
                    await self.plugins.startup()
                except Exception as exc:
                    await send({"type": "lifespan.startup.failed", "message": str(exc)})
                else:
                    await send({"type": "lifespan.startup.complete"})
            elif message.get("type") == "lifespan.shutdown":
                try:
                    await self.plugins.shutdown()
                    await self.lifecycle.shutdown()
                except Exception as exc:
                    await send({"type": "lifespan.shutdown.failed", "message": str(exc)})
                else:
                    await send({"type": "lifespan.shutdown.complete"})
                return