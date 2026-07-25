from __future__ import annotations

import argparse
import os
from pathlib import Path
from textwrap import dedent

from flaxon.utils import import_string


APP_TEMPLATE = '''from flaxon import Flaxon

app = Flaxon("{name}", debug=True)

@app.get("/")
async def home():
    return {{"message": "Hello from {name}"}}
'''

PYPROJECT_TEMPLATE = '''[build-system]
requires = ["setuptools>=75", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{package_name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["flaxon-framework[standard]>=0.1.0"]
'''


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="flaxon", description="Flaxon framework command line tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a Flaxon ASGI application")
    run_parser.add_argument("application", help="Application import string, for example app:app")
    run_parser.add_argument("--host", default="127.0.0.1")
    run_parser.add_argument("--port", type=int, default=8000)
    run_parser.add_argument("--reload", action="store_true")
    run_parser.add_argument("--workers", type=int, default=1)

    routes_parser = subparsers.add_parser("routes", help="List registered HTTP and WebSocket routes")
    routes_parser.add_argument("application")

    doctor_parser = subparsers.add_parser("doctor", help="Check application configuration and routes")
    doctor_parser.add_argument("application")

    new_parser = subparsers.add_parser("new", help="Create a starter Flaxon project")
    new_parser.add_argument("directory")

    return parser


def cmd_run(args: argparse.Namespace) -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("Uvicorn is not installed. Run: pip install 'flaxon-framework[server]'") from exc
    if args.reload or args.workers > 1:
        uvicorn.run(args.application, host=args.host, port=args.port, reload=args.reload, workers=args.workers)
    else:
        uvicorn.run(import_string(args.application), host=args.host, port=args.port)


def cmd_routes(args: argparse.Namespace) -> None:
    app = import_string(args.application)
    print(f"Routes for {app.name}")
    for route in app.router.routes:
        methods = ",".join(sorted(route.methods))
        print(f"{methods:18} {route.path:35} {route.name}")
    for route in app.router.websocket_routes:
        print(f"{'WEBSOCKET':18} {route.path:35} {route.name}")


def cmd_doctor(args: argparse.Namespace) -> None:
    app = import_string(args.application)
    warnings: list[str] = []
    failures: list[str] = []
    print(f"Flaxon Doctor - {app.name}")
    print(f"[PASS] Application imported successfully")
    print(f"[PASS] {len(app.router.routes)} HTTP route(s) registered")
    print(f"[PASS] {len(app.router.websocket_routes)} WebSocket route(s) registered")
    if app.debug and str(app.config.get("ENV", "development")).lower() == "production":
        warnings.append("Debug mode is enabled in production.")
    if app.config.get("SECRET_KEY") in {None, "", "change-me", "change-this-in-production"}:
        warnings.append("A strong production SECRET_KEY is not configured.")
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for route in app.router.routes:
        key = (route.path, tuple(sorted(route.methods)))
        if key in seen:
            failures.append(f"Duplicate route: {route.methods} {route.path}")
        seen.add(key)
    for warning in warnings:
        print(f"[WARN] {warning}")
    for failure in failures:
        print(f"[FAIL] {failure}")
    print(f"Result: {len(warnings)} warning(s), {len(failures)} failure(s)")
    if failures:
        raise SystemExit(1)


def cmd_new(args: argparse.Namespace) -> None:
    directory = Path(args.directory)
    directory.mkdir(parents=True, exist_ok=False)
    package_name = directory.name.lower().replace(" ", "-").replace("_", "-")
    (directory / "app.py").write_text(APP_TEMPLATE.format(name=directory.name), encoding="utf-8")
    (directory / "pyproject.toml").write_text(PYPROJECT_TEMPLATE.format(package_name=package_name), encoding="utf-8")
    (directory / ".gitignore").write_text(".venv/\n__pycache__/\n.env\n", encoding="utf-8")
    (directory / "README.md").write_text(
        dedent(
            f"""\
            # {directory.name}

            Install dependencies and run:

            ```bash
            python -m pip install -e .
            flaxon run app:app --reload
            ```
            """
        ),
        encoding="utf-8",
    )
    print(f"Created Flaxon project at {directory.resolve()}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    commands = {
        "run": cmd_run,
        "routes": cmd_routes,
        "doctor": cmd_doctor,
        "new": cmd_new,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
