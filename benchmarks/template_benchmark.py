#!/usr/bin/env python
"""
Template rendering benchmarks.
"""

import json
import tempfile
import time
from pathlib import Path
from typing import Any

from flaxon import Flaxon
from flaxon.jinax import Jinax
from flaxon.testing import TestClient


def create_templates(temp_dir: Path) -> None:
    """Create test templates."""
    (temp_dir / "simple.html").write_text("<h1>Hello, {{ name }}!</h1>")

    (temp_dir / "loop.html").write_text("""
<ul>
{% for item in items %}
    <li>{{ item.name }}: {{ item.value }}</li>
{% endfor %}
</ul>
""")

    (temp_dir / "complex.html").write_text("""
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

    (temp_dir / "base.html").write_text("""
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

    (temp_dir / "filters.html").write_text("""
<h1>{{ name|upper }}</h1>
<p>{{ price|currency("USD") }}</p>
<p>{{ date|date("%Y-%m-%d") }}</p>
""")


def benchmark_simple_template() -> dict[str, Any]:
    """Benchmark simple template rendering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        create_templates(temp_dir)

        app = Flaxon("test-simple")
        app.use_templates(Jinax(temp_dir, auto_reload=False))

        @app.get("/")
        async def home(request):
            return await request.render("simple.html", {"name": "World"})

        client = TestClient(app)

        # Warm up
        client.get("/")

        start = time.perf_counter()
        for _ in range(100):
            client.get("/")
        elapsed = time.perf_counter() - start

    return {
        "name": "Simple Template",
        "iterations": 100,
        "time_seconds": round(elapsed, 4),
        "renders_per_second": round(100 / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_loop_template() -> dict[str, Any]:
    """Benchmark template with loops."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        create_templates(temp_dir)

        app = Flaxon("test-loop")
        app.use_templates(Jinax(temp_dir, auto_reload=False))

        @app.get("/")
        async def home(request):
            return await request.render("loop.html", {
                "items": [{"name": f"Item {i}", "value": i} for i in range(100)],
            })

        client = TestClient(app)

        client.get("/")

        start = time.perf_counter()
        for _ in range(50):
            client.get("/")
        elapsed = time.perf_counter() - start

    return {
        "name": "Loop Template (100 items)",
        "iterations": 50,
        "time_seconds": round(elapsed, 4),
        "renders_per_second": round(50 / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_complex_template() -> dict[str, Any]:
    """Benchmark complex template with inheritance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        create_templates(temp_dir)

        app = Flaxon("test-complex")
        app.use_templates(Jinax(temp_dir, auto_reload=False))

        @app.get("/")
        async def home(request):
            return await request.render("complex.html", {
                "title": "Complex Template",
                "items": [{"name": f"Item {i}", "value": i} for i in range(100)],
                "users": [
                    {"name": f"User {i}", "email": f"user{i}@example.com"}
                    for i in range(50)
                ],
            })

        client = TestClient(app)

        client.get("/")

        start = time.perf_counter()
        for _ in range(30):
            client.get("/")
        elapsed = time.perf_counter() - start

    return {
        "name": "Complex Template (100 items, 50 users, inheritance)",
        "iterations": 30,
        "time_seconds": round(elapsed, 4),
        "renders_per_second": round(30 / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_filters_template() -> dict[str, Any]:
    """Benchmark template with filters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        create_templates(temp_dir)

        app = Flaxon("test-filters")
        app.use_templates(Jinax(temp_dir, auto_reload=False))

        @app.get("/")
        async def home(request):
            return await request.render("filters.html", {
                "name": "hello world",
                "price": 99.99,
                "date": "2024-01-01T00:00:00",
            })

        client = TestClient(app)

        client.get("/")

        start = time.perf_counter()
        for _ in range(100):
            client.get("/")
        elapsed = time.perf_counter() - start

    return {
        "name": "Template with Filters",
        "iterations": 100,
        "time_seconds": round(elapsed, 4),
        "renders_per_second": round(100 / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_template_caching() -> dict[str, Any]:
    """Benchmark template caching performance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        create_templates(temp_dir)

        app = Flaxon("test-cache")
        app.use_templates(Jinax(temp_dir, auto_reload=False))

        @app.get("/")
        async def home(request):
            return await request.render("simple.html", {"name": "World"})

        client = TestClient(app)

        # Warm up cache
        client.get("/")

        start = time.perf_counter()
        for _ in range(100):
            client.get("/")
        elapsed = time.perf_counter() - start

    return {
        "name": "Template Caching",
        "iterations": 100,
        "time_seconds": round(elapsed, 4),
        "renders_per_second": round(100 / elapsed, 0) if elapsed > 0 else 0,
    }


def run_benchmarks() -> list[dict[str, Any]]:
    """Run all template benchmarks."""
    results = [
        benchmark_simple_template(),
        benchmark_loop_template(),
        benchmark_complex_template(),
        benchmark_filters_template(),
        benchmark_template_caching(),
    ]
    return results


def main() -> None:
    """Run and display benchmarks."""
    print("=" * 60)
    print("Flaxon Template Benchmarks")
    print("=" * 60)

    results = run_benchmarks()

    for result in results:
        print(f"\n{result['name']}:")
        print(f"  Time: {result['time_seconds']}s")
        for key, value in result.items():
            if key not in ["name", "time_seconds"]:
                print(f"  {key}: {value}")

    import os
    os.makedirs("benchmarks/results", exist_ok=True)

    with open("benchmarks/results/template_benchmark.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to benchmarks/results/template_benchmark.json")


if __name__ == "__main__":
    main()