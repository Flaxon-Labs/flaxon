from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class RedisAdapter(BaseAdapter):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        database: int = 0,
        password: str | None = None,
        decode_responses: bool = True,
        **kwargs: Any,
    ) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.password = password
        self.decode_responses = decode_responses
        self.kwargs = kwargs
        self._client = None

    async def connect(self) -> None:
        try:
            import redis.asyncio as redis
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.database,
                password=self.password,
                decode_responses=self.decode_responses,
                **self.kwargs,
            )
        except ImportError as exc:
            raise RuntimeError("redis is required. Install with: pip install redis") from exc

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def execute(self, query: str, *args: Any) -> Any:
        raise NotImplementedError("Redis does not support SQL queries")

    async def fetch_one(self, query: str, *args: Any) -> dict[str, Any] | None:
        raise NotImplementedError("Redis does not support SQL queries")

    async def fetch_all(self, query: str, *args: Any) -> list[dict[str, Any]]:
        raise NotImplementedError("Redis does not support SQL queries")

    async def fetch_val(self, query: str, *args: Any) -> Any:
        raise NotImplementedError("Redis does not support SQL queries")

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if ttl:
            await self._client.setex(key, ttl, value)
        else:
            await self._client.set(key, value)

    async def get(self, key: str) -> Any:
        return await self._client.get(key)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self._client.exists(key))

    async def expire(self, key: str, ttl: int) -> None:
        await self._client.expire(key, ttl)

    async def incr(self, key: str) -> int:
        return await self._client.incr(key)

    async def decr(self, key: str) -> int:
        return await self._client.decr(key)

    async def hset(self, key: str, field: str, value: Any) -> None:
        await self._client.hset(key, field, value)

    async def hget(self, key: str, field: str) -> Any:
        return await self._client.hget(key, field)

    async def hgetall(self, key: str) -> dict[str, Any]:
        return await self._client.hgetall(key)

    async def lpush(self, key: str, *values: Any) -> None:
        await self._client.lpush(key, *values)

    async def rpush(self, key: str, *values: Any) -> None:
        await self._client.rpush(key, *values)

    async def lpop(self, key: str) -> Any:
        return await self._client.lpop(key)

    async def rpop(self, key: str) -> Any:
        return await self._client.rpop(key)

    async def lrange(self, key: str, start: int, stop: int) -> list[Any]:
        return await self._client.lrange(key, start, stop)

    async def sadd(self, key: str, *values: Any) -> None:
        await self._client.sadd(key, *values)

    async def srem(self, key: str, *values: Any) -> None:
        await self._client.srem(key, *values)

    async def smembers(self, key: str) -> set[Any]:
        return await self._client.smembers(key)

    async def begin(self) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass

    async def ping(self) -> bool:
        try:
            return bool(await self._client.ping())
        except Exception:
            return False
