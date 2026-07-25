from __future__ import annotations

from typing import Any

from .operation import OperationBuilder


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
        for route in app.router.routes:
            path = route.path
            method = "get"
            operation = OperationBuilder(path, method).build()
            self.add_path(path, method, operation)

        return self.generate()


def generate_openapi(app: Any, title: str = "Flaxon API", version: str = "1.0.0") -> dict[str, Any]:
    generator = OpenAPIGenerator(title, version)
    return generator.generate_from_app(app)
