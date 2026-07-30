from __future__ import annotations

import time
from typing import Any

from .manager import DatabaseManager


class DatabaseHealthCheck:
    def __init__(self, db: DatabaseManager, name: str = "database") -> None:
        self.db = db
        self.name = name

    async def check(self) -> dict[str, Any]:
        start = time.perf_counter()

        try:
            await self.db.fetch_val("SELECT 1")
            latency = (time.perf_counter() - start) * 1000

            return {
                "name": self.name,
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "pool_size": self.db.pool_size,
                "available": self.db.available_connections,
            }
        except Exception as exc:
            return {
                "name": self.name,
                "status": "unhealthy",
                "error": str(exc),
            }

    async def is_healthy(self) -> bool:
        result = await self.check()
        return result["status"] == "healthy"


class HealthRegistry:
    def __init__(self) -> None:
        self._checks: dict[str, Any] = {}

    def register(self, name: str, check: Any) -> None:
        self._checks[name] = check

    def unregister(self, name: str) -> None:
        self._checks.pop(name, None)

    async def check_all(self) -> dict[str, Any]:
        results = {}
        for name, check in self._checks.items():
            if hasattr(check, "check"):
                results[name] = await check.check()
            else:
                results[name] = await check()
        return results

    async def check_one(self, name: str) -> dict[str, Any] | None:
        check = self._checks.get(name)
        if check is None:
            return None

        if hasattr(check, "check"):
            return await check.check()
        return await check()

    async def overall_status(self) -> dict[str, Any]:
        results = await self.check_all()
        all_healthy = all(r.get("status") == "healthy" for r in results.values())

        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": results,
            "timestamp": time.time(),
        }
