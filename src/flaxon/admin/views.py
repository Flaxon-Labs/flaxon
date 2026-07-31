from __future__ import annotations

from typing import Any

from flaxon.http import HTMLResponse, RedirectResponse, Request


class AdminView:
    def __init__(self, admin_model: Any, request: Request, dashboard: Any) -> None:
        self.admin_model = admin_model
        self.request = request
        self.dashboard = dashboard

    async def render(self) -> HTMLResponse | RedirectResponse:
        raise NotImplementedError


class ChangeListView(AdminView):
    async def render(self) -> HTMLResponse:
        context = {
            "model": self.admin_model,
            "verbose_name": self.admin_model.get_verbose_name(),
            "verbose_name_plural": self.admin_model.get_verbose_name_plural(),
            "list_display": self.admin_model.list_display,
            "list_filter": self.admin_model.list_filter,
            "search_fields": self.admin_model.search_fields,
            "actions": self.admin_model.get_actions(),
        }
        return await self.dashboard.jinax.render_response("admin/list.html", context)


class DetailView(AdminView):
    def __init__(self, admin_model: Any, request: Request, dashboard: Any, object_id: str) -> None:
        super().__init__(admin_model, request, dashboard)
        self.object_id = object_id

    async def render(self) -> HTMLResponse:
        context = {
            "model": self.admin_model,
            "verbose_name": self.admin_model.get_verbose_name(),
            "object_id": self.object_id,
        }
        return await self.dashboard.jinax.render_response("admin/detail.html", context)


class CreateView(AdminView):
    async def render(self) -> HTMLResponse | RedirectResponse:
        if self.request.method == "POST":
            # Extract form payload for model creation logic
            form_data = await self.request.form() if hasattr(self.request, "form") else {}
            
            # Hook for model saving instance if supported by model manager
            if hasattr(self.admin_model, "create_instance"):
                await self.admin_model.create_instance(form_data)

            return RedirectResponse(
                f"{self.dashboard.url_prefix}/{self.admin_model.get_name()}",
                status_code=302,
            )

        context = {
            "model": self.admin_model,
            "verbose_name": self.admin_model.get_verbose_name(),
            "fields": self.admin_model.fields,
            "readonly_fields": self.admin_model.readonly_fields,
        }
        return await self.dashboard.jinax.render_response("admin/add.html", context)


class UpdateView(AdminView):
    def __init__(self, admin_model: Any, request: Request, dashboard: Any, object_id: str) -> None:
        super().__init__(admin_model, request, dashboard)
        self.object_id = object_id

    async def render(self) -> HTMLResponse | RedirectResponse:
        if self.request.method == "POST":
            form_data = await self.request.form() if hasattr(self.request, "form") else {}

            # Hook for updating model instance
            if hasattr(self.admin_model, "update_instance"):
                await self.admin_model.update_instance(self.object_id, form_data)

            return RedirectResponse(
                f"{self.dashboard.url_prefix}/{self.admin_model.get_name()}",
                status_code=302,
            )

        context = {
            "model": self.admin_model,
            "verbose_name": self.admin_model.get_verbose_name(),
            "object_id": self.object_id,
            "fields": self.admin_model.fields,
            "readonly_fields": self.admin_model.readonly_fields,
        }
        return await self.dashboard.jinax.render_response("admin/edit.html", context)


class DeleteView(AdminView):
    def __init__(self, admin_model: Any, request: Request, dashboard: Any, object_id: str) -> None:
        super().__init__(admin_model, request, dashboard)
        self.object_id = object_id

    async def render(self) -> HTMLResponse | RedirectResponse:
        if self.request.method == "POST":
            # Hook for deleting model instance
            if hasattr(self.admin_model, "delete_instance"):
                await self.admin_model.delete_instance(self.object_id)

            return RedirectResponse(
                f"{self.dashboard.url_prefix}/{self.admin_model.get_name()}",
                status_code=302,
            )

        context = {
            "model": self.admin_model,
            "verbose_name": self.admin_model.get_verbose_name(),
            "object_id": self.object_id,
        }
        return await self.dashboard.jinax.render_response("admin/delete.html", context)