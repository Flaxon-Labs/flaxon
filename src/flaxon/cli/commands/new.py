from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ..commands import Command
from ..generator import Generator


class NewCommand(Command):
    def __init__(self) -> None:
        super().__init__(
            name="new",
            handler=self._run,
            help_text="Create a new Flaxon project",
            description="Generate a starter Flaxon project",
        )

    def _add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("directory", help="Project directory name")
        parser.add_argument("--template", default="basic", help="Project template to use")
        parser.add_argument("--no-venv", action="store_true", help="Skip virtual environment creation")

    def _run(self, args: argparse.Namespace, console: Any) -> int:
        directory = Path(args.directory)
        if directory.exists():
            console.error(f"Directory '{args.directory}' already exists")
            return 1

        console.info(f"Creating Flaxon project: {args.directory}")

        generator = Generator()

        try:
            generator.generate(directory, args.template)

            if not args.no_venv:
                console.info("Creating virtual environment...")
                import subprocess
                subprocess.run(["python", "-m", "venv", ".venv"], cwd=directory, check=False)

            console.success(f"Project created at {directory.resolve()}")
            console.info("\nNext steps:")
            console.info(f"  cd {args.directory}")
            if not args.no_venv:
                console.info("  source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate")
            console.info("  python -m pip install -e .")
            console.info("  flaxon run app:app --reload")
            return 0

        except Exception as exc:
            console.error(f"Failed to create project: {exc}")
            return 1
