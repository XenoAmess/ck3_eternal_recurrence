#!/usr/bin/env python3
"""Dry-run by default; add --execute for the managed no-DLL CK3 control."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.environment import make_spec  # noqa: E402
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.runtime import DEFAULT_NATIVE_BRIDGE_PIPE  # noqa: E402
from xar_autoplayer.startup_control import (  # noqa: E402
    build_no_bridge_startup_control_plan,
    no_bridge_startup_control,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Load the exact anchored CK3 checkpoint under Job/watchdog control "
            "with DLL injection and game input disabled. Defaults to dry-run."
        )
    )
    result.add_argument("--state-dir", type=Path, required=True)
    result.add_argument("--game-dir", type=Path, required=True)
    result.add_argument(
        "--checkpoint-pipe",
        default=DEFAULT_NATIVE_BRIDGE_PIPE,
        help="pipe identity stored by the native session that created the checkpoint",
    )
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
            payload = no_bridge_startup_control(
                spec,
                checkpoint_pipe_name=args.checkpoint_pipe,
                timeout_seconds=args.timeout,
            )
        else:
            payload = build_no_bridge_startup_control_plan(
                spec,
                checkpoint_pipe_name=args.checkpoint_pipe,
                timeout_seconds=args.timeout,
            )
    except (AgentError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
