#!/usr/bin/env python
"""
JSON serialization and deserialization benchmarks.
"""

import json
import time
from typing import Any

from flaxon import Flaxon
from flaxon.http import JSONResponse, Response
from flaxon.testing import TestClient


def create_test_data(size: int = 100) -> dict[str, Any]:
    """Create test data of a given size."""
    return {
        "users": [
            {
                "id": i,
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "profile": {
                    "age": 20 + (i % 50),
                    "city": f"City {i % 10}",
                    "bio": "Lorem ipsum dolor sit amet" * 5,
                },
                "posts": [
                    {"id": j, "title": f"Post {j}", "content": "Content" * 10}
                    for j in range(5)
                ],
            }
            for i in range(size)
        ],
        "metadata": {
            "total": size,
            "page": 1,
            "per_page": 20,
        },
    }


def benchmark_json_serialization() -> dict[str, Any]:
    """Benchmark JSON serialization."""
    data = create_test_data(100)

    start = time.perf_counter()

    serialized = []
    for _ in range(100):
        response = JSONResponse(data)
        serialized.append(response)

    elapsed = time.perf_counter() - start

    return {
        "name": "JSON Serialization",
        "iterations": 100,
        "time_seconds": round(elapsed, 4),
        "ops_per_second": round(100 / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_json_deserialization() -> dict[str, Any]:
    """Benchmark JSON deserialization."""
    data = create_test_data(100)
    json_str = json.dumps(data, default=str)

    start = time.perf_counter()

    for _ in range(100):
        json.loads(json_str)

    elapsed = time.perf_counter() - start

    return {
        "name": "JSON Deserialization",
        "iterations": 100,
        "time_seconds": round(elapsed, 4),
        "ops_per_second": round(100 / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_response_conversion() -> dict[str, Any]:
    """Benchmark response conversion from Python objects."""
    data = create_test_data(100)

    start = time.perf_counter()

    for _ in range(100):
        response = Response.from_value(data)

    elapsed = time.perf_counter() - start

    return {
        "name": "Response Conversion",
        "iterations": 100,
        "time_seconds": round(elapsed, 4),
        "ops_per_second": round(100 / elapsed, 0) if elapsed > 0 else 0,
    }


def benchmark_json_response_overhead() -> dict[str, Any]:
    """Benchmark JSON response overhead in a full request cycle."""
    app = Flaxon("test-json-overhead")

    @app.get("/small")
    async def small():
        return {"message": "Hello", "status": "ok"}

    @app.get("/medium")
    async def medium():
        return {
            "users": [
                {"id": i, "name": f"User {i}", "email": f"user{i}@example.com"}
                for i in range(50)
            ]
        }

    @app.get("/large")
    async def large():
        return {
            "users": [
                {
                    "id": i,
                    "name": f"User {i}",
                    "email": f"user{i}@example.com",
                    "profile": {"age": 20 + (i % 50), "city": f"City {i % 10}"},
                }
                for i in range(200)
            ]
        }

    client = TestClient(app)

    start = time.perf_counter()
    for _ in range(100):
        client.get("/small")
    small_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(100):
        client.get("/medium")
    medium_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(50):
        client.get("/large")
    large_elapsed = time.perf_counter() - start

    return {
        "name": "JSON Response Overhead",
        "small_requests": 100,
        "small_time_seconds": round(small_elapsed, 4),
        "medium_requests": 100,
        "medium_time_seconds": round(medium_elapsed, 4),
        "large_requests": 50,
        "large_time_seconds": round(large_elapsed, 4),
    }


def run_benchmarks() -> list[dict[str, Any]]:
    """Run all JSON benchmarks."""
    results = [
        benchmark_json_serialization(),
        benchmark_json_deserialization(),
        benchmark_response_conversion(),
        benchmark_json_response_overhead(),
    ]
    return results


def main() -> None:
    """Run and display benchmarks."""
    print("=" * 60)
    print("Flaxon JSON Benchmarks")
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

    with open("benchmarks/results/json_benchmark.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to benchmarks/results/json_benchmark.json")


if __name__ == "__main__":
    main()