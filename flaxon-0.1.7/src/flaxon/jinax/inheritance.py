from __future__ import annotations

from typing import Any


class InheritanceManager:
    def __init__(self) -> None:
        self._blocks: dict[str, list[dict[str, Any]]] = {}
        self._extends: dict[str, str] = {}

    def register_block(self, template: str, block_name: str, content: str) -> None:
        if template not in self._blocks:
            self._blocks[template] = []
        self._blocks[template].append({
            "name": block_name,
            "content": content,
        })

    def register_extends(self, template: str, parent: str) -> None:
        self._extends[template] = parent

    def get_parent(self, template: str) -> str | None:
        return self._extends.get(template)

    def get_block(self, template: str, block_name: str) -> str | None:
        blocks = self._blocks.get(template, [])
        for block in blocks:
            if block["name"] == block_name:
                return block["content"]
        return None

    def get_all_blocks(self, template: str) -> dict[str, str]:
        blocks = self._blocks.get(template, [])
        return {block["name"]: block["content"] for block in blocks}

    def resolve_inheritance(self, template: str) -> list[str]:
        chain = [template]
        current = template

        while True:
            parent = self.get_parent(current)
            if parent is None:
                break
            chain.append(parent)
            current = parent

        return chain

    def render_with_inheritance(self, template: str, context: dict[str, Any]) -> str:
        chain = self.resolve_inheritance(template)

        result = ""
        for tpl in reversed(chain):
            blocks = self.get_all_blocks(tpl)
            if not blocks:
                continue

        return result
