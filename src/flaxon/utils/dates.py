from __future__ import annotations

from datetime import UTC, date, datetime


def parse_datetime(value: str | int | float | datetime | None) -> datetime | None:
    """Parse a datetime from various formats."""
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=UTC)

    if isinstance(value, str):
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

    return None


def parse_date(value: str | date | datetime | None) -> date | None:
    """Parse a date from various formats."""
    if value is None:
        return None

    if isinstance(value, date):
        return value

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

    return None


def format_datetime(value: datetime | None, format: str = "%Y-%m-%dT%H:%M:%SZ") -> str | None:
    """Format a datetime as a string."""
    if value is None:
        return None
    return value.strftime(format)


def format_date(value: date | None, format: str = "%Y-%m-%d") -> str | None:
    """Format a date as a string."""
    if value is None:
        return None
    return value.strftime(format)


def format_timestamp(value: datetime | int | float | None) -> float | None:
    """Convert a datetime to a timestamp."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, datetime):
        return value.timestamp()

    return None


def now() -> datetime:
    """Get the current UTC datetime."""
    return datetime.now(UTC)


def today() -> date:
    """Get the current UTC date."""
    return now().date()


def isoformat(value: datetime | date | None) -> str | None:
    """Convert a datetime or date to ISO format."""
    if value is None:
        return None
    return value.isoformat()
