from __future__ import annotations

import json
from typing import Any


class RedisSubscriptionBackend:
    def __init__(self, redis_url: str = "redis://localhost:6379/0", prefix: str = "graphql:subscription") -> None:
        self.redis_url = redis_url
        self.prefix = prefix
        self._client = None
        self._pub = None
        self._sub = None

    async def connect(self) -> None:
        try:
            import redis.asyncio as redis
            self._client = redis.from_url(self.redis_url, decode_responses=True)
            self._pub = redis.from_url(self.redis_url, decode_responses=True)
            self._sub = redis.from_url(self.redis_url, decode_responses=True)
        except ImportError as exc:
            raise RuntimeError("redis is required. Install with: pip install redis") from exc

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
        if self._pub:
            await self._pub.close()
            self._pub = None
        if self._sub:
            await self._sub.close()
            self._sub = None

    def _key(self, operation_id: str) -> str:
        return f"{self.prefix}:{operation_id}"

    async def subscribe(self, operation_id: str, context: Any, variables: dict[str, Any]) -> str:
        import uuid
        subscription_id = str(uuid.uuid4())

        data = {
            "subscription_id": subscription_id,
            "operation_id": operation_id,
            "variables": variables,
        }

        await self._client.hset(
            self._key(operation_id),
            subscription_id,
            json.dumps(data),
        )

        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> None:
        await self._client.hdel(self._key(""), subscription_id)

    async def publish(self, operation_id: str, data: Any) -> None:
        await self._pub.publish(
            self._key(operation_id),
            json.dumps(data),
        )

    async def next(self, subscription_id: str) -> Any:
        pubsub = self._sub.pubsub()
        await pubsub.subscribe(self._key(""))

        async for message in pubsub.listen():
            if message["type"] == "message":
                return json.loads(message["data"])
            if message["type"] == "unsubscribe":
                break

        return None