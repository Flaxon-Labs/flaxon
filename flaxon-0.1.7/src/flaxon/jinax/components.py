from __future__ import annotations

from typing import Any


class Component:
    def __init__(self, name: str, template: str) -> None:
        self.name = name
        self.template = template
        self._slots: dict[str, str] = {}

    def render(self, context: dict[str, Any]) -> str:
        return self.template.format(**context)

    def slot(self, name: str, content: str) -> None:
        self._slots[name] = content


class ComponentRegistry:
    def __init__(self) -> None:
        self._components: dict[str, Component] = {}

    def register(self, component: Component) -> None:
        self._components[component.name] = component

    def get(self, name: str) -> Component | None:
        return self._components.get(name)

    def render(self, name: str, context: dict[str, Any]) -> str:
        component = self.get(name)
        if component is None:
            return ""
        return component.render(context)

    def list_components(self) -> list[str]:
        return list(self._components.keys())


class ComponentLoader:
    def __init__(self, directory: str) -> None:
        self.directory = directory
        self.registry = ComponentRegistry()

    def load_components(self) -> None:
        from pathlib import Path

        path = Path(self.directory)
        if not path.exists():
            return

        for file in path.glob("*.html"):
            name = file.stem
            with open(file, encoding="utf-8") as f:
                content = f.read()
            self.registry.register(Component(name, content))
