import sys

import pytest

from flaxon.cli.main import create_parser, main


def test_cli_registers_builtin_commands():
    parser = create_parser()
    for command in ("run", "routes", "doctor", "docs", "inspect", "migrate", "test", "worker"):
        args = parser.parse_args([command, "app:app"] if command not in {"migrate", "test"} else [command])
        assert args.command == command


def test_cli_routes_accepts_output_options():
    args = create_parser().parse_args(["routes", "app:app", "--format", "json", "--output", "routes.json"])
    assert args.format == "json"
    assert args.output == "routes.json"


def test_cli_version(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["flaxon", "--version"])
    with pytest.raises(SystemExit) as result:
        main()
    assert result.value.code == 0
    assert "Flaxon" in capsys.readouterr().out
