from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from flaxon.http import HTMLResponse


class Jinax:
    """Optional Flaxon template integration powered by Jinja2.

    Flaxon itself does not require Jinja2. Install the templates extra when
    server-side HTML rendering is desired.
    """

    def __init__(
        self,
        template_directory: str | Path = "templates",
        *,
        auto_reload: bool = False,
        strict_undefined: bool = True,
        globals: dict[str, Any] | None = None,
        filters: dict[str, Callable[..., Any]] | None = None,
    ) -> None:
        try:
            from jinja2 import Environment, FileSystemLoader, StrictUndefined, Undefined, select_autoescape
        except ImportError as exc:
            raise RuntimeError(
                "Jinax requires Jinja2. Install it with: pip install 'flaxon-framework[templates]'"
            ) from exc

        undefined = StrictUndefined if strict_undefined else Undefined
        self.environment = Environment(
            loader=FileSystemLoader(str(template_directory)),
            autoescape=select_autoescape(("html", "htm", "xml")),
            enable_async=True,
            auto_reload=auto_reload,
            undefined=undefined,
        )
        self.environment.globals.update(globals or {})
        self.environment.filters.update(filters or {})
        self.environment.filters.setdefault("currency", self.currency)

    @staticmethod
    def currency(value: Any, code: str = "USD") -> str:
        try:
            amount = float(value)
        except (TypeError, ValueError):
            return str(value)
        return f"{code} {amount:,.2f}"

    def add_global(self, name: str, value: Any) -> None:
        self.environment.globals[name] = value

    def add_filter(self, name: str, func: Callable[..., Any]) -> None:
        self.environment.filters[name] = func

    async def render(self, template_name: str, context: dict[str, Any] | None = None) -> str:
        template = self.environment.get_template(template_name)
        return await template.render_async(**(context or {}))

    async def render_response(
        self,
        template_name: str,
        context: dict[str, Any] | None = None,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> HTMLResponse:
        html = await self.render(template_name, context)
        return HTMLResponse(html, status_code=status_code, headers=headers)
