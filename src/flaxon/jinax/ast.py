from __future__ import annotations

from typing import Any


class ASTNode:
    def __init__(self, type: str, value: Any, children: list[ASTNode] | None = None) -> None:
        self.type = type
        self.value = value
        self.children = children or []

    def add_child(self, child: ASTNode) -> None:
        self.children.append(child)

    def __repr__(self) -> str:
        return f"ASTNode({self.type}, {self.value!r}, {len(self.children)} children)"


class ProgramNode(ASTNode):
    def __init__(self, body: list[ASTNode] | None = None) -> None:
        super().__init__("program", None, body or [])


class TextNode(ASTNode):
    def __init__(self, value: str) -> None:
        super().__init__("text", value)


class VariableNode(ASTNode):
    def __init__(self, value: str) -> None:
        super().__init__("variable", value)


class StatementNode(ASTNode):
    def __init__(self, value: str) -> None:
        super().__init__("statement", value)


class IfNode(ASTNode):
    def __init__(self, condition: str, body: list[ASTNode], else_body: list[ASTNode] | None = None) -> None:
        super().__init__("if", condition, body)
        self.else_body = else_body or []


class ForNode(ASTNode):
    def __init__(self, target: str, iterable: str, body: list[ASTNode], else_body: list[ASTNode] | None = None) -> None:
        super().__init__("for", f"{target} in {iterable}", body)
        self.target = target
        self.iterable = iterable
        self.else_body = else_body or []


class BlockNode(ASTNode):
    def __init__(self, name: str, body: list[ASTNode]) -> None:
        super().__init__("block", name, body)
        self.name = name


class ExtendsNode(ASTNode):
    def __init__(self, template: str) -> None:
        super().__init__("extends", template)


class IncludeNode(ASTNode):
    def __init__(self, template: str) -> None:
        super().__init__("include", template)
