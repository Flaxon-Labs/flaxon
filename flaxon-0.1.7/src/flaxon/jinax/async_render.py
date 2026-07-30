from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any


class AsyncRenderer:
    def __init__(self, environment: Any) -> None:
        self.environment = environment

    async def render(self, template_name: str, context: dict[str, Any]) -> str:
        template = self.environment.get_template(template_name)
        if hasattr(template, "render_async"):
            return await template.render_async(**context)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, template.render, context)

    async def render_string(self, source: str, context: dict[str, Any]) -> str:
        template = self.environment.from_string(source)
        if hasattr(template, "render_async"):
            return await template.render_async(**context)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, template.render, context)

    async def render_many(self, templates: list[tuple[str, dict[str, Any]]]) -> list[str]:
        tasks = [self.render(name, ctx) for name, ctx in templates]
        return await asyncio.gather(*tasks)


class AsyncFilter:
    def __init__(self, func: Callable) -> None:
        self.func = func

    async def apply(self, value: Any, *args: Any, **kwargs: Any) -> Any:
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(value, *args, **kwargs)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.func, value, *args, **kwargs)


class AsyncFunction:
    def __init__(self, func: Callable) -> None:
        self.func = func

    async def call(self, *args: Any, **kwargs: Any) -> Any:
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(*args, **kwargs)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.func, *args, **kwargs)


def async_render(func: Callable) -> Callable:
    async def wrapper(*args: Any, **kwargs: Any) -> str:
        result = func(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result
    return wrapper


class AsyncTemplateCache:
    def __init__(self, cache: Any) -> None:
        self.cache = cache

    async def get(self, key: str) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.cache.get, key)

    async def set(self, key: str, value: Any) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.cache.set, key, value)

    async def invalidate(self, key: str) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.cache.invalidate, key)
