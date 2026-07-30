from __future__ import annotations

from typing import Any


class CustomBackend:
    def __init__(self, backend: Any) -> None:
        self.backend = backend

    async def get(self, key: str) -> Any:
        if hasattr(self.backend, "get"):
            result = self.backend.get(key)
            if hasattr(result, "__await__"):
                return await result
            return result
        raise NotImplementedError("Backend does not support get")

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if hasattr(self.backend, "set"):
            result = self.backend.set(key, value, ttl)
            if hasattr(result, "__await__"):
                await result
            return
        raise NotImplementedError("Backend does not support set")

    async def delete(self, key: str) -> None:
        if hasattr(self.backend, "delete"):
            result = self.backend.delete(key)
            if hasattr(result, "__await__"):
                await result
            return
        raise NotImplementedError("Backend does not support delete")

    async def clear(self) -> None:
        if hasattr(self.backend, "clear"):
            result = self.backend.clear()
            if hasattr(result, "__await__"):
                await result
            return
        raise NotImplementedError("Backend does not support clear")

    async def exists(self, key: str) -> bool:
        if hasattr(self.backend, "exists"):
            result = self.backend.exists(key)
            if hasattr(result, "__await__"):
                return await result
            return result
        raise NotImplementedError("Backend does not support exists")

    async def expire(self, key: str, ttl: int) -> None:
        if hasattr(self.backend, "expire"):
            result = self.backend.expire(key, ttl)
            if hasattr(result, "__await__"):
                await result
            return
        raise NotImplementedError("Backend does not support expire")

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        if hasattr(self.backend, "get_many"):
            result = self.backend.get_many(keys)
            if hasattr(result, "__await__"):
                return await result
            return result
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(self, items: dict[str, Any], ttl: int | None = None) -> None:
        if hasattr(self.backend, "set_many"):
            result = self.backend.set_many(items, ttl)
            if hasattr(result, "__await__"):
                await result
            return
        for key, value in items.items():
            await self.set(key, value, ttl)

    async def delete_many(self, keys: list[str]) -> None:
        if hasattr(self.backend, "delete_many"):
            result = self.backend.delete_many(keys)
            if hasattr(result, "__await__"):
                await result
            return
        for key in keys:
            await self.delete(key)

    async def increment(self, key: str, amount: int = 1) -> int:
        if hasattr(self.backend, "increment"):
            result = self.backend.increment(key, amount)
            if hasattr(result, "__await__"):
                return await result
            return result
        value = await self.get(key)
        if value is None:
            new_value = amount
        else:
            new_value = int(value) + amount
        await self.set(key, new_value)
        return new_value

    async def decrement(self, key: str, amount: int = 1) -> int:
        if hasattr(self.backend, "decrement"):
            result = self.backend.decrement(key, amount)
            if hasattr(result, "__await__"):
                return await result
            return result
        return await self.increment(key, -amount)
