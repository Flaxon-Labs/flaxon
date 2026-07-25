import sys

import pytest


def test_python_version():
    assert sys.version_info >= (3, 11), "Python 3.11+ is required"


def test_sys_path_compatibility():
    import sys
    assert isinstance(sys.path, list)


def test_import_flaxon():
    import flaxon
    assert flaxon.__version__ is not None


def test_asyncio_running():
    import asyncio

    async def test():
        return True

    result = asyncio.run(test())
    assert result is True


def test_type_hints_compatibility():
    from typing import Any, Dict, List, Optional, Union

    def test_func(data: Dict[str, Any]) -> List[Optional[str]]:
        return []

    assert callable(test_func)


def test_dataclass_compatibility():
    from dataclasses import dataclass

    @dataclass
    class Test:
        name: str
        age: int

    t = Test("test", 25)
    assert t.name == "test"
    assert t.age == 25


def test_enum_compatibility():
    from enum import Enum

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    assert Color.RED.value == 1


def test_contextlib_compatibility():
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def test_context():
        yield "test"

    import asyncio

    async def run():
        async with test_context() as value:
            assert value == "test"

    asyncio.run(run())


def test_pathlib_compatibility():
    from pathlib import Path

    p = Path("/test/path")
    assert p.name == "path"


def test_import_metadata_compatibility():
    import importlib.metadata

    try:
        version = importlib.metadata.version("flaxon-framework")
        assert version is not None
    except importlib.metadata.PackageNotFoundError:
        pass