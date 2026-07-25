from __future__ import annotations

from typing import Any

from flaxon.exceptions import HTTPException


class ValidationError(HTTPException):
    def __init__(self, fields: dict[str, list[str]]) -> None:
        super().__init__(
            422,
            "Request validation failed.",
            code="FX-VAL-001",
            extra={"fields": fields},
        )
        self.fields = fields


class FieldError(ValueError):
    pass
