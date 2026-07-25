from __future__ import annotations

from typing import Any, Generic, TypeVar

from .manager import DatabaseManager

T = TypeVar("T")


class Repository(Generic[T]):
    def __init__(self, db: DatabaseManager, table_name: str) -> None:
        self.db = db
        self.table_name = table_name

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(data)))
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders}) RETURNING *"
        return await self.db.fetch_one(query, *data.values())

    async def get(self, id: Any, id_column: str = "id") -> dict[str, Any] | None:
        query = f"SELECT * FROM {self.table_name} WHERE {id_column} = $1"
        return await self.db.fetch_one(query, id)

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        query = f"SELECT * FROM {self.table_name} LIMIT ${1} OFFSET ${2}"
        return await self.db.fetch_all(query, limit, offset)

    async def update(self, id: Any, data: dict[str, Any], id_column: str = "id") -> dict[str, Any] | None:
        set_clause = ", ".join(f"{key} = ${i+2}" for i, key in enumerate(data.keys()))
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {id_column} = $1 RETURNING *"
        return await self.db.fetch_one(query, id, *data.values())

    async def delete(self, id: Any, id_column: str = "id") -> bool:
        query = f"DELETE FROM {self.table_name} WHERE {id_column} = $1"
        result = await self.db.execute(query, id)
        return True

    async def count(self) -> int:
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        return await self.db.fetch_val(query)

    async def exists(self, id: Any, id_column: str = "id") -> bool:
        query = f"SELECT EXISTS(SELECT 1 FROM {self.table_name} WHERE {id_column} = $1)"
        return bool(await self.db.fetch_val(query, id))

    async def find_by(self, column: str, value: Any) -> list[dict[str, Any]]:
        query = f"SELECT * FROM {self.table_name} WHERE {column} = $1"
        return await self.db.fetch_all(query, value)

    async def find_one_by(self, column: str, value: Any) -> dict[str, Any] | None:
        query = f"SELECT * FROM {self.table_name} WHERE {column} = $1 LIMIT 1"
        return await self.db.fetch_one(query, value)

    async def bulk_create(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not items:
            return []

        columns = list(items[0].keys())
        column_str = ", ".join(columns)
        placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))

        results = []
        for item in items:
            values = [item.get(col) for col in columns]
            query = f"INSERT INTO {self.table_name} ({column_str}) VALUES ({placeholders}) RETURNING *"
            result = await self.db.fetch_one(query, *values)
            results.append(result)

        return results

    async def bulk_update(self, items: list[dict[str, Any]], id_column: str = "id") -> list[dict[str, Any]]:
        results = []
        for item in items:
            id_value = item.get(id_column)
            if id_value is None:
                continue
            data = {k: v for k, v in item.items() if k != id_column}
            result = await self.update(id_value, data, id_column)
            results.append(result)
        return results

    async def delete_all(self) -> int:
        query = f"DELETE FROM {self.table_name}"
        result = await self.db.execute(query)
        return 0

    async def paginate(self, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        offset = (page - 1) * per_page
        items = await self.get_all(per_page, offset)
        total = await self.count()
        total_pages = (total + per_page - 1) // per_page

        return {
            "items": items,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
