from __future__ import annotations

from typing import Any


class Node:
    def __init__(self, type: str, value: Any) -> None:
        self.type = type
        self.value = value

    def __repr__(self) -> str:
        return f"Node({self.type}, {self.value!r})"


class TextNode(Node):
    def __init__(self, value: str) -> None:
        super().__init__("text", value)


class VariableNode(Node):
    def __init__(self, value: str) -> None:
        super().__init__("variable", value)


class StatementNode(Node):
    def __init__(self, value: str) -> None:
        super().__init__("statement", value)


class CommentNode(Node):
    def __init__(self, value: str) -> None:
        super().__init__("comment", value)


class IfNode(Node):
    def __init__(self, condition: str, body: list[Node], else_body: list[Node] | None = None) -> None:
        super().__init__("if", condition)
        self.body = body
        self.else_body = else_body


class ForNode(Node):
    def __init__(self, target: str, iterable: str, body: list[Node], else_body: list[Node] | None = None) -> None:
        super().__init__("for", f"{target} in {iterable}")
        self.target = target
        self.iterable = iterable
        self.body = body
        self.else_body = else_body


class BlockNode(Node):
    def __init__(self, name: str, body: list[Node]) -> None:
        super().__init__("block", name)
        self.name = name
        self.body = body


class ExtendsNode(Node):
    def __init__(self, template: str) -> None:
        super().__init__("extends", template)


class IncludeNode(Node):
    def __init__(self, template: str) -> None:
        super().__init__("include", template)
