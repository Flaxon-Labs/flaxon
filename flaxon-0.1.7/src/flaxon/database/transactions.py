"""Transaction helpers."""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .manager import DatabaseManager


class Transaction:
    """An awaitable transaction that also supports ``async with``."""

    def __init__(self, manager: DatabaseManager) -> None:
        self.manager = manager
        self.depth = 0
        self._active = False
        self._connection: Any = None

    def __await__(self) -> Generator[Any, None, Transaction]:
        return self._prepare().__await__()

    async def _prepare(self) -> Transaction:
        if not self.manager._direct and self._connection is None:
            self._connection = await self.manager.pool.acquire()
        return self

    async def __aenter__(self) -> Transaction:
        await self.begin()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
        await self.close()

    async def begin(self) -> None:
        await self._prepare()
        self.depth = self.manager._transaction_depth
        self.manager._transaction_depth += 1
        if self.depth == 0:
            target = self.manager.pool if self.manager._direct else self._connection
            if hasattr(target, "begin"):
                await target.begin()
            else:
                await target.execute("BEGIN")
        else:
            await self._execute_raw(f"SAVEPOINT flaxon_tx_{self.depth}")
        self._active = True

    async def commit(self) -> None:
        if not self._active:
            return
        if self.depth == 0:
            target = self.manager.pool if self.manager._direct else self._connection
            if hasattr(target, "commit"):
                await target.commit()
            else:
                await target.execute("COMMIT")
        else:
            await self._execute_raw(f"RELEASE SAVEPOINT flaxon_tx_{self.depth}")
        self.manager._transaction_depth -= 1
        self._active = False

    async def rollback(self) -> None:
        if not self._active:
            return
        if self.depth == 0:
            target = self.manager.pool if self.manager._direct else self._connection
            if hasattr(target, "rollback"):
                await target.rollback()
            else:
                await target.execute("ROLLBACK")
        else:
            await self._execute_raw(f"ROLLBACK TO SAVEPOINT flaxon_tx_{self.depth}")
        self.manager._transaction_depth -= 1
        self._active = False

    async def close(self) -> None:
        if self._connection is not None:
            await self.manager.pool.release(self._connection)
            self._connection = None

    async def _execute_raw(self, query: str, *args: Any) -> Any:
        target = self.manager.pool if self.manager._direct else self._connection
        return await target.execute(query, *args)

    async def execute(self, query: str, *args: Any) -> Any:
        if not self._active:
            raise RuntimeError("Transaction not active")
        return await self._execute_raw(query, *args)


def transaction(func: Any) -> Any:
    """Inject a transaction into an async instance method."""
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        async with self._db.transaction() as current:
            kwargs["transaction"] = current
            return await func(self, *args, **kwargs)
    return wrapper
