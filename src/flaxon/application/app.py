"""The main Flaxon ASGI application."""

from __future__ import annotations

import inspect
from pathlib import Path
import secrets
import time
import traceback
from collections.abc import Callable
from typing import Any
import uuid

from flaxon.admin import AdminConfig, AdminDashboard
from flaxon.debugging import Dashboard, Debugger, ErrorStore
from flaxon.dependency_injection import Container
from flaxon.exceptions import HTTPException
from flaxon.graphql import GraphQLSchema
from flaxon.graphql.playground import AltairPlayground, GraphiQLPlayground
from flaxon.health import HealthRegistry, LivenessProbe, ReadinessProbe, StartupProbe
from flaxon.http import HTMLResponse, JSONResponse, Request, Response
from flaxon.metrics import MetricsCollector, PrometheusExporter
from flaxon.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from flaxon.plugins import PluginManager
from flaxon.routing import Router
from flaxon.sessions import SessionManager
from flaxon.sessions.backends.memory import MemoryBackend
from flaxon.websocket import WebSocket, WebSocketManager

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
        
        # Core Infrastructure
        self.router = Router()
        self.state = State()
        self.lifecycle = Lifecycle()
        self.jinax: Any = None
        self.websocket_manager = WebSocketManager()
        self.error_store = ErrorStore()
        self.debugger = Debugger(debug=self.debug)
        self.plugins = PluginManager(self)
        self.container = Container()

        # Session Management
        self.sessions = SessionManager(
            backend=MemoryBackend(),
            secret_key=self.config.get_secret_key() or secrets.token_hex(32),
            cookie_secure=not self.debug,
        )

        # Middleware Stack Setup
        self._middleware: list[tuple[type[Any], dict[str, Any]]] = [
            (RequestIDMiddleware, {}),
            (SecurityHeadersMiddleware, {}),
        ]
        self._middleware_stack: Any = None

        # Health & Observability
        self.health = HealthRegistry()
        self._liveness_probe = LivenessProbe(self.health)
        self._readiness_probe = ReadinessProbe(self.health)
        self._startup_probe = StartupProbe(self.health)
        self.metrics = MetricsCollector()

        # System Endpoints
        self.router.route("/health", methods=("GET",), name="flaxon_health")(self._health_check)
        self.router.route("/health/live", methods=("GET",), name="flaxon_health_live")(self._health_live)
        self.router.route("/health/ready", methods=("GET",), name="flaxon_health_ready")(self._health_ready)
        self.router.route("/metrics", methods=("GET",), name="flaxon_metrics")(self._metrics_endpoint)

        if self.debug:
            self.router.route("/__debug__", methods=("GET",), name="flaxon_debug_dashboard")(self._debug_dashboard)

        # Admin & GraphQL Properties Initialization
        self._admin: AdminDashboard | None = None
        self._graphql_schema: GraphQLSchema | None = None

    # ============================================================
    # SYSTEM & DIAGNOSTIC ENDPOINTS
    # ============================================================

    async def _health_check(self) -> Any:
        """Liveness-style health check covering all registered checks."""
        return (await self._liveness_probe.check()).to_response()

    async def _health_live(self) -> Any:
        """Kubernetes-style liveness probe."""
        return (await self._liveness_probe.check()).to_response()

    async def _health_ready(self) -> Any:
        """Kubernetes-style readiness probe."""
        return (await self._readiness_probe.check()).to_response()

    async def _metrics_endpoint(self) -> Any:
        """Prometheus-format metrics for whatever has been recorded on self.metrics."""
        return PrometheusExporter(self.metrics).response()

    async def _debug_dashboard(self) -> HTMLResponse:
        """Render the debug dashboard showing recent errors (debug mode only)."""
        return Dashboard(self.error_store, debug=self.debug).render()

    # ============================================================
    # ROUTING & MIDDLEWARE METHODS
    # ============================================================

    def route(
        self, path: str, *, methods: set[str] | list[str] | tuple[str, ...] = ("GET",), name: str | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
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
        template_dir: str | None = None,
    ) -> Any:
        """Enable the admin dashboard."""
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
        """Enable GraphQL support."""
        self._graphql_schema = schema or GraphQLSchema()

        @self.router.post(url)
        async def graphql_endpoint(request: Request) -> Response:
            return await self._handle_graphql(request)

        if enable_playground:
            self._register_graphql_playground(url)

        return self._graphql_schema

    async def _handle_graphql(self, request: Request) -> Response:
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
        graphiql = GraphiQLPlayground(endpoint=url)
        altair = AltairPlayground(endpoint=url)

        @self.router.get(f"{url}/graphiql")
        async def graphiql_route(request: Request) -> HTMLResponse:
            return await graphiql.render(request)

        @self.router.get(f"{url}/altair")
        async def altair_route(request: Request) -> HTMLResponse:
            return await altair.render(request)

        @self.router.get(url)
        async def playground_index(request: Request) -> HTMLResponse:
            html_path = Path(__file__).parent.parent / "graphql" / "playground" / "index.html"
            html_content = html_path.read_text()
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
    # ASGI INTERFACE & HANDLERS
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

        # Session Middleware Initialization
        session_cookie = request.cookies.get(self.sessions.cookie_name)
        session_is_new = True
        if session_cookie:
            parsed = self.sessions.parse_cookie(session_cookie)
            if parsed:
                existing = await self.sessions.get(parsed[0])
                if existing is not None and not existing.is_expired():
                    request.session = existing
                    session_is_new = False
        if session_is_new:
            request.session = await self.sessions.create()

        # Routing and Execution
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

        # Save session header updates
        if session_is_new or request.session.is_dirty():
            await self.sessions.save(request.session)
            response.headers["set-cookie"] = self.sessions.create_cookie(request.session)

        if request.method == "HEAD":
            response.body = b""
            response.headers["content-length"] = "0"

        await response(scope, receive, send)

    async def _invoke(self, endpoint: Callable[..., Any], request: Request | WebSocket, params: dict[str, Any]) -> Any:
        signature = inspect.signature(endpoint)
        container_kwargs = self.container.resolve(endpoint)
        kwargs: dict[str, Any] = {}
        for name, parameter in signature.parameters.items():
            if name in params:
                kwargs[name] = params[name]
            elif name in {"request", "socket", "websocket"}:
                kwargs[name] = request
            elif name in container_kwargs:
                kwargs[name] = container_kwargs[name]
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
            if self.debug:
                print(f"\n--- Unhandled WebSocket error on {scope.get('path')} ---")
                traceback.print_exc()
                self.error_store.store(
                    {
                        "error_id": str(uuid.uuid4()),
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "path": str(scope.get("path", "")),
                        "timestamp": time.time(),
                    }
                )
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
                    self._startup_probe.mark_started()
                    self._readiness_probe.mark_ready()
                    await send({"type": "lifespan.startup.complete"})
            elif message.get("type") == "lifespan.shutdown":
                self._readiness_probe.mark_not_ready()
                try:
                    await self.plugins.shutdown()
                    await self.lifecycle.shutdown()
                except Exception as exc:
                    await send({"type": "lifespan.shutdown.failed", "message": str(exc)})
                else:
                    await send({"type": "lifespan.shutdown.complete"})
                return