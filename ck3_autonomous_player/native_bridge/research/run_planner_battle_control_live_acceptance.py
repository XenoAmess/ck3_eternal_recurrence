#!/usr/bin/env python3
"""Run a managed planner-integrated battle-control hold acceptance.

The harness clones an existing isolated CK3 profile, replaces only the clone's
last_save.ck3 with an explicitly hash-bound battle autosave, prepares the
clone against the current production runtime, and drives the production
service/planner through at least two exact query -> one-day advance -> requery
cycles.

Only the exact subject query and life-advance may reach the driver. Active
combat retreat preview/order literals are rejected before dispatch. CK3
lifetime and process-tree cleanup remain owned by native_session; this script
never invokes taskkill or Stop-Process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import threading
import time
from typing import Any, Callable
import uuid


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.bridge.battle_control_contract import (  # noqa: E402
    query_battle_control_snapshot_v1_step,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.environment import (  # noqa: E402
    ensure_state_path_safe,
    is_relative_to,
    make_spec,
    paths_overlap,
    prepare_profile,
    verify_profile,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.native_auto_run import (  # noqa: E402
    _cleanup_report,
    _compact_session_report,
    _identity,
    _wait_for_readiness,
)
from xar_autoplayer.native_session import native_session  # noqa: E402
from xar_autoplayer.runtime import NativeBridgeLaunchConfig, utc_now  # noqa: E402


PURE_NATIVE_MODE = "native-headless"
ONE_GAME_DAY_RAW = 24
MINIMUM_CYCLES = 2
_ADVANCE_PHASES = frozenset(
    {
        "native_war_battle_control_progress",
        "native_war_global_battle_control_progress",
    }
)
_CONTINUING_TRANSITIONS = frozenset(
    {"same_combat_advanced", "same_combat_reopened"}
)
_TERMINATION_QUERY_PATTERN = re.compile(
    r"query-war-termination-options-[1-9][0-9]*"
)
_MAX_READ_ONLY_PREREQUISITES = 8
_CLONE_MARKER_NAME = ".xar-planner-battle-control-clone.json"
_PROFILE_ROOT_EXCLUDES = frozenset(
    {
        "crashes",
        "dumps",
        "exceptions",
        "logs",
        "mod",
        "mod-content",
        "save games",
        "last_save.ck3",
        "xar-autoplayer-environment.json",
    }
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-state-dir", type=Path, required=True)
    parser.add_argument(
        "--state-dir",
        type=Path,
        help=(
            "new isolated clone root; omitted creates a unique directory "
            "under the system temporary directory"
        ),
    )
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument(
        "--battle-save",
        type=Path,
        required=True,
        help="absolute path or source-profile-relative battle autosave",
    )
    parser.add_argument("--expected-battle-save-sha256", required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--subject-army-id", type=int, required=True)
    parser.add_argument("--cycles", type=int, default=MINIMUM_CYCLES)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--readiness-timeout", type=float, default=240.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--retain-clone",
        action="store_true",
        help=(
            "retain the isolated clone for diagnostics; retained runs cannot "
            "qualify as fully cleaned"
        ),
    )
    return parser


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest().upper()


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _positive_seconds(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a positive number")
    result = float(value)
    if not result > 0.0:
        raise ValueError(f"{name} must be a positive number")
    return result


def _expected_sha256(value: object) -> str:
    text = str(value).strip().upper()
    if not re.fullmatch(r"[0-9A-F]{64}", text):
        raise ValueError(
            "expected battle save SHA-256 must contain 64 hex digits"
        )
    return text


def _subject(
    snapshot: dict[str, object], subject_army_id: int
) -> dict[str, object] | None:
    armies = snapshot.get("player_armies")
    if not isinstance(armies, list):
        return None
    for row in armies:
        if isinstance(row, dict) and row.get("army_id") == subject_army_id:
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
        )
    } | {
        "subject_army": _subject(snapshot, subject_army_id),
        "battle_cache": {
            key: snapshot.get(key)
            for key in (
                "battle_control_snapshot_v1_status",
                "battle_control_snapshot_v1_query_sequence",
                "battle_control_snapshot_v1_subject_army_id",
                "battle_control_snapshot_v1_queried_snapshot_id",
                "battle_control_snapshot_v1_queried_revision",
            )
        },
    }


def _frame_summary(frame: dict[str, object]) -> dict[str, object]:
    def compact_side(role: str) -> dict[str, object] | None:
        side = frame.get(role)
        if not isinstance(side, dict):
            return None
        ordered = side.get("ordered_armies")
        return {
            "ordered_public_cunit_ids": [
                row.get("public_cunit_id")
                for row in (ordered if isinstance(ordered, list) else [])
                if isinstance(row, dict)
            ],
            "derived_current_fighting_raw": side.get(
                "derived_current_fighting_raw"
            ),
            "derived_soft_casualties_raw": side.get(
                "derived_soft_casualties_raw"
            ),
            "participant_hard_total_raw": side.get(
                "participant_hard_total_raw"
            ),
        }

    return {
        "frame_sha256": _canonical_sha256(frame),
        "snapshot_revision": frame.get("snapshot_revision"),
        "observed_date_raw": frame.get("observed_date_raw"),
        "subject_public_cunit_id": frame.get("subject_public_cunit_id"),
        "subject_native_carmy_id": frame.get("subject_native_carmy_id"),
        "combat_id": frame.get("combat_id"),
        "province_id": frame.get("province_id"),
        "phase": frame.get("phase"),
        "phase_raw": frame.get("phase_raw"),
        "phase_day": frame.get("phase_day"),
        "winner_side": frame.get("winner_side"),
        "forced_winner_side": frame.get("forced_winner_side"),
        "finalized": frame.get("finalized"),
        "battle_result_id": frame.get("battle_result_id"),
        "attacker": compact_side("attacker"),
        "defender": compact_side("defender"),
    }


def _planned_step(
    planned: dict[str, object],
) -> tuple[dict[str, object], str, int]:
    plan = planned.get("plan")
    if not isinstance(plan, dict):
        raise RuntimeError("planner result lacks a plan object")
    step = plan.get("selected_step")
    if not isinstance(step, str) or not step:
        raise RuntimeError(
            "planner returned no executable step: " + str(plan.get("reason"))
        )
    revision = planned.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int):
        raise RuntimeError("planner result lacks a valid public revision")
    return plan, step, revision


def _require_query_plan(
    planned: dict[str, object], query_step: str
) -> dict[str, object]:
    plan, step, _revision = _planned_step(planned)
    if (
        plan.get("phase") != "native_war_battle_control_query"
        or step != query_step
    ):
        raise RuntimeError(
            "planner did not request the exact battle query: "
            f"phase={plan.get('phase')!r}, step={step!r}"
        )
    return plan


def _matching_transition(
    plan: dict[str, object],
    *,
    subject_army_id: int,
    combat_id: int,
) -> dict[str, object] | None:
    transitions = plan.get("battle_transitions")
    if not isinstance(transitions, list):
        return None
    for row in transitions:
        if (
            isinstance(row, dict)
            and row.get("status") in _CONTINUING_TRANSITIONS
            and row.get("subject_army_id") == subject_army_id
            and row.get("before_combat_id") == combat_id
            and row.get("after_combat_id") == combat_id
        ):
            return row
    return None


def _require_advance_plan(
    planned: dict[str, object],
    *,
    subject_army_id: int,
    combat_id: int,
    require_transition: bool,
) -> tuple[dict[str, object], dict[str, object] | None]:
    plan, step, _revision = _planned_step(planned)
    if step != "life-advance" or plan.get("phase") not in _ADVANCE_PHASES:
        raise RuntimeError(
            "planner did not select bounded battle hold: "
            f"phase={plan.get('phase')!r}, step={step!r}"
        )
    evidence = plan.get("battle_control_frames")
    if not (
        isinstance(evidence, list)
        and any(
            isinstance(row, dict)
            and row.get("subject_army_id") == subject_army_id
            and row.get("combat_id") == combat_id
            for row in evidence
        )
    ):
        raise RuntimeError(
            "planner hold lacks current-revision battle-control evidence"
        )
    transition = _matching_transition(
        plan,
        subject_army_id=subject_army_id,
        combat_id=combat_id,
    )
    if require_transition and transition is None:
        raise RuntimeError(
            "planner did not verify a legal same-CombatID transition"
        )
    return plan, transition


def _execute_planned(
    service: GameplayBridgeService,
    planned: dict[str, object],
    *,
    allowed_steps: frozenset[str],
) -> dict[str, object]:
    _plan, step, revision = _planned_step(planned)
    if step not in allowed_steps or "retreat" in step.casefold():
        raise RuntimeError(
            "planner selected a forbidden live-acceptance step before "
            f"dispatch: {step!r}"
        )
    return service.execute_step(step, expected_revision=revision)


def _binding(snapshot: dict[str, object]) -> tuple[object, ...]:
    return tuple(
        snapshot.get(key)
        for key in (
            "snapshot_id",
            "revision",
            "native_revision",
            "date_raw",
            "paused",
        )
    )


def _drain_read_only_prerequisites(
    service: GameplayBridgeService,
    planned: dict[str, object],
    *,
    subject_army_id: int,
    combat_id: int,
    require_transition: bool,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Run only planner-selected termination queries before a battle hold."""
    rows: list[dict[str, object]] = []
    current = planned
    for _index in range(_MAX_READ_ONLY_PREREQUISITES + 1):
        plan, step, _revision = _planned_step(current)
        if step == "life-advance":
            _require_advance_plan(
                current,
                subject_army_id=subject_army_id,
                combat_id=combat_id,
                require_transition=require_transition,
            )
            return current, rows
        if not (
            plan.get("phase") == "native_war_termination_query"
            and _TERMINATION_QUERY_PATTERN.fullmatch(step)
        ):
            raise RuntimeError(
                "planner did not select bounded battle hold or an approved "
                "read-only prerequisite: "
                f"phase={plan.get('phase')!r}, step={step!r}"
            )
        if len(rows) >= _MAX_READ_ONLY_PREREQUISITES:
            raise RuntimeError(
                "planner exceeded the bounded read-only prerequisite count"
            )
        before = service.snapshot()
        _assert_active_subject(before, subject_army_id)
        result = _execute_planned(
            service,
            current,
            allowed_steps=frozenset({step}),
        )
        after = service.snapshot()
        _assert_active_subject(after, subject_army_id)
        if not (
            _binding(before) == _binding(after)
            and result.get("step") == step
            and result.get("accepted") is True
            and result.get("status") == "available"
        ):
            raise RuntimeError(
                "planner prerequisite query changed the paused native frame "
                "or returned a malformed result"
            )
        rows.append(
            {
                "plan": plan,
                "step": step,
                "before": _compact_snapshot(before, subject_army_id),
                "result": result,
                "after": _compact_snapshot(after, subject_army_id),
                "native_frame_unchanged": True,
            }
        )
        current = service.plan_turn()
    raise RuntimeError("unreachable read-only prerequisite loop")


def _query_frame(
    result: dict[str, object],
    *,
    query_step: str,
    subject_army_id: int,
    expected_snapshot: dict[str, object],
) -> dict[str, object]:
    frame = result.get("battle_control_snapshot")
    if not (
        result.get("step") == query_step
        and result.get("accepted") is True
        and result.get("status") == "available"
        and isinstance(frame, dict)
        and frame.get("subject_public_cunit_id") == subject_army_id
        and frame.get("observed_date_raw") == expected_snapshot.get("date_raw")
        and frame.get("snapshot_revision")
        == expected_snapshot.get("native_revision")
        and result.get("queried_snapshot_id")
        == expected_snapshot.get("snapshot_id")
        and result.get("queried_revision")
        == expected_snapshot.get("revision")
        and result.get("queried_native_revision")
        == expected_snapshot.get("native_revision")
    ):
        raise RuntimeError(
            "battle query is not available and bound to the planned paused "
            "snapshot revision"
        )
    return frame


def _assert_active_subject(
    snapshot: dict[str, object], subject_army_id: int
) -> dict[str, object]:
    row = _subject(snapshot, subject_army_id)
    if not (
        isinstance(row, dict)
        and row.get("controllable") is True
        and row.get("in_combat") is True
        and snapshot.get("paused") is True
    ):
        raise RuntimeError(
            "subject army is not controllable in active paused combat"
        )
    return row


def _run_planner_cycles(
    service: GameplayBridgeService,
    *,
    subject_army_id: int,
    cycles: int,
    wait_after_advance: Callable[[], dict[str, object]],
) -> dict[str, object]:
    query_step = query_battle_control_snapshot_v1_step(subject_army_id)
    allowed_steps = frozenset({query_step, "life-advance"})
    initial_snapshot = service.snapshot()
    _assert_active_subject(initial_snapshot, subject_army_id)

    initial_query_planned = service.plan_turn()
    initial_query_plan = _require_query_plan(
        initial_query_planned, query_step
    )
    initial_query_result = _execute_planned(
        service, initial_query_planned, allowed_steps=allowed_steps
    )
    initial_frame = _query_frame(
        initial_query_result,
        query_step=query_step,
        subject_army_id=subject_army_id,
        expected_snapshot=initial_snapshot,
    )
    combat_id = _positive_int(initial_frame.get("combat_id"), "combat_id")
    current_advance_planned, current_prerequisites = (
        _drain_read_only_prerequisites(
            service,
            service.plan_turn(),
            subject_army_id=subject_army_id,
            combat_id=combat_id,
            require_transition=False,
        )
    )
    initial_hold_plan, _unused = _require_advance_plan(
        current_advance_planned,
        subject_army_id=subject_army_id,
        combat_id=combat_id,
        require_transition=False,
    )

    executed_steps = [query_step]
    executed_steps.extend(
        row["step"] for row in current_prerequisites
    )
    cycle_rows: list[dict[str, object]] = []
    prior_frame = initial_frame
    for cycle_index in range(1, cycles + 1):
        advance_plan, incoming_transition = _require_advance_plan(
            current_advance_planned,
            subject_army_id=subject_army_id,
            combat_id=combat_id,
            require_transition=cycle_index > 1,
        )
        before = service.snapshot()
        _assert_active_subject(before, subject_army_id)
        if before.get("date_raw") != prior_frame.get("observed_date_raw"):
            raise RuntimeError(
                "pre-advance semantic date differs from current battle frame"
            )
        advance_result = _execute_planned(
            service, current_advance_planned, allowed_steps=allowed_steps
        )
        executed_steps.append("life-advance")
        readiness = wait_after_advance()
        after = service.snapshot()
        _assert_active_subject(after, subject_army_id)

        before_date = before.get("date_raw")
        after_date = after.get("date_raw")
        if not (
            isinstance(before_date, int)
            and not isinstance(before_date, bool)
            and isinstance(after_date, int)
            and not isinstance(after_date, bool)
            and after_date - before_date == ONE_GAME_DAY_RAW
            and advance_result.get("starting_date_raw") == before_date
            and advance_result.get("ending_date_raw") == after_date
            and advance_result.get("elapsed_days") == 1
        ):
            raise RuntimeError(
                "life-advance did not prove exactly one real CK3 day"
            )

        post_query_planned = service.plan_turn()
        post_query_plan = _require_query_plan(
            post_query_planned, query_step
        )
        post_query_result = _execute_planned(
            service, post_query_planned, allowed_steps=allowed_steps
        )
        executed_steps.append(query_step)
        current_frame = _query_frame(
            post_query_result,
            query_step=query_step,
            subject_army_id=subject_army_id,
            expected_snapshot=after,
        )
        if current_frame.get("combat_id") != combat_id:
            raise RuntimeError(
                "post-advance query changed CombatID during continuing hold"
            )

        verified_planned, verified_prerequisites = (
            _drain_read_only_prerequisites(
                service,
                service.plan_turn(),
                subject_army_id=subject_army_id,
                combat_id=combat_id,
                require_transition=True,
            )
        )
        executed_steps.extend(
            row["step"] for row in verified_prerequisites
        )
        verified_plan, transition = _require_advance_plan(
            verified_planned,
            subject_army_id=subject_army_id,
            combat_id=combat_id,
            require_transition=True,
        )
        cycle_rows.append(
            {
                "cycle_index": cycle_index,
                "incoming_verified_transition": incoming_transition,
                "pre_advance_read_only_prerequisites": (
                    current_prerequisites
                ),
                "advance_plan": advance_plan,
                "before": _compact_snapshot(before, subject_army_id),
                "advance_result": advance_result,
                "readiness": readiness,
                "after": _compact_snapshot(after, subject_army_id),
                "date_delta_raw": after_date - before_date,
                "post_advance_query_plan": post_query_plan,
                "post_advance_query_result": post_query_result,
                "post_advance_frame": _frame_summary(current_frame),
                "post_requery_read_only_prerequisites": (
                    verified_prerequisites
                ),
                "verified_next_hold_plan": verified_plan,
                "verified_transition": transition,
                "same_combat_id": current_frame.get("combat_id") == combat_id,
                "frame_changed": current_frame != prior_frame,
            }
        )
        prior_frame = current_frame
        current_advance_planned = verified_planned
        current_prerequisites = verified_prerequisites

    approved_steps = all(
        step in {query_step, "life-advance"}
        or _TERMINATION_QUERY_PATTERN.fullmatch(step) is not None
        for step in executed_steps
    )
    assertions = {
        "minimum_two_cycles": len(cycle_rows) >= MINIMUM_CYCLES,
        "every_advance_exactly_one_day": all(
            row.get("date_delta_raw") == ONE_GAME_DAY_RAW
            for row in cycle_rows
        ),
        "every_requery_same_combat_id": all(
            row.get("same_combat_id") is True for row in cycle_rows
        ),
        "every_cycle_planner_verified_transition": all(
            isinstance(row.get("verified_transition"), dict)
            and row["verified_transition"].get("status")
            in _CONTINUING_TRANSITIONS
            for row in cycle_rows
        ),
        "retreat_actions_executed": sum(
            1 for step in executed_steps if "retreat" in step.casefold()
        ),
        "only_approved_steps_executed": approved_steps,
        "only_life_advance_mutated_gameplay": approved_steps,
        "read_only_prerequisites_preserved_native_frame": all(
            row.get("native_frame_unchanged") is True
            for cycle in cycle_rows
            for row in (
                cycle.get("pre_advance_read_only_prerequisites", [])
                if isinstance(
                    cycle.get("pre_advance_read_only_prerequisites"), list
                )
                else []
            )
        )
        and all(
            row.get("native_frame_unchanged") is True
            for cycle in cycle_rows
            for row in (
                cycle.get("post_requery_read_only_prerequisites", [])
                if isinstance(
                    cycle.get("post_requery_read_only_prerequisites"), list
                )
                else []
            )
        ),
    }
    return {
        "subject_army_id": subject_army_id,
        "combat_id": combat_id,
        "query_step": query_step,
        "initial_snapshot": _compact_snapshot(
            initial_snapshot, subject_army_id
        ),
        "initial_query_plan": initial_query_plan,
        "initial_query_result": initial_query_result,
        "initial_frame": _frame_summary(initial_frame),
        "initial_hold_plan": initial_hold_plan,
        "cycles": cycle_rows,
        "executed_steps": executed_steps,
        "assertions": assertions,
    }


def _resolve_battle_save(
    source_profile: Path,
    requested: Path,
    expected_sha256: str,
) -> tuple[Path, dict[str, object]]:
    candidate = (
        requested.resolve()
        if requested.is_absolute()
        else (source_profile / requested).resolve()
    )
    if not is_relative_to(candidate, source_profile) or not candidate.is_file():
        raise AgentError(
            "battle save must be an existing file inside the source profile: "
            f"{candidate}"
        )
    actual_sha256 = _sha256_file(candidate)
    if actual_sha256 != expected_sha256:
        raise AgentError(
            "battle save SHA-256 differs: "
            f"{actual_sha256} != {expected_sha256}"
        )
    return candidate, {
        "source_path": str(candidate),
        "source_profile_relative_path": candidate.relative_to(
            source_profile
        ).as_posix(),
        "size": candidate.stat().st_size,
        "sha256": actual_sha256,
    }


def _copy_source_profile(source_profile: Path, target_profile: Path) -> None:
    for path in source_profile.rglob("*"):
        if path.is_symlink():
            raise AgentError(f"source profile contains a symlink: {path}")

    def ignore(directory: str, names: list[str]) -> set[str]:
        if Path(directory).resolve() == source_profile:
            return set(names) & _PROFILE_ROOT_EXCLUDES
        return set()

    shutil.copytree(
        source_profile,
        target_profile,
        copy_function=shutil.copy2,
        ignore=ignore,
    )


def _prepare_isolated_clone(
    *,
    source_state_dir: Path,
    target_state_dir: Path,
    game_dir: Path,
    battle_save: Path,
    expected_battle_save_sha256: str,
    clone_nonce: str,
) -> tuple[Any, dict[str, object]]:
    source_state = source_state_dir.resolve()
    source_profile = source_state / "profile"
    target_state = target_state_dir.resolve()
    if not source_profile.is_dir():
        raise AgentError(f"source profile is missing: {source_profile}")
    if target_state.exists():
        raise AgentError(
            f"isolated clone target already exists: {target_state}"
        )
    ensure_state_path_safe(target_state)
    if paths_overlap(source_state, target_state):
        raise AgentError("source and target state directories overlap")
    selected_save, save_identity = _resolve_battle_save(
        source_profile,
        battle_save,
        expected_battle_save_sha256,
    )

    target_state.mkdir(parents=True, exist_ok=False)
    marker = target_state / _CLONE_MARKER_NAME
    marker.write_text(
        json.dumps(
            {
                "kind": "xar_planner_battle_control_clone",
                "nonce": clone_nonce,
                "source_state_dir": str(source_state),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _copy_source_profile(source_profile, target_state / "profile")
    spec = make_spec(target_state, game_dir)
    manifest = prepare_profile(spec)

    target_save_dir = spec.profile_dir / "save games"
    target_save_dir.mkdir(parents=True, exist_ok=True)
    target_named_save = target_save_dir / selected_save.name
    shutil.copy2(selected_save, target_named_save)
    target_last_save = spec.profile_dir / "last_save.ck3"
    shutil.copy2(selected_save, target_last_save)
    cloned_save_sha256 = _sha256_file(target_named_save)
    cloned_last_sha256 = _sha256_file(target_last_save)
    if not (
        cloned_save_sha256 == expected_battle_save_sha256
        and cloned_last_sha256 == expected_battle_save_sha256
    ):
        raise AgentError("cloned battle save bytes differ after copy")
    verified = verify_profile(spec)
    mod = manifest.get("mod")
    return spec, {
        "source_state_dir": str(source_state),
        "target_state_dir": str(target_state),
        "excluded_profile_roots": sorted(_PROFILE_ROOT_EXCLUDES),
        "battle_save": save_identity
        | {
            "cloned_save_path": str(target_named_save),
            "cloned_last_save_path": str(target_last_save),
            "cloned_save_sha256": cloned_save_sha256,
            "cloned_last_save_sha256": cloned_last_sha256,
        },
        "prepared_environment_sha256": verified.get("environment_sha256"),
        "prepared_production_tree_sha256": (
            mod.get("production_tree_sha256")
            if isinstance(mod, dict)
            else None
        ),
    }


def _run_live_session(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    subject_army_id: int,
    cycles: int,
    timeout: float,
    readiness_timeout: float,
) -> dict[str, object]:
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    session_thread: threading.Thread | None = None
    session_started = False
    driver_closed = False
    readiness: dict[str, object] | None = None
    loop: dict[str, object] | None = None
    primary_error: str | None = None

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec,
                timeout_seconds=timeout + 90.0,
                native_bridge=config,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=False,
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
            name="xar-planner-battle-control-live-session",
            daemon=False,
        )
        session_thread.start()
        session_started = True
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=readiness_timeout,
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=False,
            allow_terminal=False,
        )

        def wait_after_advance() -> dict[str, object]:
            return _wait_for_readiness(
                driver,
                session_done=session_done,
                session_state=session_state,
                timeout_seconds=readiness_timeout,
                stable_seconds=0.0,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=False,
                allow_terminal=False,
            )

        loop = _run_planner_cycles(
            service,
            subject_army_id=subject_army_id,
            cycles=cycles,
            wait_after_advance=wait_after_advance,
        )
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if session_thread is not None and session_started:
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
    assertions = (
        loop.get("assertions") if isinstance(loop, dict) else None
    )
    loop_ok = bool(
        isinstance(assertions, dict)
        and assertions.get("minimum_two_cycles") is True
        and assertions.get("every_advance_exactly_one_day") is True
        and assertions.get("every_requery_same_combat_id") is True
        and assertions.get("every_cycle_planner_verified_transition") is True
        and assertions.get("retreat_actions_executed") == 0
        and assertions.get("only_approved_steps_executed") is True
        and assertions.get("only_life_advance_mutated_gameplay") is True
        and assertions.get(
            "read_only_prerequisites_preserved_native_frame"
        )
        is True
    )
    return {
        "ok": bool(
            primary_error is None
            and loop_ok
            and cleanup.get("ok") is True
        ),
        "session_started": session_started,
        "readiness": readiness,
        "identity": _identity(config, readiness, spec),
        "planner_loop": loop,
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": primary_error,
    }


def _cleanup_clone(
    target_state_dir: Path,
    *,
    clone_nonce: str,
    retain_clone: bool,
    session_started: bool,
    session_cleanup_proven: bool,
) -> dict[str, object]:
    target = target_state_dir.resolve()
    if retain_clone:
        return {
            "attempted": False,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": "--retain-clone prevents full cleanup qualification",
        }
    if session_started and not session_cleanup_proven:
        return {
            "attempted": False,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": (
                "managed process cleanup was not proven; clone retained "
                "instead of deleting a possibly live userdir"
            ),
        }
    marker = target / _CLONE_MARKER_NAME
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
        if not (
            payload.get("kind") == "xar_planner_battle_control_clone"
            and payload.get("nonce") == clone_nonce
        ):
            raise AgentError("isolated clone marker differs")
        ensure_state_path_safe(target)
        shutil.rmtree(target)
        removed = not target.exists()
        return {
            "attempted": True,
            "removed": removed,
            "path": str(target),
            "ok": removed,
            "reason": None if removed else "clone directory still exists",
        }
    except BaseException as error:
        return {
            "attempted": True,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": f"{type(error).__name__}: {error}",
        }


def _target_state_dir(requested: Path | None) -> Path:
    if requested is not None:
        return requested.expanduser().resolve()
    return Path(tempfile.gettempdir()).resolve() / (
        "xar-planner-battle-control-" + uuid.uuid4().hex
    )


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started_wall = utc_now()
    started = time.monotonic()
    cycles = _positive_int(args.cycles, "cycles")
    if cycles < MINIMUM_CYCLES:
        raise ValueError(f"cycles must be at least {MINIMUM_CYCLES}")
    subject_army_id = _positive_int(
        args.subject_army_id, "subject_army_id"
    )
    timeout = _positive_seconds(args.timeout, "timeout")
    readiness_timeout = _positive_seconds(
        args.readiness_timeout, "readiness_timeout"
    )
    expected_save_sha256 = _expected_sha256(
        args.expected_battle_save_sha256
    )
    source_state = args.source_state_dir.expanduser().resolve()
    target_state = _target_state_dir(args.state_dir)
    output = args.output.expanduser().resolve()
    if output.exists():
        raise AgentError(f"artifact output already exists: {output}")
    if is_relative_to(output, target_state):
        raise AgentError(
            "artifact output must be outside the disposable clone state"
        )
    if target_state.exists():
        raise AgentError(
            f"isolated clone target already exists: {target_state}"
        )
    clone_nonce = uuid.uuid4().hex
    clone: dict[str, object] | None = None
    live: dict[str, object] | None = None
    primary_error: str | None = None
    source_save_path: Path | None = None
    source_save_before_sha256: str | None = None
    config = NativeBridgeLaunchConfig(
        mode=PURE_NATIVE_MODE,
        pipe_name=args.bridge_pipe,
        dll_path=args.bridge_dll.expanduser().resolve(),
        injector_path=args.bridge_injector.expanduser().resolve(),
    )

    try:
        source_profile = source_state / "profile"
        source_save_path, _unused = _resolve_battle_save(
            source_profile,
            args.battle_save,
            expected_save_sha256,
        )
        source_save_before_sha256 = _sha256_file(source_save_path)
        spec, clone = _prepare_isolated_clone(
            source_state_dir=source_state,
            target_state_dir=target_state,
            game_dir=args.game_dir.expanduser().resolve(),
            battle_save=args.battle_save,
            expected_battle_save_sha256=expected_save_sha256,
            clone_nonce=clone_nonce,
        )
        live = _run_live_session(
            spec=spec,
            config=config,
            subject_army_id=subject_army_id,
            cycles=cycles,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
        )
        if live.get("ok") is not True:
            primary_error = str(
                live.get("error") or "planner live loop did not qualify"
            )
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"

    source_save_after_sha256 = (
        _sha256_file(source_save_path)
        if source_save_path is not None and source_save_path.is_file()
        else None
    )
    source_save_unchanged = bool(
        source_save_before_sha256 is not None
        and source_save_before_sha256 == source_save_after_sha256
    )
    session_started = bool(
        isinstance(live, dict) and live.get("session_started") is True
    )
    session_cleanup_proven = bool(
        isinstance(live, dict)
        and isinstance(live.get("cleanup"), dict)
        and live["cleanup"].get("ok") is True
    )
    clone_cleanup = (
        _cleanup_clone(
            target_state,
            clone_nonce=clone_nonce,
            retain_clone=bool(args.retain_clone),
            session_started=session_started,
            session_cleanup_proven=session_cleanup_proven,
        )
        if target_state.exists()
        else {
            "attempted": False,
            "removed": True,
            "path": str(target_state),
            "ok": True,
            "reason": "clone was not materialized",
        }
    )
    if clone_cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            clone_cleanup.get("reason") or "clone cleanup was not proven"
        )
    if not source_save_unchanged and primary_error is None:
        primary_error = "source battle autosave changed during isolated run"

    ok = bool(
        primary_error is None
        and isinstance(live, dict)
        and live.get("ok") is True
        and clone_cleanup.get("ok") is True
        and source_save_unchanged
    )
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_planner_battle_control_live_acceptance",
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "bounds": {
            "cycles_requested": cycles,
            "minimum_cycles": MINIMUM_CYCLES,
            "one_game_day_raw": ONE_GAME_DAY_RAW,
            "timeout_seconds": timeout,
            "readiness_timeout_seconds": readiness_timeout,
        },
        "policy": {
            "planner": (
                "choose_one_life_turn via GameplayBridgeService.plan_turn"
            ),
            "allowed_live_steps": [
                query_battle_control_snapshot_v1_step(subject_army_id),
                "life-advance",
                "query-war-termination-options-N (read-only prerequisite)",
            ],
            "retreat_actions_allowed": False,
            "visual_fallback_allowed": False,
        },
        "clone": clone,
        "source_save_invariant": {
            "path": str(source_save_path) if source_save_path else None,
            "before_sha256": source_save_before_sha256,
            "after_sha256": source_save_after_sha256,
            "unchanged": source_save_unchanged,
        },
        "live": live,
        "clone_cleanup": clone_cleanup,
        "error": primary_error,
    }
    return payload, 0 if ok else 1


def main() -> int:
    args = _parser().parse_args()
    payload, exit_code = _run(args)
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    live = payload.get("live")
    loop = live.get("planner_loop") if isinstance(live, dict) else None
    print(
        json.dumps(
            {
                "ok": payload.get("ok"),
                "output": str(output),
                "artifact_sha256": _sha256_file(output),
                "combat_id": (
                    loop.get("combat_id") if isinstance(loop, dict) else None
                ),
                "cleanup": (
                    live.get("cleanup") if isinstance(live, dict) else None
                ),
                "clone_cleanup": payload.get("clone_cleanup"),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
