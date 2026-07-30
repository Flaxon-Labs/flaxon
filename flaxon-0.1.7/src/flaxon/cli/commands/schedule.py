from __future__ import annotations

import argparse

from ..base import Command


class ScheduleCommand(Command):
    def __init__(self) -> None:
        super().__init__(
            name="schedule",
            handler=self._run,
            help_text="Run scheduled tasks",
            description="Execute scheduled tasks",
        )

    def _add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("application", help="Application import string, e.g., app:app")
        parser.add_argument("--once", action="store_true", help="Run once and exit")

    def _run(self, args: argparse.Namespace, console: Any) -> int:
        console.info("Starting scheduler...")

        try:
            from flaxon.utils.import_string import import_string
            app = import_string(args.application)
            console.info(f"Loaded application: {app.name}")

            import asyncio

            from flaxon.tasks import Scheduler
            from flaxon.tasks.queue import TaskQueue

            queue = TaskQueue()
            scheduler = Scheduler(queue)

            console.info("Scheduler started. Press Ctrl+C to stop.")

            try:
                asyncio.run(scheduler.start())
            except KeyboardInterrupt:
                console.info("\nShutting down scheduler...")
                asyncio.run(scheduler.stop())

            return 0

        except Exception as exc:
            console.error(f"Failed to start scheduler: {exc}")
            return 1
