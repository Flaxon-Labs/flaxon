from __future__ import annotations

from typing import Any


class Runtime:
    def __init__(self, environment: Any) -> None:
        self.environment = environment
        self._context: dict[str, Any] = {}

    def render(self, template: str, context: dict[str, Any] | None = None) -> str:
        ctx = {**self._context, **(context or {})}
        template_obj = self.environment.get_template(template)
        return template_obj.render(**ctx)

    async def render_async(self, template: str, context: dict[str, Any] | None = None) -> str:
        ctx = {**self._context, **(context or {})}
        template_obj = self.environment.get_template(template)
        return await template_obj.render_async(**ctx)

    def render_string(self, source: str, context: dict[str, Any] | None = None) -> str:
        ctx = {**self._context, **(context or {})}
        template_obj = self.environment.from_string(source)
        return template_obj.render(**ctx)

    async def render_string_async(self, source: str, context: dict[str, Any] | None = None) -> str:
        ctx = {**self._context, **(context or {})}
        template_obj = self.environment.from_string(source)
        return await template_obj.render_async(**ctx)

    def add_global(self, name: str, value: Any) -> None:
        self._context[name] = value

    def get_global(self, name: str) -> Any:
        return self._context.get(name)

    def clear(self) -> None:
        self._context.clear()
