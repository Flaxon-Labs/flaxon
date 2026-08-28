from __future__ import annotations

import asyncio

from flaxon import Flaxon
from flaxon.admin import AdminDashboard, admin_model
from flaxon.admin.cms import CMS, CMSField, ContentType
from flaxon.testing import TestClient


def _cms_app():
    app = Flaxon("admin-cms-extreme", debug=True)
    admin = AdminDashboard(
        app,
        users=[{"username": "admin", "password": "Admin123!"}],
    )
    cms = CMS(app, auth=admin.auth)
    cms.register(
        ContentType(
            "article",
            fields=[
                CMSField("title", required=True),
                CMSField("body", type="richtext"),
                CMSField("status", type="select", choices=["draft", "published"]),
            ],
            search_fields=["title", "body"],
        )
    )
    token = asyncio.run(admin.auth.login("admin", "Admin123!"))
    headers = {"cookie": f"session_id={token}", "x-csrf-token": admin.csrf_token()}
    return app, admin, cms, TestClient(app), headers


def test_cms_survives_high_volume_queries_and_resource_mutations():
    _, _, cms, client, headers = _cms_app()

    # Seed a large dataset directly so the test can exercise query boundaries
    # without tripping the production mutation rate limit.
    article = cms.content_types["article"]
    for index in range(249):
        article.create(
            {
                "title": f"Article {index:03d}",
                "body": f"Body {index} searchable" if index % 10 == 1 else "Body",
                "status": "published" if index % 2 else "draft",
            }
        )

    created = client.post(
        "/admin/cms/api/article/items",
        json_data={"title": "API mutation", "body": "created through HTTP", "status": "draft"},
        headers=headers,
    )
    assert created.status_code == 201

    page = client.get(
        "/admin/cms/api/article/items?page=13&per_page=20&order_by=-title",
        headers=headers,
    )
    assert page.status_code == 200
    payload = page.json()
    assert payload["total"] == 250
    assert payload["page"] == 13
    assert len(payload["items"]) == 10
    assert payload["items"][0]["title"] == "Article 008"

    filtered = client.get(
        "/admin/cms/api/article/items?q=searchable&filter_status=published&per_page=200",
        headers=headers,
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 25

    assert client.get("/admin/cms/api/article/items?per_page=0", headers=headers).status_code == 200
    assert client.get("/admin/cms/api/article/items?per_page=9999", headers=headers).json()["per_page"] == 200

    invalid = client.post("/admin/cms/api/article/items", json_data={"body": "missing title"}, headers=headers)
    assert invalid.status_code in {400, 422}

    no_csrf = client.post(
        "/admin/cms/api/article/items",
        json_data={"title": "blocked"},
        headers={"cookie": headers["cookie"]},
    )
    assert no_csrf.status_code in {400, 403, 419}

    taxonomy = client.post(
        "/admin/cms/api/taxonomies",
        json_data={"name": "topics", "terms": {"python": []}},
        headers=headers,
    )
    assert taxonomy.status_code == 200
    comment = client.post(
        "/admin/cms/api/comments",
        json_data={"content_type": "article", "record_id": "1", "body": "moderate me"},
        headers=headers,
    )
    assert comment.status_code == 201
    comment_id = comment.json()["id"]
    assert client.patch(
        f"/admin/cms/api/comments/{comment_id}",
        json_data={"status": "approved"},
        headers=headers,
    ).json()["status"] == "approved"
    assert client.put(
        "/admin/cms/api/menus/main",
        json_data=[{"label": "Home", "url": "/", "children": [{"label": "Articles", "url": "/articles"}]}],
        headers=headers,
    ).status_code == 200


def test_admin_model_lists_and_protected_mutations_under_load():
    app = Flaxon("admin-extreme", debug=True)
    admin = AdminDashboard(app, users=[{"username": "admin", "password": "Admin123!"}])

    @admin_model(search_fields=["name"], list_filter=["active"], list_display=["id", "name", "active"])
    class Product:
        _items = {}
        _next_id = 1

        @classmethod
        async def get_instances(cls):
            return list(cls._items.values())

        @classmethod
        async def get_instance(cls, object_id):
            return cls._items.get(str(object_id))

        @classmethod
        async def create_instance(cls, data):
            object_id = str(cls._next_id)
            cls._next_id += 1
            cls._items[object_id] = {"id": object_id, **data}
            return cls._items[object_id]

        @classmethod
        async def update_instance(cls, object_id, data):
            if str(object_id) not in cls._items:
                return None
            cls._items[str(object_id)].update(data)
            return cls._items[str(object_id)]

        @classmethod
        async def delete_instance(cls, object_id):
            return cls._items.pop(str(object_id), None) is not None

    token = asyncio.run(admin.auth.login("admin", "Admin123!"))
    headers = {"cookie": f"session_id={token}", "x-csrf-token": admin.csrf_token()}
    client = TestClient(app)
    for index in range(150):
        asyncio.run(Product.create_instance({"name": f"Product {index:03d}", "active": index % 2 == 0}))

    listing = client.get("/admin/product?q=Product 0&page=1&per_page=20", headers=headers)
    assert listing.status_code == 200
    assert "Product 149" not in listing.text
    assert "Product 000" in listing.text

    assert client.get("/admin/product", headers={}).status_code in {302, 401, 403}
    protected_settings = client.post(
        "/admin/settings",
        content="environment=test",
        headers={
            "cookie": headers["cookie"],
            "content-type": "application/x-www-form-urlencoded",
        },
    )
    assert protected_settings.status_code in {403, 419}


def test_admin_rate_limit_rejects_mutation_burst():
    _, _, _, client, headers = _cms_app()

    responses = [
        client.post(
            "/admin/cms/api/taxonomies",
            json_data={"name": f"burst-{index}", "terms": {}},
            headers=headers,
        )
        for index in range(121)
    ]

    assert any(response.status_code == 429 for response in responses)
