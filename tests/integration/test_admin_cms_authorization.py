from __future__ import annotations

import asyncio

import pytest

from flaxon import Flaxon
from flaxon.admin import AdminDashboard
from flaxon.admin.cms import CMS, CMSField, ContentType
from flaxon.testing import TestClient


def _read_only_cms():
    app = Flaxon("admin-cms-authorization")
    dashboard = AdminDashboard(
        app,
        users=[
            {"username": "editor", "password": "Editor123!", "roles": ["readonly"], "permissions": ["admin:read"]},
        ],
    )
    cms = CMS(app, auth=dashboard.auth)
    cms.register(ContentType("article", fields=[CMSField("title", required=True)]))
    token = asyncio.run(dashboard.auth.login("editor", "Editor123!"))
    headers = {
        "cookie": f"session_id={token}",
        "x-csrf-token": dashboard.csrf_token(),
    }
    return cms, TestClient(app), headers


@pytest.mark.integration
def test_cms_read_only_user_cannot_mutate_content_or_resources():
    cms, client, headers = _read_only_cms()
    cms.content_types["article"].create({"title": "Visible article"})

    assert client.get("/admin/cms/api/article/items", headers=headers).status_code == 200
    assert client.post(
        "/admin/cms/api/article/items",
        json_data={"title": "Blocked article"},
        headers=headers,
    ).status_code == 403
    assert client.post(
        "/admin/cms/api/taxonomies",
        json_data={"name": "topics"},
        headers=headers,
    ).status_code == 403
