#!/usr/bin/env python
"""
Middleware performance benchmarks.
"""

import json
import time
from typing import Any

from flaxon import Flaxon
from flaxon.middleware import CORSMiddleware, RequestIDMiddleware, SecurityHeadersMiddleware
from flaxon.security import RateLimitMiddleware
from flaxon.testing import TestClient


def create_app_with_middleware(count: int = 5) -> Flaxon:
    """Create an app with a specified number of middleware."""
    app = Flaxon("test-mw")

    for i in range(count):
        class CustomMiddleware:
            def __init__(self, app):
                self.app = app

            async def __call__(self, scope, receive, send):
                await self.app(scope, receive, send)

        app.add_middleware(CustomMiddleware)

    @app.get("/")
    async def home():
        return {"ok": True}

    return app


def benchmark_no_middleware() -> dict[str, Any]:
    """Benchmark with no middleware."""
    app = Flaxon("test-no-mw")

    @app.get("/")
    async def home():
        return {"ok": True}

    client = TestClient(app)

    start = time.perf_counter()
    for _ in range(1000):
        client.get("/")
    elapsed = time.perf_counter() - start

    return {
        "name": "No Middleware",
        "requests": 1000,
        "time_seconds": round(elapsed, 4),
        "rps": round(1000 / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_request_id_middleware() -> dict[str, Any]:
    """Benchmark with RequestIDMiddleware."""
    app = Flaxon("test-rid")
    app.add_middleware(RequestIDMiddleware)

    @app.get("/")
    async def home():
        return {"ok": True}

    client = TestClient(app)

    start = time.perf_counter()
    for _ in range(1000):
        client.get("/")
    elapsed = time.perf_counter() - start

    return {
        "name": "RequestIDMiddleware",
        "requests": 1000,
        "time_seconds": round(elapsed, 4),
        "rps": round(1000 / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_security_headers_middleware() -> dict[str, Any]:
    """Benchmark with SecurityHeadersMiddleware."""
    app = Flaxon("test-sh")
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/")
    async def home():
        return {"ok": True}

    client = TestClient(app)

    start = time.perf_counter()
    for _ in range(1000):
        client.get("/")
    elapsed = time.perf_counter() - start

    return {
        "name": "SecurityHeadersMiddleware",
        "requests": 1000,
        "time_seconds": round(elapsed, 4),
        "rps": round(1000 / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_cors_middleware() -> dict[str, Any]:
    """Benchmark with CORSMiddleware."""
    app = Flaxon("test-cors")
    app.add_middleware(CORSMiddleware, allowed_origins=["*"])

    @app.get("/")
    async def home():
        return {"ok": True}

    client = TestClient(app)

    start = time.perf_counter()
    for _ in range(1000):
        client.get("/")
    elapsed = time.perf_counter() - start

    return {
        "name": "CORSMiddleware",
        "requests": 1000,
        "time_seconds": round(elapsed, 4),
        "rps": round(1000 / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_multiple_middleware() -> dict[str, Any]:
    """Benchmark with multiple middleware."""
    app = Flaxon("test-multi")

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CORSMiddleware, allowed_origins=["*"])
    app.add_middleware(RateLimitMiddleware, requests=10000, window_seconds=60)

    @app.get("/")
    async def home():
        return {"ok": True}

    client = TestClient(app)

    start = time.perf_counter()
    for _ in range(1000):
        client.get("/")
    elapsed = time.perf_counter() - start

    return {
        "name": "Multiple Middleware (4)",
        "requests": 1000,
        "time_seconds": round(elapsed, 4),
        "rps": round(1000 / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_middleware_stack_with_count() -> dict[str, Any]:
    """Benchmark with different middleware stack sizes."""
    results = {}

    for count in [0, 1, 5, 10, 20]:
        app = create_app_with_middleware(count)
        client = TestClient(app)

        start = time.perf_counter()
        for _ in range(500):
            client.get("/")
        elapsed = time.perf_counter() - start

        results[f"{count}_middleware"] = {
            "count": count,
            "requests": 500,
            "time_seconds": round(elapsed, 4),
            "rps": round(500 / elapsed, 0) if elapsed > 0 else 0,
        }

    return {
        "name": "Middleware Stack Size",
        "results": results,
    }


def run_benchmarks() -> list[dict[str, Any]]:
    """Run all middleware benchmarks."""
    results = [
        benchmark_no_middleware(),
        benchmark_request_id_middleware(),
        benchmark_security_headers_middleware(),
        benchmark_cors_middleware(),
        benchmark_multiple_middleware(),
        benchmark_middleware_stack_with_count(),
    ]
    return results


def main() -> None:
    """Run and display benchmarks."""
    print("=" * 60)
    print("Flaxon Middleware Benchmarks")
    print("=" * 60)

    results = run_benchmarks()

    for result in results:
        if result.get("name") == "Middleware Stack Size":
            print(f"\n{result['name']}:")
            for key, value in result.get("results", {}).items():
                print(f"  {key}: {value['rps']} RPS")
        else:
            print(f"\n{result['name']}:")
            print(f"  Time: {result['time_seconds']}s")
            print(f"  RPS: {result.get('rps', 0)}")

    import os
    os.makedirs("benchmarks/results", exist_ok=True)

    with open("benchmarks/results/middleware_benchmark.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to benchmarks/results/middleware_benchmark.json")


if __name__ == "__main__":
    main()