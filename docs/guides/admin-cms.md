# Admin and CMS Production Guide

Flaxon provides two complementary management surfaces:

- `AdminDashboard` manages application models, users, roles, settings, media,
  audit activity, search, and operational status.
- `CMS` provides schema-driven content editing through a browser SPA, including
  publishing workflows, revisions, taxonomies, comments, menus, and data
  import/export.

The bundled UI is a reference client. Every CMS action is also available as a
JSON API, so a team can replace the SPA with React, Vue, mobile, or server-side
clients without replacing the backend contracts.

## Quick Start

```python
from flaxon import Flaxon
from flaxon.admin import AdminConfig, AdminDashboard
from flaxon.admin.cms import CMS

app = Flaxon("backoffice", debug=True)

admin = AdminDashboard(
    app,
    config=AdminConfig(site_title="Acme Backoffice", timezone="UTC"),
    url_prefix="/admin",
    storage_path="admin.sqlite3",
    users=[{"username": "admin", "password": "change-me"}],
)

cms = CMS(app, url_prefix="/admin/cms", title="Acme Content", auth=admin.auth)
```

Run locally:

```bash
flaxon run app:app --reload --port 8000
```

Use `/admin/login`, `/admin/`, and `/admin/cms/`. Development credentials
should be replaced with environment-managed credentials before deployment.

## Persistence and Migrations

For a self-contained local store, set `storage_path` (the parent directory must
already exist). This persists users,
roles, settings, activity, media metadata, CMS records, taxonomies, comments,
menus, and revisions in the admin store. Do not use the default in-memory mode
for production or multiple workers.

For an application-owned database, generate and apply the migration:

```python
from flaxon.admin import write_admin_migration

write_admin_migration("migrations")
```

```bash
flaxon migrate --database sqlite://./app.db --migrations-dir migrations
```

Pass the configured `DatabaseManager` as `database=` to both `AdminDashboard`
and `CMS`. The framework keeps the admin/CMS namespace contract separate from
your domain repositories, so existing application tables are not modified.

For PostgreSQL, MySQL, SQLAlchemy, or a custom repository, implement the
database methods used by the services (`execute`, `fetch_one`, and
`fetch_all`) and pass that object as `database=`. Keep writes transactional.

## Authentication and Authorization

Admin routes are authenticated by the dashboard session backend. Use an
application-owned backend when the application already has identity:

```python
admin = AdminDashboard(app, auth_backend=my_auth_backend)
cms = CMS(app, auth=admin.auth)
```

Permissions are checked at the route boundary. Common permissions are:

| Permission | Scope |
|---|---|
| `admin:read` | Dashboard, model lists, activity, operations |
| `admin:write` | Model create/update/actions |
| `admin:users` | User and role management |
| `admin:media` | Upload and manage assets |
| `admin:settings` | Change site settings |
| `<model>:create` | Create a specific model |
| `<model>:read` | Read a specific model |
| `<model>:update` | Update a specific model |
| `<model>:delete` | Delete a specific model |
| `admin:superuser` | Full access |

Roles map to permissions through the role editor or `admin.roles`. Do not
grant `admin:superuser` to normal editors. Use separate editor and publisher
roles when content approval is required.

Security options include login throttling, CSRF validation, TOTP MFA,
single-use password reset tokens, optional email verification, file type and
size validation, path traversal protection, and rich-text allowlist
sanitization.

```python
admin = AdminDashboard(
    app,
    require_email_verification=True,
    password_reset_sender=send_reset_message,
    email_verification_sender=send_verification_message,
    max_upload_size=10 * 1024 * 1024,
    allowed_upload_types={"image/jpeg", "image/png", "image/webp", "application/pdf"},
)
```

Browser forms include a hidden `_csrf` field. SPA mutations include the same
token in the `X-CSRF-Token` header. Custom clients must preserve this rule.

The backend exposes revision comparison data, menu hierarchy data, media
metadata operations, scheduled status fields, durable thumbnail jobs, resumable
uploads, audit verification, and notification preferences. The bundled SPA is
the reference client for the core workflows; applications needing a full
editorial calendar, visual diff workspace, nested menu tree editor, or external
notification delivery should build those views and adapters on these APIs.

## Model Admin

Register a model with async CRUD hooks:

```python
from flaxon.admin import admin_model

@admin_model(
    list_display=["id", "name", "price"],
    list_filter=["active"],
    search_fields=["name", "sku"],
    fields=["name", "sku", "price", "active"],
)
class Product:
    _items = {}

    @classmethod
    async def get_instances(cls): return list(cls._items.values())
    @classmethod
    async def get_instance(cls, id): return cls._items.get(id)
    @classmethod
    async def create_instance(cls, data):
        data["id"] = str(len(cls._items) + 1)
        cls._items[data["id"]] = data
        return data
    @classmethod
    async def update_instance(cls, id, data):
        if id not in cls._items: return None
        cls._items[id].update(data)
        return cls._items[id]
    @classmethod
    async def delete_instance(cls, id):
        return cls._items.pop(id, None) is not None
```

The model list supports search, exact filters, sorting, pagination, selection,
bulk actions, create, edit, detail, delete confirmation, and history links.
Use `admin.register(model, ...)` when decorator registration is not suitable.

`admin_action` marks reusable action methods; attach custom callables to the
registered `AdminModel` when an action needs custom labels or a separate
service:

```python
async def archive(ids):
    for record_id in ids:
        await Product.update_instance(record_id, {"active": False})

admin.registry.get("product").add_action("archive", archive)
```

Use `admin_display` for computed read-only columns. Keep authorization in the
dashboard permission map and business validation in the model/service layer.

## CMS Content Types

```python
from flaxon.admin.cms import CMSField, ContentType

cms.register(ContentType(
    name="post",
    label="Post",
    label_plural="Posts",
    fields=[
        CMSField("title", required=True),
        CMSField("summary", type="textarea"),
        CMSField("body", type="richtext"),
        CMSField("hero", type="image"),
        CMSField("published_on", type="datetime"),
        CMSField("related", type="relationship"),
        CMSField("blocks", type="repeater"),
        CMSField("seo", type="json"),
    ],
    list_display=["title", "status", "updated_at"],
    list_filter=["status"],
    search_fields=["title", "summary", "body"],
    statuses=["draft", "review", "approved", "scheduled", "published", "archived"],
))
```

Supported field types are `text`, `textarea`, `richtext`, `boolean`, `number`,
`date`, `datetime`, `email`, `url`, `select`, `json`, `repeater`,
`relationship`, `file`, and `image`. Required fields and select choices are
validated by the content type. Slugs are generated from `slug_source` unless
explicitly supplied.

The SPA provides list search/filter/sort/pagination, bulk publish/unpublish,
draft autosave, unsaved-change warnings, status and schedule controls, media
fields, revision history, import/export, comments, taxonomy management, and a
drag-and-drop menu editor.

## Editorial Workflows

Use the status field as the editorial state machine. A typical workflow is:

`draft -> review -> approved -> scheduled -> published -> archived`

The backend validates configured statuses. Records with a future `publish_at`
are treated as scheduled until the next query after their publish time. For
approval rules, register hooks or enforce transitions in a service before
calling `ContentType.update`.

```python
def audit_content(record):
    return record

cms.add_hook("after_update", audit_content)
```

Each create, update, delete, and restore creates a revision. The history API
returns revision metadata, before/after values, changed fields, and restore
operations. Treat revision payloads as audit data and restrict access to
trusted editors.

## Taxonomies, Comments, and Menus

The SPA exposes these resources from the CMS header. They are also JSON APIs:

- Taxonomies: create/delete a taxonomy and add/update/delete terms.
- Comments: list, create, approve, reject, mark spam, and delete comments.
- Menus: read and replace ordered menu items, including nested `children`.

Applications should validate public comment input, add anti-spam controls, and
only expose approved comments on the public site. Menu item URLs should be
validated before rendering into a public navigation.

## Media

The admin media library supports upload, folders, previews/URLs, MIME and size
validation, metadata editing, rename, and delete. Configure a durable upload
directory or replace `FileStorage` with object storage. Never trust a client
filename or content type; retain the allowlist and size limit at the server.

For a custom picker, use the media API and store the returned stable URL or
asset identifier in a CMS `image` or `file` field. Do not store arbitrary
client-provided paths.

## JSON API

With `url_prefix="/admin/cms"`, the SPA API is:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/config` | Content schemas and UI metadata |
| GET | `/api/stats` | Per-type counts |
| GET | `/api/<type>/items` | Search/filter/sort/paginate records |
| POST | `/api/<type>/items` | Create |
| GET | `/api/<type>/items/<id>` | Read |
| PUT | `/api/<type>/items/<id>` | Update |
| DELETE | `/api/<type>/items/<id>` | Delete |
| GET | `/api/<type>/items/<id>/history` | Revisions and comparisons |
| POST | `/api/<type>/items/<id>/restore/<revision>` | Restore revision |
| POST | `/api/<type>/actions/<action>` | Bulk action |
| GET | `/api/export/<type>` | JSON or CSV export |
| POST | `/api/import/<type>` | JSON/CSV import with row errors |
| GET/POST | `/api/taxonomies` | Taxonomy collection |
| GET/PATCH/DELETE | `/api/taxonomies/<name>` | Taxonomy terms |
| GET/POST | `/api/comments` | Comment queue |
| PATCH/DELETE | `/api/comments/<id>` | Moderate/delete comment |
| GET/PUT | `/api/menus/<name>` | Menu management |

All mutating API calls require `X-CSRF-Token` and an authenticated session.
Use the response `errors` array from imports to display row-level validation
feedback. Limit `per_page` to the server-supported maximum.

## Custom UI and Extension Points

The SPA is intentionally replaceable. A custom client should:

1. Fetch `/api/config` and generate fields from the schema.
2. Preserve CSRF and session cookies.
3. Render explicit loading, empty, validation, conflict, and permission states.
4. Use history before destructive restore operations.
5. Subscribe to Redis-backed events when running multiple workers.

Backend extensions include `AdminDashboard.register_widget`, dashboard hooks,
CMS hooks (`before_create`, `after_create`, `before_update`, `after_update`,
`before_delete`, `after_delete`, and restore hooks), custom model actions,
custom templates, `AuthenticationBackend`, storage adapters, and Redis session
and WebSocket broadcasting.

## Production Checklist

- Apply admin/CMS migrations through `flaxon migrate`.
- Use PostgreSQL/MySQL or a durable SQLite deployment; do not use in-memory state.
- Set a strong secret and unique admin passwords through secret management.
- Keep CSRF enabled and serve admin over HTTPS.
- Configure login rate limits, MFA, reset delivery, and email verification.
- Use Redis or a shared database session backend for multiple workers.
- Configure a durable media/object-storage backend and strict MIME limits.
- Add public-site comment moderation and spam protection.
- Restrict rich text allowlists to the tags and attributes your renderer needs.
- Export and retain audit activity and test restore procedures.
- Run API tests plus browser tests for login, create/edit, publishing, media,
  moderation, import/export, and permission boundaries.

The complete runnable reference is
`docs/examples/cms/full_admin_cms/app.py`.

## Production Addendum

The following configuration enables the hardened Admin/CMS path without
changing the existing registration code:

```python
admin = AdminDashboard(
    app,
    storage_path="var/admin.sqlite3",
    redis_url="redis://localhost:6379/0",
    redis_protocol=2,
    redis_max_connections=100,
    session_idle_timeout=1800,
    media_scanner=clamav_scan,
)
cms = CMS(app, auth=admin.auth, redis_url="redis://localhost:6379/0")
```

Use Redis for every web and worker process. It coordinates sessions, Admin
rate limits, CMS publishing locks, and WebSocket events. Use
`flaxon migrate` for the application-owned schema before the first deploy.

The Admin exposes durable resumable media upload endpoints, Admin model
CSV/JSON import/export endpoints, notification preferences, audit-chain
verification, and provider-backed WebAuthn endpoints. See the [Admin API
Reference](../api/admin.md) for paths and CSRF requirements.

Do not claim that WebAuthn or antivirus scanning is enabled merely because the
Flaxon adapters are present. Inject a maintained WebAuthn provider and a real
scanner service, then test their ceremonies and failure behavior in staging.
