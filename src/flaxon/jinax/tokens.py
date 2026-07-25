from __future__ import annotations

from enum import Enum


class TokenType(Enum):
    TEXT = "text"
    VARIABLE = "variable"
    STATEMENT = "statement"
    COMMENT = "comment"
    EOF = "eof"


class Token:
    def __init__(self, type: TokenType, value: str, line: int, column: int) -> None:
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self) -> str:
        return f"Token({self.type.value}, {self.value!r}, {self.line}, {self.column})"

    def __str__(self) -> str:
        return f"{self.type.value}: {self.value}"
