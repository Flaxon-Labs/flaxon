from __future__ import annotations

from typing import Any


class Documentation:
    def __init__(self, title: str = "Flaxon API", version: str = "1.0.0") -> None:
        self.title = title
        self.version = version
        self._info: dict[str, Any] = {
            "title": title,
            "version": version,
        }

    def description(self, description: str) -> Documentation:
        self._info["description"] = description
        return self

    def terms_of_service(self, url: str) -> Documentation:
        self._info["termsOfService"] = url
        return self

    def contact(self, name: str, email: str | None = None, url: str | None = None) -> Documentation:
        contact = {"name": name}
        if email:
            contact["email"] = email
        if url:
            contact["url"] = url
        self._info["contact"] = contact
        return self

    def license(self, name: str, url: str | None = None) -> Documentation:
        license_info = {"name": name}
        if url:
            license_info["url"] = url
        self._info["license"] = license_info
        return self

    def build(self) -> dict[str, Any]:
        return self._info


class DocumentationBuilder:
    def __init__(self) -> None:
        self.doc = Documentation()

    def build(self) -> dict[str, Any]:
        return self.doc.build()

    def with_title(self, title: str) -> DocumentationBuilder:
        self.doc._info["title"] = title
        return self

    def with_version(self, version: str) -> DocumentationBuilder:
        self.doc._info["version"] = version
        return self

    def with_description(self, description: str) -> DocumentationBuilder:
        self.doc.description(description)
        return self

    def with_contact(self, name: str, email: str | None = None) -> DocumentationBuilder:
        self.doc.contact(name, email)
        return self

    def with_license(self, name: str, url: str | None = None) -> DocumentationBuilder:
        self.doc.license(name, url)
        return self
