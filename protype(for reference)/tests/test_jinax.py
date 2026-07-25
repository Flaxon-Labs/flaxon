from pathlib import Path

from flaxon import Flaxon
from flaxon.jinax import Jinax
from flaxon.testing import TestClient


def test_jinax_render(tmp_path: Path):
    (tmp_path / "hello.html").write_text("<h1>Hello {{ name }}</h1>", encoding="utf-8")
    app = Flaxon("test")
    app.use_templates(Jinax(tmp_path))

    @app.get("/")
    async def home(request):
        return await request.render("hello.html", {"name": "Flaxon"})

    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.text == "<h1>Hello Flaxon</h1>"
