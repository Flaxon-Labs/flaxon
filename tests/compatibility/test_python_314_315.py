import compileall
import sys

import pytest


SUPPORTED = {(3, 14), (3, 15)}


@pytest.mark.parametrize("major, minor", [(3, 14), (3, 15)])
def test_supported_python_runtime(major, minor):
    if (major, minor) not in SUPPORTED or sys.version_info[:2] != (major, minor):
        pytest.skip(f"requires Python {major}.{minor}")
    assert sys.version_info >= (major, minor)


@pytest.mark.parametrize("major, minor", [(3, 14), (3, 15)])
def test_flaxon_sources_compile_on_supported_python(major, minor):
    if sys.version_info[:2] != (major, minor):
        pytest.skip(f"requires Python {major}.{minor}")
    assert compileall.compile_dir("src/flaxon", quiet=1, force=False)


@pytest.mark.parametrize("major, minor", [(3, 14), (3, 15)])
def test_asyncio_and_typing_baseline(major, minor):
    if sys.version_info[:2] != (major, minor):
        pytest.skip(f"requires Python {major}.{minor}")
    import asyncio
    from typing import TypeVar

    T = TypeVar("T")

    async def identity(value: T) -> T:
        return value

    assert asyncio.run(identity("flaxon")) == "flaxon"
