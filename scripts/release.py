#!/usr/bin/env python
"""
Release script for Flaxon.

This script handles the release process including version updates,
changelog generation, and PyPI publishing.
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def get_current_version() -> str:
    """Get the current version from the package."""
    init_file = Path("src/flaxon/__init__.py")
    content = init_file.read_text()

    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)

    raise ValueError("Could not find version in __init__.py")


def update_version(version: str) -> None:
    """Update the version in __init__.py."""
    init_file = Path("src/flaxon/__init__.py")
    content = init_file.read_text()

    content = re.sub(
        r'__version__\s*=\s*["\']([^"\']+)["\']',
        f'__version__ = "{version}"',
        content,
    )

    init_file.write_text(content)
    print(f"Updated version to {version}")


def update_changelog(version: str) -> None:
    """Update the changelog with the new version."""
    changelog = Path("CHANGELOG.md")
    content = changelog.read_text()

    today = datetime.now().strftime("%Y-%m-%d")

    # Find the unreleased section
    unreleased_pattern = r"## \[Unreleased\](.*?)(?=\n## \[|$)"
    match = re.search(unreleased_pattern, content, re.DOTALL)

    if match:
        unreleased_content = match.group(1)
        new_entry = f"""## [{version}] - {today}{unreleased_content}"""

        content = content.replace(f"## [Unreleased]{unreleased_content}", new_entry)

        changelog.write_text(content)
        print(f"Updated changelog with version {version}")


def create_git_tag(version: str) -> None:
    """Create a git tag for the release."""
    tag = f"v{version}"

    result = subprocess.run(
        ["git", "tag", "-a", tag, "-m", f"Release {version}"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error creating tag: {result.stderr}")
        sys.exit(1)

    print(f"Created tag: {tag}")


def push_git_tag(version: str) -> None:
    """Push the git tag to remote."""
    tag = f"v{version}"

    result = subprocess.run(
        ["git", "push", "origin", tag],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error pushing tag: {result.stderr}")
        sys.exit(1)

    print(f"Pushed tag: {tag}")


def publish_to_pypi() -> None:
    """Publish the package to PyPI."""
    print("Publishing to PyPI...")

    result = subprocess.run(
        [sys.executable, "-m", "twine", "upload", "dist/*"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error publishing to PyPI: {result.stderr}")
        sys.exit(1)

    print("Published to PyPI successfully.")


def publish_to_testpypi() -> None:
    """Publish the package to TestPyPI."""
    print("Publishing to TestPyPI...")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "twine",
            "upload",
            "--repository-url",
            "https://test.pypi.org/legacy/",
            "dist/*",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error publishing to TestPyPI: {result.stderr}")
        sys.exit(1)

    print("Published to TestPyPI successfully.")


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Release Flaxon")
    parser.add_argument(
        "version",
        help="Version to release (e.g., 0.1.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes",
    )
    parser.add_argument(
        "--testpypi",
        action="store_true",
        help="Publish to TestPyPI instead of PyPI",
    )
    parser.add_argument(
        "--no-tag",
        action="store_true",
        help="Skip creating git tag",
    )
    parser.add_argument(
        "--no-publish",
        action="store_true",
        help="Skip publishing to PyPI",
    )

    args = parser.parse_args()

    version = args.version
    current_version = get_current_version()

    print(f"Current version: {current_version}")
    print(f"New version: {version}")

    if not args.dry_run:
        confirm = input("Proceed with release? (y/N): ")
        if confirm.lower() != "y":
            print("Aborted.")
            sys.exit(0)

    if args.dry_run:
        print("DRY RUN - No changes will be made")

    # Update version
    if not args.dry_run:
        update_version(version)
        update_changelog(version)

    # Build distributions
    print("Building distributions...")
    subprocess.run([sys.executable, "scripts/build.py", "--clean"], check=True)

    # Create and push tag
    if not args.dry_run and not args.no_tag:
        create_git_tag(version)
        push_git_tag(version)

    # Publish to PyPI
    if not args.dry_run and not args.no_publish:
        if args.testpypi:
            publish_to_testpypi()
        else:
            publish_to_pypi()

    print(f"\nRelease {version} complete!")


if __name__ == "__main__":
    main()