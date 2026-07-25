
---

## docs/guides/databases.md

```markdown
# Databases

## Overview

Flaxon is database-agnostic. You can use any database, ORM, or driver that works with Python.

## Using SQLAlchemy

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, select

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@app.on_startup
async def startup():
    app.state.db = AsyncSessionLocal

@app.on_shutdown
async def shutdown():
    await engine.dispose()

@app.get("/users")
async def get_users():
    async with app.state.db() as session:
        result = await session.execute(select(User))
        return [user.to_dict() for user in result.scalars()]
    Using SQLAlchemy with Repository Pattern
python
from flaxon.database import Repository
from flaxon.database.adapters.sqlalchemy import SQLAlchemyAdapter

adapter = SQLAlchemyAdapter(DATABASE_URL)
db = DatabaseManager(adapter)

class UserRepository(Repository):
    def __init__(self, db):
        super().__init__(db, table_name="users")

    async def find_by_email(self, email: str):
        return await self.find_one_by("email", email)

repo = UserRepository(db)
Using asyncpg (PostgreSQL)
python
import asyncpg

@app.on_startup
async def startup():
    app.state.db = await asyncpg.create_pool(
        host="localhost",
        database="mydb",
        user="user",
        password="password",
    )

@app.on_shutdown
async def shutdown():
    await app.state.db.close()

@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    row = await app.state.db.fetchrow(
        "SELECT * FROM users WHERE id = $1", user_id
    )
    return dict(row) if row else None
Using SQLite (aiosqlite)
python
import aiosqlite

@app.on_startup
async def startup():
    app.state.db = await aiosqlite.connect("app.db")

@app.on_shutdown
async def shutdown():
    await app.state.db.close()

@app.get("/users")
async def get_users():
    cursor = await app.state.db.execute("SELECT * FROM users")
    rows = await cursor.fetchall()
    return [dict(zip(["id", "name"], row)) for row in rows]
Using MongoDB (Motor)
python
from motor.motor_asyncio import AsyncIOMotorClient

@app.on_startup
async def startup():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    app.state.db = client.mydb

@app.get("/users")
async def get_users():
    users = await app.state.db.users.find().to_list(100)
    return [{"id": str(user["_id"]), "name": user["name"]} for user in users]
Using Redis
python
import redis.asyncio as redis

@app.on_startup
async def startup():
    app.state.redis = redis.from_url("redis://localhost:6379")

@app.on_shutdown
async def shutdown():
    await app.state.redis.close()

@app.get("/cache/<key>")
async def get_cache(key: str):
    value = await app.state.redis.get(key)
    return {"key": key, "value": value}
Database Health Checks
python
from flaxon.health import DatabaseHealthCheck

db_check = DatabaseHealthCheck(db)
health.register(db_check)

@app.get("/health/db")
async def db_health():
    return await db_check.check()
Transactions
python
@app.post("/transfer")
async def transfer(request):
    async with app.state.db.transaction() as tx:
        await tx.execute("UPDATE accounts SET balance = balance - 100 WHERE id = $1", 1)
        await tx.execute("UPDATE accounts SET balance = balance + 100 WHERE id = $1", 2)
    return {"success": True}
Migrations
python
from flaxon.database import MigrationRunner

runner = MigrationRunner(db, "migrations")

# Generate a migration
version = await runner.generate_migration(
    name="create_users_table",
    up="""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    """,
)

# Apply migrations
await runner.migrate()

# Rollback
await runner.rollback(steps=1)
Database Connection Example
python
from flaxon import Flaxon
from flaxon.database import DatabaseManager
from flaxon.database.adapters.postgresql import PostgreSQLAdapter

app = Flaxon("db-demo")

# Setup
adapter = PostgreSQLAdapter(
    host="localhost",
    database="mydb",
    user="user",
    password="pass",
)
db = DatabaseManager(adapter)

@app.on_startup
async def startup():
    await db.initialize()

@app.on_shutdown
async def shutdown():
    await db.close()

@app.get("/users")
async def list_users():
    return await db.fetch_all("SELECT * FROM users")

@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    return await db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)

@app.post("/users")
async def create_user(request):
    data = await request.json()
    return await db.fetch_one(
        "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *",
        data["name"],
        data["email"],
    )