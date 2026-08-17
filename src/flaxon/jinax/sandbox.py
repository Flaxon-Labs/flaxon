from __future__ import annotations

import ast
import builtins
from typing import Any


class Sandbox:
    def __init__(self, allowed_modules: list[str] | None = None) -> None:
        self.allowed_modules = allowed_modules or []
        self._restricted_globals = self._create_restricted_globals()

    def _create_restricted_globals(self) -> dict[str, Any]:
        restricted = {}

        safe_builtins = {
            "abs": builtins.abs,
            "all": builtins.all,
            "any": builtins.any,
            "bool": builtins.bool,
            "dict": builtins.dict,
            "enumerate": builtins.enumerate,
            "float": builtins.float,
            "int": builtins.int,
            "len": builtins.len,
            "list": builtins.list,
            "max": builtins.max,
            "min": builtins.min,
            "range": builtins.range,
            "round": builtins.round,
            "str": builtins.str,
            "sum": builtins.sum,
            "tuple": builtins.tuple,
            "zip": builtins.zip,
        }

        restricted.update(safe_builtins)

        restricted.update({
            "__import__": None,
            "eval": None,
            "exec": None,
            "compile": None,
            "open": None,
            "input": None,
            "globals": None,
            "locals": None,
            "vars": None,
            "dir": None,
            "help": None,
        })

        return restricted

    def is_safe_module(self, module_name: str) -> bool:
        return module_name in self.allowed_modules

    def evaluate(self, expr: str, context: dict[str, Any]) -> Any:
        try:
            tree = ast.parse(expr, mode="eval")
            return self._evaluate_node(tree.body, context)
        except (ArithmeticError, KeyError, SyntaxError, TypeError, ValueError):
            return None

    def execute(self, code: str, context: dict[str, Any]) -> None:
        """Evaluate safe expression statements without executing Python code.

        The previous implementation delegated to ``exec``, which made this
        class an unsafe execution primitive.  Templates only need expression
        evaluation; statements are intentionally rejected.
        """
        try:
            tree = ast.parse(code, mode="exec")
            for statement in tree.body:
                if not isinstance(statement, ast.Expr):
                    raise ValueError("Only expressions are supported")
                self._evaluate_node(statement.value, context)
        except (ArithmeticError, KeyError, SyntaxError, TypeError, ValueError):
            pass

    def _evaluate_node(self, node: ast.AST, context: dict[str, Any]) -> Any:
        """Interpret a deliberately small, data-only expression language."""
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id.startswith("_"):
                raise ValueError("Private names are not allowed")
            if node.id in context:
                return context[node.id]
            value = self._restricted_globals.get(node.id)
            if value is None:
                raise ValueError(f"Unknown name: {node.id}")
            return value
        if isinstance(node, ast.List):
            return [self._evaluate_node(element, context) for element in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(self._evaluate_node(element, context) for element in node.elts)
        if isinstance(node, ast.Set):
            return {self._evaluate_node(element, context) for element in node.elts}
        if isinstance(node, ast.Dict):
            return {
                self._evaluate_node(key, context): self._evaluate_node(value, context)
                for key, value in zip(node.keys, node.values, strict=True)
            }
        if isinstance(node, ast.Subscript):
            value = self._evaluate_node(node.value, context)
            index = self._evaluate_node(node.slice, context)
            return value[index]
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                raise ValueError("Private attributes are not allowed")
            value = self._evaluate_node(node.value, context)
            if not isinstance(value, dict):
                raise ValueError("Attribute access is only supported for mappings")
            return value[node.attr]
        if isinstance(node, ast.UnaryOp):
            value = self._evaluate_node(node.operand, context)
            if isinstance(node.op, ast.Not):
                return not value
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return +value
            raise ValueError("Unsupported unary operation")
        if isinstance(node, ast.BinOp):
            left = self._evaluate_node(node.left, context)
            right = self._evaluate_node(node.right, context)
            operations = {
                ast.Add: lambda: left + right,
                ast.Sub: lambda: left - right,
                ast.Mult: lambda: left * right,
                ast.Div: lambda: left / right,
                ast.FloorDiv: lambda: left // right,
                ast.Mod: lambda: left % right,
                ast.Pow: lambda: left**right,
            }
            for operation, handler in operations.items():
                if isinstance(node.op, operation):
                    return handler()
            raise ValueError("Unsupported binary operation")
        if isinstance(node, ast.BoolOp):
            values = [self._evaluate_node(value, context) for value in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
            raise ValueError("Unsupported boolean operation")
        if isinstance(node, ast.Compare):
            left = self._evaluate_node(node.left, context)
            comparisons = {
                ast.Eq: lambda a, b: a == b,
                ast.NotEq: lambda a, b: a != b,
                ast.Lt: lambda a, b: a < b,
                ast.LtE: lambda a, b: a <= b,
                ast.Gt: lambda a, b: a > b,
                ast.GtE: lambda a, b: a >= b,
                ast.In: lambda a, b: a in b,
                ast.NotIn: lambda a, b: a not in b,
            }
            for operator, comparator_node in zip(node.ops, node.comparators, strict=True):
                right = self._evaluate_node(comparator_node, context)
                for operation, handler in comparisons.items():
                    if isinstance(operator, operation):
                        if not handler(left, right):
                            return False
                        break
                else:
                    raise ValueError("Unsupported comparison")
                left = right
            return True
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only approved functions may be called")
            function = self._evaluate_node(node.func, context)
            if function not in self._restricted_globals.values():
                raise ValueError("Function is not approved")
            return function(
                *(self._evaluate_node(argument, context) for argument in node.args),
                **{
                    keyword.arg: self._evaluate_node(keyword.value, context)
                    for keyword in node.keywords
                    if keyword.arg is not None
                },
            )
        raise ValueError(f"Unsupported expression: {type(node).__name__}")


class SandboxMiddleware:
    def __init__(self, app: Any, allowed_modules: list[str] | None = None) -> None:
        self.app = app
        self.sandbox = Sandbox(allowed_modules)

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        await self.app(scope, receive, send)
