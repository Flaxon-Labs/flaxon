import time
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

        (path / "simple.html").write_text("<h1>Hello, {{ name }}!</h1>")

        (path / "complex.html").write_text("""
{% extends "base.html" %}

{% block content %}
    <h1>{{ title }}</h1>
    <ul>
    {% for item in items %}
        <li>{{ item.name }}: {{ item.value }}</li>
    {% endfor %}
    </ul>
    <div>
    {% for user in users %}
        <div class="user">
            <h3>{{ user.name }}</h3>
            <p>{{ user.email }}</p>
        </div>
    {% endfor %}
    </div>
{% endblock %}
""")

        (path / "base.html").write_text("""
<!doctype html>
<html>
<head><title>{% block title %}Test{% endblock %}</title></head>
<body>
    <header>Header</header>
    <main>{% block content %}{% endblock %}</main>
    <footer>Footer</footer>
</body>
</html>
""")

        yield path


@pytest.fixture
def app_with_jinax(template_dir):
    app = Flaxon("test-jinax-perf")
    app.use_templates(Jinax(template_dir, auto_reload=False))

    @app.get("/simple")
    async def simple(request):
        return await request.render("simple.html", {"name": "World"})

    @app.get("/complex")
    async def complex(request):
        return await request.render("complex.html", {
            "title": "Complex Template",
            "items": [{"name": f"Item {i}", "value": i} for i in range(100)],
            "users": [
                {"name": f"User {i}", "email": f"user{i}@example.com"}
                for i in range(50)
            ],
        })

    return app


def test_simple_template_render_speed(app_with_jinax):
    client = TestClient(app_with_jinax)

    start = time.perf_counter()

    for _ in range(100):
        client.get("/simple")

    elapsed = time.perf_counter() - start
    assert elapsed < 2.0


def test_complex_template_render_speed(app_with_jinax):
    client = TestClient(app_with_jinax)

    start = time.perf_counter()

    for _ in range(50):
        client.get("/complex")

    elapsed = time.perf_counter() - start
    assert elapsed < 2.0


def test_template_caching_speed(template_dir):
    app = Flaxon("test-cache")
    app.use_templates(Jinax(template_dir, auto_reload=False))

    @app.get("/")
    async def home(request):
        return await request.render("simple.html", {"name": "World"})

    client = TestClient(app)

    client.get("/")

    start = time.perf_counter()

    for _ in range(100):
        client.get("/")

    elapsed = time.perf_counter() - start
    assert elapsed < 2.0


def test_async_template_render_speed(template_dir):
    app = Flaxon("test-async")
    app.use_templates(Jinax(template_dir, auto_reload=False))

    @app.get("/")
    async def home(request):
        return await request.render("simple.html", {"name": "World"})

    client = TestClient(app)

    start = time.perf_counter()

    for _ in range(100):
        client.get("/")

    elapsed = time.perf_counter() - start
    assert elapsed < 2.0


def test_template_with_filters_speed(template_dir):
    app = Flaxon("test-filters")

    jinax = Jinax(template_dir, auto_reload=False)

    def uppercase(value):
        return value.upper()

    jinax.add_filter("uppercase", uppercase)
    app.use_templates(jinax)

    @app.get("/")
    async def home(request):
        return await request.render("simple.html", {"name": "World"})

    client = TestClient(app)

    start = time.perf_counter()

    for _ in range(100):
        client.get("/")

    elapsed = time.perf_counter() - start
    assert elapsed < 2.0


def test_template_inheritance_speed(template_dir):
    app = Flaxon("test-inheritance")
    app.use_templates(Jinax(template_dir, auto_reload=False))

    @app.get("/")
    async def home(request):
        return await request.render("complex.html", {
            "title": "Test",
            "items": [{"name": f"Item {i}", "value": i} for i in range(50)],
            "users": [
                {"name": f"User {i}", "email": f"user{i}@example.com"}
                for i in range(25)
            ],
        })

    client = TestClient(app)

    start = time.perf_counter()

    for _ in range(50):
        client.get("/")

    elapsed = time.perf_counter() - start
    assert elapsed < 2.0