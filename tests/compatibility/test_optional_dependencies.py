import importlib
import sys

from importlib.metadata import version

import pytest


def test_import_optional_dependencies():
    dependencies = [
        ("uvicorn", "server"),
        ("jinja2", "templates"),
        ("pytest", "dev"),
        ("pytest_cov", "dev"),
        ("ruff", "dev"),
        ("mypy", "dev"),
        ("build", "dev"),
        ("twine", "dev"),
        ("mkdocs", "docs"),
    ]

    for module_name, group in dependencies:
        try:
            importlib.import_module(module_name)
            print(f"{module_name} imported successfully")
        except ImportError:
            print(f"{module_name} not installed (group: {group})")


def test_uvicorn_optional():
    try:
        import uvicorn
        assert uvicorn.__version__ is not None
    except ImportError:
        pytest.skip("Uvicorn not installed")


def test_jinja2_optional():
    try:
        import jinja2
        assert jinja2.__version__ is not None
    except ImportError:
        pytest.skip("Jinja2 not installed")


def test_asyncpg_optional():
    try:
        import asyncpg
        assert asyncpg.__version__ is not None
    except ImportError:
        pytest.skip("asyncpg not installed")


def test_aiosqlite_optional():
    try:
        import aiosqlite
        assert aiosqlite.__version__ is not None
    except ImportError:
        pytest.skip("aiosqlite not installed")


def test_redis_optional():
    try:
        import redis
        assert redis.__version__ is not None
    except ImportError:
        pytest.skip("redis not installed")


def test_msgpack_optional():
    try:
        import msgpack
        assert msgpack.__version__ is not None
    except ImportError:
        pytest.skip("msgpack not installed")


def test_pytest_optional():
    try:
        import pytest
        assert pytest.__version__ is not None
    except ImportError:
        pytest.skip("pytest not installed")


def test_ruff_optional():
    try:
        import ruff
        assert version("ruff")
    except ImportError:
        pytest.skip("ruff not installed")


def test_mypy_optional():
    try:
        import mypy
        assert version("mypy")
    except ImportError:
        pytest.skip("mypy not installed")


def test_mkdocs_optional():
    try:
        import mkdocs
        assert version("mkdocs")
    except ImportError:
        pytest.skip("mkdocs not installed")


def test_build_optional():
    try:
        import build
        assert version("build")
    except ImportError:
        pytest.skip("build not installed")
