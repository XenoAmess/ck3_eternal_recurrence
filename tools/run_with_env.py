"""Run one argv command with explicit environment overrides and no shell."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess


ENVIRONMENT_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def parse_environment(rows: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in rows:
        name, separator, value = row.partition("=")
        if not separator or ENVIRONMENT_NAME.fullmatch(name) is None:
            raise ValueError(f"invalid environment override: {row!r}")
        if "\0" in value:
            raise ValueError(f"environment override contains NUL: {name}")
        result[name] = value
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--cwd", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    if not command:
        parser.error("an argv command is required after --")
    environment = os.environ.copy()
    environment.update(parse_environment(args.env))
    completed = subprocess.run(
        command,
        cwd=str(args.cwd.expanduser().resolve()) if args.cwd else None,
        env=environment,
        check=False,
    )
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
