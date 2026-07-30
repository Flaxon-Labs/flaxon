from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any


class FileSystemBackend:
    def __init__(self, cache_dir: str = ".cache", default_ttl: int = 300) -> None:
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()

    def _ensure_dir(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.cache"

    def _is_expired(self, path: Path, ttl: int | None = None) -> bool:
        try:
            mtime = path.stat().st_mtime
            ttl = ttl or self.default_ttl
            if ttl <= 0:
                return False
            return time.time() - mtime > ttl
        except OSError:
            return True

    async def get(self, key: str) -> Any:
        self._ensure_dir()
        path = self._key_path(key)

        if not path.exists():
            return None

        if self._is_expired(path):
            await self.delete(key)
            return None

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("value")
        except (json.JSONDecodeError, OSError):
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._ensure_dir()
        path = self._key_path(key)
        ttl = ttl or self.default_ttl

        data = {
            "value": value,
            "created": time.time(),
            "ttl": ttl,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, default=str, ensure_ascii=False)

    async def delete(self, key: str) -> None:
        path = self._key_path(key)
        if path.exists():
            path.unlink(missing_ok=True)

    async def clear(self) -> None:
        self._ensure_dir()
        for path in self.cache_dir.glob("*.cache"):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    async def exists(self, key: str) -> bool:
        path = self._key_path(key)
        if not path.exists():
            return False
        return not self._is_expired(path)

    async def expire(self, key: str, ttl: int) -> None:
        path = self._key_path(key)
        if not path.exists():
            return

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            data["ttl"] = ttl
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, default=str, ensure_ascii=False)
        except (json.JSONDecodeError, OSError):
            pass

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(self, items: dict[str, Any], ttl: int | None = None) -> None:
        for key, value in items.items():
            await self.set(key, value, ttl)

    async def delete_many(self, keys: list[str]) -> None:
        for key in keys:
            await self.delete(key)

    async def increment(self, key: str, amount: int = 1) -> int:
        async with self._lock:
            value = await self.get(key)
            if value is None:
                new_value = amount
            else:
                new_value = int(value) + amount
            await self.set(key, new_value)
            return new_value

    async def decrement(self, key: str, amount: int = 1) -> int:
        return await self.increment(key, -amount)

    def get_stats(self) -> dict[str, Any]:
        self._ensure_dir()
        files = list(self.cache_dir.glob("*.cache"))
        return {
            "total_files": len(files),
            "cache_dir": str(self.cache_dir),
        }
