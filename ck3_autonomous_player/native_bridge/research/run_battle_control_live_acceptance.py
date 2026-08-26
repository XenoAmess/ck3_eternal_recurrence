#!/usr/bin/env python3
"""Run one managed exact-build battle-control live probe.

This helper deliberately owns only one CK3 session.  A caller can first load
the profile's ``last_save.ck3`` and materialize a managed checkpoint, then run
the helper again with ``--cold-start-checkpoint`` to prove cold restoration.
All process cleanup remains inside the production native-session supervisor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import threading
import time
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.environment import make_spec  # noqa: E402
from xar_autoplayer.native_auto_run import (  # noqa: E402
    _cleanup_report,
    _wait_for_readiness,
)
from xar_autoplayer.native_session import native_session  # noqa: E402
from xar_autoplayer.runtime import NativeBridgeLaunchConfig, utc_now  # noqa: E402


PURE_NATIVE_MODE = "native-headless"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--subject-army-id", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=420.0)
    parser.add_argument("--readiness-timeout", type=float, default=180.0)
    parser.add_argument("--cold-start-checkpoint", action="store_true")
    parser.add_argument("--save-checkpoint", action="store_true")
    parser.add_argument("--advance-days", type=int, default=0)
    return parser


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _subject(snapshot: dict[str, object], army_id: int) -> dict[str, object] | None:
    armies = snapshot.get("player_armies")
    if not isinstance(armies, list):
        return None
    for row in armies:
        if isinstance(row, dict) and row.get("army_id") == army_id:
            return row
    return None


def _compact_snapshot(
    snapshot: dict[str, object], subject_army_id: int
) -> dict[str, object]:
    return {
        key: snapshot.get(key)
        for key in (
            "snapshot_id",
            "revision",
            "native_revision",
            "date_raw",
            "phase",
            "map_ready",
            "paused",
            "episode_character_id",
            "episode_run_id",
            "active_event",
            "active_wars",
        )
    } | {"subject_army": _subject(snapshot, subject_army_id)}


def _compact_session_report(report: object) -> object:
    if not isinstance(report, dict):
        return report
    return {
        key: report.get(key)
        for key in (
            "pid",
            "pipe",
            "started_at",
            "finished_at",
            "elapsed_seconds",
            "exit_reason",
            "process_exit_code",
            "restart_count",
            "restart_shutdowns",
            "shutdown",
            "cold_start_checkpoint",
            "ok",
        )
    }


def _query_pair(
    service: GameplayBridgeService,
    subject_army_id: int,
    snapshot: dict[str, object],
) -> dict[str, object]:
    revision = snapshot.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int):
        raise RuntimeError("paused snapshot lacks a valid public revision")
    first = service.query_battle_control_snapshot_v1(
        subject_army_id,
        expected_revision=revision,
    )
    second = service.query_battle_control_snapshot_v1(
        subject_army_id,
        expected_revision=revision,
    )
    first_frame = first["battle_control_snapshot"]
    second_frame = second["battle_control_snapshot"]
    stable = first_frame == second_frame
    first_sequence = first.get("query_sequence")
    second_sequence = second.get("query_sequence")
    sequence_increased = bool(
        isinstance(first_sequence, int)
        and not isinstance(first_sequence, bool)
        and isinstance(second_sequence, int)
        and not isinstance(second_sequence, bool)
        and second_sequence > first_sequence
    )
    return {
        "first": first,
        "second": second,
        "frame_sha256": _canonical_sha256(first_frame),
        "immediate_frame_equal": stable,
        "query_sequence_increased": sequence_increased,
        "ok": stable and sequence_increased,
    }


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started_wall = utc_now()
    started = time.monotonic()
    spec = make_spec(args.state_dir, args.game_dir)
    config = NativeBridgeLaunchConfig(
        mode=PURE_NATIVE_MODE,
        pipe_name=args.bridge_pipe,
        dll_path=args.bridge_dll.resolve(),
        injector_path=args.bridge_injector.resolve(),
    )
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    session_thread: threading.Thread | None = None
    primary_error: str | None = None
    readiness: dict[str, object] | None = None
    initial_snapshot: dict[str, object] | None = None
    query_pair: dict[str, object] | None = None
    checkpoint: dict[str, object] | None = None
    advances: list[dict[str, object]] = []
    driver_closed = False

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec,
                timeout_seconds=float(args.timeout) + 90.0,
                native_bridge=config,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=bool(args.cold_start_checkpoint),
                stop_event=stop_event,
            )
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    try:
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        session_thread = threading.Thread(
            target=supervise,
            name="xar-battle-control-live-session",
            daemon=False,
        )
        session_thread.start()
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=float(args.readiness_timeout),
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=bool(args.cold_start_checkpoint),
            allow_terminal=False,
        )
        initial_snapshot = service.snapshot()
        subject = _subject(initial_snapshot, args.subject_army_id)
        if not (
            isinstance(subject, dict)
            and subject.get("controllable") is True
            and subject.get("in_combat") is True
        ):
            raise RuntimeError("subject army is not controllable in active combat")
        query_pair = _query_pair(service, args.subject_army_id, initial_snapshot)
        if query_pair.get("ok") is not True:
            raise RuntimeError("immediate repeated battle frames differ")

        if args.save_checkpoint:
            current = service.snapshot()
            checkpoint = service.save_checkpoint(
                expected_revision=int(current["revision"])
            )

        previous_frame = query_pair["first"]["battle_control_snapshot"]
        for day_index in range(1, args.advance_days + 1):
            before = service.snapshot()
            result = service.execute_step(
                "life-advance", expected_revision=int(before["revision"])
            )
            binding = _wait_for_readiness(
                driver,
                session_done=session_done,
                session_state=session_state,
                timeout_seconds=float(args.readiness_timeout),
                stable_seconds=0.0,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=False,
                allow_terminal=True,
            )
            after = service.snapshot()
            after_subject = _subject(after, args.subject_army_id)
            row: dict[str, object] = {
                "day_index": day_index,
                "before": _compact_snapshot(before, args.subject_army_id),
                "advance": result,
                "readiness": binding,
                "after": _compact_snapshot(after, args.subject_army_id),
                "battle_query": None,
                "frame_changed": None,
            }
            if (
                isinstance(after_subject, dict)
                and after_subject.get("controllable") is True
                and after_subject.get("in_combat") is True
            ):
                pair = _query_pair(service, args.subject_army_id, after)
                current_frame = pair["first"]["battle_control_snapshot"]
                row["battle_query"] = pair
                row["frame_changed"] = current_frame != previous_frame
                previous_frame = current_frame
            else:
                row["terminal_discriminant"] = {
                    "subject_present": isinstance(after_subject, dict),
                    "in_combat": (
                        after_subject.get("in_combat")
                        if isinstance(after_subject, dict)
                        else None
                    ),
                    "retreating": (
                        after_subject.get("retreating")
                        if isinstance(after_subject, dict)
                        else None
                    ),
                    "active_wars": after.get("active_wars"),
                }
            advances.append(row)
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if session_thread is not None:
            session_thread.join()
        stop_elapsed = round(max(0.0, time.monotonic() - stop_started), 3)
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                detail = f"{type(error).__name__}: {error}"
                primary_error = (
                    detail
                    if primary_error is None
                    else f"{primary_error}; driver close failed: {detail}"
                )

    cleanup = _cleanup_report(
        session_state.get("report"),
        session_error=session_state.get("error"),
        driver_closed=driver_closed,
        elapsed_seconds=stop_elapsed,
    )
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            session_state.get("error")
            or cleanup.get("reason")
            or "managed cleanup was not proven"
        )
    advance_ok = all(
        (
            row.get("battle_query") is not None
            and isinstance(row.get("battle_query"), dict)
            and row["battle_query"].get("ok") is True
            and row.get("frame_changed") is True
        )
        or isinstance(row.get("terminal_discriminant"), dict)
        for row in advances
    )
    ok = bool(
        primary_error is None
        and query_pair is not None
        and query_pair.get("ok") is True
        and cleanup.get("ok") is True
        and advance_ok
    )
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_battle_control_snapshot_v1_live_acceptance",
        "started_at": started_wall,
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "load_kind": (
            "cold_checkpoint" if args.cold_start_checkpoint else "continue_last_save"
        ),
        "subject_army_id": args.subject_army_id,
        "identity": {
            "pipe": config.pipe_name,
            "bridge_dll": str(config.dll_path),
            "bridge_dll_sha256": _sha256_file(config.dll_path),
            "bridge_injector": str(config.injector_path),
            "bridge_injector_sha256": _sha256_file(config.injector_path),
        },
        "readiness": readiness,
        "initial_snapshot": (
            _compact_snapshot(initial_snapshot, args.subject_army_id)
            if initial_snapshot is not None
            else None
        ),
        "initial_query_pair": query_pair,
        "checkpoint": checkpoint,
        "advances": advances,
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": primary_error,
    }
    return payload, 0 if ok else 1


def main() -> int:
    args = _parser().parse_args()
    if args.advance_days < 0:
        raise SystemExit("--advance-days must be non-negative")
    payload, exit_code = _run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "ok": payload["ok"],
        "output": str(args.output.resolve()),
        "frame_sha256": (
            payload.get("initial_query_pair", {}).get("frame_sha256")
            if isinstance(payload.get("initial_query_pair"), dict)
            else None
        ),
        "cleanup": payload["cleanup"],
        "error": payload["error"],
    }, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
