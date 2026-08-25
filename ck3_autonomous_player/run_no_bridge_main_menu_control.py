#!/usr/bin/env python3
"""Dry-run by default; add --execute for the managed CK3 main-menu control."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.environment import make_spec  # noqa: E402
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.startup_control import (  # noqa: E402
    build_no_bridge_main_menu_survival_plan,
    no_bridge_main_menu_survival_control,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Start CK3 without DLL injection, game input, or a save-loading "
            "argument and observe only main-menu window survival. Defaults "
            "to dry-run."
        )
    )
    result.add_argument("--state-dir", type=Path, required=True)
    result.add_argument("--game-dir", type=Path, required=True)
    result.add_argument("--timeout", type=float, default=240.0)
    result.add_argument(
        "--execute",
        action="store_true",
        help="actually launch CK3; without this flag the command is read-only",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    spec = make_spec(args.state_dir, args.game_dir)
    try:
        if args.execute:
            payload = no_bridge_main_menu_survival_control(
                spec, timeout_seconds=args.timeout
            )
        else:
            payload = build_no_bridge_main_menu_survival_plan(
                spec, timeout_seconds=args.timeout
            )
    except (AgentError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
