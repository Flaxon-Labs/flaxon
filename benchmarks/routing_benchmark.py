#!/usr/bin/env python
"""
Route matching and registration benchmarks.
"""

import json
import time
from typing import Any

from flaxon import Flaxon, Router


def create_router_with_routes(count: int = 1000) -> Router:
    """Create a router with a specified number of routes."""
    router = Router()

    for i in range(count):
        @router.get(f"/users/{i}")
        async def get_user():
            return {"id": i}

        @router.post(f"/users/{i}/posts")
        async def create_post():
            return {"user_id": i}

        @router.get(f"/products/{i}/reviews")
        async def get_reviews():
            return {"product_id": i}

        if i % 10 == 0:
            @router.get(f"/users/{i}/posts/{i}/comments")
            async def get_comments():
                return {"ok": True}

    return router


def benchmark_route_registration() -> dict[str, Any]:
    """Benchmark route registration speed."""
    start = time.perf_counter()

    router = create_router_with_routes(1000)

    elapsed = time.perf_counter() - start

    return {
        "name": "Route Registration",
        "routes": len(router.routes),
        "time_seconds": round(elapsed, 4),
        "routes_per_second": round(len(router.routes) / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_route_matching() -> dict[str, Any]:
    """Benchmark route matching speed."""
    router = create_router_with_routes(1000)

    start = time.perf_counter()

    matches = 0
    for i in range(1000):
        try:
            router.match(f"/users/{i}", "GET")
            matches += 1
        except Exception:
            pass

    elapsed = time.perf_counter() - start

    return {
        "name": "Route Matching",
        "matches": matches,
        "time_seconds": round(elapsed, 4),
        "matches_per_second": round(matches / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_url_generation() -> dict[str, Any]:
    """Benchmark URL generation speed."""
    router = create_router_with_routes(1000)

    start = time.perf_counter()

    urls = []
    for i in range(1000):
        try:
            url = router.url_for("get_user", i=i)
            urls.append(url)
        except Exception:
            pass

    elapsed = time.perf_counter() - start

    return {
        "name": "URL Generation",
        "urls": len(urls),
        "time_seconds": round(elapsed, 4),
        "urls_per_second": round(len(urls) / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_path_compilation() -> dict[str, Any]:
    """Benchmark path compilation speed."""
    paths = [
        "/users/<int:user_id>",
        "/users/<int:user_id>/posts/<int:post_id>",
        "/users/<int:user_id>/posts/<int:post_id>/comments/<int:comment_id>",
        "/api/v1/users/<uuid:user_id>/profile",
        "/products/<slug:product_slug>/reviews",
    ]

    start = time.perf_counter()

    compiled = []
    for path in paths * 100:
        from flaxon.routing.route import compile_path
        compiled.append(compile_path(path))

    elapsed = time.perf_counter() - start

    return {
        "name": "Path Compilation",
        "paths": len(compiled),
        "time_seconds": round(elapsed, 4),
        "paths_per_second": round(len(compiled) / elapsed, 0) if elapsed > 0 else 0,
    }


def run_benchmarks() -> list[dict[str, Any]]:
    """Run all routing benchmarks."""
    results = [
        benchmark_route_registration(),
        benchmark_route_matching(),
        benchmark_url_generation(),
        benchmark_path_compilation(),
    ]
    return results


def main() -> None:
    """Run and display benchmarks."""
    print("=" * 60)
    print("Flaxon Routing Benchmarks")
    print("=" * 60)

    results = run_benchmarks()

    for result in results:
        print(f"\n{result['name']}:")
        print(f"  Time: {result['time_seconds']}s")
        for key, value in result.items():
            if key not in ["name", "time_seconds"]:
                print(f"  {key}: {value}")

    # Save results
    import os
    os.makedirs("benchmarks/results", exist_ok=True)

    with open("benchmarks/results/routing_benchmark.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to benchmarks/results/routing_benchmark.json")


if __name__ == "__main__":
    main()