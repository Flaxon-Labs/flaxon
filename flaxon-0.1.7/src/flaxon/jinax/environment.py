from __future__ import annotations

from collections.abc import Callable
from typing import Any


class Environment:
    def __init__(
        self,
        loader: Any,
        autoescape: bool = True,
        enable_async: bool = True,
        auto_reload: bool = False,
        strict_undefined: bool = False,
    ) -> None:
        try:
            from jinja2 import Environment as JinjaEnvironment, StrictUndefined, Undefined, select_autoescape
        except ImportError as exc:
            raise RuntimeError("Jinja2 is required. Install with: pip install jinja2") from exc

        undefined = StrictUndefined if strict_undefined else Undefined
        self._env = JinjaEnvironment(
            loader=loader,
            autoescape=select_autoescape(("html", "htm", "xml")) if autoescape else False,
            enable_async=enable_async,
            auto_reload=auto_reload,
            undefined=undefined,
        )
        self._globals: dict[str, Any] = {}
        self._filters: dict[str, Callable[..., Any]] = {}

    def add_global(self, name: str, value: Any) -> None:
        self._globals[name] = value
        self._env.globals[name] = value

    def add_filter(self, name: str, func: Callable[..., Any]) -> None:
        self._filters[name] = func
        self._env.filters[name] = func

    def get_template(self, name: str) -> Any:
        return self._env.get_template(name)

    def from_string(self, source: str) -> Any:
        return self._env.from_string(source)

    @property
    def globals(self) -> dict[str, Any]:
        return self._globals

    @property
    def filters(self) -> dict[str, Callable[..., Any]]:
        return self._filters
