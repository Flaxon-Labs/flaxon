from __future__ import annotations

from collections.abc import Callable
from typing import Any


class Directive:
    def __init__(self, name: str, handler: Callable[..., str]) -> None:
        self.name = name
        self.handler = handler

    def process(self, *args: Any, **kwargs: Any) -> str:
        return self.handler(*args, **kwargs)


class DirectiveRegistry:
    def __init__(self) -> None:
        self._directives: dict[str, Directive] = {}

    def register(self, directive: Directive) -> None:
        self._directives[directive.name] = directive

    def register_function(self, name: str, handler: Callable[..., str]) -> None:
        self.register(Directive(name, handler))

    def get(self, name: str) -> Directive | None:
        return self._directives.get(name)

    def process(self, name: str, *args: Any, **kwargs: Any) -> str:
        directive = self.get(name)
        if directive is None:
            return ""
        return directive.process(*args, **kwargs)

    def list_directives(self) -> list[str]:
        return list(self._directives.keys())


class BuiltinDirectives:
    @staticmethod
    def now(format: str = "%Y-%m-%d %H:%M:%S") -> str:
        from datetime import datetime
        return datetime.now().strftime(format)

    @staticmethod
    def upper(value: str) -> str:
        return value.upper()

    @staticmethod
    def lower(value: str) -> str:
        return value.lower()

    @staticmethod
    def capitalize(value: str) -> str:
        return value.capitalize()

    @staticmethod
    def title(value: str) -> str:
        return value.title()

    @staticmethod
    def join(values: list[str], separator: str = ", ") -> str:
        return separator.join(values)

    @staticmethod
    def first(items: list[Any]) -> Any:
        return items[0] if items else None

    @staticmethod
    def last(items: list[Any]) -> Any:
        return items[-1] if items else None

    @staticmethod
    def length(value: Any) -> int:
        return len(value) if hasattr(value, "__len__") else 0

    @staticmethod
    def default(value: Any, default_value: Any) -> Any:
        return value if value is not None else default_value

    @staticmethod
    def json(value: Any) -> str:
        import json
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def safe(value: str) -> str:
        return value


def register_builtin_directives(registry: DirectiveRegistry) -> None:
    registry.register_function("now", BuiltinDirectives.now)
    registry.register_function("upper", BuiltinDirectives.upper)
    registry.register_function("lower", BuiltinDirectives.lower)
    registry.register_function("capitalize", BuiltinDirectives.capitalize)
    registry.register_function("title", BuiltinDirectives.title)
    registry.register_function("join", BuiltinDirectives.join)
    registry.register_function("first", BuiltinDirectives.first)
    registry.register_function("last", BuiltinDirectives.last)
    registry.register_function("length", BuiltinDirectives.length)
    registry.register_function("default", BuiltinDirectives.default)
    registry.register_function("json", BuiltinDirectives.json)
    registry.register_function("safe", BuiltinDirectives.safe)
