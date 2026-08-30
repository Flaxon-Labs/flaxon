from __future__ import annotations

import os
import asyncio
import time
import secrets
import csv
import io
import base64
import hashlib
from io import BytesIO
from pathlib import Path
from typing import Any

from flaxon.exceptions import BadRequest, Forbidden, NotFound
from flaxon.http import HTMLResponse, JSONResponse, RedirectResponse, Request, Response
from flaxon.files import FileStorage
from flaxon.security import CSRF, Sanitizer
from flaxon.security.rate_limit import DistributedRateLimiter
from flaxon.jinax import Jinax

from .config import AdminConfig
from .registry import Registry, default_registry
from .views import ChangeListView, CreateView, DeleteView, DetailView, UpdateView
from .services import AdminActivity, AdminAuth, AdminRateLimit, AdminStore, AdminStoreSessionBackend, RedisAdminSessionBackend
from .production import DurableJobStore, DurableJobWorker, ImmutableAuditLog, NotificationService, ResumableUploadStore, WebAuthnService

_PACKAGE_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


class AdminDashboard:
    def __init__(
        self,
        app: Any,
        config: AdminConfig | None = None,
        url_prefix: str = "/admin",
        template_dir: str | None = None,
        registry: Registry | None = None,
        users: list[dict[str, Any]] | None = None,
        auth_backend: Any | None = None,
        upload_dir: str = "uploads",
        store: AdminStore | None = None,
        storage_path: str | None = None,
        redis_url: str | None = None,
        database: Any | None = None,
        password_reset_sender: Any | None = None,
        email_verification_sender: Any | None = None,
        require_email_verification: bool = False,
        max_upload_size: int = 10 * 1024 * 1024,
        allowed_upload_types: set[str] | None = None,
        media_storage: Any | None = None,
        redis_protocol: int = 2,
        redis_max_connections: int = 100,
        thumbnail_sync_limit: int = 2 * 1024 * 1024,
        session_idle_timeout: int | None = None,
        media_scanner: Any | None = None,
        media_retention_days: int = 365,
        webauthn_provider: Any | None = None,
    ) -> None:
        self.app = app
        self.config = config or AdminConfig()
        self.url_prefix = url_prefix.rstrip("/")
        self.registry = registry or default_registry
        self.widgets: list[Any] = []
        self.hooks: dict[str, list[Any]] = {}
        self.jinax = Jinax(template_dir or _PACKAGE_TEMPLATE_DIR, auto_reload=True)
        self.jinax.add_global("dashboard", self)
        self.store = store or (AdminStore(storage_path) if storage_path else None)
        self.database = database or getattr(app, "database", None) or getattr(app, "db", None)
        self._database_loaded = False
        setattr(self.app, "_flaxon_admin_store", self.store)
        persisted_users = list((self.store.list("users") if self.store else {}).values())
        session_backend = auth_backend
        if session_backend is None:
            if redis_url:
                session_backend = RedisAdminSessionBackend(redis_url, protocol=redis_protocol, max_connections=redis_max_connections, idle_timeout=session_idle_timeout)
            elif self.store is not None:
                session_backend = AdminStoreSessionBackend(self.store, idle_timeout=session_idle_timeout)
        self.auth = AdminAuth(persisted_users or users, session_backend, store=self.store, session_idle_timeout=session_idle_timeout)
        self.password_reset_sender = password_reset_sender
        self.email_verification_sender = email_verification_sender
        self.require_email_verification = require_email_verification
        self.max_upload_size = max_upload_size
        self.allowed_upload_types = allowed_upload_types or {"image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf", "text/plain"}
        self.media_storage = media_storage
        self.thumbnail_sync_limit = thumbnail_sync_limit
        self.media_scanner = media_scanner
        self.media_retention_days = max(1, media_retention_days)
        self._thumbnail_tasks: set[asyncio.Task[Any]] = set()
        self._job_worker_task: asyncio.Task[Any] | None = None
        self._auth_rate_redis: Any = None
        self._auth_rate_limiter: DistributedRateLimiter | None = None
        self._redis_url = redis_url
        self._redis_protocol = redis_protocol
        self._redis_max_connections = redis_max_connections
        self.csrf = CSRF(secrets.token_urlsafe(32))
        self._csrf_token = self.csrf.generate_token()
        setattr(self.app, "_flaxon_admin_auth", self.auth)
        setattr(self.app, "_flaxon_admin_dashboard", self)
        self.activities: list[AdminActivity] = [AdminActivity(**item) for item in ((self.store.get("meta", "activities", []) if self.store else []))]
        self.notifications: list[dict[str, Any]] = (self.store.get("meta", "notifications", []) if self.store else []) or []
        self.operations: list[dict[str, Any]] = (self.store.get("operations", "records", []) if self.store else []) or []
        if self.store and hasattr(self.store, "list_operations"):
            self.operations = self.store.list_operations(1000)
        self.roles: dict[str, list[str]] = (self.store.get("meta", "roles", {}) if self.store else {}) or {
            "staff": ["admin:read", "admin:write"],
            "editor": ["admin:read", "admin:write", "admin:media"],
            "administrator": ["admin:superuser"],
        }
        self.auth.role_permissions = self.roles
        self.job_store = DurableJobStore(self.store) if self.store else None
        self.job_worker = DurableJobWorker(self.job_store) if self.job_store else None
        self.audit_log = ImmutableAuditLog(self.store) if self.store else None
        self.notification_service = NotificationService(self.store) if self.store else None
        self.resumable_uploads = ResumableUploadStore(self.store) if self.store else None
        self.webauthn = WebAuthnService(self.store, webauthn_provider) if self.store else None
        if self.job_worker:
            self.job_worker.register("media.thumbnail", lambda payload: self._generate_thumbnail(payload["relative"], None))
        if self.store:
            saved_config = self.store.get("meta", "config")
            if saved_config:
                self.config.site_title = saved_config.get("site_title", self.config.site_title)
                self.config.site_header = saved_config.get("site_header", self.config.site_header)
                self.config.timezone = saved_config.get("timezone", self.config.timezone)
            for record in self.auth.users.values():
                self.store.set("users", record["username"], record)
        self.media = FileStorage(upload_dir)
        self.media_metadata: dict[str, dict[str, Any]] = (self.store.get("media", "metadata", {}) if self.store else {}) or {}
        self.media_folders: list[str] = (self.store.get("media", "folders", []) if self.store else []) or []
        if redis_url and hasattr(self.app, "websocket_manager"):
            from flaxon.websocket.redis_backend import RedisBroadcaster
            self._redis_broadcaster = RedisBroadcaster(redis_url, protocol=redis_protocol, max_connections=redis_max_connections)
            self.app.on_startup(lambda: self.app.websocket_manager.configure_broadcaster(self._redis_broadcaster))
            self.app.on_shutdown(self.app.websocket_manager.close_broadcaster)
        if hasattr(self.app, "mount_static"):
            self.app.mount_static("/uploads", upload_dir)
        self._mount_static()
        if hasattr(self.app, "add_middleware"):
            self.app.add_middleware(
                AdminRateLimit,
                prefix=self.url_prefix,
                redis_url=redis_url,
                redis_protocol=redis_protocol,
                redis_max_connections=redis_max_connections,
            )
        if hasattr(self.app, "on_shutdown"):
            self.app.on_shutdown(self._stop_thumbnail_tasks)
        if hasattr(self.app, "on_startup") and self.job_worker:
            self.app.on_startup(self._start_job_worker)
        self._register_routes()

    async def _stop_thumbnail_tasks(self) -> None:
        if self._job_worker_task is not None:
            self._job_worker_task.cancel()
            await asyncio.gather(self._job_worker_task, return_exceptions=True)
            self._job_worker_task = None
        for task in tuple(self._thumbnail_tasks):
            task.cancel()
        if self._thumbnail_tasks:
            await asyncio.gather(*self._thumbnail_tasks, return_exceptions=True)
        self._thumbnail_tasks.clear()
        if self._auth_rate_redis is not None:
            await self._auth_rate_redis.aclose()
            self._auth_rate_redis = None

    async def _start_job_worker(self) -> None:
        if self.job_worker is None or self._job_worker_task is not None:
            return
        self._job_worker_task = asyncio.create_task(self._job_worker_loop())

    async def _job_worker_loop(self) -> None:
        while True:
            await self.job_worker.run_once(limit=5)
            await asyncio.sleep(0.5)

    async def _allow_auth_action(self, request: Request, action: str, account: str = "anonymous") -> bool:
        if not self._redis_url:
            return True
        if self._auth_rate_redis is None:
            import redis.asyncio as redis
            self._auth_rate_redis = redis.from_url(self._redis_url, decode_responses=True, protocol=self._redis_protocol, max_connections=self._redis_max_connections)
            self._auth_rate_limiter = DistributedRateLimiter(self._auth_rate_redis, prefix="flaxon:admin:auth")
        client = request.scope.get("client") if hasattr(request, "scope") else None
        ip = str(client[0]) if isinstance(client, (tuple, list)) and client else "unknown"
        key = f"{action}:{account.strip().lower()}:{ip}"
        return await self._auth_rate_limiter.check(key, requests=5, window_seconds=300)

    def _mount_static(self) -> None:
        if hasattr(self.app, "mount_static"):
            static_dir = os.path.join(os.path.dirname(__file__), "static")
            self.app.mount_static("/static", static_dir)

    def _register_routes(self) -> None:
        router = self.app.router

        router.get(f"{self.url_prefix}/login")(self.login)
        router.post(f"{self.url_prefix}/login")(self.login)
        router.get(f"{self.url_prefix}/password-reset")(self.password_reset)
        router.post(f"{self.url_prefix}/password-reset")(self.password_reset)
        router.get(f"{self.url_prefix}/verify-email")(self.verify_email)
        router.post(f"{self.url_prefix}/verify-email")(self.verify_email)
        router.get(f"{self.url_prefix}/logout")(self.logout)
        router.post(f"{self.url_prefix}/logout")(self.logout)
        router.get(f"{self.url_prefix}/profile")(self.profile)
        router.post(f"{self.url_prefix}/profile")(self.profile)
        router.get(f"{self.url_prefix}/users")(self.users_view)
        router.post(f"{self.url_prefix}/users")(self.users_view)
        router.get(f"{self.url_prefix}/roles")(self.roles_view)
        router.post(f"{self.url_prefix}/roles")(self.roles_view)
        router.patch(f"{self.url_prefix}/users/<username>")(self.user_api)
        router.delete(f"{self.url_prefix}/users/<username>")(self.user_api)
        router.get(f"{self.url_prefix}/media")(self.media_view)
        router.post(f"{self.url_prefix}/media")(self.media_view)
        router.post(f"{self.url_prefix}/media/resumable")(self.resumable_media)
        router.patch(f"{self.url_prefix}/media/resumable/<upload_id>")(self.resumable_media)
        router.post(f"{self.url_prefix}/media/resumable/<upload_id>/complete")(self.resumable_media)
        router.get(f"{self.url_prefix}/media/folders")(self.media_folders_api)
        router.post(f"{self.url_prefix}/media/folders")(self.media_folders_api)
        router.patch(f"{self.url_prefix}/media/<path:filename>")(self.media_api)
        router.delete(f"{self.url_prefix}/media/<path:filename>")(self.media_api)
        router.get(f"{self.url_prefix}/search")(self.search)
        router.get(f"{self.url_prefix}/<model_name>/export")(self.model_export)
        router.post(f"{self.url_prefix}/<model_name>/import")(self.model_import)
        router.get(f"{self.url_prefix}/<model_name>/<object_id>/history")(self.history)
        router.get(f"{self.url_prefix}/settings")(self.settings_view)
        router.post(f"{self.url_prefix}/settings")(self.settings_view)
        router.get(f"{self.url_prefix}/activity")(self.activity_view)
        router.get(f"{self.url_prefix}/activity/export")(self.activity_export)
        router.route(f"{self.url_prefix}/notifications", methods={"GET", "POST"}, name="notifications_api")(self.notifications_api)
        router.route(f"{self.url_prefix}/notifications/preferences", methods={"GET", "POST"}, name="notification_preferences")(self.notification_preferences)
        router.get(f"{self.url_prefix}/audit/verify")(self.audit_verify)
        router.post(f"{self.url_prefix}/profile/webauthn/register/begin")(self.webauthn_api)
        router.post(f"{self.url_prefix}/profile/webauthn/register/finish")(self.webauthn_api)
        router.post(f"{self.url_prefix}/profile/webauthn/authenticate/begin")(self.webauthn_api)
        router.post(f"{self.url_prefix}/profile/webauthn/authenticate/finish")(self.webauthn_api)
        router.get(f"{self.url_prefix}/operations")(self.operations_view)
        router.get(f"{self.url_prefix}/operations/tasks")(self.operations_tasks_api)
        router.get(f"{self.url_prefix}")(self.index)
        router.get(f"{self.url_prefix}/")(self.index)
        router.get(f"{self.url_prefix}/<model_name>")(self.list_view)
        router.get(f"{self.url_prefix}/<model_name>/add")(self.add_view)
        router.post(f"{self.url_prefix}/<model_name>/add")(self.add_view)
        router.get(f"{self.url_prefix}/<model_name>/<object_id>")(self.detail_view)
        router.get(f"{self.url_prefix}/<model_name>/<object_id>/edit")(self.edit_view)
        router.post(f"{self.url_prefix}/<model_name>/<object_id>/edit")(self.edit_view)
        router.get(f"{self.url_prefix}/<model_name>/<object_id>/delete")(self.delete_view)
        router.post(f"{self.url_prefix}/<model_name>/<object_id>/delete")(self.delete_view)
        router.post(f"{self.url_prefix}/<model_name>/actions/<action_name>")(self.model_action)

    def register(self, model: Any, **options: Any) -> None:
        """Register a model with the dashboard's registry."""
        self.registry.register(model, **options)

    def register_widget(self, widget: Any) -> Any:
        self.widgets.append(widget)
        return widget

    def add_hook(self, name: str, callback: Any) -> Any:
        self.hooks.setdefault(name, []).append(callback)
        return callback

    def run_hook(self, name: str, value: Any) -> Any:
        for callback in self.hooks.get(name, []):
            value = callback(value)
        return value

    def unregister(self, model: Any) -> None:
        """Unregister a model from the dashboard's registry."""
        self.registry.unregister(model)

    async def index(self, request: Request) -> Response:
        user = await self._require_user(request, "admin:read")
        counts = {}
        total = 0
        for model in self.registry.get_all():
            values = await self._instances(model.model)
            counts[model.get_name()] = len(values)
            total += len(values)
        context = {
            "title": self.config.site_title,
            "models": self.registry.get_all(),
            "config": self.config,
            "user": user,
            "counts": counts,
            "total_records": total,
            "recent_changes": len(self.activities),
            "user_count": len(self.auth.users),
            "activities": [a.to_dict() for a in self.activities[-10:][::-1]],
        }
        return await self.jinax.render_response("admin/index.html", context)

    async def list_view(self, request: Request, model_name: str) -> Response:
        await self._require_model_user(request, model_name, "read")
        admin_model = self.registry.get(model_name)
        if not admin_model:
            return await self._not_found()
        view = ChangeListView(admin_model, request, self)
        return await view.render()

    async def add_view(self, request: Request, model_name: str) -> Response:
        await self._require_model_user(request, model_name, "create")
        admin_model = self.registry.get(model_name)
        if not admin_model:
            return await self._not_found()
        view = CreateView(admin_model, request, self)
        return await view.render()

    async def detail_view(self, request: Request, model_name: str, object_id: str) -> Response:
        await self._require_model_user(request, model_name, "read")
        admin_model = self.registry.get(model_name)
        if not admin_model:
            return await self._not_found()
        view = DetailView(admin_model, request, self, object_id)
        return await view.render()

    async def edit_view(self, request: Request, model_name: str, object_id: str) -> Response:
        await self._require_model_user(request, model_name, "update")
        admin_model = self.registry.get(model_name)
        if not admin_model:
            return await self._not_found()
        view = UpdateView(admin_model, request, self, object_id)
        return await view.render()

    async def delete_view(self, request: Request, model_name: str, object_id: str) -> Response:
        await self._require_model_user(request, model_name, "delete")
        admin_model = self.registry.get(model_name)
        if not admin_model:
            return await self._not_found()
        view = DeleteView(admin_model, request, self, object_id)
        return await view.render()

    async def model_action(self, request: Request, model_name: str, action_name: str) -> Response:
        user = await self._require_user(request)
        permission_action = "delete" if action_name == "delete" else action_name
        try:
            self.auth.authorize(user, f"{model_name}:{permission_action}")
        except Forbidden:
            self.auth.authorize(user, "admin:superuser")
        admin_model = self.registry.get(model_name)
        if not admin_model:
            return await self._not_found()
        action = admin_model.get_actions().get(action_name)
        if action is None:
            raise NotFound(f"Unknown action '{action_name}'.")
        form = await request.form()
        ids = form.get_list("ids") if hasattr(form, "get_list") else []
        result = action(ids) if callable(action) else None
        if hasattr(result, "__await__"):
            await result
        self.record_activity("action", model_name, request, details={"action": action_name, "count": len(ids)})
        return RedirectResponse(f"{self.url_prefix}/{model_name}", status_code=302)

    async def _not_found(self) -> Response:
        return await self.jinax.render_response("admin/404.html", status_code=404)

    async def _require_user(self, request: Request, permission: str | None = None) -> Any:
        await self._load_database()
        user = await self.auth.current_user(request)
        if permission:
            self.auth.authorize(user, permission)
        return user

    async def _load_database(self) -> None:
        if self._database_loaded or self.database is None:
            return
        await self.database.execute(
            "CREATE TABLE IF NOT EXISTS flaxon_admin_store (namespace VARCHAR(255) NOT NULL, key VARCHAR(255) NOT NULL, value TEXT NOT NULL, PRIMARY KEY(namespace, key))"
        )
        rows = await self.database.fetch_all("SELECT namespace, key, value FROM flaxon_admin_store")
        for row in rows:
            try:
                value = __import__("json").loads(row["value"])
            except (TypeError, ValueError):
                continue
            if row["namespace"] == "users":
                self.auth.add_user(value)
            elif row["namespace"] == "meta" and row["key"] == "activities":
                self.activities = [AdminActivity(**item) for item in value or []]
            elif row["namespace"] == "meta" and row["key"] == "config":
                self.config.site_title = value.get("site_title", self.config.site_title)
                self.config.site_header = value.get("site_header", self.config.site_header)
                self.config.timezone = value.get("timezone", self.config.timezone)
            elif row["namespace"] == "meta" and row["key"] == "roles":
                self.roles = value or self.roles
                self.auth.role_permissions = self.roles
            elif row["namespace"] == "meta" and row["key"] == "notifications":
                self.notifications = value or []
            elif row["namespace"] == "operations" and row["key"] == "records":
                self.operations = value or []
        self._database_loaded = True

    async def _persist_database(self) -> None:
        if self.database is None:
            return
        import json
        existing_users = await self.database.fetch_all(
            "SELECT key FROM flaxon_admin_store WHERE namespace = $1",
            "users",
        )
        current_user_keys = set(self.auth.users)
        for row in existing_users:
            key = str(row["key"])
            if key not in current_user_keys:
                await self.database.execute(
                    "DELETE FROM flaxon_admin_store WHERE namespace = $1 AND key = $2",
                    "users", key,
                )
        values = {"users": {key: record for key, record in self.auth.users.items()}, "meta": {
            "activities": [item.to_dict() for item in self.activities[-500:]],
            "notifications": self.notifications[-1000:],
            "config": self.config.to_dict(),
            "roles": self.roles,
        }}
        for namespace, entries in values.items():
            for key, value in entries.items():
                await self.database.execute(
                    "INSERT INTO flaxon_admin_store(namespace, key, value) VALUES ($1, $2, $3) ON CONFLICT(namespace, key) DO UPDATE SET value = excluded.value",
                    namespace, key, json.dumps(value, default=str),
                )

    async def _require_model_user(self, request: Request, model_name: str, action: str) -> Any:
        user = await self._require_user(request)
        try:
            self.auth.authorize(user, f"{model_name}:{action}")
        except Forbidden:
            self.auth.authorize(user, "admin:read" if action == "read" else "admin:write")
        return user

    async def _instances(self, model: Any) -> list[Any]:
        if not hasattr(model, "get_instances"):
            return []
        result = model.get_instances()
        return list(await result if hasattr(result, "__await__") else result)

    def record_activity(self, action: str, resource: str, request: Request, record_id: str | None = None, **details: Any) -> None:
        user = getattr(request, "user", None)
        username = getattr(user, "username", "system")
        timestamp = time.time()
        self.activities.append(AdminActivity(action, resource, record_id, username, timestamp, details))
        if self.audit_log is not None:
            client = request.scope.get("client") if hasattr(request, "scope") else None
            ip = str(client[0]) if isinstance(client, (tuple, list)) and client else None
            headers = getattr(request, "headers", {})
            user_agent = headers.get("user-agent") if hasattr(headers, "get") else None
            self.audit_log.append(action, username, {"resource": resource, "record_id": record_id, **details}, ip=ip, user_agent=user_agent)
        self.notifications.append({
            "id": secrets.token_urlsafe(12),
            "action": action,
            "resource": resource,
            "record_id": record_id,
            "username": username,
            "timestamp": timestamp,
            "details": details,
            "read_by": [],
        })
        if self.store:
            self.store.set("meta", "activities", [item.to_dict() for item in self.activities[-500:]])
            self.store.set("meta", "notifications", self.notifications[-1000:])

    def csrf_token(self) -> str:
        return self._csrf_token

    def validate_csrf(self, data: dict[str, Any]) -> dict[str, Any]:
        token = data.pop("_csrf", None)
        if not token or not self.csrf.verify_token(str(token)):
            raise Forbidden("CSRF token missing or invalid")
        return data

    async def login(self, request: Request) -> Response:
        if request.method == "GET":
            return await self.jinax.render_response("admin/login.html", {"title": self.config.site_title, "error": None, "csrf_token": self.csrf_token(), "reset_url": f"{self.url_prefix}/password-reset"})
        form = await request.form()
        data = self.validate_csrf(form.to_dict())
        username = str(data.get("username", ""))
        if self.require_email_verification and self.auth.users.get(username, {}).get("email") and not self.auth.users.get(username, {}).get("email_verified"):
            token = None
        else:
            client = request.scope.get("client") if hasattr(request, "scope") else None
            client_key = str(client[0]) if isinstance(client, (tuple, list)) and client else None
            token = await self.auth.login(username, str(data.get("password", "")), str(data.get("otp", "")), client_key)
        if token is None:
            return await self.jinax.render_response("admin/login.html", {"title": self.config.site_title, "error": "Invalid username or password.", "csrf_token": self.csrf_token(), "reset_url": f"{self.url_prefix}/password-reset"}, status_code=401)
        response = RedirectResponse(f"{self.url_prefix}/", status_code=302)
        self.auth.attach_cookie(response, token)
        return response

    async def logout(self, request: Request) -> Response:
        await self.auth.logout(request)
        response = RedirectResponse(f"{self.url_prefix}/login", status_code=302)
        self.auth.clear_cookie(response)
        return response

    async def password_reset(self, request: Request) -> Response:
        context = {"title": self.config.site_title, "csrf_token": self.csrf_token(), "message": None, "error": None, "reset_url": f"{self.url_prefix}/password-reset", "login_url": f"{self.url_prefix}/login"}
        if request.method == "POST":
            data = self.validate_csrf((await request.form()).to_dict())
            token = str(data.get("token", "")).strip()
            if token:
                if not self.auth.reset_password(token, str(data.get("password", ""))):
                    context["error"] = "This reset link is invalid or expired."
                else:
                    await self._persist_database()
                    context["message"] = "Password reset. You can sign in now."
            else:
                identifier = str(data.get("identifier", ""))
                allowed = await self._allow_auth_action(request, "password-reset", identifier)
                reset_token = self.auth.request_password_reset(identifier) if allowed else None
                if reset_token and self.password_reset_sender:
                    result = self.password_reset_sender(identifier, reset_token)
                    if hasattr(result, "__await__"):
                        await result
                context["message"] = "If the account exists, reset instructions have been sent."
        return await self.jinax.render_response("admin/password_reset.html", context)

    async def verify_email(self, request: Request) -> Response:
        context = {"title": self.config.site_title, "csrf_token": self.csrf_token(), "message": None, "error": None, "login_url": f"{self.url_prefix}/login"}
        if request.method == "POST":
            data = self.validate_csrf((await request.form()).to_dict())
            if self.auth.verify_email(str(data.get("token", ""))):
                await self._persist_database()
                context["message"] = "Email address verified."
            else:
                context["error"] = "This verification link is invalid or expired."
        elif request.query.get("token"):
            if self.auth.verify_email(request.query["token"]):
                await self._persist_database()
                context["message"] = "Email address verified."
            else:
                context["error"] = "This verification link is invalid or expired."
        return await self.jinax.render_response("admin/verify_email.html", context)

    async def profile(self, request: Request) -> Response:
        user = await self._require_user(request, "admin:write")
        error = None
        mfa_uri = None
        recovery_codes: list[str] = []
        if request.method == "POST":
            form = self.validate_csrf((await request.form()).to_dict())
            record = self.auth.users.get(user.username)
            if record is not None:
                record["email"] = str(form.get("email", record.get("email", "")))
                if form.get("password"):
                    try:
                        self.auth.validate_password(str(form["password"]))
                    except ValueError as exc:
                        error = str(exc)
                    else:
                        record["password_hash"] = self.auth.hasher.hash(str(form["password"]))
                if form.get("mfa_action") == "enable":
                    if await self._allow_auth_action(request, "mfa-enroll", user.username):
                        mfa_uri, recovery_codes = self.auth.begin_mfa_setup(user.username, self.config.site_title)
                    else:
                        error = "Too many MFA enrollment attempts. Try again later."
                elif form.get("mfa_action") == "confirm":
                    allowed = await self._allow_auth_action(request, "mfa-confirm", user.username)
                    if not allowed or not self.auth.confirm_mfa_setup(user.username, str(form.get("otp", ""))):
                        error = "Enter the current six-digit code to confirm MFA."
                elif form.get("mfa_action") == "disable":
                    allowed = await self._allow_auth_action(request, "mfa-disable", user.username)
                    code = str(form.get("otp", ""))
                    valid = self.auth.verify_otp(record.get("mfa_secret", ""), code)
                    valid = valid or self.auth.consume_recovery_code(user.username, code)
                    if not allowed or not valid:
                        error = "Enter a valid authenticator or recovery code to disable MFA."
                    else:
                        record.pop("mfa_secret", None)
                        record.pop("mfa_recovery_codes", None)
                if form.get("email_action") == "send_verification":
                    verification_token = self.auth.request_email_verification(user.username)
                    if verification_token and self.email_verification_sender:
                        result = self.email_verification_sender(record.get("email", ""), verification_token)
                        if hasattr(result, "__await__"):
                            await result
                if self.store:
                    self.store.set("users", record["username"], record)
                self.record_activity("profile_updated", "user", request, user.id)
                await self._persist_database()
        record = self.auth.users.get(user.username, {})
        mfa_qr = self._mfa_qr_data(mfa_uri)
        return await self.jinax.render_response("admin/profile.html", {"user": user, "models": self.registry.get_all(), "error": error, "mfa_enabled": bool(record.get("mfa_secret")), "mfa_secret": record.get("mfa_pending_secret") if mfa_uri else None, "mfa_uri": mfa_uri, "mfa_qr": mfa_qr, "mfa_recovery_codes": recovery_codes, "mfa_pending": bool(record.get("mfa_pending_secret")), "email_verified": bool(record.get("email_verified"))})

    @staticmethod
    def _mfa_qr_data(uri: str | None) -> str | None:
        if not uri:
            return None
        try:
            import qrcode
            image = qrcode.make(uri)
            output = BytesIO()
            image.save(output, format="PNG")
            return "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")
        except (ImportError, OSError):
            return None

    async def users_view(self, request: Request) -> Response:
        await self._require_user(request, "admin:users")
        error = None
        if request.method == "POST":
            form = self.validate_csrf((await request.form()).to_dict())
            try:
                roles = [r.strip() for r in str(form.get("roles", "staff")).split(",") if r.strip()]
                self.auth.add_user({"username": form.get("username", ""), "email": form.get("email", ""), "password": form.get("password", ""), "roles": roles})
                if self.store:
                    created = self.auth.users[str(form.get("username", ""))]
                    self.store.set("users", created["username"], created)
                self.record_activity("user_created", "user", request, details={"username": form.get("username")})
                await self._persist_database()
            except (ValueError, TypeError) as exc:
                error = str(exc)
        return await self.jinax.render_response("admin/users.html", {"users": [self.auth.public(u) for u in self.auth.users.values()], "roles": sorted(self.roles), "models": self.registry.get_all(), "error": error})

    async def roles_view(self, request: Request) -> Response:
        await self._require_user(request, "admin:users")
        error = None
        if request.method == "POST":
            form = self.validate_csrf((await request.form()).to_dict())
            name = str(form.get("name", "")).strip()
            if form.get("action") == "delete":
                if name in {"staff", "administrator"}:
                    error = "System roles cannot be deleted."
                elif name not in self.roles:
                    error = "Role not found."
                else:
                    del self.roles[name]
                    self.auth.role_permissions = self.roles
                    if self.store:
                        self.store.set("meta", "roles", self.roles)
                    self.record_activity("role_deleted", "role", request, details={"role": name})
                    await self._persist_database()
                return await self.jinax.render_response("admin/roles.html", {"roles": self.roles, "models": self.registry.get_all(), "error": error})
            permissions = [item.strip() for item in str(form.get("permissions", "")).split(",") if item.strip()]
            if not name:
                error = "Role name is required."
            else:
                self.roles[name] = permissions
                self.auth.role_permissions = self.roles
                if self.store:
                    self.store.set("meta", "roles", self.roles)
                self.record_activity("role_updated", "role", request, details={"role": name})
                await self._persist_database()
        return await self.jinax.render_response("admin/roles.html", {"roles": self.roles, "models": self.registry.get_all(), "error": error})

    async def user_api(self, request: Request, username: str) -> Response:
        actor = await self._require_user(request, "admin:users")
        if not self.csrf.verify_token(request.headers.get("x-csrf-token", "")):
            raise Forbidden("CSRF token missing or invalid")
        record = self.auth.users.get(username)
        if record is None:
            raise NotFound("User not found.")
        if request.method == "DELETE":
            if username == actor.username:
                raise BadRequest("You cannot delete your own account.")
            del self.auth.users[username]
            if hasattr(self.auth.backend, "revoke_all"):
                await self.auth.backend.revoke_all(record.get("id", username))
            if self.store:
                self.store.delete("users", username)
            await self._persist_database()
            return JSONResponse({"deleted": True})
        data = await request.json() or {}
        if "email" in data:
            record["email"] = str(data["email"])
        if "roles" in data:
            record["roles"] = list(data["roles"] or [])
        if "permissions" in data:
            record["permissions"] = list(data["permissions"] or [])
        if "active" in data:
            record["active"] = bool(data["active"])
        if data.get("password"):
            try:
                self.auth.validate_password(str(data["password"]))
            except ValueError as exc:
                raise BadRequest(str(exc)) from exc
            record["password_hash"] = self.auth.hasher.hash(str(data["password"]))
        if self.store:
            self.store.set("users", username, record)
        await self._persist_database()
        return JSONResponse(self.auth.public(record))

    async def media_view(self, request: Request) -> Response:
        await self._require_user(request, "admin:media")
        message = None
        if request.method == "POST":
            form = await request.form()
            self.validate_csrf(form.to_dict())
            upload = next((v for v in form.get_all().values() if hasattr(v, "filename")), None)
            if upload is not None:
                if getattr(upload, "size", 0) > self.max_upload_size:
                    raise BadRequest("Uploaded file exceeds the configured size limit.")
                content_type = str(getattr(upload, "content_type", "application/octet-stream"))
                if content_type not in self.allowed_upload_types:
                    raise BadRequest("This file type is not allowed.")
                folder = "/".join(Sanitizer.sanitize_filename(part) for part in str(form.get("folder", "")).split("/") if part.strip())
                if self.media_storage is not None:
                    filename = Sanitizer.sanitize_filename(str(getattr(upload, "filename", "upload.bin")))
                    relative = "/".join(part for part in (folder, filename) if part)
                    content = await upload.read()
                    content = await self._validate_media_bytes(content, content_type)
                    await self._storage_write(relative, content, content_type)
                    path = relative
                    upload_size = len(content)
                else:
                    path = self.media.save(upload, path=folder)
                    relative = str(os.path.relpath(path, self.media.base_path)).replace(os.sep, "/")
                    upload_size = getattr(upload, "size", 0)
                    with open(path, "rb") as media_file:
                        original_content = media_file.read()
                    sanitized_content = await self._validate_media_bytes(original_content, content_type)
                    if sanitized_content != original_content:
                        with open(path, "wb") as media_file:
                            media_file.write(sanitized_content)
                        upload_size = len(sanitized_content)
                    self.media_metadata.setdefault(relative, {})["sha256"] = hashlib.sha256(sanitized_content).hexdigest()
                if self.media_storage is not None:
                    self.media_metadata.setdefault(relative, {})["sha256"] = hashlib.sha256(content).hexdigest()
                self.media_metadata.setdefault(relative, {})["content_type"] = content_type
                self.media_metadata[relative]["original_name"] = str(getattr(upload, "filename", ""))
                self.media_metadata[relative]["size"] = upload_size
                if content_type.startswith("image/"):
                    try:
                        from PIL import Image
                        if self.media_storage is not None:
                            image_bytes = content
                            with Image.open(BytesIO(image_bytes)) as image:
                                image.verify()
                            with Image.open(BytesIO(image_bytes)) as image:
                                self.media_metadata[relative]["width"], self.media_metadata[relative]["height"] = image.size
                            if upload_size <= self.thumbnail_sync_limit:
                                self.media_metadata[relative]["thumbnail_status"] = "pending"
                                self._schedule_thumbnail(relative, image_bytes)
                            else:
                                self.media_metadata[relative]["thumbnail_status"] = "pending"
                                self._schedule_thumbnail(relative, image_bytes)
                        else:
                            with Image.open(path) as image:
                                image.verify()
                            with Image.open(path) as image:
                                self.media_metadata[relative]["width"], self.media_metadata[relative]["height"] = image.size
                            if upload_size <= self.thumbnail_sync_limit:
                                thumbnail = self.media.create_thumbnail(path)
                                if thumbnail:
                                    self.media_metadata[relative]["thumbnail_url"] = self.media.get_url(thumbnail)
                            else:
                                self.media_metadata[relative]["thumbnail_status"] = "pending"
                                self._schedule_thumbnail(relative, None)
                    except (ImportError, OSError, ValueError) as exc:
                        if self.media_storage is not None:
                            await self.media_storage.delete(relative)
                        else:
                            self.media.delete(path)
                        self.media_metadata.pop(relative, None)
                        raise BadRequest("Uploaded image data is invalid.") from exc
                if self.store:
                    self.store.set("media", "metadata", self.media_metadata)
                self.record_activity("media_uploaded", "media", request, details={"filename": upload.filename})
                await self._persist_database()
                message = self.media_storage.get_url(path) if self.media_storage is not None else self.media.get_url(path)
        files = await self._media_files()
        return await self.jinax.render_response("admin/media.html", {"files": files, "folders": self.media_folders, "message": message, "models": self.registry.get_all()})

    async def resumable_media(self, request: Request, upload_id: str | None = None) -> Response:
        await self._require_user(request, "admin:media")
        if self.resumable_uploads is None:
            raise BadRequest("Resumable uploads require persistent AdminStore storage.")
        if not self.csrf.verify_token(request.headers.get("x-csrf-token", "")):
            raise Forbidden("CSRF token missing or invalid")
        if request.method == "POST" and upload_id is None:
            data = await request.json() or {}
            filename = Sanitizer.sanitize_filename(str(data.get("filename", "upload.bin")))
            total_size = int(data.get("total_size", 0))
            if total_size <= 0 or total_size > self.max_upload_size:
                raise BadRequest("Invalid upload size.")
            return JSONResponse({"upload_id": self.resumable_uploads.create(filename, total_size, data.get("sha256"))}, status_code=201)
        if upload_id is None:
            raise NotFound("Upload session not found.")
        if request.method == "PATCH":
            offset = int(request.headers.get("upload-offset", "0"))
            chunk = await request.body()
            self.resumable_uploads.put_chunk(upload_id, offset, chunk)
            return JSONResponse({"upload_id": upload_id, "offset": offset + len(chunk)})
        filename, content = self.resumable_uploads.finalize(upload_id)
        content_type = "application/octet-stream"
        content = await self._validate_media_bytes(content, content_type)
        if self.media_storage is not None:
            await self._storage_write(filename, content, content_type)
            url = self.media_storage.get_url(filename)
        else:
            path = self.media.save_bytes(content, filename)
            url = self.media.get_url(path)
        self.media_metadata[filename] = {"original_name": filename, "size": len(content), "content_type": content_type, "sha256": hashlib.sha256(content).hexdigest()}
        if self.store:
            self.store.set("media", "metadata", self.media_metadata)
        return JSONResponse({"filename": filename, "url": url, "sha256": self.media_metadata[filename]["sha256"]}, status_code=201)

    def _schedule_thumbnail(self, relative: str, image_bytes: bytes | None) -> None:
        if self.job_worker is not None:
            self.job_store.enqueue("media.thumbnail", {"relative": relative}, max_attempts=4)
            return
        task = asyncio.create_task(self._generate_thumbnail(relative, image_bytes))
        self._thumbnail_tasks.add(task)
        task.add_done_callback(self._thumbnail_tasks.discard)

    async def _generate_thumbnail(self, relative: str, image_bytes: bytes | None) -> None:
        try:
            if self.media_storage is None:
                thumbnail = await asyncio.to_thread(self.media.create_thumbnail, str(self.media._safe_path(relative)))
                if thumbnail:
                    self.media_metadata.setdefault(relative, {})["thumbnail_url"] = self.media.get_url(thumbnail)
            else:
                from PIL import Image
                with Image.open(BytesIO(image_bytes or await self.media_storage.read(relative))) as image:
                    image.thumbnail((320, 240))
                    output = BytesIO()
                    image.convert("RGB").save(output, format="JPEG", quality=85)
                thumb_name = f"thumbnails/{Path(relative).stem}.jpg"
                await self._storage_write(thumb_name, output.getvalue(), "image/jpeg")
                self.media_metadata.setdefault(relative, {})["thumbnail_url"] = self.media_storage.get_url(thumb_name)
            self.media_metadata.setdefault(relative, {})["thumbnail_status"] = "ready"
            if self.store:
                self.store.set("media", "metadata", self.media_metadata)
        except Exception as exc:  # Thumbnail failures are recorded for the Admin operations view.
            self.media_metadata.setdefault(relative, {})["thumbnail_status"] = "failed"

    async def _storage_write(self, path: str, data: bytes, content_type: str | None = None) -> None:
        try:
            result = self.media_storage.write(path, data, content_type) if content_type else self.media_storage.write(path, data)
        except TypeError:
            result = self.media_storage.write(path, data)
        if hasattr(result, "__await__"):
            await result

    async def _validate_media_bytes(self, data: bytes, content_type: str) -> bytes:
        if self.media_scanner is not None:
            result = self.media_scanner(data, content_type)
            result = await result if hasattr(result, "__await__") else result
            if result is False:
                raise BadRequest("The uploaded file failed security scanning.")
        if content_type.startswith("image/"):
            try:
                from PIL import Image
                image = Image.open(BytesIO(data))
                image.load()
                output = BytesIO()
                image.save(output, format="JPEG" if content_type in {"image/jpeg", "image/jpg"} else image.format or "PNG", exif=b"")
                return output.getvalue()
            except (ImportError, OSError, ValueError):
                return data
        return data

    async def _media_files(self) -> list[dict[str, Any]]:
        if self.media_storage is not None:
            files = []
            for relative in await self.media_storage.list(""):
                if not relative or relative.startswith("thumbnails/"):
                    continue
                size = await self.media_storage.size(relative)
                files.append({"name": Path(relative).name, "size": size, "relative_name": relative, "url": self.media_storage.get_url(relative), "metadata": self.media_metadata.get(relative, {})})
            return files
        files = []
        for path in self.media.base_path.rglob("*"):
            if path.is_file():
                relative = str(path.relative_to(self.media.base_path)).replace(os.sep, "/")
                files.append(self.media.get_file_info(str(path)) | {"relative_name": relative, "url": self.media.get_url(str(path)), "metadata": self.media_metadata.get(relative, {})})
        return files

    async def media_folders_api(self, request: Request) -> Response:
        await self._require_user(request, "admin:media")
        if request.method == "POST":
            if not self.csrf.verify_token(request.headers.get("x-csrf-token", "")):
                raise Forbidden("CSRF token missing or invalid")
            data = await request.json() or {}
            folder = "/".join(Sanitizer.sanitize_filename(part) for part in str(data.get("name", "")).split("/") if part.strip())
            if not folder:
                raise BadRequest("Folder name is required.")
            self.media._safe_path(folder).mkdir(parents=True, exist_ok=True)
            if folder not in self.media_folders:
                self.media_folders.append(folder)
                if self.store:
                    self.store.set("media", "folders", self.media_folders)
        return JSONResponse({"folders": self.media_folders})

    async def media_api(self, request: Request, filename: str) -> Response:
        await self._require_user(request, "admin:media")
        if not self.csrf.verify_token(request.headers.get("x-csrf-token", "")):
            raise Forbidden("CSRF token missing or invalid")
        filename = "/".join(Sanitizer.sanitize_filename(part) for part in filename.split("/") if part not in {"", "."})
        path = str(self.media._safe_path(filename))
        exists = await self.media_storage.exists(filename) if self.media_storage is not None else self.media.exists(path)
        if not exists:
            raise NotFound("Media file not found.")
        if request.method == "DELETE":
            if self.media_storage is not None:
                await self.media_storage.delete(filename)
            else:
                self.media.delete(path)
            self.media_metadata.pop(filename, None)
            if self.store:
                self.store.set("media", "metadata", self.media_metadata)
            return JSONResponse({"deleted": True})
        data = await request.json() or {}
        new_name = "/".join(Sanitizer.sanitize_filename(part) for part in str(data.get("name", filename)).split("/") if part not in {"", "."})
        target = str(self.media._safe_path(new_name))
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        if self.media_storage is not None:
            await self._storage_write(new_name, await self.media_storage.read(filename), self.media_metadata.get(filename, {}).get("content_type"))
            await self.media_storage.delete(filename)
        else:
            os.replace(path, target)
        metadata = self.media_metadata.pop(filename, {})
        metadata.update(data.get("metadata") or {})
        self.media_metadata[new_name] = metadata
        if self.store:
            self.store.set("media", "metadata", self.media_metadata)
        url = self.media_storage.get_url(new_name) if self.media_storage is not None else self.media.get_url(target)
        return JSONResponse({"name": new_name, "url": url, "metadata": metadata})

    async def search(self, request: Request) -> Response:
        await self._require_user(request, "admin:read")
        needle = request.query.get("q", "").lower().strip()
        results = []
        if needle:
            for model in self.registry.get_all():
                for obj in await self._instances(model.model):
                    values = obj if isinstance(obj, dict) else getattr(obj, "__dict__", {})
                    if needle in " ".join(str(v) for v in values.values()).lower():
                        results.append({"model": model.get_name(), "label": model.get_verbose_name(), "id": values.get("id", ""), "values": values})
        return await self.jinax.render_response("admin/search.html", {"query": needle, "results": results, "models": self.registry.get_all()})

    async def model_export(self, request: Request, model_name: str) -> Response:
        await self._require_model_user(request, model_name, "read")
        admin_model = self.registry.get(model_name)
        if not admin_model:
            return await self._not_found()
        values = await self._instances(admin_model.model)
        records = [value if isinstance(value, dict) else getattr(value, "__dict__", {}) for value in values]
        fmt = request.query.get("format", "json").lower()
        if fmt == "csv":
            output = io.StringIO()
            fields = sorted({key for record in records for key in record})
            writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)
            return Response(output.getvalue(), media_type="text/csv; charset=utf-8", headers={"content-disposition": f"attachment; filename={model_name}.csv"})
        return JSONResponse(records, headers={"content-disposition": f"attachment; filename={model_name}.json"})

    async def model_import(self, request: Request, model_name: str) -> Response:
        await self._require_model_user(request, model_name, "create")
        admin_model = self.registry.get(model_name)
        if not admin_model:
            return await self._not_found()
        form = await request.form() if "multipart/form-data" in request.headers.get("content-type", "") else None
        raw = next((value for value in form.get_all().values() if hasattr(value, "filename")), None) if form else None
        if raw is not None:
            payload = (await raw.read()).decode("utf-8")
            fmt = "csv" if str(raw.filename).lower().endswith(".csv") else "json"
        else:
            payload = await request.text()
            fmt = "csv" if "csv" in request.headers.get("content-type", "") else "json"
        try:
            records = list(csv.DictReader(io.StringIO(payload))) if fmt == "csv" else json.loads(payload)
        except (TypeError, ValueError, csv.Error) as exc:
            raise BadRequest(f"Invalid import document: {exc}") from exc
        if not isinstance(records, list):
            raise BadRequest("Import document must contain a list of records.")
        created, errors = [], []
        for row, record in enumerate(records, 1):
            if not isinstance(record, dict):
                errors.append({"row": row, "error": "Record must be an object."})
                continue
            try:
                result = admin_model.model.create_instance(record) if hasattr(admin_model.model, "create_instance") else None
                result = await result if hasattr(result, "__await__") else result
                created.append(result or record)
            except Exception as exc:  # noqa: BLE001
                errors.append({"row": row, "error": str(exc)})
        self.record_activity("imported", model_name, request, details={"imported": len(created), "errors": len(errors)})
        return JSONResponse({"imported": len(created), "errors": errors}, status_code=201 if not errors else 207)

    async def settings_view(self, request: Request) -> Response:
        await self._require_user(request, "admin:settings")
        if request.method == "POST":
            form = self.validate_csrf((await request.form()).to_dict())
            self.config.site_title = str(form.get("site_title", self.config.site_title))
            self.config.site_header = str(form.get("site_header", self.config.site_header))
            self.config.timezone = str(form.get("timezone", self.config.timezone))
            self.config.settings.update({k: v for k, v in form.items() if k not in {"site_title", "site_header", "timezone"}})
            if self.store:
                self.store.set("meta", "config", self.config.to_dict())
            self.record_activity("settings_updated", "settings", request)
            await self._persist_database()
        return await self.jinax.render_response("admin/settings.html", {"config": self.config, "models": self.registry.get_all()})

    async def history(self, request: Request, model_name: str, object_id: str) -> Response:
        user = await self._require_user(request, "admin:read")
        model = self.registry.get(model_name)
        if not model:
            return await self._not_found()
        entries = [a.to_dict() for a in self.activities if a.resource == model_name and a.record_id == object_id]
        return await self.jinax.render_response("admin/history.html", {"model": model, "object_id": object_id, "entries": entries[::-1], "models": self.registry.get_all(), "user": user})

    async def activity_view(self, request: Request) -> Response:
        await self._require_user(request, "admin:read")
        query = request.query.get("q", "").lower()
        entries = [item.to_dict() for item in self.activities if not query or query in f"{item.action} {item.resource} {item.username}".lower()]
        return await self.jinax.render_response("admin/activity.html", {"entries": entries[::-1], "models": self.registry.get_all()})

    async def activity_export(self, request: Request) -> Response:
        await self._require_user(request, "admin:read")
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["action", "resource", "record_id", "username", "timestamp", "details"])
        writer.writeheader()
        for item in reversed(self.activities):
            writer.writerow(item.to_dict())
        return Response(output.getvalue(), media_type="text/csv; charset=utf-8", headers={"content-disposition": "attachment; filename=flaxon-activity.csv"})

    async def notifications_api(self, request: Request) -> Response:
        """Return and update durable per-user admin notifications."""
        user = await self._require_user(request, "admin:read")
        username = getattr(user, "username", "system")
        if request.method == "POST":
            if not self.csrf.verify_token(request.headers.get("x-csrf-token", "")):
                raise Forbidden("CSRF token missing or invalid")
            body = await request.json() or {}
            ids = body.get("ids")
            if body.get("all"):
                ids = [item["id"] for item in self.notifications]
            if not isinstance(ids, list):
                raise BadRequest("Notification ids must be a list.")
            selected = {str(item) for item in ids}
            for item in self.notifications:
                if item.get("id") in selected and username not in item.setdefault("read_by", []):
                    item["read_by"].append(username)
            if self.store:
                self.store.set("meta", "notifications", self.notifications[-1000:])
            await self._persist_database()
        entries = [item for item in self.notifications[::-1] if username not in item.get("read_by", [])][:20]
        return JSONResponse({
            "items": entries,
            "unread": len(entries),
        })

    async def notification_preferences(self, request: Request) -> Response:
        user = await self._require_user(request, "admin:read")
        if self.notification_service is None:
            raise BadRequest("Notification preferences require persistent AdminStore storage.")
        username = str(user.username)
        if request.method == "POST":
            if not self.csrf.verify_token(request.headers.get("x-csrf-token", "")):
                raise Forbidden("CSRF token missing or invalid")
            self.notification_service.set_preferences(username, await request.json() or {})
        return JSONResponse(self.notification_service.preferences(username))

    async def audit_verify(self, request: Request) -> Response:
        await self._require_user(request, "admin:read")
        return JSONResponse({"valid": self.audit_log.verify() if self.audit_log else False})

    async def webauthn_api(self, request: Request) -> Response:
        user = await self._require_user(request, "admin:write")
        if self.webauthn is None:
            raise BadRequest("WebAuthn requires persistent AdminStore storage.")
        if not self.csrf.verify_token(request.headers.get("x-csrf-token", "")):
            raise Forbidden("CSRF token missing or invalid")
        data = await request.json() or {}
        operation = request.path.rsplit("/", 1)[-1]
        if operation == "begin":
            result = self.webauthn.begin_registration(user.username) if "/register/" in request.path else self.webauthn.begin_authentication(user.username)
        elif "/register/" in request.path:
            result = self.webauthn.finish_registration(user.username, data)
        else:
            result = self.webauthn.finish_authentication(user.username, data)
        if hasattr(result, "__await__"):
            result = await result
        return JSONResponse({"result": result})

    async def operations_view(self, request: Request) -> Response:
        await self._require_user(request, "admin:read")
        health = getattr(self.app, "health", None)
        checks = []
        if health is not None and hasattr(health, "checks"):
            checks = [{"name": name, "status": getattr(check, "status", "registered")} for name, check in getattr(health, "checks", {}).items()]
            self._record_operation("health", {"checks": checks})
        metrics = getattr(self.app, "metrics", None)
        tasks = await self._task_snapshots()
        return await self.jinax.render_response("admin/operations.html", {"checks": checks, "metrics": metrics, "tasks": tasks, "operations": self.operations[-100:], "models": self.registry.get_all()})

    async def operations_tasks_api(self, request: Request) -> Response:
        await self._require_user(request, "admin:read")
        return JSONResponse({"tasks": await self._task_snapshots()})

    async def _task_snapshots(self) -> list[dict[str, Any]]:
        queue = getattr(self.app, "task_queue", None) or getattr(self.app, "tasks", None)
        if queue is None or not hasattr(queue, "get_all_tasks"):
            return []
        tasks = await queue.get_all_tasks()
        snapshots = [{"id": task.id, "name": task.name, "status": getattr(task.status, "value", str(task.status)), "error": task.error, "queue": task.queue, "created_at": task.created_at.isoformat()} for task in tasks]
        failures = [item for item in snapshots if item["status"] in {"failed", "timeout"}]
        if failures:
            self._record_operation("task_failure", {"tasks": failures})
        return snapshots

    def _record_operation(self, kind: str, payload: dict[str, Any]) -> None:
        record = {"id": secrets.token_hex(8), "kind": kind, "timestamp": time.time(), **payload}
        self.operations.append(record)
        self.operations = self.operations[-1000:]
        if self.store and hasattr(self.store, "record_operation"):
            self.store.record_operation(kind, payload, record["id"])
        elif self.store:
            self.store.set("operations", "records", self.operations)

    def get_urls(self) -> list[tuple[str, str, Any]]:
        return [
            (f"{self.url_prefix}/", "GET", self.index),
            (f"{self.url_prefix}/<model_name>", "GET", self.list_view),
            (f"{self.url_prefix}/<model_name>/add", "GET", self.add_view),
            (f"{self.url_prefix}/<model_name>/add", "POST", self.add_view),
            (f"{self.url_prefix}/<model_name>/<object_id>", "GET", self.detail_view),
            (f"{self.url_prefix}/<model_name>/<object_id>/edit", "GET", self.edit_view),
            (f"{self.url_prefix}/<model_name>/<object_id>/edit", "POST", self.edit_view),
            (f"{self.url_prefix}/<model_name>/<object_id>/history", "GET", self.history),
            (f"{self.url_prefix}/<model_name>/<object_id>/delete", "POST", self.delete_view),
        ]
