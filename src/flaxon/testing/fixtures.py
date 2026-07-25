from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any


class Fixture:
    def __init__(self, name: str, setup: Callable, teardown: Callable | None = None) -> None:
        self.name = name
        self.setup = setup
        self.teardown = teardown
        self._instance: Any = None

    async def load(self) -> Any:
        if self._instance is not None:
            return self._instance

        result = self.setup()
        if asyncio.iscoroutine(result):
            self._instance = await result
        else:
            self._instance = result

        return self._instance

    async def unload(self) -> None:
        if self.teardown and self._instance is not None:
            result = self.teardown(self._instance)
            if asyncio.iscoroutine(result):
                await result
        self._instance = None


class FixtureLoader:
    def __init__(self) -> None:
        self._fixtures: dict[str, Fixture] = {}

    def register(self, fixture: Fixture) -> None:
        self._fixtures[fixture.name] = fixture

    def register_function(self, name: str, setup: Callable, teardown: Callable | None = None) -> None:
        self.register(Fixture(name, setup, teardown))

    def get(self, name: str) -> Fixture | None:
        return self._fixtures.get(name)

    async def load(self, name: str) -> Any:
        fixture = self.get(name)
        if fixture is None:
            raise ValueError(f"Fixture '{name}' not found")
        return await fixture.load()

    async def load_all(self) -> dict[str, Any]:
        result = {}
        for name, fixture in self._fixtures.items():
            result[name] = await fixture.load()
        return result

    async def unload(self, name: str) -> None:
        fixture = self.get(name)
        if fixture:
            await fixture.unload()

    async def unload_all(self) -> None:
        for fixture in self._fixtures.values():
            await fixture.unload()

    def clear(self) -> None:
        self._fixtures.clear()
