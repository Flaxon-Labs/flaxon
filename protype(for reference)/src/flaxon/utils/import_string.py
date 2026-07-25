from __future__ import annotations

import importlib
from typing import Any


def import_string(value: str) -> Any:
    """Import an object from a ``module:attribute`` string."""
    if ":" not in value:
        raise ValueError("Import string must use the form 'module:attribute'.")
    module_name, attribute = value.split(":", 1)
    module = importlib.import_module(module_name)
    return getattr(module, attribute)
