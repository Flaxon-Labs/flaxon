import pytest
import pytest_asyncio

from flaxon.database import DatabaseManager
from flaxon.database.adapters.sqlite import SQLiteAdapter


@pytest_asyncio.fixture
async def db():
    adapter = SQLiteAdapter(database=":memory:")
    manager = DatabaseManager(adapter)
    await manager.initialize()

    await manager.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    """)

    yield manager

    await manager.close()


@pytest.mark.asyncio
async def test_transaction_commit(db):
    async with db.transaction() as tx:
        await tx.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            "Alice",
            "alice@example.com",
        )
        await tx.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            "Bob",
            "bob@example.com",
        )

    rows = await db.fetch_all("SELECT * FROM users ORDER BY id")
    assert len(rows) == 2
    assert rows[0]["name"] == "Alice"
    assert rows[1]["name"] == "Bob"


@pytest.mark.asyncio
async def test_transaction_rollback(db):
    try:
        async with db.transaction() as tx:
            await tx.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                "Alice",
                "alice@example.com",
            )
            await tx.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                "Bob",
                "bob@example.com",
            )
            raise ValueError("Something went wrong")
    except ValueError:
        pass

    rows = await db.fetch_all("SELECT * FROM users")
    assert len(rows) == 0


@pytest.mark.asyncio
async def test_transaction_nested(db):
    async with db.transaction() as tx1:
        await tx1.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            "Alice",
            "alice@example.com",
        )

        async with db.transaction() as tx2:
            await tx2.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                "Bob",
                "bob@example.com",
            )

    rows = await db.fetch_all("SELECT * FROM users ORDER BY id")
    assert len(rows) == 2


@pytest.mark.asyncio
async def test_transaction_rollback_nested(db):
    try:
        async with db.transaction() as tx1:
            await tx1.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                "Alice",
                "alice@example.com",
            )

            async with db.transaction() as tx2:
                await tx2.execute(
                    "INSERT INTO users (name, email) VALUES (?, ?)",
                    "Bob",
                    "bob@example.com",
                )
                raise ValueError("Error in nested transaction")
    except ValueError:
        pass

    rows = await db.fetch_all("SELECT * FROM users")
    assert len(rows) == 0


@pytest.mark.asyncio
async def test_transaction_manual_commit_rollback(db):
    tx = await db.transaction()
    await tx.begin()

    await tx.execute(
        "INSERT INTO users (name, email) VALUES (?, ?)",
        "Alice",
        "alice@example.com",
    )

    await tx.commit()
    await tx.close()

    rows = await db.fetch_all("SELECT * FROM users")
    assert len(rows) == 1
