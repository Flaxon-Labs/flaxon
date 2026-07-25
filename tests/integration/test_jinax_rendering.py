import tempfile
from pathlib import Path

import pytest

from flaxon import Flaxon
from flaxon.jinax import Jinax
from flaxon.testing import TestClient


@pytest.fixture
def template_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)

        (path / "base.html").write_text("""
<!doctype html>
<html>
<head><title>{% block title %}Flaxon{% endblock %}</title></head>
<body>
    <header>{% block header %}Default Header{% endblock %}</header>
    <main>{% block content %}{% endblock %}</main>
    <footer>Footer</footer>
</body>
</html>
""")

        (path / "home.html").write_text("""
{% extends "base.html" %}

{% block title %}Home{% endblock %}

{% block header %}Welcome to Flaxon{% endblock %}

{% block content %}
    <h1>Hello, {{ name }}!</h1>
    <ul>
    {% for item in items %}
        <li>{{ item }}</li>
    {% endfor %}
    </ul>
    <p>Current time: {{ now() }}</p>
{% endblock %}
""")

        (path / "variable.html").write_text("""
<h1>{{ title }}</h1>
<p>{{ description }}</p>
<p>{{ user.name }} ({{ user.email }})</p>
""")

        yield path


@pytest.fixture
def app_with_jinax(template_dir):
    app = Flaxon("test-jinax", debug=True)
    app.use_templates(Jinax(template_dir, auto_reload=True, strict_undefined=True))

    @app.get("/")
    async def home(request):
        return await request.render("home.html", {
            "name": "Flaxon",
            "items": ["Routing", "Validation", "Templates", "WebSockets"],
        })

    @app.get("/variable")
    async def variable(request):
        return await request.render("variable.html", {
            "title": "Variable Test",
            "description": "Testing variable rendering",
            "user": {"name": "Alice", "email": "alice@example.com"},
        })

    return app


def test_jinax_render(app_with_jinax):
    client = TestClient(app_with_jinax)
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Welcome to Flaxon" in response.text
    assert "Hello, Flaxon!" in response.text
    assert "Routing" in response.text
    assert "Validation" in response.text
    assert "Templates" in response.text
    assert "WebSockets" in response.text
    assert "Footer" in response.text


def test_jinax_variable_render(app_with_jinax):
    client = TestClient(app_with_jinax)
    response = client.get("/variable")

    assert response.status_code == 200
    assert "Variable Test" in response.text
    assert "Testing variable rendering" in response.text
    assert "Alice" in response.text
    assert "alice@example.com" in response.text


def test_jinax_template_inheritance(app_with_jinax):
    client = TestClient(app_with_jinax)
    response = client.get("/")

    assert "Default Header" not in response.text
    assert "Welcome to Flaxon" in response.text


def test_jinax_custom_filter(template_dir):
    app = Flaxon("test-filter", debug=True)

    def currency_filter(value, symbol="$"):
        return f"{symbol}{value:.2f}"

    jinax = Jinax(template_dir, auto_reload=True)
    jinax.add_filter("currency", currency_filter)
    app.use_templates(jinax)

    @app.get("/filter")
    async def filter_test(request):
        return await request.render("variable.html", {
            "title": "Filter Test",
            "description": "Testing currency filter",
            "user": {"name": "Product", "email": "$49.99"},
        })

    client = TestClient(app)
    response = client.get("/filter")
    assert response.status_code == 200
