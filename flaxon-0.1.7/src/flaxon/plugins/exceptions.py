from __future__ import annotations

from flaxon.exceptions import FlaxonError


class PluginError(FlaxonError):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class PluginNotFoundError(PluginError):
    def __init__(self, message: str = "Plugin not found") -> None:
        super().__init__(message)


class PluginLoadError(PluginError):
    def __init__(self, message: str = "Failed to load plugin") -> None:
        super().__init__(message)


class PluginRegistrationError(PluginError):
    def __init__(self, message: str = "Failed to register plugin") -> None:
        super().__init__(message)


class PluginDiscoveryError(PluginError):
    def __init__(self, message: str = "Failed to discover plugin") -> None:
        super().__init__(message)
