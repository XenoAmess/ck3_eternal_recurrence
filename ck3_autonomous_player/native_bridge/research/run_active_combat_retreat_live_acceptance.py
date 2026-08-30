#!/usr/bin/env python3
"""Run one managed active-combat retreat transition probe.

The helper owns exactly one CK3 process tree.  It advances an immutable battle
checkpoint to the requested day, proves legality plus one exact native route,
consumes the resulting battle-bound token, proves the immediate retreating
army semantics, and then reads the prior full-generation CombatID without a
selected-army eligibility dependency.  A full-side run is GREEN only when the
old combat reaches an explicit terminal/reopen transition or is generation-
checked as removed.  An owner-subset run instead requires the affected owner
rows to leave while every unaffected same-side row remains in the old combat.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import threading
import time


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
    parser.add_argument("--target-province-id", type=int, required=True)
    parser.add_argument(
        "--expected-scope",
        choices=("full_side", "owner_subset"),
        default="full_side",
    )
    parser.add_argument("--advance-days-before-preview", type=int, default=15)
    parser.add_argument("--postcondition-timeout", type=float, default=10.0)
    parser.add_argument("--timeout", type=float, default=480.0)
    parser.add_argument("--readiness-timeout", type=float, default=180.0)
    parser.add_argument("--cold-start-checkpoint", action="store_true")
    return parser


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _subject(
    snapshot: dict[str, object], army_id: int
) -> dict[str, object] | None:
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


def _route_reaches(subject: object, target_province_id: int) -> bool:
    if not isinstance(subject, dict):
        return False
    route = subject.get("route_province_ids")
    return bool(
        isinstance(route, list)
        and route
        and route[-1] == target_province_id
    )


def _retreat_semantic_ready(
    snapshot: dict[str, object],
    subject_army_id: int,
    target_province_id: int,
) -> bool:
    subject = _subject(snapshot, subject_army_id)
    if subject is None:
        compact_subject = snapshot.get("subject_army")
        if (
            isinstance(compact_subject, dict)
            and compact_subject.get("army_id") == subject_army_id
        ):
            subject = compact_subject
    return bool(
        isinstance(subject, dict)
        and subject.get("retreating") is True
        and subject.get("move_target_province_id") == target_province_id
        and _route_reaches(subject, target_province_id)
    )


def _battle_combat_id(pre_action_battle: object) -> int | None:
    if not isinstance(pre_action_battle, dict):
        return None
    direct = pre_action_battle.get("combat_id")
    if (
        isinstance(direct, int)
        and not isinstance(direct, bool)
        and -(2**31) <= direct <= 2**31 - 1
        and direct != -1
    ):
        return direct
    frame = pre_action_battle.get("battle_control_snapshot")
    if not isinstance(frame, dict):
        return None
    nested = frame.get("combat_id")
    return (
        nested
        if isinstance(nested, int)
        and not isinstance(nested, bool)
        and -(2**31) <= nested <= 2**31 - 1
        and nested != -1
        else None
    )


def _full_side_transition_ready(
    transition: object,
    pre_action_battle: object,
    subject_army_id: int,
) -> bool:
    if not isinstance(transition, dict) or not isinstance(
        pre_action_battle, dict
    ):
        return False
    pre_combat_id = _battle_combat_id(pre_action_battle)
    if (
        pre_action_battle.get("side_scope") != "full_side"
        or transition.get("battle_transition_ready") is not True
        or transition.get("combat_id") != pre_combat_id
    ):
        return False
    status = transition.get("status")
    if status == "combat_not_found":
        return True
    if status != "available":
        return False
    side_index = pre_action_battle.get("side_index")
    if side_index not in {0, 1}:
        return False
    attacker_ids = transition.get(
        "attacker_public_cunit_ids_in_stored_order"
    )
    defender_ids = transition.get(
        "defender_public_cunit_ids_in_stored_order"
    )
    if not isinstance(attacker_ids, list) or not isinstance(
        defender_ids, list
    ):
        return False
    expected_winner = "defender" if side_index == 0 else "attacker"
    if (
        transition.get("winner_side") == expected_winner
        and transition.get("phase") in {"pursuit", "done"}
    ):
        return True
    # A same-day reinforcement may reopen a retained CombatID after the whole
    # selected side has already left.  That is a valid full-side transition
    # only when the retreating CUnit is absent from both current side arrays.
    return bool(
        transition.get("winner_side") == "none"
        and transition.get("phase") in {"maneuver", "main"}
        and subject_army_id not in attacker_ids
        and subject_army_id not in defender_ids
    )


def _pre_side_public_cunit_ids(
    pre_action_battle: object, side_index: int
) -> list[int] | None:
    if not isinstance(pre_action_battle, dict) or side_index not in {0, 1}:
        return None
    frame = pre_action_battle.get("battle_control_snapshot")
    if not isinstance(frame, dict):
        return None
    side = frame.get("attacker" if side_index == 0 else "defender")
    if not isinstance(side, dict):
        return None
    armies = side.get("ordered_armies")
    if not isinstance(armies, list):
        return None
    result: list[int] = []
    for row in armies:
        value = row.get("public_cunit_id") if isinstance(row, dict) else None
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value <= 0
            or value in result
        ):
            return None
        result.append(value)
    return result


def _owner_subset_transition_ready(
    transition: object,
    pre_action_battle: object,
    subject_army_id: int,
) -> bool:
    if not isinstance(transition, dict) or not isinstance(
        pre_action_battle, dict
    ):
        return False
    pre_combat_id = _battle_combat_id(pre_action_battle)
    side_index = pre_action_battle.get("side_index")
    affected = pre_action_battle.get(
        "affected_public_cunit_ids_in_stored_order"
    )
    unaffected = pre_action_battle.get(
        "unaffected_same_side_public_cunit_ids_in_stored_order"
    )
    if (
        pre_action_battle.get("side_scope") != "owner_subset"
        or side_index not in {0, 1}
        or not isinstance(affected, list)
        or not affected
        or subject_army_id not in affected
        or not isinstance(unaffected, list)
        or not unaffected
        or transition.get("battle_transition_ready") is not True
        or transition.get("status") != "available"
        or transition.get("combat_id") != pre_combat_id
    ):
        return False
    attacker_ids = transition.get(
        "attacker_public_cunit_ids_in_stored_order"
    )
    defender_ids = transition.get(
        "defender_public_cunit_ids_in_stored_order"
    )
    if not isinstance(attacker_ids, list) or not isinstance(
        defender_ids, list
    ):
        return False
    selected_after = attacker_ids if side_index == 0 else defender_ids
    opposite_after = defender_ids if side_index == 0 else attacker_ids
    pre_opposite = _pre_side_public_cunit_ids(
        pre_action_battle, 1 - int(side_index)
    )
    return bool(
        pre_opposite
        and all(value not in attacker_ids for value in affected)
        and all(value not in defender_ids for value in affected)
        and all(value in selected_after for value in unaffected)
        and all(value in opposite_after for value in pre_opposite)
    )


def _expected_scope_transition_ready(
    expected_scope: str,
    transition: object,
    pre_action_battle: object,
    subject_army_id: int,
) -> bool:
    if expected_scope == "full_side":
        return _full_side_transition_ready(
            transition, pre_action_battle, subject_army_id
        )
    if expected_scope == "owner_subset":
        return _owner_subset_transition_ready(
            transition, pre_action_battle, subject_army_id
        )
    return False


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
    advances: list[dict[str, object]] = []
    pre_action_snapshot: dict[str, object] | None = None
    pre_action_battle: dict[str, object] | None = None
    preview: dict[str, object] | None = None
    order: dict[str, object] | None = None
    post_snapshots: list[dict[str, object]] = []
    post_transition_query: dict[str, object] | None = None
    post_transition_query_error: str | None = None
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
            name="xar-active-combat-retreat-live-session",
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

        for day_index in range(1, args.advance_days_before_preview + 1):
            before = service.snapshot()
            before_subject = _subject(before, args.subject_army_id)
            if not (
                isinstance(before_subject, dict)
                and before_subject.get("controllable") is True
                and before_subject.get("in_combat") is True
            ):
                raise RuntimeError(
                    f"subject left active combat before day {day_index}"
                )
            advance = service.execute_step(
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
            advances.append(
                {
                    "day_index": day_index,
                    "before": _compact_snapshot(
                        before, args.subject_army_id
                    ),
                    "advance": advance,
                    "readiness": binding,
                    "after": _compact_snapshot(after, args.subject_army_id),
                }
            )

        pre_action_snapshot = service.snapshot()
        pre_action_battle = service.query_battle_control_snapshot_v1(
            args.subject_army_id,
            expected_revision=int(pre_action_snapshot["revision"]),
        )
        if pre_action_battle.get("side_scope") != args.expected_scope:
            raise RuntimeError(
                "active retreat scope differs: "
                f"{pre_action_battle.get('side_scope')!r} != "
                f"{args.expected_scope!r}"
            )
        legality = pre_action_battle.get("legality")
        if not (
            isinstance(legality, dict)
            and legality.get("status") == "available"
            and legality.get("legal_now") is True
        ):
            raise RuntimeError("active retreat is not legal at the action frame")
        preview = service.preview_active_combat_retreat_v1(
            args.subject_army_id,
            args.target_province_id,
            expected_revision=int(pre_action_snapshot["revision"]),
        )
        if not (
            preview.get("status") == "available"
            and preview.get("action_ready") is True
        ):
            raise RuntimeError(
                "active retreat target preview did not become action-ready"
            )
        target_preview = preview.get("target_preview")
        if not isinstance(target_preview, dict):
            raise RuntimeError("active retreat preview lacks target proof")
        candidate_token = target_preview.get("candidate_token")
        if not isinstance(candidate_token, str) or not candidate_token:
            raise RuntimeError("active retreat preview lacks candidate token")
        order = service.order_active_combat_retreat_v1(
            args.subject_army_id,
            expected_revision=int(preview["source_binding"]["revision"]),
            expected_combat_id=int(preview["combat_id"]),
            expected_side_index=int(preview["side_index"]),
            expected_scope=str(preview["side_scope"]),
            target_province_id=args.target_province_id,
            candidate_token=candidate_token,
        )
        if not (
            order.get("accepted") is True
            and order.get("status") == "accepted_verification_pending"
        ):
            raise RuntimeError("active retreat order was not accepted")

        deadline = time.monotonic() + float(args.postcondition_timeout)
        while True:
            observed = service.snapshot()
            post_snapshots.append(
                _compact_snapshot(observed, args.subject_army_id)
            )
            if _retreat_semantic_ready(
                observed,
                args.subject_army_id,
                args.target_province_id,
            ):
                break
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    "retreating/target/route semantic postcondition timed out"
                )
            time.sleep(0.05)

        post = service.snapshot()
        try:
            prior_combat_id = _battle_combat_id(pre_action_battle)
            if prior_combat_id is None:
                raise RuntimeError(
                    "pre-action battle lacks a non-missing full CombatID"
                )
            post_transition_query = service.query_battle_transition_v1(
                prior_combat_id,
                expected_revision=int(post["revision"]),
            )
        except BaseException as error:
            post_transition_query_error = (
                f"{type(error).__name__}: {error}"
            )
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
    semantic_action_ready = bool(
        order is not None
        and order.get("accepted") is True
        and post_snapshots
        and _retreat_semantic_ready(
            post_snapshots[-1],
            args.subject_army_id,
            args.target_province_id,
        )
    )
    prior_combat_transition_observed = bool(
        isinstance(post_transition_query, dict)
        and post_transition_query.get("battle_transition_ready") is True
    )
    expected_scope_transition_ready = _expected_scope_transition_ready(
        args.expected_scope,
        post_transition_query,
        pre_action_battle,
        args.subject_army_id,
    )
    ok = bool(
        primary_error is None
        and semantic_action_ready
        and expected_scope_transition_ready
        and cleanup.get("ok") is True
    )
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_active_combat_retreat_v1_live_acceptance",
        "started_at": started_wall,
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "load_kind": (
            "cold_checkpoint"
            if args.cold_start_checkpoint
            else "continue_last_save"
        ),
        "subject_army_id": args.subject_army_id,
        "target_province_id": args.target_province_id,
        "expected_scope": args.expected_scope,
        "advance_days_before_preview": args.advance_days_before_preview,
        "identity": {
            "pipe": config.pipe_name,
            "bridge_dll": str(config.dll_path),
            "bridge_dll_sha256": _sha256_file(config.dll_path),
            "bridge_injector": str(config.injector_path),
            "bridge_injector_sha256": _sha256_file(config.injector_path),
        },
        "readiness": readiness,
        "advances": advances,
        "pre_action_snapshot": (
            _compact_snapshot(pre_action_snapshot, args.subject_army_id)
            if pre_action_snapshot is not None
            else None
        ),
        "pre_action_battle": pre_action_battle,
        "preview": preview,
        "order": order,
        "post_snapshots": post_snapshots,
        "post_transition_query": post_transition_query,
        "post_transition_query_error": post_transition_query_error,
        "readiness_gates": {
            "retreat_semantic_action_live_ready": semantic_action_ready,
            "prior_combat_transition_observed": (
                prior_combat_transition_observed
            ),
            "full_side_postcondition_live_ready": bool(
                args.expected_scope == "full_side"
                and semantic_action_ready
                and expected_scope_transition_ready
            ),
            "owner_subset_postcondition_live_ready": bool(
                args.expected_scope == "owner_subset"
                and semantic_action_ready
                and expected_scope_transition_ready
            ),
            "expected_scope_postcondition_live_ready": bool(
                semantic_action_ready and expected_scope_transition_ready
            ),
        },
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": primary_error,
    }
    return payload, 0 if ok else 1


def main() -> int:
    args = _parser().parse_args()
    if args.advance_days_before_preview < 0:
        raise SystemExit("--advance-days-before-preview must be non-negative")
    if args.postcondition_timeout <= 0:
        raise SystemExit("--postcondition-timeout must be positive")
    payload, exit_code = _run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "output": str(args.output.resolve()),
                "readiness_gates": payload["readiness_gates"],
                "cleanup": payload["cleanup"],
                "error": payload["error"],
            },
            ensure_ascii=False,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
