import sys

import pytest


@pytest.mark.skipif(sys.version_info < (3, 13), reason="Python 3.13+ required")
def test_python_313_features():
    assert sys.version_info >= (3, 13)


@pytest.mark.skipif(sys.version_info < (3, 13), reason="Python 3.13+ required")
def test_asyncio_timeout():
    import asyncio

    async def test():
        async with asyncio.timeout(0.1):
            await asyncio.sleep(0.05)
            return True

    result = asyncio.run(test())
    assert result is True


@pytest.mark.skipif(sys.version_info < (3, 13), reason="Python 3.13+ required")
def test_exception_group_handling():
    try:
        raise ExceptionGroup("test", [ValueError("error")])
    except* ValueError as e:
        assert len(e.exceptions) == 1


@pytest.mark.skipif(sys.version_info < (3, 13), reason="Python 3.13+ required")
def test_importlib_resources():
    try:
        import importlib.resources

        assert importlib.resources is not None
    except ImportError:
        pytest.skip("importlib.resources not available")


@pytest.mark.skipif(sys.version_info < (3, 13), reason="Python 3.13+ required")
def test_deprecation_warning():
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert True


@pytest.mark.skipif(sys.version_info < (3, 13), reason="Python 3.13+ required")
def test_type_hint_generics():
    from typing import TypeVar

    T = TypeVar("T")

    def test(x: T) -> T:
        return x

    assert test(42) == 42


@pytest.mark.skipif(sys.version_info < (3, 13), reason="Python 3.13+ required")
def test_asyncio_task_group():
    import asyncio

    async def test():
        async with asyncio.TaskGroup() as tg:
            task = tg.create_task(asyncio.sleep(0.1))
        return True

    result = asyncio.run(test())
    assert result is True


@pytest.mark.skipif(sys.version_info < (3, 13), reason="Python 3.13+ required")
def test_any_compatibility():
    from typing import Any

    def test(value: Any) -> Any:
        return value

    assert test(42) == 42


@pytest.mark.skipif(sys.version_info < (3, 13), reason="Python 3.13+ required")
def test_context_manager_compatibility():
    class TestContext:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    with TestContext() as ctx:
        assert ctx is not None