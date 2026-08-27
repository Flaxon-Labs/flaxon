from __future__ import annotations

import os
import time
import secrets
import csv
import io
from pathlib import Path
from typing import Any

from flaxon.exceptions import BadRequest, Forbidden, NotFound
from flaxon.http import HTMLResponse, JSONResponse, RedirectResponse, Request, Response
from flaxon.files import FileStorage
from flaxon.security import CSRF, Sanitizer
from flaxon.jinax import Jinax

from .config import AdminConfig
from .registry import Registry, default_registry
from .views import ChangeListView, CreateView, DeleteView, DetailView, UpdateView
from .services import AdminActivity, AdminAuth, AdminRateLimit, AdminStore

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
        self.auth = AdminAuth(persisted_users or users, auth_backend)
        self.password_reset_sender = password_reset_sender
        self.email_verification_sender = email_verification_sender
        self.require_email_verification = require_email_verification
        self.max_upload_size = max_upload_size
        self.allowed_upload_types = allowed_upload_types or {"image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf", "text/plain"}
        self.csrf = CSRF(secrets.token_urlsafe(32))
        self._csrf_token = self.csrf.generate_token()
        setattr(self.app, "_flaxon_admin_auth", self.auth)
        setattr(self.app, "_flaxon_admin_dashboard", self)
        self.activities: list[AdminActivity] = [AdminActivity(**item) for item in ((self.store.get("meta", "activities", []) if self.store else []))]
        self.roles: dict[str, list[str]] = (self.store.get("meta", "roles", {}) if self.store else {}) or {
            "staff": ["admin:read", "admin:write"],
            "editor": ["admin:read", "admin:write", "admin:media"],
            "administrator": ["admin:superuser"],
        }
        self.auth.role_permissions = self.roles
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
            self._redis_broadcaster = RedisBroadcaster(redis_url)
            self.app.on_startup(lambda: self.app.websocket_manager.configure_broadcaster(self._redis_broadcaster))
            self.app.on_shutdown(self.app.websocket_manager.close_broadcaster)
        if hasattr(self.app, "mount_static"):
            self.app.mount_static("/uploads", upload_dir)
        self._mount_static()
        if hasattr(self.app, "add_middleware"):
            self.app.add_middleware(AdminRateLimit, prefix=self.url_prefix)
        self._register_routes()

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
        router.get(f"{self.url_prefix}/media/folders")(self.media_folders_api)
        router.post(f"{self.url_prefix}/media/folders")(self.media_folders_api)
        router.patch(f"{self.url_prefix}/media/<path:filename>")(self.media_api)
        router.delete(f"{self.url_prefix}/media/<path:filename>")(self.media_api)
        router.get(f"{self.url_prefix}/search")(self.search)
        router.get(f"{self.url_prefix}/<model_name>/<object_id>/history")(self.history)
        router.get(f"{self.url_prefix}/settings")(self.settings_view)
        router.post(f"{self.url_prefix}/settings")(self.settings_view)
        router.get(f"{self.url_prefix}/activity")(self.activity_view)
        router.get(f"{self.url_prefix}/activity/export")(self.activity_export)
        router.get(f"{self.url_prefix}/notifications")(self.notifications_api)
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
        await self._require_user(request, "admin:write")
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
        self.activities.append(AdminActivity(action, resource, record_id, getattr(user, "username", "system"), time.time(), details))
        if self.store:
            self.store.set("meta", "activities", [item.to_dict() for item in self.activities[-500:]])

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
            token = await self.auth.login(username, str(data.get("password", "")), str(data.get("otp", "")))
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
                reset_token = self.auth.request_password_reset(identifier)
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
        if request.method == "POST":
            form = self.validate_csrf((await request.form()).to_dict())
            record = self.auth.users.get(user.username)
            if record is not None:
                record["email"] = str(form.get("email", record.get("email", "")))
                if form.get("password"):
                    record["password_hash"] = self.auth.hasher.hash(str(form["password"]))
                if form.get("mfa_action") == "enable":
                    record["mfa_secret"] = self.auth.generate_mfa_secret()
                elif form.get("mfa_action") == "disable":
                    record.pop("mfa_secret", None)
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
        return await self.jinax.render_response("admin/profile.html", {"user": user, "models": self.registry.get_all(), "error": error, "mfa_enabled": bool(record.get("mfa_secret")), "mfa_secret": record.get("mfa_secret"), "email_verified": bool(record.get("email_verified"))})

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
                path = self.media.save(upload, path=folder)
                relative = str(os.path.relpath(path, self.media.base_path)).replace(os.sep, "/")
                self.media_metadata.setdefault(relative, {})["content_type"] = content_type
                self.media_metadata[relative]["original_name"] = str(getattr(upload, "filename", ""))
                if self.store:
                    self.store.set("media", "metadata", self.media_metadata)
                self.record_activity("media_uploaded", "media", request, details={"filename": upload.filename})
                await self._persist_database()
                message = self.media.get_url(path)
        files = []
        for path in self.media.base_path.rglob("*"):
            if path.is_file():
                relative = str(path.relative_to(self.media.base_path)).replace(os.sep, "/")
                files.append(self.media.get_file_info(str(path)) | {"relative_name": relative, "url": self.media.get_url(str(path)), "metadata": self.media_metadata.get(relative, {})})
        return await self.jinax.render_response("admin/media.html", {"files": files, "folders": self.media_folders, "message": message, "models": self.registry.get_all()})

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
        if not self.media.exists(path):
            raise NotFound("Media file not found.")
        if request.method == "DELETE":
            self.media.delete(path)
            self.media_metadata.pop(filename, None)
            if self.store:
                self.store.set("media", "metadata", self.media_metadata)
            return JSONResponse({"deleted": True})
        data = await request.json() or {}
        new_name = "/".join(Sanitizer.sanitize_filename(part) for part in str(data.get("name", filename)).split("/") if part not in {"", "."})
        target = str(self.media._safe_path(new_name))
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        os.replace(path, target)
        metadata = self.media_metadata.pop(filename, {})
        metadata.update(data.get("metadata") or {})
        self.media_metadata[new_name] = metadata
        if self.store:
            self.store.set("media", "metadata", self.media_metadata)
        return JSONResponse({"name": new_name, "url": self.media.get_url(target), "metadata": metadata})

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
        """Return recent activity in the shape consumed by the admin bell."""
        await self._require_user(request, "admin:read")
        entries = self.activities[-20:][::-1]
        return JSONResponse({
            "items": [item.to_dict() for item in entries],
            "unread": len(entries),
        })

    async def operations_view(self, request: Request) -> Response:
        await self._require_user(request, "admin:read")
        health = getattr(self.app, "health", None)
        checks = []
        if health is not None and hasattr(health, "checks"):
            checks = list(getattr(health, "checks", {}).keys())
        metrics = getattr(self.app, "metrics", None)
        tasks = await self._task_snapshots()
        return await self.jinax.render_response("admin/operations.html", {"checks": checks, "metrics": metrics, "tasks": tasks, "models": self.registry.get_all()})

    async def operations_tasks_api(self, request: Request) -> Response:
        await self._require_user(request, "admin:read")
        return JSONResponse({"tasks": await self._task_snapshots()})

    async def _task_snapshots(self) -> list[dict[str, Any]]:
        queue = getattr(self.app, "task_queue", None) or getattr(self.app, "tasks", None)
        if queue is None or not hasattr(queue, "get_all_tasks"):
            return []
        tasks = await queue.get_all_tasks()
        return [{"id": task.id, "name": task.name, "status": getattr(task.status, "value", str(task.status)), "error": task.error, "queue": task.queue, "created_at": task.created_at.isoformat()} for task in tasks]

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
