"""
Route parameter handling for Flaxon.

This module provides utilities for working with route parameters
including extraction, validation, and conversion.
"""

from __future__ import annotations

import re
from typing import Any

from .converters import CONVERTERS


class Parameter:
    """
    Route parameter definition.

    Attributes:
        name: The parameter name.
        type: The parameter type (converter name).
        converter: The converter object.
    """

    def __init__(self, name: str, type_name: str = "str") -> None:
        """
        Initialize the parameter.

        Args:
            name: The parameter name.
            type_name: The parameter type (converter name).
        """
        self.name = name
        self.type = type_name

        if type_name not in CONVERTERS:
            raise ValueError(f"Unknown parameter type: {type_name}")

        self.converter = CONVERTERS[type_name]

    def convert(self, value: str) -> Any:
        """
        Convert a string value to the parameter type.

        Args:
            value: The string value.

        Returns:
            The converted value.
        """
        return self.converter.cast(value)

    def matches(self, value: str) -> bool:
        """
        Check if a string value matches the parameter pattern.

        Args:
            value: The string value.

        Returns:
            True if the value matches, False otherwise.
        """
        return bool(re.fullmatch(self.converter.regex, value))

    def __repr__(self) -> str:
        """Return a string representation of the parameter."""
        return f"Parameter({self.name}:{self.type})"


def parse_parameters(path: str) -> list[Parameter]:
    """
    Parse parameters from a path pattern.

    Args:
        path: The path pattern.

    Returns:
        A list of Parameter objects.
    """
    parameters: list[Parameter] = []

    for match in re.finditer(r"<(?:(?P<type>[a-zA-Z_][a-zA-Z0-9_]*):)?(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)>", path):
        type_name = match.group("type") or "str"
        name = match.group("name")
        parameters.append(Parameter(name, type_name))

    for match in re.finditer(r"\{(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)(?::(?P<type>[a-zA-Z_][a-zA-Z0-9_]*))?\}", path):
        name = match.group("name")
        type_name = match.group("type") or "str"
        parameters.append(Parameter(name, type_name))

    return parameters


def extract_parameters(path: str, values: dict[str, str]) -> dict[str, Any]:
    """
    Extract and convert parameters from a path.

    Args:
        path: The path pattern.
        values: The raw parameter values.

    Returns:
        A dictionary of converted parameter values.
    """
    params = parse_parameters(path)
    result: dict[str, Any] = {}

    for param in params:
        if param.name in values:
            result[param.name] = param.convert(values[param.name])

    return result


def validate_parameters(path: str, values: dict[str, str]) -> bool:
    """
    Validate parameter values against a path pattern.

    Args:
        path: The path pattern.
        values: The raw parameter values.

    Returns:
        True if all parameters are valid, False otherwise.
    """
    params = parse_parameters(path)

    for param in params:
        if param.name not in values:
            return False
        if not param.matches(values[param.name]):
            return False

    return True
