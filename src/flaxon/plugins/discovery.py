from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any

from .plugin import Plugin
from .registry import PluginRegistry


class PluginDiscovery:
    def __init__(self, registry: PluginRegistry) -> None:
        self.registry = registry

    def discover_from_path(self, path: str) -> list[Plugin]:
        plugins = []
        path_obj = Path(path)

        if not path_obj.exists():
            return plugins

        for file_path in path_obj.glob("*.py"):
            if file_path.name.startswith("_"):
                continue

            module_name = file_path.stem

            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                plugin = self._extract_plugin(module)
                if plugin:
                    plugins.append(plugin)

            except Exception:
                continue

        return plugins

    def discover_from_module(self, module_name: str) -> list[Plugin]:
        plugins = []

        try:
            module = importlib.import_module(module_name)

            plugin = self._extract_plugin(module)
            if plugin:
                plugins.append(plugin)

        except Exception:
            pass

        return plugins

    def discover_all(self, paths: list[str] | None = None) -> list[Plugin]:
        plugins = []

        if paths:
            for path in paths:
                plugins.extend(self.discover_from_path(path))

        plugins.extend(self.discover_from_path("plugins"))

        return plugins

    def _extract_plugin(self, module: Any) -> Plugin | None:
        if hasattr(module, "plugin"):
            return module.plugin

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, Plugin):
                return attr

        if hasattr(module, "setup"):
            return self._create_simple_plugin(module)

        return None

    def _create_simple_plugin(self, module: Any) -> Plugin:
        name = getattr(module, "__name__", "unknown")
        version = getattr(module, "__version__", "0.1.0")
        description = getattr(module, "__doc__", "").strip() or ""

        from .plugin import SimplePlugin

        return SimplePlugin(
            name=name,
            setup_func=module.setup,
            version=version,
            description=description,
        )
