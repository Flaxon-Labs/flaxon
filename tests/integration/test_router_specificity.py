import logging

from flaxon import Flaxon, Router
from flaxon.admin import AdminDashboard
from flaxon.admin.cms import CMS


def test_admin_and_cms_match_in_either_registration_order():
    for cms_first in (False, True):
        app = Flaxon(f"route-order-{cms_first}")
        if cms_first:
            CMS(app)
            AdminDashboard(app, users=[{"username": "admin", "password": "Admin123!"}])
        else:
            AdminDashboard(app, users=[{"username": "admin", "password": "Admin123!"}])
            CMS(app)

        match = app.router.match("/admin/cms/", "GET")
        assert match.route.endpoint.__name__ == "spa"
        api_match = app.router.match("/admin/cms/api/config", "GET")
        assert api_match.route.endpoint.__name__ == "api_config"


def test_include_router_applies_mount_prefix_without_mutating_source():
    source = Router(prefix="/api")

    @source.get("/items/<int:item_id>")
    async def item(request, item_id):
        return {"id": item_id}

    destination = Router()
    destination.include_router(source, prefix="/v1")

    assert destination.match("/v1/items/42", "GET").params == {"item_id": 42}
    assert source.match("/api/items/42", "GET").params == {"item_id": 42}


def test_collision_warning_is_emitted_but_non_overlapping_routes_are_silent(caplog):
    router = Router()
    caplog.set_level(logging.WARNING, logger="flaxon.routing.router")

    @router.get("/admin/<model_name>")
    async def model(request, model_name):
        return model_name

    @router.get("/admin/cms")
    async def cms(request):
        return "cms"

    assert any("route collision" in record.message for record in caplog.records)
    caplog.clear()

    @router.get("/settings")
    async def settings(request):
        return "settings"

    assert not caplog.records
    assert router.match("/admin/cms", "GET").route.endpoint.__name__ == "cms"
