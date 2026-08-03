from __future__ import annotations

import inspect
import typing
from typing import Any

from .operation import OperationBuilder
from .schema import SchemaBuilder


class OpenAPIGenerator:
    def __init__(self, title: str = "Flaxon API", version: str = "1.0.0") -> None:
        self.title = title
        self.version = version
        self._paths: dict[str, dict[str, Any]] = {}
        self._schemas: dict[str, Any] = {}
        self._tags: list[dict[str, str]] = []
        self._security: list[dict[str, list[str]]] = []
        self._info: dict[str, Any] = {
            "title": title,
            "version": version,
        }
        self._servers: list[dict[str, str]] = []

    def add_path(self, path: str, method: str, operation: dict[str, Any]) -> None:
        if path not in self._paths:
            self._paths[path] = {}
        self._paths[path][method.lower()] = operation

    def add_schema(self, name: str, schema: dict[str, Any]) -> None:
        self._schemas[name] = schema

    def add_tag(self, name: str, description: str | None = None) -> None:
        tag = {"name": name}
        if description:
            tag["description"] = description
        if tag not in self._tags:
            self._tags.append(tag)

    def add_server(self, url: str, description: str | None = None) -> None:
        server = {"url": url}
        if description:
            server["description"] = description
        self._servers.append(server)

    def add_security(self, scheme: str, scopes: list[str] | None = None) -> None:
        self._security.append({scheme: scopes or []})

    def add_info(self, key: str, value: Any) -> None:
        self._info[key] = value

    def generate(self) -> dict[str, Any]:
        return {
            "openapi": "3.1.0",
            "info": self._info,
            "servers": self._servers,
            "tags": self._tags,
            "paths": self._paths,
            "components": {
                "schemas": self._schemas,
                "securitySchemes": self._get_security_schemes(),
            },
            "security": self._security,
        }

    def _get_security_schemes(self) -> dict[str, Any]:
        return {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            },
            "apiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
            },
        }

    def generate_from_app(self, app: Any) -> dict[str, Any]:
        converter_to_openapi_type = {
            "int": "integer",
            "float": "number",
            "str": "string",
            "path": "string",
            "uuid": "string",
        }

        try:
            from flaxon.validation import Schema
        except ImportError:
            Schema = None

        for route in app.router.routes:
            openapi_path = route.path
            for name, converter_name in getattr(route, "parameters", []):
                openapi_path = openapi_path.replace(f"<{converter_name}:{name}>", f"{{{name}}}")
                openapi_path = openapi_path.replace(f"<{name}>", f"{{{name}}}")

            endpoint = route.endpoint
            docstring = inspect.getdoc(endpoint) or ""
            doc_lines = docstring.splitlines()
            summary = doc_lines[0].strip() if doc_lines else ""
            description = "\n".join(line for line in doc_lines[1:] if line.strip()).strip()

            try:
                hints = typing.get_type_hints(endpoint)
            except Exception:
                hints = {}

            request_schema = None
            if Schema is not None:
                for hint in hints.values():
                    if isinstance(hint, type) and issubclass(hint, Schema):
                        properties = {
                            field_name: SchemaBuilder.from_field(field)
                            for field_name, field in hint.__fields__.items()
                        }
                        required = [
                            field_name
                            for field_name, field in hint.__fields__.items()
                            if getattr(field, "required", False)
                        ]
                        request_schema = SchemaBuilder.object(properties)
                        if required:
                            request_schema["required"] = required
                        break

            for method in route.methods:
                builder = OperationBuilder(openapi_path, method.lower())
                if summary:
                    builder = builder.with_summary(summary)
                if description:
                    builder = builder.with_description(description)
                for name, converter_name in getattr(route, "parameters", []):
                    builder = builder.with_path_parameter(
                        name,
                        schema_type=converter_to_openapi_type.get(converter_name, "string"),
                    )
                if request_schema is not None and method.upper() in ("POST", "PUT", "PATCH"):
                    builder = builder.with_json_request(request_schema)
                operation = builder.build()
                self.add_path(openapi_path, method, operation)

        return self.generate()


def generate_openapi(app: Any, title: str = "Flaxon API", version: str = "1.0.0") -> dict[str, Any]:
    generator = OpenAPIGenerator(title, version)
    return generator.generate_from_app(app)