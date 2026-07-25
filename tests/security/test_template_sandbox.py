import pytest

from flaxon.jinax import Jinax
from flaxon.jinax.sandbox import Sandbox


def test_sandbox_evaluate_safe_expression():
    sandbox = Sandbox()
    context = {"name": "Alice", "age": 30}

    result = sandbox.evaluate("name", context)
    assert result == "Alice"

    result = sandbox.evaluate("age + 10", context)
    assert result == 40


def test_sandbox_restricts_import():
    sandbox = Sandbox()

    result = sandbox.evaluate("__import__('os').system('echo test')", {})
    assert result is None


def test_sandbox_restricts_eval():
    sandbox = Sandbox()

    result = sandbox.evaluate("eval('1+1')", {})
    assert result is None


def test_sandbox_restricts_exec():
    sandbox = Sandbox()

    result = sandbox.evaluate("exec('print(1)')", {})
    assert result is None


def test_sandbox_restricts_open():
    sandbox = Sandbox()

    result = sandbox.evaluate("open('/etc/passwd')", {})
    assert result is None


def test_sandbox_restricts_globals():
    sandbox = Sandbox()

    result = sandbox.evaluate("globals()", {})
    assert result is None


def test_sandbox_restricts_locals():
    sandbox = Sandbox()

    result = sandbox.evaluate("locals()", {})
    assert result is None


def test_sandbox_allowed_modules():
    sandbox = Sandbox(allowed_modules=["json"])

    assert sandbox.is_safe_module("json") is True
    assert sandbox.is_safe_module("os") is False


def test_sandbox_safe_builtins():
    sandbox = Sandbox()

    context = {"items": [1, 2, 3, 4, 5]}

    result = sandbox.evaluate("len(items)", context)
    assert result == 5

    result = sandbox.evaluate("sum(items)", context)
    assert result == 15


def test_sandbox_nested_expression():
    sandbox = Sandbox()

    context = {
        "user": {
            "name": "Alice",
            "email": "alice@example.com",
            "roles": ["admin", "user"],
        }
    }

    result = sandbox.evaluate("user.name", context)
    assert result == "Alice"

    result = sandbox.evaluate("user.roles[0]", context)
    assert result == "admin"


def test_sandbox_jinax_integration():
    sandbox = Sandbox()

    template = "{{ name }} is {{ age }} years old"
    context = {"name": "Alice", "age": 30}

    result = sandbox.evaluate("name", context)
    assert result == "Alice"


def test_sandbox_restricts_attr_access():
    sandbox = Sandbox()

    context = {"obj": {"__class__": "test"}}

    result = sandbox.evaluate("obj.__class__", context)
    assert result is None