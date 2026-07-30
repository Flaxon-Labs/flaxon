"""
Application registry for managing components.

This module provides a registry for managing application components,
services, and dependencies.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class Registry:
    """
    A simple component registry for managing application services.

    This registry allows registering, retrieving, and managing components
    by name or type.
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._components: dict[str, Any] = {}
        self._factories: dict[str, Callable[..., Any]] = {}
        self._singletons: dict[str, bool] = {}

    def register(
        self,
        name: str,
        component: Any,
        *,
        singleton: bool = True,
    ) -> None:
        """Register a component."""
        self._components[name] = component
        self._singletons[name] = singleton

    def register_factory(
        self,
        name: str,
        factory: Callable[..., Any],
        *,
        singleton: bool = True,
    ) -> None:
        """Register a component factory."""
        self._factories[name] = factory
        self._singletons[name] = singleton

    def get(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Get a component by name."""
        if name in self._factories:
            factory = self._factories[name]
            if self._singletons.get(name, True):
                if name not in self._components:
                    self._components[name] = factory(*args, **kwargs)
                return self._components[name]
            return factory(*args, **kwargs)

        if name not in self._components:
            raise KeyError(f"Component '{name}' not found in registry")

        return self._components[name]

    def get_optional(self, name: str, default: Any = None) -> Any:
        """Get a component by name, returning a default if not found."""
        try:
            return self.get(name)
        except KeyError:
            return default

    def has(self, name: str) -> bool:
        """Check if a component is registered."""
        return name in self._components or name in self._factories

    def remove(self, name: str) -> None:
        """Remove a component from the registry."""
        self._components.pop(name, None)
        self._factories.pop(name, None)
        self._singletons.pop(name, None)

    def clear(self) -> None:
        """Clear all components from the registry."""
        self._components.clear()
        self._factories.clear()
        self._singletons.clear()

    def keys(self) -> list[str]:
        """Get all registered component names."""
        return list(set(self._components.keys()) | set(self._factories.keys()))

    def values(self) -> list[Any]:
        """Get all registered component instances."""
        return list(self._components.values())

    def items(self) -> list[tuple[str, Any]]:
        """Get all registered component items."""
        return list(self._components.items())

    def __contains__(self, name: str) -> bool:
        """Check if a component is registered."""
        return self.has(name)

    def __getitem__(self, name: str) -> Any:
        """Get a component by name."""
        return self.get(name)

    def __setitem__(self, name: str, component: Any) -> None:
        """Register a component."""
        self.register(name, component)

    def __delitem__(self, name: str) -> None:
        """Remove a component."""
        self.remove(name)

    def __len__(self) -> int:
        """Get the number of registered components."""
        return len(self.keys())


class ServiceRegistry(Registry):
    """Extended registry with service-specific features."""

    def __init__(self) -> None:
        """Initialize the service registry."""
        super().__init__()
        self._dependencies: dict[str, list[str]] = {}
        self._startup_hooks: list[Callable[[], None]] = []
        self._shutdown_hooks: list[Callable[[], None]] = []

    def register_service(
        self,
        name: str,
        service: Any,
        *,
        dependencies: list[str] | None = None,
        startup: Callable[[], None] | None = None,
        shutdown: Callable[[], None] | None = None,
    ) -> None:
        """Register a service with dependencies and lifecycle hooks."""
        self.register(name, service)
        if dependencies:
            self._dependencies[name] = dependencies
        if startup:
            self._startup_hooks.append(startup)
        if shutdown:
            self._shutdown_hooks.append(shutdown)

    def resolve_dependencies(self, name: str) -> list[Any]:
        """Resolve dependencies for a service."""
        deps = self._dependencies.get(name, [])
        return [self.get(dep) for dep in deps]

    def startup(self) -> None:
        """Run all startup hooks."""
        for hook in self._startup_hooks:
            hook()

    def shutdown(self) -> None:
        """Run all shutdown hooks."""
        for hook in reversed(self._shutdown_hooks):
            hook()
