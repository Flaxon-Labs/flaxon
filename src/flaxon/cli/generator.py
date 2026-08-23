from __future__ import annotations

from pathlib import Path
from typing import Any

from .templates import TemplateEngine


class Generator:
    def __init__(self) -> None:
        self.templates = TemplateEngine()

    def generate(self, directory: Path, template: str = "basic") -> None:
        directory.mkdir(parents=True, exist_ok=True)

        app_py = self.templates.render("app.py", {"name": directory.name})
        (directory / "app.py").write_text(app_py, encoding="utf-8")

        pyproject = self.templates.render("pyproject.toml", {"package_name": directory.name.lower()})
        (directory / "pyproject.toml").write_text(pyproject, encoding="utf-8")

        gitignore = self.templates.render("gitignore")
        (directory / ".gitignore").write_text(gitignore, encoding="utf-8")

        readme = self.templates.render("README.md", {"name": directory.name})
        (directory / "README.md").write_text(readme, encoding="utf-8")

    def generate_component(self, type: str, name: str) -> None:
        filename_map = {
            "controller": f"{name}_controller.py",
            "schema": f"{name}_schema.py",
            "service": f"{name}_service.py",
            "middleware": f"{name}_middleware.py",
        }

        filename = filename_map.get(type, f"{name}.py")

        template_content = self.templates.render(
            f"{type}.py", {"name": name, "name_capitalize": name.capitalize()}
        )
        path = Path(filename)

        if path.exists():
            raise FileExistsError(f"File '{filename}' already exists")

        path.write_text(template_content, encoding="utf-8")

    def generate_from_string(self, template: str, context: dict[str, Any]) -> str:
        return self.templates.render_string(template, context)