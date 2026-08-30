from __future__ import annotations

import asyncio

import pytest

from flaxon import Flaxon
from flaxon.admin import AdminDashboard
from flaxon.admin.cms import CMS, CMSField, ContentType
from flaxon.admin.services import RedisAdminSessionBackend
from flaxon.testing import TestClient


@pytest.mark.integration
def test_redis_session_backend_exposes_explicit_pool_configuration():
    backend = RedisAdminSessionBackend(protocol=2, max_connections=17, socket_timeout=3.5)
    assert backend.protocol == 2
    assert backend.max_connections == 17
    assert backend.socket_timeout == 3.5


@pytest.mark.integration
def test_cms_config_exposes_server_authorized_capabilities():
    app = Flaxon("cms-capabilities")
    dashboard = AdminDashboard(
        app,
        users=[{"username": "reader", "password": "Reader123!", "roles": [], "permissions": ["admin:read"]}],
    )
    cms = CMS(app, auth=dashboard.auth)
    cms.register(ContentType("article", fields=[CMSField("title")]))
    token = asyncio.run(dashboard.auth.login("reader", "Reader123!"))
    response = TestClient(app).get(
        "/admin/cms/api/config",
        headers={"cookie": f"session_id={token}"},
    )
    assert response.status_code == 200
    capabilities = response.json()["types"][0]["capabilities"]
    assert capabilities == {"read": True, "create": False, "update": False, "delete": False}
