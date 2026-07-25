"""
Trie-based router for Flaxon.

This module provides a trie-based route matcher for efficient
route lookup and matching.
"""

from __future__ import annotations

import re
from typing import Any


class TrieNode:
    """
    Node in the route trie.

    Attributes:
        children: Child nodes.
        route: The route associated with this node.
        is_endpoint: Whether this node is an endpoint.
        params: Parameter names for this node.
    """

    def __init__(self) -> None:
        """Initialize a trie node."""
        self.children: dict[str, TrieNode] = {}
        self.route: Any = None
        self.is_endpoint: bool = False
        self.params: list[str] = []


class TrieRouter:
    """
    Trie-based router for efficient route matching.

    This router uses a trie data structure for O(n) route lookup
    where n is the length of the path.

    Example:
        ```python
        router = TrieRouter()

        @router.get("/users")
        async def list_users():
            return [{"id": 1}]

        @router.get("/users/<int:user_id>")
        async def get_user(user_id: int):
            return {"id": user_id}
        ```
    """

    def __init__(self) -> None:
        """Initialize the trie router."""
        self.root = TrieNode()
        self.routes: list[Any] = []

    def add_route(self, path: str, route: Any) -> None:
        """
        Add a route to the trie.

        Args:
            path: The path pattern.
            route: The route object.
        """
        node = self.root
        segments = self._split_path(path)

        for segment in segments:
            if segment not in node.children:
                node.children[segment] = TrieNode()
            node = node.children[segment]

        node.route = route
        node.is_endpoint = True
        node.params = self._extract_params(path)
        self.routes.append(route)

    def match(self, path: str) -> tuple[Any, dict[str, str]]:
        """
        Match a path against the trie.

        Args:
            path: The path to match.

        Returns:
            A tuple of (route, parameters).

        Raises:
            ValueError: If no route matches the path.
        """
        node = self.root
        segments = self._split_path(path)
        params: dict[str, str] = {}

        for segment in segments:
            # Try exact match first
            if segment in node.children:
                node = node.children[segment]
                continue

            # Try parameter matching
            matched = False
            for key, child in node.children.items():
                if key.startswith("<") or key.startswith("{"):
                    param_name = self._extract_param_name(key)
                    params[param_name] = segment
                    node = child
                    matched = True
                    break

            if not matched:
                raise ValueError(f"No route matches path: {path}")

        if not node.is_endpoint:
            raise ValueError(f"No route matches path: {path}")

        return node.route, params

    def _split_path(self, path: str) -> list[str]:
        """Split a path into segments."""
        path = path.strip("/")
        return path.split("/") if path else []

    def _extract_params(self, path: str) -> list[str]:
        """Extract parameter names from a path."""
        params = []
        for match in re.finditer(
            r"<(?:[a-zA-Z_][a-zA-Z0-9_]*:)?([a-zA-Z_][a-zA-Z0-9_]*)>", path
        ):
            params.append(match.group(1))
        for match in re.finditer(
            r"{([a-zA-Z_][a-zA-Z0-9_]*)(?::[a-zA-Z_][a-zA-Z0-9_]*)?}", path
        ):
            params.append(match.group(1))
        return params

    def _extract_param_name(self, segment: str) -> str:
        """Extract parameter name from a segment pattern."""
        match = re.search(
            r"<(?:[a-zA-Z_][a-zA-Z0-9_]*:)?([a-zA-Z_][a-zA-Z0-9_]*)>", segment
        )
        if match:
            return match.group(1)

        match = re.search(
            r"{([a-zA-Z_][a-zA-Z0-9_]*)(?::[a-zA-Z_][a-zA-Z0-9_]*)?}", segment
        )
        if match:
            return match.group(1)

        return segment

    def get_routes(self) -> list[Any]:
        """Get all registered routes."""
        return self.routes

    def clear(self) -> None:
        """Clear all routes."""
        self.root = TrieNode()
        self.routes.clear()
