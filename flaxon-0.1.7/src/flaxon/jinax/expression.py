from __future__ import annotations

import ast
import operator
from typing import Any


class ExpressionEvaluator:
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context
        self._operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            ast.And: lambda x, y: x and y,
            ast.Or: lambda x, y: x or y,
            ast.Not: operator.not_,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

    def evaluate(self, expr: str) -> Any:
        try:
            tree = ast.parse(expr, mode="eval")
            return self._evaluate_node(tree.body)
        except Exception:
            return self._evaluate_simple(expr)

    def _evaluate_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            return self.context.get(node.id)

        if isinstance(node, ast.BinOp):
            left = self._evaluate_node(node.left)
            right = self._evaluate_node(node.right)
            op = self._operators.get(type(node.op))
            if op:
                return op(left, right)
            return None

        if isinstance(node, ast.Compare):
            left = self._evaluate_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._evaluate_node(comparator)
                op_func = self._operators.get(type(op))
                if op_func:
                    result = op_func(left, right)
                    if not result:
                        return False
                    left = right
            return True

        if isinstance(node, ast.UnaryOp):
            operand = self._evaluate_node(node.operand)
            op = self._operators.get(type(node.op))
            if op:
                return op(operand)
            return None

        if isinstance(node, ast.BoolOp):
            values = [self._evaluate_node(v) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
            return None

        if isinstance(node, ast.Attribute):
            obj = self._evaluate_node(node.value)
            if hasattr(obj, node.attr):
                return getattr(obj, node.attr)
            return None

        if isinstance(node, ast.Subscript):
            obj = self._evaluate_node(node.value)
            slice_val = self._evaluate_node(node.slice)
            if isinstance(obj, (list, tuple, str)):
                return obj[slice_val]
            if isinstance(obj, dict):
                return obj.get(slice_val)
            return None

        return None

    def _evaluate_simple(self, expr: str) -> Any:
        expr = expr.strip()

        if expr in self.context:
            return self.context[expr]

        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]

        if expr.startswith("'") and expr.endswith("'"):
            return expr[1:-1]

        if expr.isdigit():
            return int(expr)

        try:
            return float(expr)
        except ValueError:
            pass

        if expr.lower() == "true":
            return True
        if expr.lower() == "false":
            return False
        if expr.lower() == "none":
            return None

        return expr
