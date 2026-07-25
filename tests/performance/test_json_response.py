import json
import time

import pytest

from flaxon import Flaxon
from flaxon.http import JSONResponse
from flaxon.testing import TestClient


@pytest.fixture
def large_data():
    return {
        "users": [
            {
                "id": i,
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "profile": {
                    "age": 20 + (i % 50),
                    "city": f"City {i % 10}",
                    "bio": "Lorem ipsum dolor sit amet" * 10,
                },
                "posts": [
                    {"id": j, "title": f"Post {j}", "content": "Content" * 20}
                    for j in range(5)
                ],
            }
            for i in range(100)
        ],
        "metadata": {
            "total": 100,
            "page": 1,
            "per_page": 20,
        },
    }


@pytest.fixture
def app_with_json():
    app = Flaxon("test-json")

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

    return app


def test_small_json_response_speed(app_with_json):
    client = TestClient(app_with_json)

    start = time.perf_counter()

    for _ in range(100):
        client.get("/small")

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_medium_json_response_speed(app_with_json):
    client = TestClient(app_with_json)

    start = time.perf_counter()

    for _ in range(100):
        client.get("/medium")

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_large_json_response_speed(app_with_json):
    client = TestClient(app_with_json)

    start = time.perf_counter()

    for _ in range(50):
        client.get("/large")

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_json_serialization_speed(large_data):
    start = time.perf_counter()

    for _ in range(100):
        response = JSONResponse(large_data)

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_json_response_with_dataclass():
    from dataclasses import dataclass

    @dataclass
    class User:
        id: int
        name: str
        email: str

    users = [User(i, f"User {i}", f"user{i}@example.com") for i in range(100)]

    start = time.perf_counter()

    for _ in range(100):
        response = JSONResponse({"users": users})

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_json_response_size():
    data = {"key": "value" * 1000}

    start = time.perf_counter()

    for _ in range(100):
        response = JSONResponse(data)

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_json_response_custom_encoder():
    from datetime import datetime

    data = {
        "timestamp": datetime.now(),
        "name": "test",
    }

    start = time.perf_counter()

    for _ in range(100):
        response = JSONResponse(data)

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0