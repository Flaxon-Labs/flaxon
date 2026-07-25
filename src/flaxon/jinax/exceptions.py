from __future__ import annotations


class JinaxError(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class TemplateNotFound(JinaxError):
    def __init__(self, template: str) -> None:
        super().__init__(f"Template '{template}' not found")
        self.template = template


class TemplateSyntaxError(JinaxError):
    def __init__(self, message: str, line: int | None = None, column: int | None = None) -> None:
        location = f" at line {line}, column {column}" if line and column else ""
        super().__init__(f"{message}{location}")
        self.line = line
        self.column = column


class TemplateRenderError(JinaxError):
    def __init__(self, message: str, template: str | None = None) -> None:
        context = f" in template '{template}'" if template else ""
        super().__init__(f"{message}{context}")
        self.template = template


class TemplateLoaderError(JinaxError):
    def __init__(self, message: str) -> None:
        super().__init__(f"Template loader error: {message}")


class TemplateCacheError(JinaxError):
    def __init__(self, message: str) -> None:
        super().__init__(f"Template cache error: {message}")


class SandboxError(JinaxError):
    def __init__(self, message: str) -> None:
        super().__init__(f"Sandbox error: {message}")


class MacroError(JinaxError):
    def __init__(self, message: str, macro: str | None = None) -> None:
        context = f" in macro '{macro}'" if macro else ""
        super().__init__(f"{message}{context}")
        self.macro = macro


class FilterError(JinaxError):
    def __init__(self, message: str, filter_name: str | None = None) -> None:
        context = f" in filter '{filter_name}'" if filter_name else ""
        super().__init__(f"{message}{context}")
        self.filter_name = filter_name


class InheritanceError(JinaxError):
    def __init__(self, message: str) -> None:
        super().__init__(f"Inheritance error: {message}")


class EscapingError(JinaxError):
    def __init__(self, message: str) -> None:
        super().__init__(f"Escaping error: {message}")
