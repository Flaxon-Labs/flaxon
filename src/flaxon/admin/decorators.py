from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from .registry import Registry


def admin_model(**options: Any) -> Callable:
    def decorator(cls: type) -> type:
        Registry().register(cls, **options)
        return cls
    return decorator


def admin_action(name: str | None = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        wrapper._admin_action = name or func.__name__
        return wrapper
    return decorator


def admin_display(header: str | None = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        wrapper._admin_display = True
        wrapper._admin_header = header or func.__name__.replace("_", " ").title()
        return wrapper
    return decorator