from __future__ import annotations

from .discovery import PluginDiscovery
from .exceptions import PluginError, PluginLoadError, PluginNotFoundError, PluginRegistrationError
from .hooks import PluginHook, PluginHooks
from .manager import PluginManager
from .plugin import Plugin, SimplePlugin
from .registry import PluginRegistry

__all__ = [
    "Plugin",
    "PluginDiscovery",
    "PluginError",
    "PluginHook",
    "PluginHooks",
    "PluginLoadError",
    "PluginManager",
    "PluginNotFoundError",
    "PluginRegistrationError",
    "PluginRegistry",
    "SimplePlugin",
]
