import json

import pytest

pytest.importorskip("aiosqlite")

from flaxon.admin.migrations import write_admin_migration
from flaxon.database import DatabaseManager, MigrationRunner
from flaxon.database.adapters.sqlite import SQLiteAdapter


@pytest.mark.asyncio
async def test_admin_migration_applies_and_rolls_back_on_sqlite(tmp_path):
    migration_path = write_admin_migration(tmp_path / "migrations")
    assert json.loads(migration_path.read_text(encoding="utf-8"))["name"] == "flaxon_admin"

    database = DatabaseManager(SQLiteAdapter(str(tmp_path / "admin.db")))
    await database.initialize()
    runner = MigrationRunner(database, str(tmp_path / "migrations"))

    applied = await runner.migrate()
    assert len(applied) == 1
    assert await database.fetch_val("SELECT COUNT(*) FROM flaxon_admin_users") == 0
    assert await database.fetch_val("SELECT COUNT(*) FROM flaxon_cms_menus") == 0

    rolled_back = await runner.rollback()
    assert rolled_back == applied
    assert await database.fetch_val(
        "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'flaxon_admin_users'"
    ) == 0
    await database.close()
