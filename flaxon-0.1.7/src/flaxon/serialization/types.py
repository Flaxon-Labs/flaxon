from __future__ import annotations

from typing import Any


class SerializationError(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class UnsupportedTypeError(SerializationError):
    def __init__(self, type_name: str, message: str | None = None) -> None:
        msg = message or f"Unsupported type: {type_name}"
        super().__init__(msg)
        self.type_name = type_name


class Serializer:
    def __init__(self, encoder: Any, decoder: Any, content_type: str = "application/json") -> None:
        self.encoder = encoder
        self.decoder = decoder
        self.content_type = content_type

    def serialize(self, data: Any) -> Any:
        return self.encoder.encode(data)

    def deserialize(self, data: Any) -> Any:
        return self.decoder.decode(data)


class SerializerRegistry:
    def __init__(self) -> None:
        self._serializers: dict[str, Serializer] = {}
        self._default: Serializer | None = None

    def register(self, name: str, serializer: Serializer) -> None:
        self._serializers[name] = serializer

    def get(self, name: str) -> Serializer | None:
        return self._serializers.get(name)

    def set_default(self, serializer: Serializer) -> None:
        self._default = serializer

    def serialize(self, data: Any, name: str | None = None) -> Any:
        if name and name in self._serializers:
            return self._serializers[name].serialize(data)
        if self._default:
            return self._default.serialize(data)
        raise ValueError("No serializer registered")

    def deserialize(self, data: Any, name: str | None = None) -> Any:
        if name and name in self._serializers:
            return self._serializers[name].deserialize(data)
        if self._default:
            return self._default.deserialize(data)
        raise ValueError("No serializer registered")
