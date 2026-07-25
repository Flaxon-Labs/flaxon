from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class CustomAdapter(BaseAdapter):
    def __init__(self, connection: Any) -> None:
        self._conn = connection

    async def connect(self) -> None:
        if hasattr(self._conn, "connect"):
            if hasattr(self._conn.connect, "__await__"):
                await self._conn.connect()
            else:
                self._conn.connect()

    async def disconnect(self) -> None:
        if hasattr(self._conn, "disconnect"):
            if hasattr(self._conn.disconnect, "__await__"):
                await self._conn.disconnect()
            else:
                self._conn.disconnect()
        elif hasattr(self._conn, "close"):
            if hasattr(self._conn.close, "__await__"):
                await self._conn.close()
            else:
                self._conn.close()

    async def execute(self, query: str, *args: Any) -> Any:
        if hasattr(self._conn, "execute"):
            if hasattr(self._conn.execute, "__await__"):
                return await self._conn.execute(query, *args)
            return self._conn.execute(query, *args)
        raise NotImplementedError("Custom adapter does not support execute")

    async def fetch_one(self, query: str, *args: Any) -> dict[str, Any] | None:
        if hasattr(self._conn, "fetch_one"):
            if hasattr(self._conn.fetch_one, "__await__"):
                return await self._conn.fetch_one(query, *args)
            return self._conn.fetch_one(query, *args)
        raise NotImplementedError("Custom adapter does not support fetch_one")

    async def fetch_all(self, query: str, *args: Any) -> list[dict[str, Any]]:
        if hasattr(self._conn, "fetch_all"):
            if hasattr(self._conn.fetch_all, "__await__"):
                return await self._conn.fetch_all(query, *args)
            return self._conn.fetch_all(query, *args)
        raise NotImplementedError("Custom adapter does not support fetch_all")

    async def fetch_val(self, query: str, *args: Any) -> Any:
        if hasattr(self._conn, "fetch_val"):
            if hasattr(self._conn.fetch_val, "__await__"):
                return await self._conn.fetch_val(query, *args)
            return self._conn.fetch_val(query, *args)
        raise NotImplementedError("Custom adapter does not support fetch_val")

    async def begin(self) -> None:
        if hasattr(self._conn, "begin"):
            if hasattr(self._conn.begin, "__await__"):
                await self._conn.begin()
            else:
                self._conn.begin()

    async def commit(self) -> None:
        if hasattr(self._conn, "commit"):
            if hasattr(self._conn.commit, "__await__"):
                await self._conn.commit()
            else:
                self._conn.commit()

    async def rollback(self) -> None:
        if hasattr(self._conn, "rollback"):
            if hasattr(self._conn.rollback, "__await__"):
                await self._conn.rollback()
            else:
                self._conn.rollback()

    async def ping(self) -> bool:
        try:
            await self.fetch_val("SELECT 1")
            return True
        except Exception:
            return False
