from __future__ import annotations

from typing import Any


class FlaxonError(Exception):
    """Base class for framework errors."""


class HTTPException(FlaxonError):
    def __init__(
        self,
        status_code: int,
        detail: str,
        *,
        code: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.code = code or f"FX-HTTP-{status_code}"
        self.headers = headers or {}
        self.extra = extra or {}


class NotFound(HTTPException):
    def __init__(self, detail: str = "The requested resource was not found.") -> None:
        super().__init__(404, detail, code="FX-HTTP-404")


class MethodNotAllowed(HTTPException):
    def __init__(self, allowed: set[str]) -> None:
        headers = {"Allow": ", ".join(sorted(allowed))}
        super().__init__(405, "The HTTP method is not allowed for this route.", headers=headers)


class ConfigurationError(FlaxonError):
    pass
