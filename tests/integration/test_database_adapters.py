import importlib.util

import pytest

from flaxon.database.adapters.custom import CustomAdapter
from flaxon.database.adapters.sqlite import SQLiteAdapter


@pytest.mark.asyncio
async def test_sqlite_adapter_crud_placeholders_and_transactions():
    db = SQLiteAdapter(":memory:")
    await db.connect()
    try:
        assert await db.ping()
        await db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        await db.begin()
        await db.execute("INSERT INTO users (name) VALUES ($1)", "Ada")
        await db.rollback()
        assert await db.fetch_val("SELECT COUNT(*) FROM users") == 0

        await db.begin()
        await db.execute("INSERT INTO users (name) VALUES (?)", "Lin")
        await db.commit()
        assert await db.fetch_one("SELECT * FROM users WHERE id = $1", 1) == {"id": 1, "name": "Lin"}
        assert await db.fetch_all("SELECT * FROM users") == [{"id": 1, "name": "Lin"}]
    finally:
        await db.disconnect()


class _Connection:
    async def connect(self): self.connected = True
    async def close(self): self.closed = True
    async def execute(self, query, *args): return query, args
    async def fetch_one(self, query, *args): return {"query": query, "args": args}
    async def fetch_all(self, query, *args): return [await self.fetch_one(query, *args)]
    async def fetch_val(self, query, *args): return 1
    async def begin(self): self.began = True
    async def commit(self): self.committed = True
    async def rollback(self): self.rolled_back = True


@pytest.mark.asyncio
async def test_custom_adapter_delegates_connection_contract():
    connection = _Connection()
    db = CustomAdapter(connection)
    await db.connect()
    assert await db.execute("SELECT 1") == ("SELECT 1", ())
    assert await db.fetch_one("SELECT 1") == {"query": "SELECT 1", "args": ()}
    assert await db.fetch_all("SELECT 1") == [{"query": "SELECT 1", "args": ()}]
    assert await db.fetch_val("SELECT 1") == 1
    await db.begin(); await db.commit(); await db.rollback()
    assert await db.ping()
    await db.disconnect()


@pytest.mark.asyncio
async def test_sqlalchemy_adapter_works_with_local_sqlite():
    pytest.importorskip("sqlalchemy")
    from flaxon.database.adapters.sqlalchemy import SQLAlchemyAdapter

    db = SQLAlchemyAdapter("sqlite+aiosqlite:///:memory:")
    await db.connect()
    try:
        assert await db.ping()
        await db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        await db.execute("INSERT INTO users (name) VALUES ($1)", "Ada")
        assert await db.fetch_val("SELECT COUNT(*) FROM users") == 1
    finally:
        await db.disconnect()


@pytest.mark.parametrize(
    "module, adapter_module, class_name",
    [
        ("asyncpg", "postgresql", "PostgreSQLAdapter"),
        ("aiomysql", "mysql", "MySQLAdapter"),
        ("motor", "mongodb", "MongoDBAdapter"),
        ("redis", "redis", "RedisAdapter"),
    ],
)
def test_external_adapter_modules_have_optional_driver_contract(module, adapter_module, class_name):
    imported = importlib.util.find_spec(module) is not None
    adapter = __import__(f"flaxon.database.adapters.{adapter_module}", fromlist=[class_name])
    assert hasattr(adapter, class_name)
    if not imported:
        pytest.skip(f"optional driver {module} is not installed")
