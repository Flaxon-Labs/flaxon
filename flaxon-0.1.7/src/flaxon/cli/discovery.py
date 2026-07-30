from __future__ import annotations

import importlib
import importlib.util
import os
from pathlib import Path
from typing import Any
from .base import Command
from .commands import DoctorCommand, GenerateCommand, NewCommand, RoutesCommand, RunCommand


class CommandDiscovery:
    def __init__(self) -> None:
        self._builtin_commands = [
            RunCommand(),
            RoutesCommand(),
            DoctorCommand(),
            NewCommand(),
            GenerateCommand(),
        ]

    def discover(self) -> list[Command]:
        commands = list(self._builtin_commands)

        try:
            import flaxon_cli
            commands.extend(self._discover_from_module(flaxon_cli))
        except ImportError:
            pass

        if os.path.exists("cli"):
            commands.extend(self._discover_from_path("cli"))

        return commands

    def _discover_from_module(self, module: Any) -> list[Command]:
        commands = []

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, Command):
                commands.append(attr)

        return commands

    def _discover_from_path(self, path: str) -> list[Command]:
        commands = []
        path_obj = Path(path)

        if not path_obj.exists():
            return commands

        for file_path in path_obj.glob("*.py"):
            if file_path.name.startswith("_"):
                continue

            try:
                spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                commands.extend(self._discover_from_module(module))

            except Exception:
                continue

        return commands
