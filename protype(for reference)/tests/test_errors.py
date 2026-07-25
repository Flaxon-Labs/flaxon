from flaxon import Flaxon
from flaxon.testing import TestClient


def test_not_found():
    app = Flaxon("test")
    response = TestClient(app).get("/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FX-HTTP-404"


def test_debug_error_has_clean_payload():
    app = Flaxon("test", debug=True)

    @app.get("/explode")
    async def explode():
        raise RuntimeError("database exploded")

    response = TestClient(app).get("/explode")
    payload = response.json()
    assert response.status_code == 500
    assert payload["error"]["code"] == "FX-DEV-500"
    assert "traceback" in payload["error"]["debug"]
