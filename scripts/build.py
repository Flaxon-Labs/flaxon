#!/usr/bin/env python
"""
Build script for Flaxon.

This script builds distribution packages for the Flaxon framework.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def clean() -> None:
    """Clean build artifacts."""
    print("Cleaning build artifacts...")

    dirs_to_clean = [
        "build",
        "dist",
        "*.egg-info",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "htmlcov",
        ".coverage",
        ".tox",
    ]

    for pattern in dirs_to_clean:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
                print(f"  Removed: {path}")
            elif path.is_file():
                path.unlink(missing_ok=True)
                print(f"  Removed: {path}")

    print("Clean complete.")


def build_wheel() -> None:
    """Build wheel distribution."""
    print("Building wheel...")
    result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("Error building wheel:")
        print(result.stderr)
        sys.exit(1)

    print("Wheel built successfully.")


def build_sdist() -> None:
    """Build source distribution."""
    print("Building source distribution...")
    result = subprocess.run(
        [sys.executable, "-m", "build", "--sdist"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("Error building source distribution:")
        print(result.stderr)
        sys.exit(1)

    print("Source distribution built successfully.")


def build_all() -> None:
    """Build all distributions."""
    print("Building all distributions...")
    result = subprocess.run(
        [sys.executable, "-m", "build"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("Error building distributions:")
        print(result.stderr)
        sys.exit(1)

    print("All distributions built successfully.")


def check_dist() -> None:
    """Check distributions with twine."""
    print("Checking distributions...")
    result = subprocess.run(
        [sys.executable, "-m", "twine", "check", "dist/*"],
        shell=True,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("Error checking distributions:")
        print(result.stderr)
        sys.exit(1)

    print("Distributions check passed.")


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Build Flaxon distributions")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts before building",
    )
    parser.add_argument(
        "--wheel",
        action="store_true",
        help="Build only wheel",
    )
    parser.add_argument(
        "--sdist",
        action="store_true",
        help="Build only source distribution",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check distributions with twine",
    )

    args = parser.parse_args()

    if args.clean:
        clean()

    if args.wheel:
        build_wheel()
    elif args.sdist:
        build_sdist()
    else:
        build_all()

    if args.check:
        check_dist()

    print("\nBuild complete!")


if __name__ == "__main__":
    main()