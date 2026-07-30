from __future__ import annotations

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
        if not self.allowed_modules:
            return True
        return module_name in self.allowed_modules

    def evaluate(self, expr: str, context: dict[str, Any]) -> Any:
        restricted_globals = {**self._restricted_globals, **context}

        try:
            return eval(expr, restricted_globals)
        except Exception:
            return None

    def execute(self, code: str, context: dict[str, Any]) -> None:
        restricted_globals = {**self._restricted_globals, **context}

        try:
            exec(code, restricted_globals)
        except Exception:
            pass


class SandboxMiddleware:
    def __init__(self, app: Any, allowed_modules: list[str] | None = None) -> None:
        self.app = app
        self.sandbox = Sandbox(allowed_modules)

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        await self.app(scope, receive, send)
