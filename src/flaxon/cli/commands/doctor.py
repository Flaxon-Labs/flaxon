from __future__ import annotations

import argparse
from typing import Any

from ..base import Command


class DoctorCommand(Command):
    def __init__(self) -> None:
        super().__init__(
            name="doctor",
            handler=self._run,
            help_text="Check application configuration and routes",
            description="Run diagnostics on the application",
        )

    def _add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("application", help="Application import string, e.g., app:app")
        parser.add_argument("--fix", action="store_true", help="Attempt to fix issues")

    def _run(self, args: argparse.Namespace, console: Any) -> int:
        from flaxon.utils.import_string import import_string

        try:
            app = import_string(args.application)
        except Exception as exc:
            console.error(f"Failed to import application: {exc}")
            return 1

        warnings = []
        failures = []

        console.info(f"Flaxon Doctor - {app.name}")

        console.success("[PASS] Application imported successfully")
        console.success(f"[PASS] {len(app.router.routes)} HTTP route(s) registered")
        console.success(f"[PASS] {len(app.router.websocket_routes)} WebSocket route(s) registered")

        if app.debug and str(app.config.get("ENV", "development")).lower() == "production":
            warnings.append("Debug mode is enabled in production.")

        if app.config.get("SECRET_KEY") in {None, "", "change-me", "change-this-in-production"}:
            warnings.append("A strong production SECRET_KEY is not configured.")

        seen = set()
        for route in app.router.routes:
            key = (route.path, tuple(sorted(route.methods)))
            if key in seen:
                failures.append(f"Duplicate route: {route.methods} {route.path}")
            seen.add(key)

        for warning in warnings:
            console.warning(f"[WARN] {warning}")

        for failure in failures:
            console.error(f"[FAIL] {failure}")

        console.info(f"Result: {len(warnings)} warning(s), {len(failures)} failure(s)")

        if failures and args.fix:
            console.info("Attempting to fix issues...")
            # Fix logic would go here

        return 1 if failures else 0
