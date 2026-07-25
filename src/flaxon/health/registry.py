from __future__ import annotations

import asyncio
from typing import Any

from .checks import HealthCheck, HealthCheckResult


class HealthRegistry:
    def __init__(self) -> None:
        self._checks: dict[str, HealthCheck] = {}

    def register(self, check: HealthCheck) -> None:
        self._checks[check.name] = check

    def register_function(self, name: str, func: Any) -> None:
        self._checks[name] = HealthCheck(name, func)

    def unregister(self, name: str) -> None:
        self._checks.pop(name, None)

    def get(self, name: str) -> HealthCheck | None:
        return self._checks.get(name)

    def list_checks(self) -> list[str]:
        return list(self._checks.keys())

    async def run_all(self) -> list[HealthCheckResult]:
        tasks = [check.run() for check in self._checks.values()]
        return await asyncio.gather(*tasks)

    async def run_one(self, name: str) -> HealthCheckResult | None:
        check = self.get(name)
        if check is None:
            return None
        return await check.run()

    async def run_selected(self, names: list[str]) -> list[HealthCheckResult]:
        tasks = []
        for name in names:
            check = self.get(name)
            if check:
                tasks.append(check.run())
        return await asyncio.gather(*tasks)

    async def run_excluding(self, exclude: list[str]) -> list[HealthCheckResult]:
        names = [name for name in self._checks.keys() if name not in exclude]
        return await self.run_selected(names)

    def clear(self) -> None:
        self._checks.clear()

    @property
    def count(self) -> int:
        return len(self._checks)

    def __len__(self) -> int:
        return len(self._checks)

    def __contains__(self, name: str) -> bool:
        return name in self._checks

    def __iter__(self):
        return iter(self._checks)
