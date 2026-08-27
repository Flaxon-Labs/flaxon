"""flaxon.admin.cms — a small, self-contained CMS for the Flaxon admin.

Drop this file plus cms.html next to it, then wire it up like AdminDashboard:

    from flaxon.admin.cms import CMS, ContentType, CMSField

    cms = CMS(app, url_prefix="/admin/cms", title="My Site CMS")

    cms.register(ContentType(
        name="post",
        label="Post",
        label_plural="Posts",
        fields=[
            CMSField("title", "Title", required=True),
            CMSField("content", "Content", type="richtext"),
            CMSField("featured_image", "Featured Image URL", type="url", required=False),
        ],
        list_display=["title", "status", "updated_at"],
        list_filter=["status"],
        search_fields=["title", "content"],
    ))

Using the CMS is entirely optional and independent of AdminDashboard — it
does not require or modify the model-based admin at all. It's a single
extra panel with its own JSON API and its own single-page UI (cms.html).

Everything is in-memory by default. Swap `ContentType.store` (a plain
dict) for your own persistence by subclassing CMS and overriding
`_get_store`/`_save_store`, or by pre-populating `content_type.items`.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from flaxon.exceptions import BadRequest, NotFound
from flaxon.http import HTMLResponse, JSONResponse, Request, Response

_PACKAGE_DIR = Path(__file__).parent
_DEFAULT_TEMPLATE_PATH = _PACKAGE_DIR / "templates" / "admin" / "cms.html"

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = _SLUG_RE.sub("-", value).strip("-")
    return value or "untitled"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

FieldType = str  # "text" | "textarea" | "richtext" | "boolean" | "number" | "date" | "email" | "url" | "select"


@dataclass
class CMSField:
    name: str
    label: str | None = None
    type: FieldType = "text"
    required: bool = False
    choices: list[str] | None = None
    help_text: str = ""
    default: Any = None

    def __post_init__(self) -> None:
        if self.label is None:
            self.label = self.name.replace("_", " ").title()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "type": self.type,
            "required": self.required,
            "choices": self.choices,
            "help_text": self.help_text,
            "default": self.default,
        }

    def coerce(self, raw: Any) -> Any:
        if raw is None:
            return self.default
        if self.type == "boolean":
            if isinstance(raw, bool):
                return raw
            return str(raw).lower() in {"1", "true", "on", "yes"}
        if self.type == "number":
            try:
                return float(raw) if "." in str(raw) else int(raw)
            except (ValueError, TypeError):
                return raw
        return raw


@dataclass
class BulkAction:
    name: str
    label: str
    handler: Callable[["ContentType", list[str]], Any]


@dataclass
class ContentType:
    name: str
    label: str | None = None
    label_plural: str | None = None
    fields: list[CMSField] = field(default_factory=list)
    list_display: list[str] | None = None
    list_filter: list[str] = field(default_factory=list)
    search_fields: list[str] = field(default_factory=list)
    has_status: bool = True
    has_slug: bool = True
    slug_source: str = "title"
    icon: str = "fa-file-lines"
    order_by: str = "-updated_at"

    # runtime state
    items: dict[str, dict[str, Any]] = field(default_factory=dict, repr=False)
    _actions: dict[str, BulkAction] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if self.label is None:
            self.label = self.name.replace("_", " ").title()
        if self.label_plural is None:
            self.label_plural = self.label + "s"
        if self.list_display is None:
            display = [f.name for f in self.fields[:3]]
            if self.has_status:
                display.append("status")
            display.append("updated_at")
            self.list_display = display

        # Built-in bulk actions.
        self.register_action("delete", "Delete selected", lambda ct, ids: [ct.delete(i) for i in ids])
        if self.has_status:
            self.register_action("publish", "Publish selected", lambda ct, ids: ct._set_status(ids, "published"))
            self.register_action("unpublish", "Unpublish selected", lambda ct, ids: ct._set_status(ids, "draft"))

    def register_action(self, name: str, label: str, handler: Callable[["ContentType", list[str]], Any]) -> None:
        self._actions[name] = BulkAction(name, label, handler)

    def field_map(self) -> dict[str, CMSField]:
        return {f.name: f for f in self.fields}

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "label_plural": self.label_plural,
            "fields": [f.to_dict() for f in self.fields],
            "list_display": self.list_display,
            "list_filter": self.list_filter,
            "search_fields": self.search_fields,
            "has_status": self.has_status,
            "has_slug": self.has_slug,
            "icon": self.icon,
            "actions": [{"name": a.name, "label": a.label} for a in self._actions.values()],
        }

    # -- data ops ----------------------------------------------------

    def validate(self, data: dict[str, Any], *, partial: bool = False) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        fmap = self.field_map()
        for f in self.fields:
            if f.name in data:
                cleaned[f.name] = f.coerce(data[f.name])
            elif not partial:
                if f.required:
                    raise BadRequest(f"Field '{f.name}' is required.")
                cleaned[f.name] = f.coerce(f.default)
        for key in data:
            if key not in fmap and key in {"status", "slug"}:
                cleaned[key] = data[key]
        return cleaned

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        cleaned = self.validate(data)
        item_id = uuid.uuid4().hex[:12]
        now = _now()
        record: dict[str, Any] = {"id": item_id, **cleaned}
        if self.has_slug:
            title_source = data.get("slug") or cleaned.get(self.slug_source) or item_id
            record["slug"] = self._unique_slug(slugify(str(title_source)))
        if self.has_status:
            record.setdefault("status", data.get("status", "draft"))
        record["created_at"] = now
        record["updated_at"] = now
        self.items[item_id] = record
        return record

    def update(self, item_id: str, data: dict[str, Any]) -> dict[str, Any]:
        record = self.items.get(item_id)
        if record is None:
            raise NotFound(f"{self.label} not found.")
        cleaned = self.validate(data, partial=True)
        record.update(cleaned)
        if self.has_slug and "slug" in data:
            record["slug"] = self._unique_slug(slugify(str(data["slug"])), exclude=item_id)
        if self.has_status and "status" in data:
            record["status"] = data["status"]
        record["updated_at"] = _now()
        return record

    def delete(self, item_id: str) -> bool:
        return self.items.pop(item_id, None) is not None

    def get(self, item_id: str) -> dict[str, Any]:
        record = self.items.get(item_id)
        if record is None:
            raise NotFound(f"{self.label} not found.")
        return record

    def _unique_slug(self, base: str, exclude: str | None = None) -> str:
        slug = base
        n = 2
        existing = {r["slug"] for i, r in self.items.items() if r.get("slug") and i != exclude}
        while slug in existing:
            slug = f"{base}-{n}"
            n += 1
        return slug

    def _set_status(self, ids: list[str], status: str) -> None:
        for item_id in ids:
            record = self.items.get(item_id)
            if record is not None:
                record["status"] = status
                record["updated_at"] = _now()

    def run_action(self, name: str, ids: list[str]) -> None:
        action = self._actions.get(name)
        if action is None:
            raise NotFound(f"Unknown action '{name}'.")
        action.handler(self, ids)

    def query(
        self,
        *,
        q: str | None = None,
        filters: dict[str, str] | None = None,
        order_by: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        records = list(self.items.values())

        if q:
            needle = q.lower()
            fields_to_search = self.search_fields or [f.name for f in self.fields if f.type in {"text", "textarea", "richtext"}]

            def matches(rec: dict[str, Any]) -> bool:
                return any(needle in str(rec.get(f, "")).lower() for f in fields_to_search)

            records = [r for r in records if matches(r)]

        if filters:
            for key, value in filters.items():
                if value == "" or value is None:
                    continue
                records = [r for r in records if str(r.get(key, "")) == str(value)]

        order = order_by or self.order_by
        reverse = order.startswith("-")
        key_name = order.lstrip("-")
        records.sort(key=lambda r: (r.get(key_name) is None, r.get(key_name)), reverse=reverse)

        total = len(records)
        page = max(1, page)
        per_page = max(1, min(per_page, 200))
        start = (page - 1) * per_page
        page_records = records[start : start + per_page]

        return {
            "items": page_records,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": max(1, (total + per_page - 1) // per_page),
        }

    def stats(self) -> dict[str, Any]:
        total = len(self.items)
        published = sum(1 for r in self.items.values() if r.get("status") == "published") if self.has_status else total
        draft = total - published if self.has_status else 0
        return {"total": total, "published": published, "draft": draft}


# ---------------------------------------------------------------------------
# CMS panel
# ---------------------------------------------------------------------------


class CMS:
    """A self-contained, WordPress/Django-admin-style content panel."""

    def __init__(
        self,
        app: Any,
        url_prefix: str = "/admin/cms",
        title: str = "CMS",
        template_path: str | Path | None = None,
    ) -> None:
        self.app = app
        self.url_prefix = url_prefix.rstrip("/")
        self.title = title
        self.template_path = Path(template_path) if template_path else _DEFAULT_TEMPLATE_PATH
        self.content_types: dict[str, ContentType] = {}
        self._mount_static()
        self._register_routes()

    def _mount_static(self) -> None:
        if hasattr(self.app, "mount_static"):
            static_dir = _PACKAGE_DIR / "static"
            self.app.mount_static("/static", str(static_dir))

    def register(self, content_type: ContentType) -> ContentType:
        self.content_types[content_type.name] = content_type
        return content_type

    def _get_type(self, name: str) -> ContentType:
        ct = self.content_types.get(name)
        if ct is None:
            raise NotFound(f"Unknown content type '{name}'.")
        return ct

    # -- routing -------------------------------------------------------

    def _register_routes(self) -> None:
        # Inserted at the front of the router's route list (rather than
        # appended) so these specific paths always match before a more
        # generic catch-all pattern that might also be registered under
        # the same prefix — e.g. AdminDashboard's `/admin/<model_name>`
        # would otherwise swallow `/admin/cms` if AdminDashboard happens
        # to be created first. This makes CMS safe to mount under an
        # AdminDashboard's url_prefix in either registration order.
        from flaxon.routing.route import Route

        router = self.app.router
        prefix = self.url_prefix

        route_specs: list[tuple[str, set[str], Any]] = [
            (f"{prefix}", {"GET"}, self.spa),
            (f"{prefix}/", {"GET"}, self.spa),
            (f"{prefix}/api/config", {"GET"}, self.api_config),
            (f"{prefix}/api/stats", {"GET"}, self.api_stats),
            (f"{prefix}/api/<type_name>/items", {"GET"}, self.api_list),
            (f"{prefix}/api/<type_name>/items", {"POST"}, self.api_create),
            (f"{prefix}/api/<type_name>/items/<item_id>", {"GET"}, self.api_get),
            (f"{prefix}/api/<type_name>/items/<item_id>", {"PUT"}, self.api_update),
            (f"{prefix}/api/<type_name>/items/<item_id>", {"DELETE"}, self.api_delete),
            (f"{prefix}/api/<type_name>/actions/<action_name>", {"POST"}, self.api_action),
        ]
        for path, methods, handler in reversed(route_specs):
            route = Route(router._path(path), handler, methods, handler.__name__)
            router.routes.insert(0, route)

    # -- handlers --------------------------------------------------------

    async def spa(self, request: Request) -> Response:
        html = self.template_path.read_text(encoding="utf-8")
        html = html.replace("__CMS_API_BASE__", f"{self.url_prefix}/api")
        html = html.replace("__CMS_TITLE__", self.title)
        return HTMLResponse(html)

    async def api_config(self, request: Request) -> Response:
        return JSONResponse({
            "title": self.title,
            "types": [ct.schema() for ct in self.content_types.values()],
        })

    async def api_stats(self, request: Request) -> Response:
        return JSONResponse({name: ct.stats() for name, ct in self.content_types.items()})

    async def api_list(self, request: Request, type_name: str) -> Response:
        ct = self._get_type(type_name)
        query = request.query
        filters = {key[len("filter_"):]: value for key, value in query.items() if key.startswith("filter_")}
        result = ct.query(
            q=query.get("q") or None,
            filters=filters,
            order_by=query.get("order_by") or None,
            page=int(query.get("page", 1) or 1),
            per_page=int(query.get("per_page", 20) or 20),
        )
        return JSONResponse(result)

    async def api_create(self, request: Request, type_name: str) -> Response:
        ct = self._get_type(type_name)
        data = await request.json()
        record = ct.create(data or {})
        return JSONResponse(record, status_code=201)

    async def api_get(self, request: Request, type_name: str, item_id: str) -> Response:
        ct = self._get_type(type_name)
        return JSONResponse(ct.get(item_id))

    async def api_update(self, request: Request, type_name: str, item_id: str) -> Response:
        ct = self._get_type(type_name)
        data = await request.json()
        record = ct.update(item_id, data or {})
        return JSONResponse(record)

    async def api_delete(self, request: Request, type_name: str, item_id: str) -> Response:
        ct = self._get_type(type_name)
        if not ct.delete(item_id):
            raise NotFound(f"{ct.label} not found.")
        return JSONResponse({"deleted": True})

    async def api_action(self, request: Request, type_name: str, action_name: str) -> Response:
        ct = self._get_type(type_name)
        body = await request.json() or {}
        ids = body.get("ids", [])
        if not isinstance(ids, list):
            raise BadRequest("'ids' must be a list.")
        ct.run_action(action_name, ids)
        return JSONResponse({"ok": True, "affected": len(ids)})