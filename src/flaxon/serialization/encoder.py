from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Encoder(ABC):
    @abstractmethod
    def encode(self, data: Any) -> Any:
        pass


class EncoderChain:
    def __init__(self, encoders: list[Encoder] | None = None) -> None:
        self.encoders = encoders or []

    def add(self, encoder: Encoder) -> EncoderChain:
        self.encoders.append(encoder)
        return self

    def encode(self, data: Any) -> Any:
        result = data
        for encoder in self.encoders:
            result = encoder.encode(result)
        return result


class EncoderRegistry:
    def __init__(self) -> None:
        self._encoders: dict[str, Encoder] = {}
        self._default_encoder: Encoder | None = None

    def register(self, name: str, encoder: Encoder) -> None:
        self._encoders[name] = encoder

    def get(self, name: str) -> Encoder | None:
        return self._encoders.get(name)

    def set_default(self, encoder: Encoder) -> None:
        self._default_encoder = encoder

    def encode(self, data: Any, name: str | None = None) -> Any:
        if name and name in self._encoders:
            return self._encoders[name].encode(data)
        if self._default_encoder:
            return self._default_encoder.encode(data)
        raise ValueError("No encoder registered")
