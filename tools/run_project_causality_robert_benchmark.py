#!/usr/bin/env python3
"""Run and evidence the complete Robert 1066 promotional benchmark.

This is an orchestration layer for filming.  It deliberately reuses the
current autonomous-player implementation without becoming part of its runtime
fingerprint: one managed CK3 process starts at the 1066 ruler-selection flow,
completes Robert's opening, then executes the existing fixed Palermo war path
through victory, disband and checkpoint.

The result is a current-run benchmark artifact.  It is not evidence of a
general war planner for arbitrary rulers, targets or game builds.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import time
import uuid


class BenchmarkError(RuntimeError):
    """A benchmark stage could not reach its verified postcondition."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agent-root",
        type=Path,
        default=Path(r"Z:\ck3_mod_rewrite"),
        help="repository whose current autonomous-player code will be used",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        required=True,
        help="prepared external XarAutoplayer state directory",
    )
    parser.add_argument(
        "--game-dir",
        type=Path,
        default=Path(r"Z:\ck3_mod_rewrite\Crusader Kings III"),
    )
    parser.add_argument("--timeout", type=float, default=7200.0)
    parser.add_argument("--max-war-months", type=int, default=18)
    parser.add_argument("--stage-hold", type=float, default=1.5)
    parser.add_argument(
        "--resume-saved-game",
        action="store_true",
        help="continue the isolated autosave instead of repeating ruler selection",
    )
    parser.add_argument(
        "--continuation-of-report",
        type=Path,
        help="fresh-opening report that owns the autosave used by this continuation",
    )
    parser.add_argument(
        "--resume-active-war",
        action="store_true",
        help="resume a post-declaration checkpoint and skip declaring the same war again",
    )
    parser.add_argument(
        "--resume-war-progress",
        action="store_true",
        help="resume an autosave after armies were raised and Palermo was occupied",
    )
    parser.add_argument(
        "--preflight-settle",
        type=float,
        default=20.0,
        help="seconds to let the fullscreen main menu become responsive after mount attestation",
    )
    return parser


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: object) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> int:
    args = _parser().parse_args()
    if args.timeout <= 0:
        raise BenchmarkError("--timeout must be positive")
    if not 1 <= args.max_war_months <= 72:
        raise BenchmarkError("--max-war-months must be between 1 and 72")
    if args.stage_hold < 0 or args.stage_hold > 15:
        raise BenchmarkError("--stage-hold must be between 0 and 15 seconds")
    if args.preflight_settle < 0 or args.preflight_settle > 120:
        raise BenchmarkError("--preflight-settle must be between 0 and 120 seconds")
    if args.resume_saved_game and args.continuation_of_report is None:
        raise BenchmarkError("--resume-saved-game requires --continuation-of-report")
    if args.resume_active_war and not args.resume_saved_game:
        raise BenchmarkError("--resume-active-war requires --resume-saved-game")
    if args.resume_war_progress and not args.resume_active_war:
        raise BenchmarkError("--resume-war-progress requires --resume-active-war")

    agent_root = args.agent_root.resolve()
    package_root = agent_root / "ck3_autonomous_player" / "src"
    if not package_root.is_dir():
        raise BenchmarkError(f"autonomous-player package is missing: {package_root}")
    sys.path.insert(0, str(package_root))

    from xar_autoplayer.environment import (  # noqa: E402
        ck3_process_inventory,
        doctor,
        ensure_state_path_safe,
        make_spec,
        sha256_file,
        verify_profile,
        write_json_atomic,
    )
    from xar_autoplayer.errors import AgentError  # noqa: E402
    from xar_autoplayer.locking import (  # noqa: E402
        exclusive_launch_lock,
        exclusive_state_lock,
    )
    from xar_autoplayer.opening_smoke import (  # noqa: E402
        OPENING_CONTRACT,
        _drive_opening,
    )
    from xar_autoplayer.runtime import (  # noqa: E402
        append_event,
        launch,
        stop_tracked,
        wait_for_runtime_attestation,
    )

    state_dir = args.state_dir.resolve()
    spec = make_spec(state_dir=state_dir, game_dir=args.game_dir.resolve())
    ensure_state_path_safe(spec.state_dir)
    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-project-causality-robert-"
        + uuid.uuid4().hex[:8]
    )
    run_dir = spec.state_dir / "runs" / run_id
    artifacts = run_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=False)
    events = run_dir / "events.jsonl"
    report_path = run_dir / "report.json"
    report: dict[str, object] = {
        "format_version": 1,
        "kind": "project_causality_robert_1066_complete_benchmark",
        "run_id": run_id,
        "started_at": _utc_now(),
        "classification": "current-fixed-robert-benchmark",
        "capability_boundary": (
            "Current code, fresh run, fixed Robert 1066 to Palermo path. "
            "Not general war autonomy for arbitrary rulers or targets."
        ),
        "resume_saved_game": bool(args.resume_saved_game),
        "resume_active_war": bool(args.resume_active_war),
        "resume_war_progress": bool(args.resume_war_progress),
        "continuation_of_report": (
            str(args.continuation_of_report.resolve())
            if args.continuation_of_report is not None
            else None
        ),
        "commands": [],
        "finalized": False,
        "ok": False,
    }
    _write_json(report_path, report)
    deadline = time.monotonic() + float(args.timeout)
    handle = None
    primary_error: BaseException | None = None

    def remaining(stage: str) -> float:
        value = deadline - time.monotonic()
        if value <= 0:
            raise BenchmarkError(f"benchmark timeout during {stage}")
        return value

    def save_report() -> None:
        _write_json(report_path, report)

    with exclusive_launch_lock(spec.game_exe):
        with exclusive_state_lock(spec.state_dir, "project-causality-robert-benchmark"):
            try:
                manifest = verify_profile(spec)
                doctor(spec, require_prepared=True)
                if ck3_process_inventory()["processes"]:
                    raise BenchmarkError("CK3 is already running")
                report["environment_sha256"] = manifest.get("environment_sha256")
                report["agent_runtime_sha256"] = manifest.get("agent_runtime", {}).get(
                    "sha256"
                )

                contract = run_dir / "opening-ui-contract.json"
                shutil.copy2(OPENING_CONTRACT, contract)
                contract_sha256 = sha256_file(contract)
                report["contract"] = {
                    "path": str(contract),
                    "sha256": contract_sha256,
                }
                save_report()

                handle = launch(spec)
                report["process"] = {
                    "pid": int(handle.process.pid),
                    "creation_date": handle.ck3_creation_date,
                }
                append_event(events, {"kind": "ck3_launched", "pid": handle.process.pid})
                report["load_attestation"] = wait_for_runtime_attestation(
                    spec,
                    handle,
                    remaining("runtime load attestation"),
                )
                append_event(events, {"kind": "single_mod_runtime_attested"})
                # Mount evidence arrives before the fullscreen menu necessarily
                # finishes its first responsive paint on this machine.  The
                # visual driver still performs its own strict responsive gate;
                # this hold only prevents racing that gate during cold startup.
                report["preflight_settle_seconds"] = args.preflight_settle
                save_report()
                time.sleep(args.preflight_settle)

                opening_started = _utc_now()
                opening = _drive_opening(
                    spec,
                    handle,
                    manifest,
                    artifacts,
                    events,
                    contract,
                    contract_sha256,
                    deadline,
                    ordinary_event_count=(0 if args.resume_saved_game else 1),
                    inspect_map_panels=(not args.resume_saved_game),
                    construct_economic_building=False,
                    assign_steward_development=False,
                    development_step=None,
                    resume_saved_game=bool(args.resume_saved_game),
                )
                report["opening"] = opening
                report["commands"].append(
                    {
                        "index": 0,
                        "command": (
                            "resume-robert-1066-autosave"
                            if args.resume_saved_game
                            else "fresh-robert-1066-opening"
                        ),
                        "started_at": opening_started,
                        "finished_at": _utc_now(),
                        "ok": True,
                        "result": opening,
                    }
                )
                save_report()
                time.sleep(args.stage_hold)

                command_index = 0

                def execute(command: str) -> dict[str, object]:
                    nonlocal command_index
                    command_index += 1
                    record: dict[str, object] = {
                        "index": command_index,
                        "command": command,
                        "started_at": _utc_now(),
                        "ok": False,
                    }
                    report["commands"].append(record)
                    save_report()
                    try:
                        result = _drive_opening(
                            spec,
                            handle,
                            manifest,
                            artifacts,
                            events,
                            contract,
                            contract_sha256,
                            deadline,
                            ordinary_event_count=0,
                            development_step=command,
                            resume_saved_game=False,
                        )
                    except Exception as error:
                        record["error"] = f"{type(error).__name__}: {error}"
                        record["finished_at"] = _utc_now()
                        save_report()
                        raise
                    record.update(
                        {
                            "ok": True,
                            "result": result,
                            "finished_at": _utc_now(),
                        }
                    )
                    save_report()
                    time.sleep(args.stage_hold)
                    return result

                def execute_with_event_recovery(
                    command: str,
                    *,
                    attempts: int = 3,
                ) -> dict[str, object]:
                    last_error: AgentError | None = None
                    for attempt in range(1, attempts + 1):
                        try:
                            return execute(command)
                        except AgentError as error:
                            last_error = error
                            report.setdefault("recovered_interruptions", []).append(
                                {
                                    "command": command,
                                    "attempt": attempt,
                                    "error": f"{type(error).__name__}: {error}",
                                }
                            )
                            save_report()
                            if attempt == attempts:
                                break
                            event_resolved = False
                            for recovery_attempt in range(1, 4):
                                try:
                                    execute("resolve-current-event")
                                    event_resolved = True
                                    break
                                except AgentError as recovery_error:
                                    report.setdefault(
                                        "event_recovery_retries", []
                                    ).append(
                                        {
                                            "command": command,
                                            "command_attempt": attempt,
                                            "recovery_attempt": recovery_attempt,
                                            "error": (
                                                f"{type(recovery_error).__name__}: "
                                                f"{recovery_error}"
                                            ),
                                        }
                                    )
                                    save_report()
                                    time.sleep(args.stage_hold)
                            if not event_resolved:
                                # The transient event may have disappeared or
                                # changed while the two-frame stability gate
                                # was observing it.  Re-observe by retrying the
                                # original command; it will either proceed from
                                # the map or report the still-visible blocker.
                                continue
                    assert last_error is not None
                    raise last_error

                # Existing current-version steps, joined into one benchmark.
                # The continuation reuses the fresh run's already recorded
                # dynasty and succession review rather than repeating it.
                if not args.resume_saved_game:
                    execute("dynasty-review")
                    execute("succession-review")
                execute("war-review")
                # ``war-declare-palermo`` owns the complete target-selection
                # and declaration sequence.  Calling ``war-target-review``
                # immediately before it toggles the same visible target a
                # second time and can close the ruler selection that the
                # declaration command expects to establish itself.
                if not args.resume_active_war:
                    execute("war-declare-palermo")
                if not args.resume_war_progress:
                    execute("war-raise-all")
                    execute_with_event_recovery("war-siege-palermo")

                victory = False
                last_score: int | None = None
                for month in range(1, args.max_war_months + 1):
                    execute_with_event_recovery(
                        "war-advance-month",
                        attempts=12,
                    )
                    status = execute("war-status")
                    war_status = status.get("war_status")
                    score = (
                        war_status.get("war_score_percent")
                        if isinstance(war_status, dict)
                        else None
                    )
                    last_score = score if isinstance(score, int) else last_score
                    if last_score is not None and last_score >= 100:
                        report["victory_month"] = month
                        execute("war-enforce-demands")
                        victory = True
                        break
                if not victory:
                    raise BenchmarkError(
                        "Palermo did not reach 100% war score within "
                        f"{args.max_war_months} months; last score={last_score!r}"
                    )
                execute("war-disband-armies")
                execute("save-checkpoint")
                report["milestone"] = {
                    "opening_from_ruler_selection": True,
                    "event_decision": True,
                    "character_and_realm_review": True,
                    "war_target": "Palermo",
                    "war_declared": True,
                    "armies_raised": True,
                    "army_moved_to_target": True,
                    "victory_enforced": True,
                    "armies_disbanded": True,
                    "checkpoint_saved": True,
                }
            except BaseException as error:
                primary_error = error
                report["error"] = f"{type(error).__name__}: {error}"
            finally:
                if handle is not None:
                    try:
                        report["shutdown_attestation"] = stop_tracked(
                            handle,
                            require_running=primary_error is None,
                        )
                    except BaseException as error:
                        report["shutdown_error"] = f"{type(error).__name__}: {error}"
                        if primary_error is None:
                            primary_error = error
                report["finished_at"] = _utc_now()
                report["ok"] = primary_error is None
                report["finalized"] = True
                write_json_atomic(report_path, report)

    print(json.dumps({"report": str(report_path), "ok": report["ok"]}, ensure_ascii=False))
    if primary_error is not None:
        raise BenchmarkError(
            f"Robert benchmark failed; report={report_path}: {primary_error}"
        ) from primary_error
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BenchmarkError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
