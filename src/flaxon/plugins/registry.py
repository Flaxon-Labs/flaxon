from __future__ import annotations

from typing import Any

from .plugin import Plugin


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin '{plugin.name}' is already registered")
        self._plugins[plugin.name] = plugin

    def unregister(self, name: str) -> None:
        if name in self._plugins:
            del self._plugins[name]

    def get(self, name: str) -> Plugin | None:
        return self._plugins.get(name)

    def has(self, name: str) -> bool:
        return name in self._plugins

    def list(self) -> list[str]:
        return list(self._plugins.keys())

    def get_all(self) -> list[Plugin]:
        return list(self._plugins.values())

    def clear(self) -> None:
        self._plugins.clear()

    def get_metadata(self) -> dict[str, dict[str, Any]]:
        return {
            name: plugin.get_metadata()
            for name, plugin in self._plugins.items()
        }

    def __len__(self) -> int:
        return len(self._plugins)

    def __contains__(self, name: str) -> bool:
        return self.has(name)

    def __iter__(self):
        return iter(self._plugins)
