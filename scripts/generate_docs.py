#!/usr/bin/env python
"""
Documentation generator for Flaxon.

This script generates API documentation from the source code.
"""

import importlib
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Any


def get_module_docstrings() -> dict[str, str]:
    """Extract docstrings from all modules."""
    docstrings = {}

    src_path = Path("src/flaxon")

    for py_file in src_path.rglob("*.py"):
        if py_file.name.startswith("_"):
            continue

        module_path = str(py_file.relative_to("src")).replace("/", ".").replace(".py", "")
        module_path = module_path.replace(".__init__", "")

        try:
            module = importlib.import_module(module_path)
            docstrings[module_path] = inspect.getdoc(module) or ""
        except Exception:
            continue

    return docstrings


def get_class_docstrings() -> dict[str, dict[str, Any]]:
    """Extract docstrings from all classes."""
    docstrings = {}

    src_path = Path("src/flaxon")

    for py_file in src_path.rglob("*.py"):
        if py_file.name.startswith("_"):
            continue

        module_path = str(py_file.relative_to("src")).replace("/", ".").replace(".py", "")
        module_path = module_path.replace(".__init__", "")

        try:
            module = importlib.import_module(module_path)

            for name in dir(module):
                obj = getattr(module, name)
                if inspect.isclass(obj) and obj.__module__ == module_path:
                    doc = inspect.getdoc(obj) or ""
                    docstrings[f"{module_path}.{name}"] = {
                        "module": module_path,
                        "name": name,
                        "docstring": doc,
                        "methods": get_method_docstrings(obj),
                    }
        except Exception:
            continue

    return docstrings


def get_method_docstrings(cls: Any) -> dict[str, str]:
    """Extract docstrings from class methods."""
    methods = {}

    for name, method in inspect.getmembers(cls, inspect.isfunction):
        if name.startswith("_"):
            continue

        doc = inspect.getdoc(method) or ""
        methods[name] = doc

    return methods


def generate_api_docs() -> dict[str, Any]:
    """Generate API documentation."""
    return {
        "modules": get_module_docstrings(),
        "classes": get_class_docstrings(),
        "generated_at": __import__("datetime").datetime.now().isoformat(),
    }


def generate_markdown_docs(api_docs: dict[str, Any]) -> None:
    """Generate markdown documentation."""
    docs_dir = Path("docs/api")
    docs_dir.mkdir(parents=True, exist_ok=True)

    for class_path, class_info in api_docs["classes"].items():
        md_content = []

        md_content.append(f"# {class_info['name']}\n")
        md_content.append(f"Module: `{class_info['module']}`\n")

        if class_info["docstring"]:
            md_content.append("## Description\n")
            md_content.append(class_info["docstring"])
            md_content.append("\n")

        if class_info["methods"]:
            md_content.append("## Methods\n")
            for method_name, doc in class_info["methods"].items():
                md_content.append(f"### {method_name}\n")
                md_content.append(doc or "No documentation available.")
                md_content.append("\n")

        file_name = f"{class_info['name'].lower()}.md"
        doc_path = docs_dir / file_name
        doc_path.write_text("\n".join(md_content))
        print(f"Generated: {doc_path}")


def generate_index_docs(api_docs: dict[str, Any]) -> None:
    """Generate index documentation."""
    md_content = []
    md_content.append("# API Reference\n")
    md_content.append("## Classes\n")

    for class_path, class_info in sorted(api_docs["classes"].items()):
        file_name = f"{class_info['name'].lower()}.md"
        md_content.append(f"- [{class_info['name']}]({file_name})")

    md_content.append("\n## Modules\n")
    for module_path, docstring in sorted(api_docs["modules"].items()):
        md_content.append(f"### {module_path}")
        if docstring:
            md_content.append(f"{docstring[:200]}...")
        md_content.append("")

    docs_dir = Path("docs/api")
    docs_dir.mkdir(parents=True, exist_ok=True)

    doc_path = docs_dir / "index.md"
    doc_path.write_text("\n".join(md_content))
    print(f"Generated: {doc_path}")


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate Flaxon documentation")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--output",
        help="Output file path",
    )

    args = parser.parse_args()

    api_docs = generate_api_docs()

    if args.format == "json":
        json_output = json.dumps(api_docs, indent=2, default=str)
        if args.output:
            Path(args.output).write_text(json_output)
        else:
            print(json_output)
    else:
        generate_markdown_docs(api_docs)
        generate_index_docs(api_docs)
        print("Documentation generated successfully!")


if __name__ == "__main__":
    main()