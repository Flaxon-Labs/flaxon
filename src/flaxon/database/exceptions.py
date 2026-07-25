from __future__ import annotations

from flaxon.exceptions import FlaxonError


class DatabaseError(FlaxonError):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class ConnectionError(DatabaseError):
    def __init__(self, message: str = "Database connection error") -> None:
        super().__init__(message)


class QueryError(DatabaseError):
    def __init__(self, message: str = "Database query error", query: str | None = None) -> None:
        super().__init__(message)
        self.query = query


class TransactionError(DatabaseError):
    def __init__(self, message: str = "Transaction error") -> None:
        super().__init__(message)


class MigrationError(DatabaseError):
    def __init__(self, message: str = "Migration error") -> None:
        super().__init__(message)


class IntegrityError(DatabaseError):
    def __init__(self, message: str = "Integrity constraint violated") -> None:
        super().__init__(message)


class NotFoundError(DatabaseError):
    def __init__(self, message: str = "Record not found") -> None:
        super().__init__(message)


class DuplicateError(DatabaseError):
    def __init__(self, message: str = "Duplicate record") -> None:
        super().__init__(message)
