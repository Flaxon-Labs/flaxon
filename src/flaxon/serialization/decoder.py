from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Decoder(ABC):
    @abstractmethod
    def decode(self, data: Any) -> Any:
        pass


class DecoderChain:
    def __init__(self, decoders: list[Decoder] | None = None) -> None:
        self.decoders = decoders or []

    def add(self, decoder: Decoder) -> DecoderChain:
        self.decoders.append(decoder)
        return self

    def decode(self, data: Any) -> Any:
        result = data
        for decoder in self.decoders:
            result = decoder.decode(result)
        return result


class DecoderRegistry:
    def __init__(self) -> None:
        self._decoders: dict[str, Decoder] = {}
        self._default_decoder: Decoder | None = None

    def register(self, name: str, decoder: Decoder) -> None:
        self._decoders[name] = decoder

    def get(self, name: str) -> Decoder | None:
        return self._decoders.get(name)

    def set_default(self, decoder: Decoder) -> None:
        self._default_decoder = decoder

    def decode(self, data: Any, name: str | None = None) -> Any:
        if name and name in self._decoders:
            return self._decoders[name].decode(data)
        if self._default_decoder:
            return self._default_decoder.decode(data)
        raise ValueError("No decoder registered")
