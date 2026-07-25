from __future__ import annotations
from flaxon import __version__

import argparse
import sys

from .console import Console
from .discovery import CommandDiscovery


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flaxon",
        description="Flaxon framework command line tools",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Flaxon {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    discovery = CommandDiscovery()
    commands = discovery.discover()

    for cmd in commands:
        cmd.add_parser(subparsers)

    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    console = Console()

    discovery = CommandDiscovery()
    commands = {cmd.name: cmd for cmd in discovery.discover()}

    if args.command in commands:
        try:
            return commands[args.command].run(args, console)
        except Exception as exc:
            console.error(f"Error: {exc}")
            return 1

    console.error(f"Unknown command: {args.command}")
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
