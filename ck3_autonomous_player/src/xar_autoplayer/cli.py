"""Command line for Phase A environment preparation and smoke attestation."""

from __future__ import annotations

import argparse
import json
import os
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
from .one_generation_run import ONE_GENERATION_CHECKPOINT_CADENCE
from .runtime import (
    DEFAULT_NATIVE_BRIDGE_PIPE,
    NATIVE_BRIDGE_DISABLED,
    NATIVE_BRIDGE_LAUNCH_MODES,
    configure_native_bridge_launch_environment,
    smoke,
)


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
    root.add_argument(
        "--bridge-mode",
        choices=(NATIVE_BRIDGE_DISABLED, *sorted(NATIVE_BRIDGE_LAUNCH_MODES)),
        default=os.environ.get("XAR_CK3_BRIDGE_MODE", NATIVE_BRIDGE_DISABLED),
        help=(
            "CK3 launch backend: disabled (default), pure native-headless, or "
            "hybrid-fallback; runtime performs no fallback itself"
        ),
    )
    root.add_argument(
        "--bridge-pipe",
        default=os.environ.get("XAR_CK3_BRIDGE_PIPE", DEFAULT_NATIVE_BRIDGE_PIPE),
        help="named pipe inherited by CK3 when --bridge-mode is enabled",
    )
    root.add_argument(
        "--bridge-dll",
        type=Path,
        default=(
            Path(os.environ["XAR_CK3_BRIDGE_DLL"])
            if os.environ.get("XAR_CK3_BRIDGE_DLL")
            else None
        ),
        help="xar_ck3_bridge.dll path; required only when --bridge-mode is enabled",
    )
    root.add_argument(
        "--bridge-injector",
        type=Path,
        default=(
            Path(os.environ["XAR_CK3_BRIDGE_INJECTOR"])
            if os.environ.get("XAR_CK3_BRIDGE_INJECTOR")
            else None
        ),
        help=(
            "xar_ck3_bridge_injector.exe path; required only when "
            "--bridge-mode is enabled"
        ),
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
        choices=(
            "auto-turn",
            "auto-run",
            "pause-map",
            "life-advance",
            "steward-development",
            "economic-event-cycle",
            "save-checkpoint",
            "restore-checkpoint",
            "dynasty-review",
            "succession-review",
            "marriage-review",
            "marriage-alliance",
            "marriage-confirm-response",
            "death-terminal",
            "strategy-review",
            "war-review",
            "war-target-review",
            "war-interaction-review",
            "war-declaration-review",
            "war-casus-belli-review",
            "war-goal-review",
            "war-declare-palermo",
            "war-raise-all",
            "war-move-palermo",
            "war-map-review",
            "war-find-palermo",
            "war-siege-palermo",
            "war-advance-week",
            "war-advance-month",
            "war-status",
            "war-enforce-demands",
            "war-disband-armies",
            "resolve-current-event",
        ),
        default="steward-development",
    )
    step_parser.add_argument("--timeout", type=float, default=240)
    dev_session_parser = commands.add_parser(
        "opening-dev-session",
        help="keep CK3 alive and hot-reload development steps read from stdin",
    )
    dev_session_parser.add_argument("--timeout", type=float, default=21600)
    native_session_parser = commands.add_parser(
        "native-session",
        help=(
            "launch and supervise pure native-headless CK3 for an MCP server; "
            "no visual fallback"
        ),
    )
    native_session_parser.add_argument("--timeout", type=float, default=21600)
    native_session_parser.add_argument(
        "--cold-start-checkpoint",
        action="store_true",
        help="launch the exact v2 xar_checkpoint save instead of last_save.ck3",
    )
    native_auto_run_parser = commands.add_parser(
        "native-auto-run",
        help=(
            "own pure native CK3, plan bounded turns, verify progress, and "
            "checkpoint without MCP or visual fallback"
        ),
    )
    native_auto_run_parser.add_argument(
        "--turns",
        type=int,
        required=True,
        help="maximum number of planner turns",
    )
    native_auto_run_parser.add_argument("--timeout", type=float, default=21600)
    native_auto_run_parser.add_argument(
        "--readiness-timeout",
        type=float,
        default=300,
        help="maximum seconds to wait for a stable paused native map",
    )
    native_auto_run_parser.add_argument(
        "--cold-start-checkpoint",
        action="store_true",
        help="launch and bind the exact v2 xar_checkpoint save",
    )
    native_auto_run_parser.add_argument(
        "--route-contact-speed",
        type=int,
        choices=(1, 2, 3, 4, 5),
        default=3,
        help=(
            "timeline speed for proof-bound contact-free one-day route "
            "slices (default: 3)"
        ),
    )
    native_auto_run_parser.add_argument(
        "--allow-route-contact-high-speed-ab",
        action="store_true",
        help=(
            "admit explicit speed 4..5 route-contact A/B arms; speed 1..3 "
            "do not require this research flag"
        ),
    )
    native_auto_run_parser.add_argument(
        "--allow-committed-route-sentinel-canary",
        action="store_true",
        help=(
            "explicitly admit the research-only speed-3 committed-route "
            "sentinel; production default remains disabled"
        ),
    )
    one_generation_parser = commands.add_parser(
        "native-one-generation",
        help=(
            "run one fixed-seed ruler lifetime through the pure native "
            "observe-plan-act-verify loop and save blocker/terminal artifacts"
        ),
    )
    one_generation_parser.add_argument(
        "--max-turns",
        type=int,
        required=True,
        help="hard planner-turn bound; exhausting it is incomplete, never GREEN",
    )
    one_generation_parser.add_argument(
        "--timeout", type=float, default=604800
    )
    one_generation_parser.add_argument(
        "--readiness-timeout",
        type=float,
        default=300,
        help="maximum seconds to wait for a stable paused native map",
    )
    one_generation_parser.add_argument(
        "--checkpoint-every-advances",
        type=int,
        default=ONE_GENERATION_CHECKPOINT_CADENCE,
        help=(
            "eligible verified advances between durable checkpoints "
            f"(default: {ONE_GENERATION_CHECKPOINT_CADENCE})"
        ),
    )
    one_generation_parser.add_argument(
        "--route-contact-speed",
        type=int,
        choices=(1, 2, 3, 4, 5),
        default=3,
        help=(
            "timeline speed for proof-bound contact-free one-day route "
            "slices (default: 3)"
        ),
    )
    one_generation_parser.add_argument(
        "--allow-route-contact-high-speed-ab",
        action="store_true",
        help=(
            "admit explicit speed 4..5 route-contact A/B arms; speed 1..3 "
            "do not require this research flag"
        ),
    )
    one_generation_parser.add_argument(
        "--allow-committed-route-sentinel-canary",
        action="store_true",
        help=(
            "explicitly admit the research-only speed-3 committed-route "
            "sentinel; production default remains disabled"
        ),
    )
    commands.add_parser(
        "strategy-review",
        help="show one-life episode history and the priorities for the next run",
    )
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
        if (
            args.command
            in {"native-session", "native-auto-run", "native-one-generation"}
            and args.bridge_mode != "native-headless"
        ):
            raise AgentError(
                f"{args.command} requires --bridge-mode native-headless; "
                "use opening-dev-session for hybrid-fallback"
            )
        configure_native_bridge_launch_environment(
            args.bridge_mode,
            pipe_name=args.bridge_pipe,
            dll_path=args.bridge_dll,
            injector_path=args.bridge_injector,
        )
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
        elif args.command == "native-session":
            from .native_session import run_from_cli

            result = run_from_cli(
                spec,
                timeout_seconds=args.timeout,
                cold_start_checkpoint=args.cold_start_checkpoint,
            )
        elif args.command == "native-auto-run":
            from .native_auto_run import native_auto_run

            result = native_auto_run(
                spec,
                turn_count=args.turns,
                timeout_seconds=args.timeout,
                readiness_timeout_seconds=args.readiness_timeout,
                cold_start_checkpoint=args.cold_start_checkpoint,
                route_contact_timeline_speed=args.route_contact_speed,
                allow_route_contact_high_speed_ab=(
                    args.allow_route_contact_high_speed_ab
                ),
                allow_committed_route_sentinel_canary=(
                    args.allow_committed_route_sentinel_canary
                ),
            )
        elif args.command == "native-one-generation":
            from .one_generation_run import native_one_generation_run

            result = native_one_generation_run(
                spec,
                max_turns=args.max_turns,
                timeout_seconds=args.timeout,
                readiness_timeout_seconds=args.readiness_timeout,
                checkpoint_every_eligible_advances=(
                    args.checkpoint_every_advances
                ),
                route_contact_timeline_speed=args.route_contact_speed,
                allow_route_contact_high_speed_ab=(
                    args.allow_route_contact_high_speed_ab
                ),
                allow_committed_route_sentinel_canary=(
                    args.allow_committed_route_sentinel_canary
                ),
            )
        elif args.command == "strategy-review":
            from .strategy import read_one_life_strategy

            ensure_state_path_safe(spec.state_dir)
            result = read_one_life_strategy(spec.state_dir)
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
    if (
        args.command in {"native-auto-run", "native-one-generation"}
        and result.get("ok") is not True
    ):
        return 1
    return 0
