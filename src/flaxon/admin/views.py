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
        model_class = self.admin_model.model
        objects: list[Any] = []
        if hasattr(model_class, "get_instances"):
            result = model_class.get_instances()
            objects = await result if hasattr(result, "__await__") else result

        context = {
            "model": self.admin_model,
            "models": self.dashboard.registry.get_all(),
            "objects": objects,
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
        model_class = self.admin_model.model
        obj = None
        if hasattr(model_class, "get_instance"):
            result = model_class.get_instance(self.object_id)
            obj = await result if hasattr(result, "__await__") else result

        context = {
            "model": self.admin_model,
            "models": self.dashboard.registry.get_all(),
            "object": obj,
            "verbose_name": self.admin_model.get_verbose_name(),
            "object_id": self.object_id,
            "fields": self.admin_model.fields,
        }
        return await self.dashboard.jinax.render_response("admin/detail.html", context)


class CreateView(AdminView):
    async def render(self) -> HTMLResponse | RedirectResponse:
        if self.request.method == "POST":
            # Extract form payload for model creation logic
            form_data = await self.request.form() if hasattr(self.request, "form") else {}
            if hasattr(form_data, "to_dict"):
                form_data = form_data.to_dict()

            # Hook for model saving instance if supported by model manager
            model_class = self.admin_model.model
            if hasattr(model_class, "create_instance"):
                result = model_class.create_instance(form_data)
                if hasattr(result, "__await__"):
                    await result

            return RedirectResponse(
                f"{self.dashboard.url_prefix}/{self.admin_model.get_name()}",
                status_code=302,
            )

        context = {
            "model": self.admin_model,
            "models": self.dashboard.registry.get_all(),
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
        model_class = self.admin_model.model

        if self.request.method == "POST":
            form_data = await self.request.form() if hasattr(self.request, "form") else {}
            if hasattr(form_data, "to_dict"):
                form_data = form_data.to_dict()

            if hasattr(model_class, "update_instance"):
                result = model_class.update_instance(self.object_id, form_data)
                if hasattr(result, "__await__"):
                    await result

            return RedirectResponse(
                f"{self.dashboard.url_prefix}/{self.admin_model.get_name()}",
                status_code=302,
            )

        obj = None
        if hasattr(model_class, "get_instance"):
            result = model_class.get_instance(self.object_id)
            obj = await result if hasattr(result, "__await__") else result

        context = {
            "model": self.admin_model,
            "models": self.dashboard.registry.get_all(),
            "object": obj,
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
            model_class = self.admin_model.model
            if hasattr(model_class, "delete_instance"):
                result = model_class.delete_instance(self.object_id)
                if hasattr(result, "__await__"):
                    await result

            return RedirectResponse(
                f"{self.dashboard.url_prefix}/{self.admin_model.get_name()}",
                status_code=302,
            )

        context = {
            "model": self.admin_model,
            "models": self.dashboard.registry.get_all(),
            "verbose_name": self.admin_model.get_verbose_name(),
            "object_id": self.object_id,
        }
        return await self.dashboard.jinax.render_response("admin/delete.html", context)