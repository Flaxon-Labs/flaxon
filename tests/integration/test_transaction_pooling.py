import pytest

from flaxon.database import DatabaseManager


class RecordingConnection:
    def __init__(self) -> None:
        self.events: list[str] = []

    async def begin(self) -> None:
        self.events.append("BEGIN")

    async def commit(self) -> None:
        self.events.append("COMMIT")

    async def execute(self, query: str, *args: object) -> None:
        self.events.append(query)


class RecordingPool:
    def __init__(self) -> None:
        self.connections = [RecordingConnection(), RecordingConnection()]
        self.available = list(self.connections)

    async def acquire(self) -> RecordingConnection:
        return self.available.pop(0)

    async def release(self, connection: RecordingConnection) -> None:
        self.available.append(connection)


@pytest.mark.asyncio
async def test_nested_pooled_transaction_reuses_outer_connection():
    pool = RecordingPool()
    database = DatabaseManager(pool)

    async with database.transaction():
        async with database.transaction():
            pass

    assert pool.connections[0].events == [
        "BEGIN",
        "SAVEPOINT flaxon_tx_1",
        "RELEASE SAVEPOINT flaxon_tx_1",
        "COMMIT",
    ]
    assert pool.connections[1].events == []
