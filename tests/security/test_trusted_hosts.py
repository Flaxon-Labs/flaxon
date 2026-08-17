from flaxon import Flaxon
from flaxon.middleware import TrustedHostsMiddleware
from flaxon.testing import TestClient


def test_trusted_host_allows_configured_hostname_with_port():
    app = Flaxon("trusted-host")
    app.add_middleware(TrustedHostsMiddleware, allowed_hosts=["example.com"])

    @app.get("/")
    async def home():
        return "ok"

    response = TestClient(app).get("/", headers={"host": "example.com:8443"})
    assert response.status_code == 200
