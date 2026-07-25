import time

import pytest

from flaxon import Flaxon, Router


@pytest.fixture
def large_router():
    router = Router()

    for i in range(1000):
        @router.get(f"/users/{i}")
        async def user(request):
            return {"id": i}

        @router.post(f"/users/{i}/posts")
        async def user_post(request):
            return {"user_id": i}

        @router.get(f"/products/{i}/reviews")
        async def product_reviews(request):
            return {"product_id": i}

    return router


@pytest.fixture
def nested_router():
    router = Router()

    for i in range(10):
        group = Router(prefix=f"/api/v{i}")

        for j in range(100):
            @group.get(f"/items/{j}")
            async def item(request):
                return {"id": j}

        router.include_router(group)

    return router


def test_router_match_speed(large_router):
    start = time.perf_counter()

    for i in range(1000):
        large_router.match(f"/users/{i}", "GET")

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_router_match_nested_speed(nested_router):
    start = time.perf_counter()

    for i in range(10):
        for j in range(100):
            nested_router.match(f"/api/v{i}/items/{j}", "GET")

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_router_url_generation_speed(large_router):
    start = time.perf_counter()

    for i in range(1000):
        large_router.url_for("user", i=i)

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_router_compilation_speed():
    start = time.perf_counter()

    router = Router()
    for i in range(100):
        @router.get(f"/users/<int:user_id>/posts/<int:post_id>/comments/<int:comment_id>")
        async def deep_route(request):
            return {"ok": True}

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_route_matching_with_parameters():
    router = Router()

    @router.get("/users/<int:user_id>/posts/<int:post_id>")
    async def post(request):
        return {"ok": True}

    start = time.perf_counter()

    for _ in range(10000):
        router.match("/users/123/posts/456", "GET")

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_router_method_allowed_check():
    router = Router()

    @router.route("/api/data", methods=["GET", "POST", "PUT", "DELETE"])
    async def data(request):
        return {"ok": True}

    start = time.perf_counter()

    for _ in range(10000):
        router.match("/api/data", "GET")
        router.match("/api/data", "POST")

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0


def test_router_not_found_speed(large_router):
    start = time.perf_counter()

    from flaxon.exceptions import NotFound

    count = 0
    for _ in range(1000):
        try:
            large_router.match("/nonexistent/path", "GET")
        except NotFound:
            count += 1

    elapsed = time.perf_counter() - start
    assert elapsed < 3.0
    assert count == 1000