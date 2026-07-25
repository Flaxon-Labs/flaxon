from __future__ import annotations

import re
from typing import Any

from .errors import FieldError

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class Field:
    def __init__(self, *, required: bool = False, default: Any = None, nullable: bool = False) -> None:
        self.required = required
        self.default = default
        self.nullable = nullable
        self.name = ""

    def bind(self, name: str) -> None:
        self.name = name

    def deserialize(self, value: Any) -> Any:
        if value is None:
            if self.nullable:
                return None
            if self.required and self.default is None:
                raise FieldError("This field is required.")
            return self.default
        return value


class String(Field):
    def __init__(self, *, min_length: int | None = None, max_length: int | None = None, strip: bool = True, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.strip = strip

    def deserialize(self, value: Any) -> str | None:
        value = super().deserialize(value)
        if value is None:
            return None
        if not isinstance(value, str):
            raise FieldError("Expected a string.")
        value = value.strip() if self.strip else value
        if self.min_length is not None and len(value) < self.min_length:
            raise FieldError(f"Must contain at least {self.min_length} characters.")
        if self.max_length is not None and len(value) > self.max_length:
            raise FieldError(f"Must contain no more than {self.max_length} characters.")
        return value


class Email(String):
    def deserialize(self, value: Any) -> str | None:
        value = super().deserialize(value)
        if value is not None and not EMAIL_RE.match(value):
            raise FieldError("Enter a valid email address.")
        return value


class Integer(Field):
    def __init__(self, *, minimum: int | None = None, maximum: int | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.minimum = minimum
        self.maximum = maximum

    def deserialize(self, value: Any) -> int | None:
        value = super().deserialize(value)
        if value is None:
            return None
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise FieldError("Expected an integer.") from exc
        if self.minimum is not None and number < self.minimum:
            raise FieldError(f"Must be at least {self.minimum}.")
        if self.maximum is not None and number > self.maximum:
            raise FieldError(f"Must be no greater than {self.maximum}.")
        return number


class Float(Field):
    def deserialize(self, value: Any) -> float | None:
        value = super().deserialize(value)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise FieldError("Expected a number.") from exc


class Boolean(Field):
    TRUE_VALUES = {True, 1, "1", "true", "yes", "on"}
    FALSE_VALUES = {False, 0, "0", "false", "no", "off"}

    def deserialize(self, value: Any) -> bool | None:
        value = super().deserialize(value)
        if value is None:
            return None
        normalized = value.lower() if isinstance(value, str) else value
        if normalized in self.TRUE_VALUES:
            return True
        if normalized in self.FALSE_VALUES:
            return False
        raise FieldError("Expected a boolean value.")


class Choice(Field):
    def __init__(self, choices: list[Any] | tuple[Any, ...] | set[Any], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.choices = set(choices)

    def deserialize(self, value: Any) -> Any:
        value = super().deserialize(value)
        if value is not None and value not in self.choices:
            values = ", ".join(map(str, sorted(self.choices, key=str)))
            raise FieldError(f"Choose one of: {values}.")
        return value
