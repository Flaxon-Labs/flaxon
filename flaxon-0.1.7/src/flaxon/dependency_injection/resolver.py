from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

from .exceptions import DependencyNotFoundError


class Resolver:
    def __init__(self, container: Any) -> None:
        self.container = container

    def resolve(self, func: Callable) -> dict[str, Any]:
        signature = inspect.signature(func)
        params = {}

        for name, param in signature.parameters.items():
            annotation = param.annotation

            if self.container.has(name):
                params[name] = self.container.get(name)
            elif annotation is not inspect.Parameter.empty:
                try:
                    params[name] = self.container.get(annotation.__name__)
                except DependencyNotFoundError:
                    pass

        return params

    def resolve_parameter(self, name: str, annotation: Any) -> Any:
        if self.container.has(name):
            return self.container.get(name)

        if annotation is not inspect.Parameter.empty:
            try:
                return self.container.get(annotation.__name__)
            except DependencyNotFoundError:
                pass

        raise DependencyNotFoundError(f"Cannot resolve parameter '{name}'")

    def resolve_dependencies(self, dependencies: dict[str, Any]) -> dict[str, Any]:
        result = {}

        for name, dep in dependencies.items():
            if isinstance(dep, str):
                result[name] = self.container.get(dep)
            elif isinstance(dep, type):
                result[name] = self.container.get(dep.__name__)
            else:
                result[name] = dep

        return result

    def get_dependencies(self, func: Callable) -> dict[str, Any]:
        signature = inspect.signature(func)
        deps = {}

        for name, param in signature.parameters.items():
            annotation = param.annotation

            if self.container.has(name):
                deps[name] = self.container.get(name)
            elif annotation is not inspect.Parameter.empty:
                try:
                    deps[name] = self.container.get(annotation.__name__)
                except DependencyNotFoundError:
                    deps[name] = param.default

        return deps
