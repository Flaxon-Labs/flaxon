from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, TypeVar

from .schema import Schema

T = TypeVar("T")


class Serializer:
    def __init__(self) -> None:
        self._serializers: dict[type, Callable[[Any], Any]] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(str, lambda v: v)
        self.register(int, lambda v: v)
        self.register(float, lambda v: v)
        self.register(bool, lambda v: v)
        self.register(list, lambda v: [self.serialize(item) for item in v])
        self.register(dict, lambda v: {k: self.serialize(v) for k, v in v.items()})
        self.register(date, lambda v: v.isoformat())
        self.register(datetime, lambda v: v.isoformat())
        self.register(Decimal, lambda v: float(v))
        self.register(Enum, lambda v: v.value)

    def register(self, type_: type, serializer: Callable[[Any], Any]) -> None:
        self._serializers[type_] = serializer

    def serialize(self, value: Any) -> Any:
        if value is None:
            return None

        value_type = type(value)

        if value_type in self._serializers:
            return self._serializers[value_type](value)

        if isinstance(value, Schema):
            return value.to_dict()

        if hasattr(value, "to_dict"):
            return value.to_dict()

        if hasattr(value, "to_json"):
            return value.to_json()

        if hasattr(value, "model_dump"):
            return value.model_dump()

        if isinstance(value, (list, tuple)):
            return [self.serialize(item) for item in value]

        if isinstance(value, dict):
            return {k: self.serialize(v) for k, v in value.items()}

        if hasattr(value, "__dataclass_fields__"):
            return {k: self.serialize(getattr(value, k)) for k in value.__dataclass_fields__}

        for type_, serializer in self._serializers.items():
            if isinstance(value, type_):
                return serializer(value)

        return value

    def to_json(self, value: Any) -> str:
        return json.dumps(self.serialize(value), ensure_ascii=False, separators=(",", ":"))

    def to_json_pretty(self, value: Any, indent: int = 2) -> str:
        return json.dumps(self.serialize(value), ensure_ascii=False, indent=indent)


_default_serializer = Serializer()


def serialize(value: Any) -> Any:
    return _default_serializer.serialize(value)


def to_json(value: Any) -> str:
    return _default_serializer.to_json(value)


def to_json_pretty(value: Any, indent: int = 2) -> str:
    return _default_serializer.to_json_pretty(value, indent)


def register_serializer(type_: type, serializer: Callable[[Any], Any]) -> None:
    _default_serializer.register(type_, serializer)


class SerializerMixin:
    def to_dict(self) -> dict[str, Any]:
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                result[key] = serialize(value)
        return result

    def to_json(self) -> str:
        return to_json(self.to_dict())

    def to_json_pretty(self, indent: int = 2) -> str:
        return to_json_pretty(self.to_dict(), indent)
