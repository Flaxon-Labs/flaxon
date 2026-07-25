from __future__ import annotations

import inspect
from typing import Any


def get_class(obj: Any) -> type:
    """Get the class of an object."""
    return obj.__class__


def get_methods(obj: Any, include_private: bool = False) -> list[str]:
    """Get all method names of an object."""
    methods = []
    for name in dir(obj):
        if not include_private and name.startswith("_"):
            continue
        attr = getattr(obj, name)
        if callable(attr):
            methods.append(name)
    return methods


def get_source(obj: Any) -> str | None:
    """Get the source code of an object."""
    try:
        return inspect.getsource(obj)
    except (OSError, TypeError, ValueError):
        return None


def get_args(func: Any) -> list[str]:
    """Get the argument names of a function."""
    signature = inspect.signature(func)
    return list(signature.parameters.keys())


def is_async(obj: Any) -> bool:
    """Check if an object is async."""
    return inspect.iscoroutinefunction(obj) or inspect.isasyncgenfunction(obj)


def is_class(obj: Any) -> bool:
    """Check if an object is a class."""
    return inspect.isclass(obj)


def is_function(obj: Any) -> bool:
    """Check if an object is a function."""
    return inspect.isfunction(obj)


def is_method(obj: Any) -> bool:
    """Check if an object is a method."""
    return inspect.ismethod(obj)


def is_module(obj: Any) -> bool:
    """Check if an object is a module."""
    return inspect.ismodule(obj)


def get_import_path(obj: Any) -> str:
    """Get the import path of an object."""
    module = getattr(obj, "__module__", None)
    name = getattr(obj, "__name__", None)
    if module and name:
        return f"{module}:{name}"
    return str(obj)


def get_annotations(func: Any) -> dict[str, Any]:
    """Get the type annotations of a function."""
    return getattr(func, "__annotations__", {})
