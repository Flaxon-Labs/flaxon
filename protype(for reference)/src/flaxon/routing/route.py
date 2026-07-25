from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from .converters import CONVERTERS

FLASK_PARAM = re.compile(r"<(?:(?P<type>[a-zA-Z_][a-zA-Z0-9_]*):)?(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)>")
BRACE_PARAM = re.compile(r"\{(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)(?::(?P<type>[a-zA-Z_][a-zA-Z0-9_]*))?\}")


def compile_path(path: str) -> tuple[re.Pattern[str], dict[str, Callable[[str], Any]]]:
    converters: dict[str, Callable[[str], Any]] = {}
    cursor = 0
    pattern = "^"
    matches = list(FLASK_PARAM.finditer(path)) or list(BRACE_PARAM.finditer(path))
    for match in matches:
        pattern += re.escape(path[cursor:match.start()])
        name = match.group("name")
        type_name = match.group("type") or "str"
        if type_name not in CONVERTERS:
            raise ValueError(f"Unknown route converter: {type_name}")
        converter = CONVERTERS[type_name]
        converters[name] = converter.cast
        pattern += f"(?P<{name}>{converter.regex})"
        cursor = match.end()
    pattern += re.escape(path[cursor:]) + "$"
    return re.compile(pattern), converters


@dataclass
class Route:
    path: str
    endpoint: Callable[..., Any]
    methods: set[str] = field(default_factory=lambda: {"GET"})
    name: str | None = None

    def __post_init__(self) -> None:
        self.methods = {method.upper() for method in self.methods}
        self.name = self.name or self.endpoint.__name__
        self.regex, self.converters = compile_path(self.path)

    def match_path(self, path: str) -> dict[str, Any] | None:
        match = self.regex.match(path)
        if not match:
            return None
        values = match.groupdict()
        return {name: self.converters[name](value) for name, value in values.items()}


@dataclass
class WebSocketRoute:
    path: str
    endpoint: Callable[..., Any]
    name: str | None = None

    def __post_init__(self) -> None:
        self.name = self.name or self.endpoint.__name__
        self.regex, self.converters = compile_path(self.path)

    def match_path(self, path: str) -> dict[str, Any] | None:
        match = self.regex.match(path)
        if not match:
            return None
        values = match.groupdict()
        return {name: self.converters[name](value) for name, value in values.items()}
