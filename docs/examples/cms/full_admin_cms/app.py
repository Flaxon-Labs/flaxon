"""Editable Flaxon admin and CMS showcase.

Run from this directory with:
    python -m flaxon run app:app --reload --port 8000

The SQLite JSON store keeps the example data across reloads and restarts.
Use admin / admin to sign in locally.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from flaxon import Flaxon
from flaxon.admin import AdminConfig, AdminDashboard, admin_model
from flaxon.admin.cms import CMS, CMSField, ContentType


ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

app = Flaxon("flaxon-admin-cms-showcase", debug=True)

admin = AdminDashboard(
    app,
    config=AdminConfig(
        site_title="Flaxon Studio",
        site_header="Flaxon Studio Admin",
        timezone="UTC",
        settings={"environment": "development", "public_site": "http://127.0.0.1:8000"},
    ),
    storage_path=str(DATA / "admin.sqlite3"),
    upload_dir=str(DATA / "uploads"),
    url_prefix="/admin",
    users=[
        {
            "username": "admin",
            "password": "admin",
            "email": "admin@example.test",
            "roles": ["administrator"],
        },
        {
            "username": "editor",
            "password": "editor",
            "email": "editor@example.test",
            "roles": ["editor"],
        },
    ],
)


@admin_model(
    list_display=["id", "name", "price", "active"],
    search_fields=["name", "sku"],
    list_filter=["active"],
    fields=["name", "sku", "price", "active"],
)
class Product:
    """Small model-admin example with list, search, filters and bulk actions."""

    _data: dict[str, dict] = {}
    _id_counter = 1

    @classmethod
    async def get_instances(cls) -> list[dict]:
        return list(cls._data.values())

    @classmethod
    async def get_instance(cls, id: str) -> dict | None:
        return cls._data.get(id)

    @classmethod
    async def create_instance(cls, data: dict) -> dict:
        product_id = str(cls._id_counter)
        cls._id_counter += 1
        record = {"id": product_id, "active": True, **data}
        cls._data[product_id] = record
        return record

    @classmethod
    async def update_instance(cls, id: str, data: dict) -> dict | None:
        if id not in cls._data:
            return None
        cls._data[id].update(data)
        return cls._data[id]

    @classmethod
    async def delete_instance(cls, id: str) -> bool:
        return cls._data.pop(id, None) is not None


async def seed_catalog(ids):
    for product in (
        {"name": "Canvas Backpack", "sku": "BAG-001", "price": 79, "active": True},
        {"name": "Studio Mug", "sku": "MUG-002", "price": 18, "active": True},
    ):
        await Product.create_instance(product)
    return ids


admin.registry.get("product").add_action("seed_catalog", seed_catalog)


admin.register_widget(lambda: {"title": "Editable showcase", "value": "All admin and CMS systems enabled"})


cms = CMS(app, url_prefix="/admin/cms", title="Flaxon Studio CMS", auth=admin.auth)

cms.register(
    ContentType(
        name="post",
        label="Post",
        label_plural="Posts",
        fields=[
            CMSField("title", "Title", required=True),
            CMSField("excerpt", "Excerpt", type="textarea"),
            CMSField("content", "Content", type="richtext"),
            CMSField("published_on", "Published on", type="datetime"),
            CMSField("featured_image", "Featured image", type="image"),
            CMSField("author_ids", "Related authors", type="relationship"),
            CMSField("blocks", "Content blocks", type="repeater"),
            CMSField("seo", "SEO metadata", type="json"),
        ],
        list_display=["title", "status", "updated_at"],
        list_filter=["status"],
        search_fields=["title", "excerpt", "content"],
    )
)

cms.register(
    ContentType(
        name="page",
        label="Page",
        label_plural="Pages",
        fields=[
            CMSField("title", "Title", required=True),
            CMSField("body", "Body", type="richtext"),
            CMSField("layout", "Layout", type="select", choices=["default", "landing", "contact"], default="default"),
            CMSField("is_indexable", "Search indexed", type="boolean", default=True),
        ],
        list_display=["title", "status", "updated_at"],
        list_filter=["status", "layout"],
        search_fields=["title", "body"],
    )
)


def _seed_content() -> None:
    post = cms.content_types["post"]
    if not post.items:
        post.create({
            "title": "Welcome to Flaxon Studio",
            "excerpt": "An editable admin and CMS reference application.",
            "content": "<p>Edit this post, schedule it, compare revisions, or restore an earlier version.</p>",
            "status": "published",
            "published_on": datetime.now(timezone.utc).isoformat(),
            "blocks": [{"type": "text", "value": "Reusable content block"}],
            "seo": {"description": "Flaxon CMS showcase"},
        })
        cms._save(post)
    cms.taxonomies.setdefault("categories", {"admin": ["CMS", "Admin"]})
    cms.taxonomies.setdefault("tags", {"workflow": ["draft", "review", "published"]})
    if not cms.comments:
        cms.comments.append({"id": "demo-comment", "status": "pending", "author": "Visitor", "body": "Please review this comment."})
    cms.menus.setdefault("main", [
        {"label": "Home", "url": "/"},
        {"label": "Posts", "url": "/admin/cms/#/post"},
        {"label": "Studio", "url": "/admin/cms/", "children": [{"label": "Pages", "url": "/admin/cms/#/page"}]},
    ])
    cms._save_resources()


_seed_content()


def announce_create(record):
    return record


cms.add_hook("after_create", announce_create)


@app.get("/")
async def home():
    return {
        "name": "Flaxon Studio showcase",
        "editable": True,
        "login": "/admin/login",
        "admin": "/admin/",
        "cms": "/admin/cms/",
        "features": {
            "admin": ["models", "users", "roles", "media", "settings", "activity", "operations", "global search"],
            "cms": ["posts", "pages", "taxonomy", "comments", "revisions", "scheduling", "import/export", "menus"],
        },
    }
