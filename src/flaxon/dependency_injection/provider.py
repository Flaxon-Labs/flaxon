from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class Provider(ABC):
    @abstractmethod
    def get(self, container: Any) -> Any:
        pass


class InstanceProvider(Provider):
    def __init__(self, instance: Any) -> None:
        self.instance = instance

    def get(self, container: Any) -> Any:
        return self.instance


class FactoryProvider(Provider):
    def __init__(self, factory: Callable[..., Any]) -> None:
        self.factory = factory

    def get(self, container: Any) -> Any:
        return self.factory()


class SingletonProvider(Provider):
    def __init__(self, factory: Callable[..., Any]) -> None:
        self.factory = factory
        self._instance = None

    def get(self, container: Any) -> Any:
        if self._instance is None:
            self._instance = self.factory()
        return self._instance


class CallableProvider(Provider):
    def __init__(self, callable_obj: Callable) -> None:
        self.callable_obj = callable_obj

    def get(self, container: Any) -> Any:
        return self.callable_obj


class LazyProvider(Provider):
    def __init__(self, import_path: str) -> None:
        self.import_path = import_path
        self._instance = None

    def get(self, container: Any) -> Any:
        if self._instance is None:
            self._instance = self._import()
        return self._instance

    def _import(self) -> Any:
        from flaxon.utils.import_string import import_string
        return import_string(self.import_path)


class ContextualProvider(Provider):
    def __init__(self, provider: Provider, context_provider: Callable[[], bool]) -> None:
        self.provider = provider
        self.context_provider = context_provider

    def get(self, container: Any) -> Any:
        if self.context_provider():
            return self.provider.get(container)
        return None


class DecoratedProvider(Provider):
    def __init__(self, provider: Provider, decorator: Callable[[Any], Any]) -> None:
        self.provider = provider
        self.decorator = decorator

    def get(self, container: Any) -> Any:
        instance = self.provider.get(container)
        return self.decorator(instance)
