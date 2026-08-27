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
        page = max(1, int(self.request.query.get("page", "1") or 1))
        per_page = min(200, max(1, int(self.request.query.get("per_page", "25") or 25)))
        query_result = None
        if hasattr(model_class, "query"):
            result = model_class.query(q=self.request.query.get("q") or None, page=page, per_page=per_page)
            query_result = await result if hasattr(result, "__await__") else result
            objects = list(query_result.get("items", []))
        elif hasattr(model_class, "get_instances"):
            result = model_class.get_instances()
            objects = list(await result if hasattr(result, "__await__") else result)
            needle = self.request.query.get("q", "").lower()
            if needle:
                fields = self.admin_model.search_fields or self.admin_model.fields
                objects = [obj for obj in objects if any(needle in str((obj.get(f) if isinstance(obj, dict) else getattr(obj, f, ""))).lower() for f in fields)]
            for field in self.admin_model.list_filter:
                value = self.request.query.get(f"filter_{field}", "")
                if value:
                    objects = [obj for obj in objects if str((obj.get(field) if isinstance(obj, dict) else getattr(obj, field, ""))) == value]
            ordering = self.request.query.get("order_by")
            if ordering:
                reverse = ordering.startswith("-")
                key = ordering.lstrip("-")
                objects.sort(key=lambda obj: (obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)), reverse=reverse)
            total = len(objects)
            objects = objects[(page - 1) * per_page : page * per_page]
            query_result = {"total": total, "pages": max(1, (total + per_page - 1) // per_page), "page": page, "per_page": per_page}

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
            "user": getattr(self.request, "user", None),
            "query": self.request.query.get("q", ""),
            "pagination": query_result or {"total": len(objects), "pages": 1, "page": 1, "per_page": len(objects)},
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
            form_data = self.dashboard.validate_csrf(form_data)

            # Hook for model saving instance if supported by model manager
            model_class = self.admin_model.model
            result = None
            if hasattr(model_class, "create_instance"):
                result = model_class.create_instance(form_data)
                if hasattr(result, "__await__"):
                    await result
            record_id = str(result.get("id", "")) if isinstance(result, dict) else None
            self.dashboard.record_activity("created", self.admin_model.get_name(), self.request, record_id)

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
            "user": getattr(self.request, "user", None),
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
            form_data = self.dashboard.validate_csrf(form_data)

            if hasattr(model_class, "update_instance"):
                result = model_class.update_instance(self.object_id, form_data)
                if hasattr(result, "__await__"):
                    await result
            self.dashboard.record_activity("updated", self.admin_model.get_name(), self.request, self.object_id)

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
            form_data = await self.request.form()
            self.dashboard.validate_csrf(form_data.to_dict())
            # Hook for deleting model instance
            model_class = self.admin_model.model
            if hasattr(model_class, "delete_instance"):
                result = model_class.delete_instance(self.object_id)
                if hasattr(result, "__await__"):
                    await result
            self.dashboard.record_activity("deleted", self.admin_model.get_name(), self.request, self.object_id)

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
