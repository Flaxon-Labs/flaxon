from __future__ import annotations

from typing import Any

from flaxon.http import HTMLResponse, Request, Response
from flaxon.jinax import Jinax

from .config import AdminConfig
from .registry import Registry
from .views import ChangeListView, CreateView, DeleteView, DetailView, UpdateView


class AdminDashboard:
    def __init__(
        self,
        app: Any,
        config: AdminConfig | None = None,
        url_prefix: str = "/admin",
        template_dir: str = "templates/admin",
    ) -> None:
        self.app = app
        self.config = config or AdminConfig()
        self.url_prefix = url_prefix.rstrip("/")
        self.registry = Registry()
        self.jinax = Jinax(template_dir, auto_reload=True)
        self._register_routes()

    def _register_routes(self) -> None:
        router = self.app.router

        router.get(f"{self.url_prefix}/", self.index)
        router.get(f"{self.url_prefix}/<model_name>", self.list_view)
        router.get(f"{self.url_prefix}/<model_name>/add", self.add_view)
        router.post(f"{self.url_prefix}/<model_name>/add", self.add_view)
        router.get(f"{self.url_prefix}/<model_name>/<id>", self.detail_view)
        router.get(f"{self.url_prefix}/<model_name>/<id>/edit", self.edit_view)
        router.post(f"{self.url_prefix}/<model_name>/<id>/edit", self.edit_view)
        router.post(f"{self.url_prefix}/<model_name>/<id>/delete", self.delete_view)

    def register(self, model: Any, **options: Any) -> None:
        self.registry.register(model, **options)

    def unregister(self, model: Any) -> None:
        self.registry.unregister(model)

    async def index(self, request: Request) -> HTMLResponse:
        context = {
            "title": self.config.site_title,
            "models": self.registry.get_all(),
            "config": self.config,
        }
        return await self.jinax.render_response("admin/index.html", context)

    async def list_view(self, request: Request, model_name: str) -> HTMLResponse:
        admin_model = self.registry.get(model_name)
        if not admin_model:
            return await self._not_found()
        view = ChangeListView(admin_model, request, self)
        return await view.render()

    async def add_view(self, request: Request, model_name: str) -> HTMLResponse:
        admin_model = self.registry.get(model_name)
        if not admin_model:
            return await self._not_found()
        view = CreateView(admin_model, request, self)
        return await view.render()

    async def detail_view(self, request: Request, model_name: str, id: str) -> HTMLResponse:
        admin_model = self.registry.get(model_name)
        if not admin_model:
            return await self._not_found()
        view = DetailView(admin_model, request, self, id)
        return await view.render()

    async def edit_view(self, request: Request, model_name: str, id: str) -> HTMLResponse:
        admin_model = self.registry.get(model_name)
        if not admin_model:
            return await self._not_found()
        view = UpdateView(admin_model, request, self, id)
        return await view.render()

    async def delete_view(self, request: Request, model_name: str, id: str) -> HTMLResponse:
        admin_model = self.registry.get(model_name)
        if not admin_model:
            return await self._not_found()
        view = DeleteView(admin_model, request, self, id)
        return await view.render()

    async def _not_found(self) -> HTMLResponse:
        return await self.jinax.render_response("admin/404.html", status_code=404)

    def get_urls(self) -> list[tuple[str, str, str]]:
        return [
            (f"{self.url_prefix}/", "GET", self.index),
            (f"{self.url_prefix}/<model_name>", "GET", self.list_view),
            (f"{self.url_prefix}/<model_name>/add", "GET", self.add_view),
            (f"{self.url_prefix}/<model_name>/add", "POST", self.add_view),
            (f"{self.url_prefix}/<model_name>/<id>", "GET", self.detail_view),
            (f"{self.url_prefix}/<model_name>/<id>/edit", "GET", self.edit_view),
            (f"{self.url_prefix}/<model_name>/<id>/edit", "POST", self.edit_view),
            (f"{self.url_prefix}/<model_name>/<id>/delete", "POST", self.delete_view),
        ]