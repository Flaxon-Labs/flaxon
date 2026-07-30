from __future__ import annotations

from .ast import ASTNode, BlockNode, ForNode, IfNode, ProgramNode, TextNode, VariableNode
from .nodes import Node


class Compiler:
    def __init__(self) -> None:
        self._output: list[str] = []
        self._indent = 0

    def compile(self, nodes: list[Node]) -> str:
        self._output = []
        self._indent = 0
        ast = self._build_ast(nodes)
        self._compile_node(ast)
        return "".join(self._output)

    def _build_ast(self, nodes: list[Node]) -> ProgramNode:
        program = ProgramNode()

        for node in nodes:
            if node.type == "text":
                program.add_child(TextNode(node.value))
            elif node.type == "variable":
                program.add_child(VariableNode(node.value))
            elif node.type == "statement":
                self._parse_statement(node.value, program)

        return program

    def _parse_statement(self, stmt: str, parent: ASTNode) -> None:
        parts = stmt.strip().split()
        if not parts:
            return

        if parts[0] == "if":
            condition = " ".join(parts[1:])
            if_node = IfNode(condition, [])
            parent.add_child(if_node)

        elif parts[0] == "for":
            if "in" in parts:
                target = parts[1]
                iterable = " ".join(parts[3:])
                for_node = ForNode(target, iterable, [])
                parent.add_child(for_node)

        elif parts[0] == "block":
            name = parts[1] if len(parts) > 1 else ""
            block_node = BlockNode(name, [])
            parent.add_child(block_node)

        elif parts[0] == "extends":
            template = " ".join(parts[1:])
            parent.add_child(ExtendsNode(template))

        elif parts[0] == "include":
            template = " ".join(parts[1:])
            parent.add_child(IncludeNode(template))

        elif parts[0] == "else" or parts[0] == "elif" or parts[0] == "endif" or parts[0] == "endfor" or parts[0] == "endblock":
            pass

    def _compile_node(self, node: ASTNode) -> None:
        if node.type == "program":
            for child in node.children:
                self._compile_node(child)

        elif node.type == "text":
            self._emit(node.value)

        elif node.type == "variable":
            self._emit(f"{{{{ {node.value} }}}}")

        elif node.type == "if":
            self._emit(f"{{% if {node.value} %}}")
            for child in node.children:
                self._compile_node(child)
            if hasattr(node, "else_body") and node.else_body:
                self._emit("{% else %}")
                for child in node.else_body:
                    self._compile_node(child)
            self._emit("{% endif %}")

        elif node.type == "for":
            self._emit(f"{{% for {node.target} in {node.iterable} %}}")
            for child in node.children:
                self._compile_node(child)
            if hasattr(node, "else_body") and node.else_body:
                self._emit("{% else %}")
                for child in node.else_body:
                    self._compile_node(child)
            self._emit("{% endfor %}")

        elif node.type == "block":
            self._emit(f"{{% block {node.name} %}}")
            for child in node.children:
                self._compile_node(child)
            self._emit("{% endblock %}")

        elif node.type == "extends":
            self._emit(f"{{% extends {node.value} %}}")

        elif node.type == "include":
            self._emit(f"{{% include {node.value} %}}")

    def _emit(self, text: str) -> None:
        if text:
            self._output.append(text)
            if text.endswith("\n"):
                self._indent = 0
