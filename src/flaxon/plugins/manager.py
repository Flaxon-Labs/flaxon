from __future__ import annotations

from typing import Any

from .discovery import PluginDiscovery
from .exceptions import PluginLoadError, PluginNotFoundError
from .hooks import PluginHooks
from .plugin import Plugin
from .registry import PluginRegistry


class PluginManager:
    def __init__(self, app: Any, registry: PluginRegistry | None = None) -> None:
        self.app = app
        self.registry = registry or PluginRegistry()
        self.hooks = PluginHooks()
        self.discovery = PluginDiscovery(self.registry)

    async def load_plugin(self, plugin: Plugin) -> None:
        if plugin.name in self.registry:
            raise PluginLoadError(f"Plugin '{plugin.name}' is already loaded")

        if plugin.requires:
            for required in plugin.requires:
                if not self.registry.has(required):
                    raise PluginLoadError(f"Required plugin '{required}' not found for '{plugin.name}'")

        self.registry.register(plugin)
        plugin.on_load()

        try:
            plugin.setup(self.app)
            self.hooks.trigger("after_load", plugin)
        except Exception as exc:
            self.registry.unregister(plugin.name)
            raise PluginLoadError(f"Failed to setup plugin '{plugin.name}': {exc}") from exc

    async def load_plugins_from_path(self, path: str) -> None:
        plugins = self.discovery.discover_from_path(path)
        for plugin in plugins:
            await self.load_plugin(plugin)

    async def load_plugins_from_module(self, module: str) -> None:
        plugins = self.discovery.discover_from_module(module)
        for plugin in plugins:
            await self.load_plugin(plugin)

    async def load_all_plugins(self, paths: list[str] | None = None) -> None:
        plugins = self.discovery.discover_all(paths)
        for plugin in plugins:
            try:
                await self.load_plugin(plugin)
            except PluginLoadError:
                pass

    async def unload_plugin(self, name: str) -> None:
        plugin = self.registry.get(name)
        if plugin is None:
            raise PluginNotFoundError(f"Plugin '{name}' not found")

        plugin.on_unload()
        self.registry.unregister(name)
        self.hooks.trigger("after_unload", plugin)

    async def unload_all(self) -> None:
        for name in self.registry.list():
            await self.unload_plugin(name)

    def get_plugin(self, name: str) -> Plugin | None:
        return self.registry.get(name)

    def list_plugins(self) -> list[str]:
        return self.registry.list()

    def is_loaded(self, name: str) -> bool:
        return self.registry.has(name)

    def get_all_plugins(self) -> list[Plugin]:
        return self.registry.get_all()

    async def startup(self) -> None:
        for plugin in self.registry.get_all():
            plugin.on_startup()

    async def shutdown(self) -> None:
        for plugin in self.registry.get_all():
            plugin.on_shutdown()
