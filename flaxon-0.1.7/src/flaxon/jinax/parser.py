from __future__ import annotations

from typing import Any

from .nodes import Node, StatementNode, TextNode, VariableNode
from .tokens import Token, TokenType


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.position = 0

    def parse(self) -> list[Node]:
        nodes = []

        while self.position < len(self.tokens) - 1:
            token = self.tokens[self.position]

            if token.type == TokenType.TEXT:
                nodes.append(TextNode(token.value))
                self.position += 1
            elif token.type == TokenType.VARIABLE:
                nodes.append(VariableNode(token.value))
                self.position += 1
            elif token.type == TokenType.STATEMENT:
                nodes.append(StatementNode(token.value))
                self.position += 1
            elif token.type == TokenType.COMMENT:
                self.position += 1
            else:
                self.position += 1

        return nodes

    def parse_expression(self, expr: str) -> Any:
        return expr
