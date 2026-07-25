from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Converter:
    regex: str
    cast: Callable[[str], Any]


CONVERTERS: dict[str, Converter] = {
    "str": Converter(r"[^/]+", str),
    "int": Converter(r"-?\d+", int),
    "float": Converter(r"-?(?:\d+(?:\.\d*)?|\.\d+)", float),
    "path": Converter(r".+", str),
    "uuid": Converter(r"[0-9a-fA-F-]{36}", uuid.UUID),
}
