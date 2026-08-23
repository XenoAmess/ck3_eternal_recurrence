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
        help="build production runtime and exact growth + 100%% single-mod profile",
    )
    commands.add_parser("verify-profile", help="verify the prepared profile contract")
    smoke_parser = commands.add_parser(
        "smoke", help="non-debug boot to visible main menu and prove the runtime load"
    )
    smoke_parser.add_argument("--timeout", type=float, default=180)
    menu_parser = commands.add_parser(
        "menu-smoke",
        help="click the unique visible New Game control and attest the bookmark lobby",
    )
    menu_parser.add_argument("--timeout", type=float, default=180)
    opening_parser = commands.add_parser(
        "opening-smoke",
        help="complete Robert's opening and answer several ordinary events",
    )
    opening_parser.add_argument("--timeout", type=float, default=900)
    opening_parser.add_argument("--ordinary-events", type=int, default=3)
    step_parser = commands.add_parser(
        "opening-step",
        help="resume the isolated autosave and run one development-only gameplay step",
    )
    step_parser.add_argument(
        "--step",
        choices=("steward-development",),
        default="steward-development",
    )
    step_parser.add_argument("--timeout", type=float, default=240)
    dev_session_parser = commands.add_parser(
        "opening-dev-session",
        help="keep CK3 alive and hot-reload development steps read from stdin",
    )
    dev_session_parser.add_argument("--timeout", type=float, default=3600)
    replay_parser = commands.add_parser(
        "opening-replay",
        help="replay one opening predicate against an archived OCR observation",
    )
    replay_parser.add_argument("--observation", type=Path, required=True)
    replay_parser.add_argument(
        "--check",
        choices=(
            "council-panel",
            "steward-development-targeting",
            "steward-development-confirmation",
            "steward-development-active",
        ),
        required=True,
    )
    crash_parser = commands.add_parser(
        "crash-smoke",
        help="kill a post-resume supervisor and attest Job/watchdog recovery",
    )
    crash_parser.add_argument("--timeout", type=float, default=180)
    recovery_parser = commands.add_parser(
        "recover-stale-control",
        help="prove current absence and archive stale crash control evidence",
    )
    recovery_parser.add_argument("--run-id", required=True)
    crash_subject = commands.add_parser("_crash-subject", help=argparse.SUPPRESS)
    crash_subject.add_argument("--probe-nonce", required=True)
    crash_subject.add_argument("--handoff", type=Path, required=True)
    crash_subject.add_argument("--handoff-sha256", required=True)
    crash_subject.add_argument("--armed", type=Path, required=True)
    crash_subject.add_argument("--watchdog-final", type=Path, required=True)
    crash_subject.add_argument("--artifacts", type=Path, required=True)
    crash_subject.add_argument("--timeout", type=float, required=True)
    crash_subject.add_argument("--outer-pid", type=int, required=True)
    crash_subject.add_argument("--outer-executable", type=Path, required=True)
    crash_subject.add_argument("--outer-creation-date", required=True)
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
        if args.command == "_crash-subject":
            from .crash_probe import run_crash_subject

            return run_crash_subject(
                spec,
                probe_nonce=args.probe_nonce,
                handoff_path=args.handoff,
                handoff_sha256=args.handoff_sha256,
                armed_path=args.armed,
                watchdog_final=args.watchdog_final,
                artifacts=args.artifacts,
                timeout_seconds=args.timeout,
                outer_identity={
                    "pid": args.outer_pid,
                    "executable": str(args.outer_executable.resolve()),
                    "creation_date": args.outer_creation_date,
                },
            )
        if args.command == "doctor":
            result = doctor(spec, require_prepared=args.prepared)
        elif args.command == "prepare-profile":
            result = prepare_profile(spec)
        elif args.command == "verify-profile":
            ensure_state_path_safe(spec.state_dir)
            with exclusive_state_lock(spec.state_dir, "verify-profile"):
                result = verify_profile(spec)
        elif args.command == "recover-stale-control":
            from .recovery import recover_stale_control

            result = recover_stale_control(spec, args.run_id)
        elif args.command == "smoke":
            result = smoke(spec, timeout_seconds=args.timeout)
        elif args.command == "menu-smoke":
            from .menu_smoke import menu_smoke

            result = menu_smoke(spec, timeout_seconds=args.timeout)
        elif args.command == "opening-smoke":
            from .opening_smoke import opening_smoke

            result = opening_smoke(
                spec,
                timeout_seconds=args.timeout,
                ordinary_event_count=args.ordinary_events,
            )
        elif args.command == "opening-step":
            from .opening_smoke import opening_step

            result = opening_step(
                spec,
                step=args.step,
                timeout_seconds=args.timeout,
            )
        elif args.command == "opening-dev-session":
            from .opening_smoke import opening_dev_session

            result = opening_dev_session(spec, timeout_seconds=args.timeout)
        elif args.command == "opening-replay":
            from .opening_smoke import replay_opening_observation

            result = replay_opening_observation(args.observation, args.check)
        elif args.command == "crash-smoke":
            from .crash_probe import crash_smoke

            result = crash_smoke(spec, timeout_seconds=args.timeout)
        else:
            raise AgentError(f"unsupported command dispatch: {args.command}")
    except (AgentError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(_summary(args.command, result), ensure_ascii=False, indent=2))
    return 0
