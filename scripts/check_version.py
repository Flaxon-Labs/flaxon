#!/usr/bin/env python
"""
Version checker for Flaxon.

This script checks that all version references are consistent.
"""

import re
from pathlib import Path
from typing import Any


def get_version_from_file(file_path: Path, pattern: str) -> str | None:
    """Extract version from a file using a regex pattern."""
    if not file_path.exists():
        return None

    content = file_path.read_text()
    match = re.search(pattern, content)

    if match:
        return match.group(1)

    return None


def get_version_from_init() -> str | None:
    """Get version from __init__.py."""
    init_file = Path("src/flaxon/__init__.py")
    return get_version_from_file(init_file, r'__version__\s*=\s*["\']([^"\']+)["\']')


def get_version_from_pyproject() -> str | None:
    """Get version from pyproject.toml."""
    pyproject = Path("pyproject.toml")
    return get_version_from_file(pyproject, r'version\s*=\s*["\']([^"\']+)["\']')


def get_version_from_changelog() -> str | None:
    """Get latest version from CHANGELOG.md."""
    changelog = Path("CHANGELOG.md")

    if not changelog.exists():
        return None

    content = changelog.read_text()
    lines = content.split("\n")

    for line in lines:
        match = re.search(r"## \[(\d+\.\d+\.\d+)\]", line)
        if match:
            return match.group(1)

    return None


def check_consistency() -> dict[str, Any]:
    """Check version consistency across files."""
    init_version = get_version_from_init()
    pyproject_version = get_version_from_pyproject()
    changelog_version = get_version_from_changelog()

    results = {
        "init_py": init_version,
        "pyproject_toml": pyproject_version,
        "changelog": changelog_version,
        "consistent": init_version == pyproject_version == changelog_version,
    }

    return results


def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("Flaxon Version Check")
    print("=" * 60)

    results = check_consistency()

    print(f"\n__init__.py:     {results['init_py']}")
    print(f"pyproject.toml:  {results['pyproject_toml']}")
    print(f"CHANGELOG.md:    {results['changelog']}")

    if results["consistent"]:
        print("\n✅ All versions are consistent!")
    else:
        print("\n❌ Version mismatch detected!")

        if results["init_py"] != results["pyproject_toml"]:
            print(f"  __init__.py ({results['init_py']}) != pyproject.toml ({results['pyproject_toml']})")

        if results["init_py"] != results["changelog"]:
            print(f"  __init__.py ({results['init_py']}) != CHANGELOG.md ({results['changelog']})")

        if results["pyproject_toml"] != results["changelog"]:
            print(f"  pyproject.toml ({results['pyproject_toml']}) != CHANGELOG.md ({results['changelog']})")

        raise SystemExit(1)


if __name__ == "__main__":
    main()