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
import csv
import io
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from flaxon.exceptions import BadRequest, NotFound
from flaxon.http import HTMLResponse, JSONResponse, Request, Response
from flaxon.security import Sanitizer
from .services import AdminAuth

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

FieldType = str  # text, textarea, richtext, boolean, number, date, datetime, email, url, select, json, repeater, relationship, file, image


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
        if self.type in {"json", "repeater", "relationship"} and isinstance(raw, str):
            try:
                return json.loads(raw)
            except (TypeError, ValueError):
                return [] if self.type in {"repeater", "relationship"} else raw
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
    statuses: list[str] = field(default_factory=lambda: ["draft", "review", "approved", "scheduled", "published", "archived"])
    has_slug: bool = True
    slug_source: str = "title"
    icon: str = "fa-file-lines"
    order_by: str = "-updated_at"
    revisions: list[dict[str, Any]] = field(default_factory=list, repr=False)

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
            "statuses": self.statuses,
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
                value = f.coerce(data[f.name])
                cleaned[f.name] = Sanitizer.allow_html(value) if f.type == "richtext" and isinstance(value, str) else value
            elif not partial:
                if f.required:
                    raise BadRequest(f"Field '{f.name}' is required.")
                cleaned[f.name] = f.coerce(f.default)
        for key in data:
            if key not in fmap and key in {"status", "slug", "publish_at"}:
                cleaned[key] = data[key]
        if self.has_status and "status" in cleaned and cleaned["status"] not in self.statuses:
            raise BadRequest(f"Invalid status '{cleaned['status']}'.")
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
        self.revisions.append({"action": "created", "item_id": item_id, "at": now, "record": dict(record)})
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
        self.revisions.append({"action": "updated", "item_id": item_id, "at": record["updated_at"], "record": dict(record)})
        return record

    def delete(self, item_id: str) -> bool:
        record = self.items.pop(item_id, None)
        if record is not None:
            self.revisions.append({"action": "deleted", "item_id": item_id, "at": _now(), "record": dict(record)})
        return record is not None

    def restore(self, item_id: str, revision: int) -> dict[str, Any]:
        revisions = [r for r in self.revisions if r["item_id"] == item_id]
        try:
            snapshot = dict(revisions[revision]["record"])
        except (IndexError, KeyError) as exc:
            raise NotFound("Revision not found.") from exc
        self.items[item_id] = snapshot
        snapshot["updated_at"] = _now()
        self.revisions.append({"action": "restored", "item_id": item_id, "at": snapshot["updated_at"], "record": dict(snapshot)})
        return snapshot

    def compare_revisions(self, item_id: str) -> list[dict[str, Any]]:
        revisions = [r for r in self.revisions if r["item_id"] == item_id]
        comparisons: list[dict[str, Any]] = []
        for index, revision in enumerate(revisions):
            before = revisions[index - 1]["record"] if index else {}
            after = revision["record"]
            keys = set(before) | set(after)
            changes = {key: {"before": before.get(key), "after": after.get(key)} for key in keys if before.get(key) != after.get(key)}
            comparisons.append({**revision, "before": before, "after": after, "changes": changes})
        return comparisons

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
        now = _now()
        for record in self.items.values():
            if self.has_status and record.get("status") == "scheduled" and record.get("publish_at") and record["publish_at"] <= now:
                record["status"] = "published"
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
        auth: AdminAuth | None = None,
        database: Any | None = None,
    ) -> None:
        self.app = app
        self.url_prefix = url_prefix.rstrip("/")
        self.title = title
        self.template_path = Path(template_path) if template_path else _DEFAULT_TEMPLATE_PATH
        self.auth = auth or getattr(app, "_flaxon_admin_auth", None)
        self.store = getattr(app, "_flaxon_admin_store", None)
        self.database = database or getattr(app, "database", None) or getattr(app, "db", None)
        self._database_loaded = False
        self.content_types: dict[str, ContentType] = {}
        self.taxonomies: dict[str, dict[str, list[str]]] = {}
        self.comments: list[dict[str, Any]] = []
        self.menus: dict[str, list[dict[str, Any]]] = {}
        self.hooks: dict[str, list[Callable[..., Any]]] = {}
        if self.store:
            self.taxonomies = self.store.get("cms", "taxonomies", {})
            self.comments = self.store.get("cms", "comments", [])
            self.menus = self.store.get("cms", "menus", {})
        self._mount_static()
        self._register_routes()

    def _mount_static(self) -> None:
        if hasattr(self.app, "mount_static"):
            static_dir = _PACKAGE_DIR / "static"
            self.app.mount_static("/static", str(static_dir))

    def register(self, content_type: ContentType) -> ContentType:
        if self.store:
            content_type.items.update(self.store.get(f"cms:{content_type.name}", "items", {}))
        self.content_types[content_type.name] = content_type
        return content_type

    def add_hook(self, name: str, callback: Callable[..., Any]) -> Callable[..., Any]:
        self.hooks.setdefault(name, []).append(callback)
        return callback

    def run_hook(self, name: str, value: Any) -> Any:
        for callback in self.hooks.get(name, []):
            value = callback(value)
        return value

    def _save(self, content_type: ContentType) -> None:
        if self.store:
            self.store.set(f"cms:{content_type.name}", "items", content_type.items)

    def _save_resources(self) -> None:
        if self.store:
            self.store.set("cms", "taxonomies", self.taxonomies)
            self.store.set("cms", "comments", self.comments)
            self.store.set("cms", "menus", self.menus)

    async def _save_content(self, content_type: ContentType) -> None:
        await self._save_database(f"cms:{content_type.name}", "items", {**content_type.items, "__revisions__": content_type.revisions})

    async def _save_all_resources(self) -> None:
        await self._save_database("cms", "taxonomies", self.taxonomies)
        await self._save_database("cms", "comments", self.comments)
        await self._save_database("cms", "menus", self.menus)

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
            (f"{prefix}/api/<type_name>/items/<item_id>/history", {"GET"}, self.api_history),
            (f"{prefix}/api/<type_name>/items/<item_id>/restore/<revision>", {"POST"}, self.api_restore),
            (f"{prefix}/api/<type_name>/actions/<action_name>", {"POST"}, self.api_action),
            (f"{prefix}/api/export/<type_name>", {"GET"}, self.api_export),
            (f"{prefix}/api/import/<type_name>", {"POST"}, self.api_import),
            (f"{prefix}/api/taxonomies", {"GET", "POST"}, self.api_taxonomies),
            (f"{prefix}/api/taxonomies/<taxonomy_name>", {"POST", "PATCH", "DELETE"}, self.api_taxonomy),
            (f"{prefix}/api/comments", {"GET", "POST"}, self.api_comments),
            (f"{prefix}/api/comments/<comment_id>", {"PATCH", "DELETE"}, self.api_comment),
            (f"{prefix}/api/menus/<menu_name>", {"GET", "PUT"}, self.api_menu),
        ]
        for path, methods, handler in reversed(route_specs):
            route = Route(router._path(path), handler, methods, handler.__name__)
            router.routes.insert(0, route)

    # -- handlers --------------------------------------------------------

    async def spa(self, request: Request) -> Response:
        await self._require_user(request)
        html = self.template_path.read_text(encoding="utf-8")
        html = html.replace("__CMS_API_BASE__", f"{self.url_prefix}/api")
        html = html.replace("__CMS_TITLE__", self.title)
        dashboard = getattr(self.app, "_flaxon_admin_dashboard", None)
        html = html.replace("__CMS_CSRF_TOKEN__", dashboard.csrf_token() if dashboard else "")
        return HTMLResponse(html)

    async def api_config(self, request: Request) -> Response:
        await self._require_user(request)
        return JSONResponse({
            "title": self.title,
            "types": [ct.schema() for ct in self.content_types.values()],
        })

    async def api_stats(self, request: Request) -> Response:
        await self._require_user(request)
        return JSONResponse({name: ct.stats() for name, ct in self.content_types.items()})

    async def api_list(self, request: Request, type_name: str) -> Response:
        await self._require_user(request)
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
        await self._require_user(request)
        ct = self._get_type(type_name)
        data = await self._body_data(request)
        if isinstance(data, dict):
            for field in ct.fields:
                upload = data.get(field.name)
                if field.type in {"file", "image"} and hasattr(upload, "filename"):
                    from flaxon.http.uploads import FileStorage
                    path = FileStorage().save(upload)
                    data[field.name] = f"/uploads/{Path(path).name}"
        record = self.run_hook("before_create", data or {})
        record = ct.create(record)
        record = self.run_hook("after_create", record)
        self._save(ct)
        await self._save_content(ct)
        return JSONResponse(record, status_code=201)

    async def api_get(self, request: Request, type_name: str, item_id: str) -> Response:
        await self._require_user(request)
        ct = self._get_type(type_name)
        return JSONResponse(ct.get(item_id))

    async def api_update(self, request: Request, type_name: str, item_id: str) -> Response:
        await self._require_user(request)
        ct = self._get_type(type_name)
        data = await self._body_data(request)
        record = ct.update(item_id, self.run_hook("before_update", data or {}))
        record = self.run_hook("after_update", record)
        self._save(ct)
        await self._save_content(ct)
        return JSONResponse(record)

    async def api_delete(self, request: Request, type_name: str, item_id: str) -> Response:
        await self._require_user(request)
        ct = self._get_type(type_name)
        deleted = ct.delete(item_id)
        self.run_hook("after_delete", {"type": type_name, "id": item_id, "deleted": deleted})
        if not deleted:
            raise NotFound(f"{ct.label} not found.")
        self._save(ct)
        await self._save_content(ct)
        return JSONResponse({"deleted": True})

    async def api_action(self, request: Request, type_name: str, action_name: str) -> Response:
        await self._require_user(request)
        ct = self._get_type(type_name)
        body = await request.json() or {}
        ids = body.get("ids", [])
        if not isinstance(ids, list):
            raise BadRequest("'ids' must be a list.")
        ct.run_action(action_name, ids)
        self._save(ct)
        await self._save_content(ct)
        return JSONResponse({"ok": True, "affected": len(ids)})

    async def api_restore(self, request: Request, type_name: str, item_id: str, revision: str) -> Response:
        await self._require_user(request)
        ct = self._get_type(type_name)
        record = ct.restore(item_id, int(revision))
        self._save(ct)
        await self._save_content(ct)
        return JSONResponse(record)

    async def api_export(self, request: Request, type_name: str) -> Response:
        await self._require_user(request)
        ct = self._get_type(type_name)
        fmt = request.query.get("format", "json").lower()
        records = list(ct.items.values())
        if fmt == "csv":
            output = io.StringIO()
            keys = sorted({key for record in records for key in record})
            writer = csv.DictWriter(output, fieldnames=keys)
            writer.writeheader(); writer.writerows(records)
            return Response(output.getvalue(), media_type="text/csv; charset=utf-8", headers={"content-disposition": f"attachment; filename={type_name}.csv"})
        return JSONResponse(records, headers={"content-disposition": f"attachment; filename={type_name}.json"})

    async def api_import(self, request: Request, type_name: str) -> Response:
        await self._require_user(request)
        ct = self._get_type(type_name)
        if "text/csv" in request.headers.get("content-type", ""):
            data = list(csv.DictReader(io.StringIO(await request.text())))
        else:
            data = await request.json()
        if not isinstance(data, list):
            raise BadRequest("Import body must be a JSON list of records.")
        created: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        for row_number, record in enumerate(data, 1):
            if not isinstance(record, dict):
                errors.append({"row": row_number, "error": "Record must be an object."})
                continue
            try:
                created.append(ct.create(record))
            except (BadRequest, ValueError, TypeError) as exc:
                errors.append({"row": row_number, "error": str(exc)})
        self._save(ct)
        await self._save_content(ct)
        return JSONResponse({"imported": len(created), "items": created, "errors": errors}, status_code=201 if created else 422)

    async def api_taxonomies(self, request: Request) -> Response:
        await self._require_user(request)
        if request.method == "POST":
            body = await request.json() or {}
            name = str(body.get("name", "")).strip()
            if not name:
                raise BadRequest("Taxonomy name is required.")
            self.taxonomies.setdefault(name, {})
            self.taxonomies[name].update({str(k): list(v) for k, v in (body.get("terms") or {}).items()})
            self._save_resources()
            await self._save_all_resources()
        return JSONResponse(self.taxonomies)

    async def api_taxonomy(self, request: Request, taxonomy_name: str) -> Response:
        await self._require_user(request)
        if taxonomy_name not in self.taxonomies:
            raise NotFound("Taxonomy not found.")
        if request.method == "DELETE":
            del self.taxonomies[taxonomy_name]
        else:
            body = await request.json() or {}
            terms = self.taxonomies[taxonomy_name]
            if "terms" in body:
                terms.update({str(k): list(v) if isinstance(v, list) else v for k, v in (body.get("terms") or {}).items()})
            if body.get("term"):
                term = slugify(str(body["term"]))
                parent = body.get("parent", "")
                terms[term] = [parent] if parent else []
        self._save_resources()
        await self._save_all_resources()
        return JSONResponse(self.taxonomies)

    async def api_comments(self, request: Request) -> Response:
        await self._require_user(request)
        if request.method == "POST":
            body = await request.json() or {}
            comment = {"id": uuid.uuid4().hex[:12], "status": "pending", "created_at": _now(), **body}
            self.comments.append(comment)
            self._save_resources()
            await self._save_all_resources()
            return JSONResponse(comment, status_code=201)
        return JSONResponse(self.comments)

    async def api_comment(self, request: Request, comment_id: str) -> Response:
        await self._require_user(request)
        comment = next((item for item in self.comments if item["id"] == comment_id), None)
        if comment is None:
            raise NotFound("Comment not found.")
        if request.method == "DELETE":
            self.comments.remove(comment); self._save_resources(); await self._save_all_resources(); return JSONResponse({"deleted": True})
        comment.update(await request.json() or {})
        self._save_resources()
        await self._save_all_resources()
        return JSONResponse(comment)

    async def api_menu(self, request: Request, menu_name: str) -> Response:
        await self._require_user(request)
        if request.method == "PUT":
            items = await request.json()
            if not isinstance(items, list):
                raise BadRequest("Menu must be a list.")
            self.menus[menu_name] = items
            self._save_resources()
            await self._save_all_resources()
        return JSONResponse({"name": menu_name, "items": self.menus.get(menu_name, [])})

    async def api_history(self, request: Request, type_name: str, item_id: str) -> Response:
        await self._require_user(request)
        ct = self._get_type(type_name)
        return JSONResponse({"items": ct.compare_revisions(item_id)})

    async def _require_user(self, request: Request) -> Any:
        await self._load_database()
        if self.auth is None:
            return None
        user = await self.auth.current_user(request)
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            dashboard = getattr(self.app, "_flaxon_admin_dashboard", None)
            if dashboard and not dashboard.csrf.verify_token(request.headers.get("x-csrf-token", "")):
                raise BadRequest("CSRF token missing or invalid")
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
                value = json.loads(row["value"])
            except (TypeError, ValueError):
                continue
            namespace, key = row["namespace"], row["key"]
            if namespace.startswith("cms:") and key == "items":
                ct = self.content_types.get(namespace[4:])
                if ct:
                    payload = value or {}
                    revisions = payload.get("__revisions__", []) if isinstance(payload, dict) else []
                    ct.items.update({k: v for k, v in payload.items() if k != "__revisions__"} if isinstance(payload, dict) else {})
                    ct.revisions.extend(revisions)
            elif namespace == "cms" and key == "taxonomies":
                self.taxonomies = value or {}
            elif namespace == "cms" and key == "comments":
                self.comments = value or []
            elif namespace == "cms" and key == "menus":
                self.menus = value or {}
        self._database_loaded = True

    async def _save_database(self, namespace: str, key: str, value: Any) -> None:
        if self.database is None:
            return
        encoded = json.dumps(value, default=str)
        await self.database.execute(
            "INSERT INTO flaxon_admin_store(namespace, key, value) VALUES ($1, $2, $3) ON CONFLICT(namespace, key) DO UPDATE SET value = excluded.value",
            namespace,
            key,
            encoded,
        )

    async def _body_data(self, request: Request) -> Any:
        content_type = request.headers.get("content-type", "")
        return (await request.form()).to_dict() if "multipart/form-data" in content_type else await request.json()
