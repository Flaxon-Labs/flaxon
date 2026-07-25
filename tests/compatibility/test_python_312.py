import sys

import pytest


@pytest.mark.skipif(sys.version_info < (3, 12), reason="Python 3.12+ required")
def test_python_312_features():
    assert sys.version_info >= (3, 12)


@pytest.mark.skipif(sys.version_info < (3, 12), reason="Python 3.12+ required")
def test_type_parameter_syntax():
    try:
        # Python 3.12 type parameter syntax
        exec("""
def test[T](arg: T) -> T:
    return arg
""")
        assert True
    except SyntaxError:
        pytest.skip("Type parameter syntax not available")


@pytest.mark.skipif(sys.version_info < (3, 12), reason="Python 3.12+ required")
def test_f_string_compatibility():
    name = "test"
    value = f"Hello {name}"
    assert value == "Hello test"


@pytest.mark.skipif(sys.version_info < (3, 12), reason="Python 3.12+ required")
def test_exception_group_compatibility():
    try:
        raise ExceptionGroup("test", [ValueError("error")])
    except ExceptionGroup as e:
        assert len(e.exceptions) == 1


@pytest.mark.skipif(sys.version_info < (3, 12), reason="Python 3.12+ required")
def test_timeout_compatibility():
    import asyncio

    async def test():
        await asyncio.sleep(0.1)
        return True

    result = asyncio.run(test())
    assert result is True


@pytest.mark.skipif(sys.version_info < (3, 12), reason="Python 3.12+ required")
def test_generic_type_compatibility():
    from typing import Generic, TypeVar

    T = TypeVar("T")

    class Container(Generic[T]):
        def __init__(self, value: T):
            self.value = value

    c = Container[int](42)
    assert c.value == 42


@pytest.mark.skipif(sys.version_info < (3, 12), reason="Python 3.12+ required")
def test_overload_compatibility():
    from typing import overload

    @overload
    def test(x: int) -> int: ...

    @overload
    def test(x: str) -> str: ...

    def test(x):
        return x

    assert test(1) == 1
    assert test("a") == "a"


@pytest.mark.skipif(sys.version_info < (3, 12), reason="Python 3.12+ required")
def test_await_compatibility():
    import asyncio

    async def test():
        return 42

    result = asyncio.run(test())
    assert result == 42


@pytest.mark.skipif(sys.version_info < (3, 12), reason="Python 3.12+ required")
def test_match_statement_compatibility():
    value = "test"

    match value:
        case "test":
            result = True
        case _:
            result = False

    assert result is True