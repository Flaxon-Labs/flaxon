from __future__ import annotations

from typing import Any

from .errors import FieldError, ValidationError
from .fields import Field


class SchemaMeta(type):
    def __new__(mcls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]):
        inherited: dict[str, Field] = {}
        for base in bases:
            inherited.update(getattr(base, "__fields__", {}))
        declared = {key: value for key, value in namespace.items() if isinstance(value, Field)}
        for key in declared:
            namespace.pop(key)
        fields = {**inherited, **declared}
        for field_name, field in fields.items():
            field.bind(field_name)
        namespace["__fields__"] = fields
        return super().__new__(mcls, name, bases, namespace)


class Schema(metaclass=SchemaMeta):
    __fields__: dict[str, Field]

    def __init__(self, **values: Any) -> None:
        for name, value in values.items():
            setattr(self, name, value)

    @classmethod
    def load(cls, data: Any) -> "Schema":
        if not isinstance(data, dict):
            raise ValidationError({"body": ["Expected a JSON object."]})
        errors: dict[str, list[str]] = {}
        values: dict[str, Any] = {}
        for name, field in cls.__fields__.items():
            try:
                values[name] = field.deserialize(data.get(name))
            except FieldError as exc:
                errors.setdefault(name, []).append(str(exc))
        if errors:
            raise ValidationError(errors)
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name, None) for name in self.__fields__}
