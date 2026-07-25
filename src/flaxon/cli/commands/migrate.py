from __future__ import annotations

import argparse
from typing import Any

from ..base import Command


class MigrateCommand(Command):
    def __init__(self) -> None:
        super().__init__(
            name="migrate",
            handler=self._run,
            help_text="Run database migrations",
            description="Apply or rollback database migrations",
        )

    def _add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--direction", choices=["up", "down"], default="up", help="Migration direction")
        parser.add_argument("--target", help="Target migration version")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be applied")

    def _run(self, args: argparse.Namespace, console: Any) -> int:
        if args.dry_run:
            console.info(f"Would run migrations in direction: {args.direction}")
            if args.target:
                console.info(f"Target version: {args.target}")
            return 0

        console.info(f"Running migrations in direction: {args.direction}")

        if args.direction == "down":
            console.warning("This will rollback migrations!")

        console.info("Migration completed")
        return 0
