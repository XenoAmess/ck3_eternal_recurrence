"""Command line for Phase A environment preparation and smoke attestation."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import sys
import threading

from .environment import (
    doctor,
    ensure_state_path_safe,
    make_spec,
    prepare_profile,
    verify_profile,
)
from .errors import AgentError
from .bridge.succession_transition_contract import (
    ORDINARY_CAMPAIGN_SUCCESSION,
    ROGUE_ONE_LIFE,
)
from .locking import exclusive_state_lock
from .next_episode_run import NEXT_EPISODE_CHECKPOINT_CADENCE
from .one_generation_run import ONE_GENERATION_CHECKPOINT_CADENCE
from .runtime import (
    DEFAULT_NATIVE_BRIDGE_PIPE,
    NATIVE_BRIDGE_DISABLED,
    NATIVE_BRIDGE_LAUNCH_MODES,
    configure_native_bridge_launch_environment,
    smoke,
)


NATIVE_AUTO_RUN_STOP_REQUEST_FILENAME = "native-auto-run.stop"
NATIVE_AUTO_RUN_STOP_POLL_SECONDS = 0.05


@contextmanager
def _deferred_native_auto_run_sigint(
    stop_event: threading.Event,
    *,
    stop_request_file: Path | None = None,
):
    """Let a console signal or operator file stop at the next paused boundary."""
    if threading.current_thread() is not threading.main_thread():
        raise AgentError("native-auto-run CLI must run on the main thread")
    if stop_request_file is not None:
        ensure_state_path_safe(stop_request_file.parent)
        stop_request_file.parent.mkdir(parents=True, exist_ok=True)
    if stop_request_file is not None and stop_request_file.exists():
        raise AgentError(
            f"stale native-auto-run stop request file: {stop_request_file}; "
            "remove it before starting a new run"
        )
    previous = signal.getsignal(signal.SIGINT)
    watcher_done = threading.Event()
    file_request_seen = threading.Event()
    watcher: threading.Thread | None = None

    def request_stop(_signum: int, _frame: object) -> None:
        if stop_event.is_set():
            raise KeyboardInterrupt
        stop_event.set()
        print(
            "Stop requested; finishing the current turn and checkpoint.",
            file=sys.stderr,
            flush=True,
        )

    signal.signal(signal.SIGINT, request_stop)
    if stop_request_file is not None:
        def watch_stop_request() -> None:
            while not watcher_done.is_set():
                if stop_request_file.is_file():
                    file_request_seen.set()
                    stop_event.set()
                    print(
                        "Stop file detected; finishing the current turn and checkpoint.",
                        file=sys.stderr,
                        flush=True,
                    )
                    return
                watcher_done.wait(NATIVE_AUTO_RUN_STOP_POLL_SECONDS)

        watcher = threading.Thread(
            target=watch_stop_request,
            name="xar-native-auto-run-operator-stop-file",
            daemon=True,
        )
        watcher.start()
        print(
            f"Operator stop request file: {stop_request_file}",
            file=sys.stderr,
            flush=True,
        )
    try:
        yield
    finally:
        watcher_done.set()
        if watcher is not None:
            watcher.join()
        if file_request_seen.is_set() and stop_request_file is not None:
            try:
                stop_request_file.unlink()
            except OSError as error:
                print(
                    f"Could not clear stop request file {stop_request_file}: {error}",
                    file=sys.stderr,
                    flush=True,
                )
        signal.signal(signal.SIGINT, previous)


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
    prepare_profile_parser = commands.add_parser(
        "prepare-profile",
        help="build production runtime and exact growth + 100%% single-mod profile",
    )
    prepare_profile_parser.add_argument(
        "--xar-enabled",
        choices=("xar_on", "xar_off"),
        default="xar_on",
        help="freeze the main mod rule for this prepared profile",
    )
    prepare_profile_parser.add_argument(
        "--display-mode",
        choices=("fullscreen", "windowed"),
        default="fullscreen",
        help="freeze a fullscreen or 1280x720 windowed display profile",
    )
    verify_profile_parser = commands.add_parser(
        "verify-profile", help="verify the prepared profile contract"
    )
    verify_profile_parser.add_argument(
        "--xar-enabled",
        choices=("xar_on", "xar_off"),
        default="xar_on",
        help="require the prepared profile to use this main mod rule",
    )
    verify_profile_parser.add_argument(
        "--display-mode",
        choices=("fullscreen", "windowed"),
        default="fullscreen",
        help="require this exact prepared display mode",
    )
    ordinary_seed_rebind_parser = commands.add_parser(
        "rebind-ordinary-seed-v1",
        help=(
            "rebind a copied ordinary xar_off checkpoint to this prepared "
            "environment without launching CK3"
        ),
    )
    ordinary_seed_rebind_parser.add_argument(
        "--expected-pipe",
        required=True,
        help="require the copied driver state to retain this exact named pipe",
    )
    ordinary_seed_rebind_parser.add_argument(
        "--receipt",
        type=Path,
        required=True,
        help="write the versioned no-launch rebind receipt to this path",
    )
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
        "--succession-lifecycle",
        choices=(ROGUE_ONE_LIFE, ORDINARY_CAMPAIGN_SUCCESSION),
        default=ROGUE_ONE_LIFE,
        help=(
            "frozen campaign lifecycle; ordinary succession is accepted "
            "only for an xar_off fresh no-pact profile"
        ),
    )
    native_auto_run_parser.add_argument(
        "--ordinary-campaign-no-pact",
        action="store_true",
        help=(
            "attest that the ordinary xar_off candidate began as a fresh "
            "campaign and never signed the Eternal Recurrence pact"
        ),
    )
    native_auto_run_parser.add_argument(
        "--route-contact-speed",
        type=int,
        choices=(1, 2, 3, 4, 5),
        default=3,
        help=(
            "timeline speed for proof-bound one-day route slices and "
            "committed-route/stationary-objective native sentinels "
            "(default: 3)"
        ),
    )
    native_auto_run_parser.add_argument(
        "--allow-route-contact-high-speed-ab",
        action="store_true",
        help=(
            "admit explicit speed 4..5 route/contact and stationary-objective "
            "sentinel A/B arms; speed 1..3 do not require this research flag"
        ),
    )
    native_auto_run_parser.add_argument(
        "--allow-stationary-objective-hold-sentinel-canary",
        action="store_true",
        help=(
            "deprecated compatibility flag; the bounded seven-day speed-3 "
            "stationary objective-hold sentinel is production-enabled by "
            "default"
        ),
    )
    native_auto_run_parser.add_argument(
        "--allow-private-faction-gift-formal-trial",
        action="store_true",
        help=(
            "enable the unadvertised exact-build faction gift submit/receipt "
            "route for one bounded acceptance run"
        ),
    )
    native_auto_run_parser.add_argument(
        "--allow-private-construction-formal-trial",
        action="store_true",
        help=(
            "enable the unadvertised exact-build construction submit/receipt "
            "route for one bounded native-auto-run acceptance run"
        ),
    )
    native_auto_run_parser.add_argument(
        "--allow-private-family-marriage-formal-trial",
        action="store_true",
        help=(
            "enable one unadvertised exact-build first-heir marriage proposal "
            "with later bilateral result for a bounded native-auto-run"
        ),
    )
    native_auto_run_parser.add_argument(
        "--allow-private-m5-joint-collector",
        action="store_true",
        help=(
            "enable one unadvertised query-only peacetime building/faction "
            "proposal collection for a bounded native-auto-run"
        ),
    )
    native_auto_run_parser.add_argument(
        "--allow-private-lifestyle-formal-trial",
        action="store_true",
        help=(
            "enable the unadvertised exact-build lifestyle focus/perk "
            "submit/receipt route for one bounded native-auto-run acceptance run"
        ),
    )
    native_auto_run_parser.add_argument(
        "--allow-private-epidemic-recovery-near-pair",
        action="store_true",
        help=(
            "on a natural exact epidemic_events.0110.c, capture recovered "
            "county IDs before selection and read same-day county modifiers "
            "and legitimacy afterward in one bounded private run"
        ),
    )
    native_auto_run_parser.add_argument(
        "--require-initial-lifestyle-focus-before-date-advance",
        action="store_true",
        help=(
            "for a bounded new-campaign opening, require one private typed "
            "focus, independent receipt, checkpoint and following-turn "
            "consumption before any date-changing action"
        ),
    )
    construction_source_parser = commands.add_parser(
        "native-query-private-construction-source-v1",
        help="one unadvertised read-only construction source probe from a cold save",
    )
    construction_source_parser.add_argument("--timeout", type=float, default=390)
    construction_source_parser.add_argument(
        "--readiness-timeout", type=float, default=300,
    )
    construction_source_parser.add_argument(
        "--cold-start-checkpoint", action="store_true",
    )
    construction_source_parser.add_argument(
        "--ownership-round-id", required=True,
        help="monotonic CK3 ownership round R<number>; diagnostic remains private",
    )
    native_auto_run_parser.add_argument(
        "--private-faction-round-id",
        help="monotonic CK3 ownership round (R<number>) for the private trial",
    )
    timeline_query_parser = commands.add_parser(
        "native-query-current-timeline-blocker-context-v1",
        help=(
            "run one unadvertised exact-build paused timeline-blocker query "
            "under production native-session ownership"
        ),
    )
    timeline_query_parser.add_argument("--timeout", type=float, default=390)
    timeline_query_parser.add_argument(
        "--readiness-timeout",
        type=float,
        default=300,
        help="maximum seconds to wait for a stable paused native map",
    )
    timeline_query_parser.add_argument(
        "--cold-start-checkpoint",
        action="store_true",
        help="launch and bind the exact v2 xar_checkpoint save (required)",
    )
    timeline_query_parser.add_argument(
        "--private-timeline-query-round-id",
        required=True,
        help="monotonic CK3 ownership round R<number>; keeps this route private",
    )
    outbound_white_peace_query_parser = commands.add_parser(
        "native-query-outbound-war-white-peace-status-v1",
        help=(
            "cold-restore and issue one public sender-side pending "
            "white-peace query without gameplay or date advance"
        ),
    )
    outbound_white_peace_query_parser.add_argument("--war-id", type=int, required=True)
    outbound_white_peace_query_parser.add_argument("--timeout", type=float, default=390)
    outbound_white_peace_query_parser.add_argument(
        "--readiness-timeout", type=float, default=300
    )
    outbound_white_peace_query_parser.add_argument(
        "--cold-start-checkpoint",
        action="store_true",
        help="launch and bind the exact xar_checkpoint save (required)",
    )
    outbound_white_peace_query_parser.add_argument(
        "--ownership-round-id",
        required=True,
        help="monotonic CK3 ownership round R<number>",
    )
    timeline_action_parser = commands.add_parser(
        "native-continue-death-succession-modal-v1",
        help=(
            "run the single unadvertised exact-build death-succession typed "
            "Close, independent postcondition, life-advance, and checkpoint"
        ),
    )
    timeline_action_parser.add_argument("--timeout", type=float, default=390)
    timeline_action_parser.add_argument(
        "--readiness-timeout",
        type=float,
        default=300,
        help="maximum seconds to wait for the paused R777 source frame",
    )
    timeline_action_parser.add_argument(
        "--cold-start-checkpoint",
        action="store_true",
        help="launch and bind the exact sealed history-3 checkpoint (required)",
    )
    timeline_action_parser.add_argument(
        "--private-timeline-action-round-id",
        required=True,
        help="monotonic CK3 ownership round R<number>; keeps this route private",
    )
    timeline_action_parser.add_argument(
        "--expected-played-character-id", type=int, required=True
    )
    timeline_action_parser.add_argument(
        "--expected-episode-run-id", required=True
    )
    timeline_action_parser.add_argument(
        "--expected-date-raw", type=int, required=True
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
            "timeline speed for proof-bound one-day route slices and "
            "committed-route/stationary-objective native sentinels "
            "(default: 3)"
        ),
    )
    one_generation_parser.add_argument(
        "--allow-route-contact-high-speed-ab",
        action="store_true",
        help=(
            "admit explicit speed 4..5 route/contact and stationary-objective "
            "sentinel A/B arms; speed 1..3 do not require this research flag"
        ),
    )
    one_generation_parser.add_argument(
        "--allow-stationary-objective-hold-sentinel-canary",
        action="store_true",
        help=(
            "deprecated compatibility flag; the bounded seven-day speed-3 "
            "stationary objective-hold sentinel is production-enabled by "
            "default"
        ),
    )
    next_episode_parser = commands.add_parser(
        "native-next-episode",
        help=(
            "settle the current native episode, reload its immutable seed, "
            "execute visible gameplay, and save a new-run checkpoint"
        ),
    )
    next_episode_parser.add_argument(
        "--max-turns",
        type=int,
        required=True,
        help=(
            "hard planner-turn bound; exhausting it before the new-run "
            "checkpoint is incomplete"
        ),
    )
    next_episode_parser.add_argument("--timeout", type=float, default=21600)
    next_episode_parser.add_argument(
        "--readiness-timeout",
        type=float,
        default=300,
        help="maximum seconds to wait for a stable paused native map",
    )
    next_episode_parser.add_argument(
        "--checkpoint-every-advances",
        type=int,
        default=NEXT_EPISODE_CHECKPOINT_CADENCE,
        help=(
            "eligible verified new-episode advances before its checkpoint "
            f"(default: {NEXT_EPISODE_CHECKPOINT_CADENCE})"
        ),
    )
    next_episode_parser.add_argument(
        "--route-contact-speed",
        type=int,
        choices=(1, 2, 3, 4, 5),
        default=3,
        help=(
            "timeline speed for proof-bound route/contact and stationary "
            "objective sentinels (default: 3)"
        ),
    )
    next_episode_parser.add_argument(
        "--allow-route-contact-high-speed-ab",
        action="store_true",
        help="admit explicit speed 4..5 route/contact A/B arms",
    )
    next_episode_parser.add_argument(
        "--allow-stationary-objective-hold-sentinel-canary",
        action="store_true",
        help=(
            "deprecated compatibility flag; the bounded seven-day speed-3 "
            "stationary objective-hold sentinel is production-enabled by "
            "default"
        ),
    )
    one_generation_preflight_parser = commands.add_parser(
        "native-one-generation-preflight",
        help=(
            "verify the prepared profile and exact one-generation resume "
            "anchor without launching CK3"
        ),
    )
    one_generation_preflight_parser.add_argument(
        "--expected-character-id",
        type=int,
        required=True,
        help="require the durable episode to belong to this CharacterID",
    )
    one_generation_preflight_parser.add_argument(
        "--expected-episode-run-id",
        required=True,
        help="require the durable episode to have this exact run ID",
    )
    one_generation_preflight_parser.add_argument(
        "--expected-checkpoint-sha256",
        required=True,
        help="require this exact checkpoint SHA-256",
    )
    one_generation_preflight_parser.add_argument(
        "--expected-driver-state-sha256",
        required=True,
        help="require this exact driver-state SHA-256",
    )
    one_generation_preflight_parser.add_argument(
        "--xar-enabled",
        choices=("xar_on", "xar_off"),
        default="xar_on",
        help="require the prepared profile to use this main mod rule",
    )
    one_generation_preflight_parser.add_argument(
        "--succession-lifecycle",
        choices=(ROGUE_ONE_LIFE, ORDINARY_CAMPAIGN_SUCCESSION),
        default=ROGUE_ONE_LIFE,
        help="require this frozen succession lifecycle on the resume anchor",
    )
    one_generation_preflight_parser.add_argument(
        "--ordinary-campaign-no-pact",
        action="store_true",
        help=(
            "attest that an ordinary xar_off checkpoint comes from a fresh "
            "campaign that never signed the Eternal Recurrence pact"
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
            "display": payload["display"],
        }
    if command == "verify-profile":
        return {
            "ok": True,
            "profile_dir": payload["profile_dir"],
            "environment_sha256": payload["environment_sha256"],
            "display": payload["display"],
        }
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    spec = make_spec(args.state_dir, args.game_dir)
    try:
        if (
            args.command
            in {
                "native-session",
                "native-auto-run",
                "native-query-current-timeline-blocker-context-v1",
                "native-query-private-construction-source-v1",
                "native-query-outbound-war-white-peace-status-v1",
                "native-continue-death-succession-modal-v1",
                "native-one-generation",
                "native-next-episode",
            }
            and args.bridge_mode != "native-headless"
        ):
            raise AgentError(
                f"{args.command} requires --bridge-mode native-headless; "
                "use opening-dev-session for hybrid-fallback"
            )
        if args.command not in {
            "native-one-generation-preflight",
            "rebind-ordinary-seed-v1",
        }:
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
            result = prepare_profile(
                spec, xar_enabled=args.xar_enabled, display_mode=args.display_mode
            )
        elif args.command == "verify-profile":
            ensure_state_path_safe(spec.state_dir)
            with exclusive_state_lock(spec.state_dir, "verify-profile"):
                result = verify_profile(
                    spec, xar_enabled=args.xar_enabled, display_mode=args.display_mode
                )
        elif args.command == "rebind-ordinary-seed-v1":
            from .environment import write_json_atomic
            from .ordinary_seed_rebinder import rebind_ordinary_seed_v1

            result = rebind_ordinary_seed_v1(
                spec,
                expected_pipe_name=args.expected_pipe,
            )
            write_json_atomic(args.receipt.resolve(), result)
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

            operator_stop_event = threading.Event()
            stop_request_file = (
                spec.state_dir / NATIVE_AUTO_RUN_STOP_REQUEST_FILENAME
            )
            with _deferred_native_auto_run_sigint(
                operator_stop_event,
                stop_request_file=stop_request_file,
            ):
                private_faction_options = (
                    {
                        "allow_private_faction_gift_formal_trial": True,
                        "private_faction_round_id": args.private_faction_round_id,
                    }
                    if args.allow_private_faction_gift_formal_trial
                    else {}
                )
                private_construction_options = (
                    {"allow_private_construction_formal_trial": True}
                    if args.allow_private_construction_formal_trial
                    else {}
                )
                private_family_marriage_options = (
                    {"allow_private_family_marriage_formal_trial": True}
                    if args.allow_private_family_marriage_formal_trial
                    else {}
                )
                private_m5_options = (
                    {"allow_private_m5_joint_collector": True}
                    if args.allow_private_m5_joint_collector
                    else {}
                )
                private_lifestyle_options = {}
                if args.allow_private_lifestyle_formal_trial:
                    private_lifestyle_options["allow_private_lifestyle_formal_trial"] = True
                if args.require_initial_lifestyle_focus_before_date_advance:
                    private_lifestyle_options[
                        "require_initial_lifestyle_focus_before_date_advance"
                    ] = True
                private_epidemic_options = (
                    {"allow_private_epidemic_recovery_near_pair": True}
                    if args.allow_private_epidemic_recovery_near_pair
                    else {}
                )
                succession_options = (
                    {
                        "succession_lifecycle": args.succession_lifecycle,
                        "ordinary_campaign_no_pact": (
                            args.ordinary_campaign_no_pact
                        ),
                    }
                    if (
                        args.succession_lifecycle
                        != ROGUE_ONE_LIFE
                        or args.ordinary_campaign_no_pact
                    )
                    else {}
                )
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
                    allow_stationary_objective_hold_sentinel_canary=(
                        args.allow_stationary_objective_hold_sentinel_canary
                    ),
                    **private_faction_options,
                    **private_construction_options,
                    **private_family_marriage_options,
                    **private_m5_options,
                    **private_lifestyle_options,
                    **private_epidemic_options,
                    **succession_options,
                    operator_stop_event=operator_stop_event,
                )
        elif args.command == "native-query-current-timeline-blocker-context-v1":
            from .timeline_blocker_query_run import (
                query_current_timeline_blocker_once,
            )

            result = query_current_timeline_blocker_once(
                spec,
                timeout_seconds=args.timeout,
                readiness_timeout_seconds=args.readiness_timeout,
                private_timeline_query_round_id=(
                    args.private_timeline_query_round_id
                ),
                cold_start_checkpoint=args.cold_start_checkpoint,
            )
        elif args.command == "native-query-private-construction-source-v1":
            from .construction_source_query_run import (
                query_private_construction_source_once,
            )

            result = query_private_construction_source_once(
                spec,
                timeout_seconds=args.timeout,
                readiness_timeout_seconds=args.readiness_timeout,
                ownership_round_id=args.ownership_round_id,
                cold_start_checkpoint=args.cold_start_checkpoint,
            )
        elif args.command == "native-query-outbound-war-white-peace-status-v1":
            from .outbound_white_peace_status_query_run import (
                query_outbound_white_peace_status_once,
            )

            result = query_outbound_white_peace_status_once(
                spec,
                war_id=args.war_id,
                timeout_seconds=args.timeout,
                readiness_timeout_seconds=args.readiness_timeout,
                ownership_round_id=args.ownership_round_id,
                cold_start_checkpoint=args.cold_start_checkpoint,
            )
        elif args.command == "native-continue-death-succession-modal-v1":
            from .timeline_blocker_action_run import (
                continue_death_succession_modal_once,
            )

            result = continue_death_succession_modal_once(
                spec,
                timeout_seconds=args.timeout,
                readiness_timeout_seconds=args.readiness_timeout,
                private_timeline_action_round_id=(
                    args.private_timeline_action_round_id
                ),
                expected_played_character_id=(
                    args.expected_played_character_id
                ),
                expected_episode_run_id=args.expected_episode_run_id,
                expected_date_raw=args.expected_date_raw,
                cold_start_checkpoint=args.cold_start_checkpoint,
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
                allow_stationary_objective_hold_sentinel_canary=(
                    args.allow_stationary_objective_hold_sentinel_canary
                ),
            )
        elif args.command == "native-next-episode":
            from .next_episode_run import native_next_episode_run

            result = native_next_episode_run(
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
                allow_stationary_objective_hold_sentinel_canary=(
                    args.allow_stationary_objective_hold_sentinel_canary
                ),
            )
        elif args.command == "native-one-generation-preflight":
            from .one_generation_preflight import (
                native_one_generation_preflight,
            )

            result = native_one_generation_preflight(
                spec,
                pipe_name=args.bridge_pipe,
                expected_character_id=args.expected_character_id,
                expected_episode_run_id=args.expected_episode_run_id,
                expected_checkpoint_sha256=(
                    args.expected_checkpoint_sha256
                ),
                expected_driver_state_sha256=(
                    args.expected_driver_state_sha256
                ),
                xar_enabled=args.xar_enabled,
                succession_lifecycle=args.succession_lifecycle,
                ordinary_campaign_no_pact=args.ordinary_campaign_no_pact,
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
        args.command
        in {
            "native-auto-run",
            "native-query-current-timeline-blocker-context-v1",
            "native-query-private-construction-source-v1",
            "native-query-outbound-war-white-peace-status-v1",
            "native-continue-death-succession-modal-v1",
            "native-one-generation",
            "native-next-episode",
            "native-one-generation-preflight",
        }
        and result.get("ok") is not True
    ):
        if (
            args.command == "native-auto-run"
            and result.get("status") == "operator_stop_checkpointed"
            and result.get("outcome") == "operator_stopped"
            and result.get("cleanup", {}).get("ok") is True
        ):
            return 0
        return 1
    return 0
