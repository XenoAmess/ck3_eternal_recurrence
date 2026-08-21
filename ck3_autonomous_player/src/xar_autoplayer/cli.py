"""Command line for Phase A environment preparation and smoke attestation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .environment import (
    doctor,
    ensure_state_path_safe,
    make_spec,
    prepare_profile,
    verify_profile,
)
from .errors import AgentError
from .locking import exclusive_state_lock
from .runtime import smoke


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="xar-autoplayer")
    root.add_argument(
        "--state-dir",
        type=Path,
        help="external persistent state root (default: XAR_AUTOPLAYER_STATE_DIR or LocalAppData)",
    )
    root.add_argument(
        "--game-dir",
        type=Path,
        help="CK3 installation root (default: repository reference installation)",
    )
    commands = root.add_subparsers(dest="command", required=True)
    doctor_parser = commands.add_parser("doctor", help="check the host and safety boundary")
    doctor_parser.add_argument("--prepared", action="store_true")
    commands.add_parser(
        "prepare-profile",
        help="build production runtime and exact growth + 100% single-mod profile",
    )
    commands.add_parser("verify-profile", help="verify the prepared profile contract")
    smoke_parser = commands.add_parser(
        "smoke", help="non-debug boot to visible main menu and prove the runtime load"
    )
    smoke_parser.add_argument("--timeout", type=float, default=180)
    return root


def _summary(command: str, payload: dict[str, object]) -> dict[str, object]:
    if command == "prepare-profile":
        return {
            "ok": True,
            "profile_dir": payload["profile_dir"],
            "environment_sha256": payload["environment_sha256"],
            "enabled_mods": payload["load_profile"]["enabled_mods"],
            "rules_sha256": payload["rules"]["profile_sha256"],
            "production_tree_sha256": payload["mod"]["production_tree_sha256"],
        }
    if command == "verify-profile":
        return {
            "ok": True,
            "profile_dir": payload["profile_dir"],
            "environment_sha256": payload["environment_sha256"],
        }
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    spec = make_spec(args.state_dir, args.game_dir)
    try:
        if args.command == "doctor":
            result = doctor(spec, require_prepared=args.prepared)
        elif args.command == "prepare-profile":
            result = prepare_profile(spec)
        elif args.command == "verify-profile":
            ensure_state_path_safe(spec.state_dir)
            with exclusive_state_lock(spec.state_dir, "verify-profile"):
                result = verify_profile(spec)
        else:
            result = smoke(spec, timeout_seconds=args.timeout)
    except (AgentError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(_summary(args.command, result), ensure_ascii=False, indent=2))
    return 0
