#!/usr/bin/env python3
"""Run a research-only CK3 timeline-speed matrix from managed checkpoints.

This harness never changes the production life-advance selector.  It drives
the already-advertised ``set-speed-N``/resume/pause primitives through the
production native-session supervisor, measures the final paused state rather
than trusting command ACKs, and leaves event/interaction resolution to the
caller.

``stop-envelope`` samples all five speeds in one recovered episode.
``battle-parity`` restores the immutable checkpoint before every arm and is
limited to speeds 1/2/3 until an application-main same-day battle sentinel is
implemented and wired into this harness.

``terminal-parity`` also restores before every arm, but admits all five speeds
because it binds comparison to the passive exact-build terminal journal rather
than to the later external pause.  It compares the native terminal date,
phase/day, winner, result, wipe, participant order, and battle-war-score row;
it does not claim that 4/5 can yet stop at arbitrary mid-battle decision days.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import threading
import time
from typing import Callable


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
RAW_HOURS_PER_DAY = 24
ALL_SPEEDS = (1, 2, 3, 4, 5)
EXTERNAL_BATTLE_SPEEDS = (1, 2, 3)
MATRIX_MODES = ("stop-envelope", "battle-parity", "terminal-parity")
STOP_ENVELOPE_SCENARIOS = ("neutral", "active-battle")
MAX_TIMELINE_COMMAND_ATTEMPTS = 2
METADATA_KEYS = frozenset(
    {
        "backend_id",
        "native_revision",
        "queried_connection_generation",
        "queried_native_revision",
        "queried_revision",
        "queried_snapshot_id",
        "query_sequence",
        "revision",
        "snapshot_id",
        "snapshot_revision",
    }
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=MATRIX_MODES, default="stop-envelope")
    parser.add_argument(
        "--stop-envelope-scenario",
        choices=STOP_ENVELOPE_SCENARIOS,
        default="neutral",
    )
    parser.add_argument("--speeds", type=int, nargs="+", default=list(ALL_SPEEDS))
    parser.add_argument("--samples-per-speed", type=int, default=6)
    parser.add_argument("--target-days", type=int, default=1)
    parser.add_argument("--terminal-max-days", type=int, default=45)
    parser.add_argument("--terminal-max-pause-lag-days", type=int, default=1)
    parser.add_argument("--subject-army-id", type=int)
    parser.add_argument("--timeout", type=float, default=7200.0)
    parser.add_argument("--readiness-timeout", type=float, default=180.0)
    parser.add_argument("--slice-timeout", type=float, default=90.0)
    parser.add_argument("--cold-start-checkpoint", action="store_true")
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


def _file_identity(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "size": stat.st_size,
        "sha256": _sha256_file(path),
    }


def _validate_speed_request(
    mode: str,
    speeds: tuple[int, ...],
    *,
    samples_per_speed: int,
    target_days: int,
    terminal_max_days: int = 45,
    terminal_max_pause_lag_days: int = 1,
) -> None:
    if mode not in MATRIX_MODES:
        raise ValueError(f"unknown matrix mode {mode!r}")
    if not speeds:
        raise ValueError("at least one speed is required")
    if len(set(speeds)) != len(speeds):
        raise ValueError("--speeds must not contain duplicates")
    invalid = [speed for speed in speeds if speed not in ALL_SPEEDS]
    if invalid:
        raise ValueError(f"speeds must be in 1..5; invalid={invalid}")
    if samples_per_speed <= 0:
        raise ValueError("--samples-per-speed must be positive")
    if target_days <= 0:
        raise ValueError("--target-days must be positive")
    if terminal_max_days <= 0:
        raise ValueError("--terminal-max-days must be positive")
    if terminal_max_pause_lag_days < 0:
        raise ValueError("--terminal-max-pause-lag-days must be nonnegative")
    unsupported = [
        speed for speed in speeds if speed not in EXTERNAL_BATTLE_SPEEDS
    ]
    if mode == "battle-parity" and unsupported:
        raise ValueError(
            "battle-parity speeds 4/5 require an application-main same-day "
            "run-until-date-or-battle-sentinel primitive; external Python "
            f"polling is intentionally refused (requested={unsupported})"
        )
    if mode in {"battle-parity", "terminal-parity"} and (
        1 not in speeds or len(speeds) < 2
    ):
        raise ValueError(
            f"{mode} requires speed 1 plus at least one comparison speed"
        )


def _balanced_speed_schedule(
    speeds: tuple[int, ...], samples_per_speed: int
) -> list[int]:
    """Return a balanced ascending/descending schedule.

    For the approved five-speed, six-sample matrix this is exactly
    ``1,2,3,4,5,5,4,3,2,1`` repeated three times.  Odd sample counts retain
    the same ordering and omit already-full arms.
    """
    if not speeds:
        raise ValueError("at least one speed is required")
    if samples_per_speed <= 0:
        raise ValueError("samples_per_speed must be positive")
    schedule: list[int] = []
    counts = {speed: 0 for speed in speeds}
    cycle = tuple(speeds) + tuple(reversed(speeds))
    while any(count < samples_per_speed for count in counts.values()):
        for speed in cycle:
            if counts[speed] >= samples_per_speed:
                continue
            schedule.append(speed)
            counts[speed] += 1
    return schedule


def _integer(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _date_raw(snapshot: dict[str, object]) -> int:
    value = _integer(snapshot.get("date_raw"))
    if value is None:
        raise RuntimeError("semantic snapshot lacks integer date_raw")
    return value


def _subject(
    snapshot: dict[str, object], army_id: int | None
) -> dict[str, object] | None:
    if army_id is None:
        return None
    armies = snapshot.get("player_armies")
    if not isinstance(armies, list):
        return None
    for row in armies:
        if isinstance(row, dict) and row.get("army_id") == army_id:
            return row
    return None


def _diagnostics(snapshot: dict[str, object]) -> dict[str, object]:
    value = snapshot.get("diagnostics")
    return value if isinstance(value, dict) else {}


def _connection_generation(snapshot: dict[str, object]) -> int | None:
    return _integer(_diagnostics(snapshot).get("connection_generation"))


def _heartbeat_sequence(snapshot: dict[str, object]) -> int | None:
    heartbeat = _diagnostics(snapshot).get("last_heartbeat")
    if not isinstance(heartbeat, dict):
        return None
    return _integer(heartbeat.get("sequence"))


def _episode_identity(snapshot: dict[str, object]) -> tuple[object, object]:
    return (
        snapshot.get("episode_character_id"),
        snapshot.get("episode_run_id"),
    )


def _pending_interaction(snapshot: dict[str, object]) -> object:
    return snapshot.get("pending_character_interaction")


def _terminal(snapshot: dict[str, object]) -> bool:
    return bool(
        snapshot.get("one_life_terminal") is True
        or isinstance(snapshot.get("one_life_terminal_reason"), str)
    )


def _runtime_interrupt_reason(snapshot: dict[str, object]) -> str | None:
    if snapshot.get("map_ready") is not True:
        return "map_not_ready"
    if snapshot.get("active_event") is not None:
        return "active_event"
    if _pending_interaction(snapshot) is not None:
        return "pending_character_interaction"
    if _terminal(snapshot):
        return "one_life_terminal"
    return None


def _compact_snapshot(
    snapshot: dict[str, object], subject_army_id: int | None
) -> dict[str, object]:
    keys = (
        "snapshot_id",
        "revision",
        "native_revision",
        "date_raw",
        "phase",
        "map_ready",
        "paused",
        "speed",
        "episode_character_id",
        "episode_run_id",
        "active_event",
        "pending_character_interaction",
        "active_wars",
        "one_life_terminal",
        "one_life_terminal_reason",
    )
    return {key: copy.deepcopy(snapshot.get(key)) for key in keys} | {
        "connection_generation": _connection_generation(snapshot),
        "heartbeat_sequence": _heartbeat_sequence(snapshot),
        "subject_army": copy.deepcopy(_subject(snapshot, subject_army_id)),
    }


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
    revision = _integer(snapshot.get("revision"))
    if revision is None:
        raise RuntimeError("paused snapshot lacks a valid public revision")
    started_ns = time.perf_counter_ns()
    first = service.query_battle_control_snapshot_v1(
        subject_army_id,
        expected_revision=revision,
    )
    second = service.query_battle_control_snapshot_v1(
        subject_army_id,
        expected_revision=revision,
    )
    elapsed_ms = (time.perf_counter_ns() - started_ns) / 1_000_000.0
    first_frame = first["battle_control_snapshot"]
    second_frame = second["battle_control_snapshot"]
    first_sequence = _integer(first.get("query_sequence"))
    second_sequence = _integer(second.get("query_sequence"))
    stable = first_frame == second_frame
    sequence_increased = bool(
        first_sequence is not None
        and second_sequence is not None
        and second_sequence > first_sequence
    )
    return {
        "first": first,
        "second": second,
        "frame_sha256": _canonical_sha256(first_frame),
        "normalized_frame_sha256": _normalized_battle_frame_hash(first_frame),
        "immediate_frame_equal": stable,
        "query_sequence_increased": sequence_increased,
        "elapsed_ms": round(elapsed_ms, 3),
        "ok": stable and sequence_increased,
    }


def _normalize_battle_frame(value: object) -> object:
    """Remove transport/query binding metadata while retaining battle state."""
    if isinstance(value, dict):
        return {
            key: _normalize_battle_frame(item)
            for key, item in sorted(value.items())
            if key not in METADATA_KEYS
        }
    if isinstance(value, list):
        return [_normalize_battle_frame(item) for item in value]
    return value


def _normalized_battle_frame_hash(frame: object) -> str:
    return _canonical_sha256(_normalize_battle_frame(frame))


def _terminal_transition_frame(result: object) -> dict[str, object]:
    if not isinstance(result, dict):
        raise RuntimeError("terminal query returned a non-object")
    frame = result.get("battle_terminal_transition")
    if not isinstance(frame, dict):
        raise RuntimeError("terminal query omitted battle_terminal_transition")
    return frame


def _terminal_cursor_pair(
    service: GameplayBridgeService,
    *,
    combat_id: int,
    subject_army_id: int,
    snapshot: dict[str, object],
) -> dict[str, object]:
    """Freeze the process-local journal cursor before one restored arm.

    Restoring a save does not rewind the bridge-owned journal ring.  Therefore
    an old event for the same restored CombatID is legal here; the global
    ``latest_sequence`` is the exclusion cursor for this arm.
    """
    revision = _integer(snapshot.get("revision"))
    if revision is None:
        raise RuntimeError("paused snapshot lacks a valid public revision")
    first = service.query_battle_terminal_transition_v1(
        combat_id,
        subject_army_id,
        expected_revision=revision,
        after_terminal_sequence=None,
    )
    second = service.query_battle_terminal_transition_v1(
        combat_id,
        subject_army_id,
        expected_revision=revision,
        after_terminal_sequence=None,
    )
    first_frame = _terminal_transition_frame(first)
    second_frame = _terminal_transition_frame(second)
    first_sequence = _integer(first.get("query_sequence"))
    second_sequence = _integer(second.get("query_sequence"))
    journal = second_frame.get("terminal_journal")
    latest = (
        _integer(journal.get("latest_sequence"))
        if isinstance(journal, dict)
        else None
    )
    stable = first_frame == second_frame
    sequence_increased = bool(
        first_sequence is not None
        and second_sequence is not None
        and second_sequence > first_sequence
    )
    ok = bool(stable and sequence_increased and latest is not None and latest >= 0)
    return {
        "first": first,
        "second": second,
        "cursor": latest if latest and latest > 0 else None,
        "immediate_frame_equal": stable,
        "query_sequence_increased": sequence_increased,
        "ok": ok,
    }


def _terminal_outcome_projection(frame: dict[str, object]) -> dict[str, object]:
    """Select only exact terminal-event semantics, not late pause state."""
    journal = frame.get("terminal_journal")
    prior = frame.get("prior")
    removal = frame.get("removal")
    journal = journal if isinstance(journal, dict) else {}
    prior = prior if isinstance(prior, dict) else {}
    removal = removal if isinstance(removal, dict) else {}
    return {
        "event_status": journal.get("event_status"),
        "combat_id": prior.get("combat_id"),
        "terminal_kind": prior.get("terminal_kind"),
        "terminal_date_raw": prior.get("terminal_date_raw"),
        "suppress_normal_result_envelopes": prior.get(
            "suppress_normal_result_envelopes"
        ),
        "phase_raw": prior.get("phase_raw"),
        "phase_day": prior.get("phase_day"),
        "winner_raw": prior.get("winner_raw"),
        "finalized_before": prior.get("finalized_before"),
        "daily_guard_raw": prior.get("daily_guard_raw"),
        "province_id": prior.get("province_id"),
        "battle_result_id": prior.get("battle_result_id"),
        "wipe_raw": prior.get("wipe_raw"),
        "attacker_primary_participant_character_id": prior.get(
            "attacker_primary_participant_character_id"
        ),
        "defender_primary_participant_character_id": prior.get(
            "defender_primary_participant_character_id"
        ),
        "attacker_public_cunit_ids_in_stored_order": copy.deepcopy(
            prior.get("attacker_public_cunit_ids_in_stored_order")
        ),
        "defender_public_cunit_ids_in_stored_order": copy.deepcopy(
            prior.get("defender_public_cunit_ids_in_stored_order")
        ),
        "battle_warscore": copy.deepcopy(prior.get("battle_warscore")),
        "prior_combat_strictly_resolves": removal.get(
            "prior_combat_strictly_resolves"
        ),
        "prior_province_contains_prior_combat_id": removal.get(
            "prior_province_contains_prior_combat_id"
        ),
        "result_strictly_resolves": removal.get("result_strictly_resolves"),
        "result_relevant_player_count": removal.get(
            "result_relevant_player_count"
        ),
    }


def _terminal_outcome_pair(
    service: GameplayBridgeService,
    *,
    combat_id: int,
    subject_army_id: int,
    after_terminal_sequence: int | None,
    snapshot: dict[str, object],
) -> dict[str, object]:
    revision = _integer(snapshot.get("revision"))
    if revision is None:
        raise RuntimeError("paused terminal snapshot lacks a valid revision")
    first = service.query_battle_terminal_transition_v1(
        combat_id,
        subject_army_id,
        expected_revision=revision,
        after_terminal_sequence=after_terminal_sequence,
    )
    second = service.query_battle_terminal_transition_v1(
        combat_id,
        subject_army_id,
        expected_revision=revision,
        after_terminal_sequence=after_terminal_sequence,
    )
    first_frame = _terminal_transition_frame(first)
    second_frame = _terminal_transition_frame(second)
    first_sequence = _integer(first.get("query_sequence"))
    second_sequence = _integer(second.get("query_sequence"))
    stable = first_frame == second_frame
    sequence_increased = bool(
        first_sequence is not None
        and second_sequence is not None
        and second_sequence > first_sequence
    )
    projection = _terminal_outcome_projection(first_frame)
    projection_without_battle_warscore = copy.deepcopy(projection)
    projection_without_battle_warscore.pop("battle_warscore", None)
    journal = first_frame.get("terminal_journal")
    journal = journal if isinstance(journal, dict) else {}
    event_sequence = _integer(journal.get("event_sequence"))
    requested_cursor = _integer(journal.get("requested_after_sequence"))
    cursor_binding = requested_cursor == after_terminal_sequence
    event_follows_cursor = bool(
        event_sequence is not None
        and (
            after_terminal_sequence is None
            or event_sequence > after_terminal_sequence
        )
    )
    terminal_date_raw = _integer(projection.get("terminal_date_raw"))
    phase_day = _integer(projection.get("phase_day"))
    terminal_kind = projection.get("terminal_kind")
    ready = bool(
        first_frame.get("status") == "available"
        and first_frame.get("battle_terminal_transition_ready") is True
        and projection.get("event_status") == "observed"
        and terminal_kind in {"normal_result", "no_normal_result"}
        and projection.get("combat_id") == combat_id
        and cursor_binding
        and event_follows_cursor
        and terminal_date_raw is not None
        and phase_day is not None
        and phase_day >= 0
        and projection.get("prior_combat_strictly_resolves") is False
    )
    return {
        "first": first,
        "second": second,
        "immediate_frame_equal": stable,
        "query_sequence_increased": sequence_increased,
        "projection": projection,
        "normalized_outcome_sha256": _canonical_sha256(projection),
        "outcome_without_battle_warscore_sha256": _canonical_sha256(
            projection_without_battle_warscore
        ),
        "ok": bool(stable and sequence_increased and ready),
    }


def _neutral_start_reason(snapshot: dict[str, object]) -> str | None:
    reason = _runtime_interrupt_reason(snapshot)
    if reason is not None:
        return reason
    if snapshot.get("paused") is not True:
        return "map_not_paused"
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return "active_wars_unavailable"
    if wars:
        return "active_war"
    armies = snapshot.get("player_armies")
    for army in armies if isinstance(armies, list) else []:
        if not isinstance(army, dict):
            continue
        if army.get("in_combat") is True:
            return "player_army_in_combat"
        if army.get("retreating") is True or army.get("army_state") == "retreating":
            return "player_army_retreating"
    return None


def _battle_start_reason(
    snapshot: dict[str, object], subject_army_id: int
) -> str | None:
    reason = _runtime_interrupt_reason(snapshot)
    if reason is not None:
        return reason
    if snapshot.get("paused") is not True:
        return "map_not_paused"
    subject = _subject(snapshot, subject_army_id)
    if not isinstance(subject, dict):
        return "subject_army_missing"
    if subject.get("controllable") is not True:
        return "subject_army_not_controllable"
    if subject.get("in_combat") is not True:
        return "subject_army_not_in_combat"
    return None


def _submit_and_observe(
    driver: NativeHeadlessGameplayDriver,
    step: str,
    current: dict[str, object],
    predicate: Callable[[dict[str, object]], bool],
    *,
    timeout_seconds: float,
) -> tuple[dict[str, object], dict[str, object]]:
    """Submit an idempotent timeline primitive and prove its state result.

    The private primitive deliberately avoids the public command-history
    persistence barrier while CK3 is running.  This is a research harness
    optimization only; production commands and selectors are unchanged.
    """
    attempts: list[dict[str, object]] = []
    if predicate(current):
        now_ns = time.perf_counter_ns()
        return current, {
            "step": step,
            "already_satisfied": True,
            "attempts": attempts,
            "submit_ns": None,
            "ack_ns": None,
            "observed_ns": now_ns,
        }
    deadline = time.monotonic() + timeout_seconds
    observed = current
    first_submit_ns: int | None = None
    last_ack_ns: int | None = None
    for attempt_number in range(1, MAX_TIMELINE_COMMAND_ATTEMPTS + 1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        submit_ns = time.perf_counter_ns()
        if first_submit_ns is None:
            first_submit_ns = submit_ns
        result = driver._execute_primitive_step(
            step,
            expected_revision=None,
            timeout_seconds=remaining,
            internal_semantic_snapshot=True,
        )
        ack_ns = time.perf_counter_ns()
        last_ack_ns = ack_ns
        observed = driver._wait_for_life_advance_snapshot(
            driver.take_internal_semantic_snapshot(),
            predicate,
            timeout_seconds=min(2.0, max(0.001, deadline - time.monotonic())),
        )
        observed_ns = time.perf_counter_ns()
        attempts.append(
            {
                "attempt": attempt_number,
                "submit_ns": submit_ns,
                "ack_ns": ack_ns,
                "observed_ns": observed_ns,
                "ack_wall_ms": round((ack_ns - submit_ns) / 1_000_000.0, 3),
                "observe_wall_ms": round(
                    (observed_ns - ack_ns) / 1_000_000.0, 3
                ),
                "result": result,
                "postcondition": predicate(observed),
            }
        )
        if predicate(observed):
            return observed, {
                "step": step,
                "already_satisfied": False,
                "attempts": attempts,
                "submit_ns": first_submit_ns,
                "ack_ns": last_ack_ns,
                "observed_ns": observed_ns,
            }
    raise RuntimeError(
        f"timeline step {step} did not reach its observed postcondition; "
        f"last_date_raw={observed.get('date_raw')}, "
        f"last_speed={observed.get('speed')}, "
        f"last_paused={observed.get('paused')}, attempts={len(attempts)}"
    )


def _run_timeline_slice(
    driver: NativeHeadlessGameplayDriver,
    starting: dict[str, object],
    *,
    speed: int,
    target_days: int,
    timeout_seconds: float,
) -> dict[str, object]:
    """Run one no-barrier speed arm and always attempt to leave CK3 paused."""
    if starting.get("paused") is not True or starting.get("map_ready") is not True:
        raise RuntimeError("timeline slice requires a paused, map-ready snapshot")
    starting_date_raw = _date_raw(starting)
    target_date_raw = starting_date_raw + target_days * RAW_HOURS_PER_DAY
    slice_started_ns = time.perf_counter_ns()
    current = starting
    speed_action: dict[str, object] | None = None
    resume_action: dict[str, object] | None = None
    pause_action: dict[str, object] | None = None
    first_target_observed_ns: int | None = None
    first_target_observed_date_raw: int | None = None
    interrupt_reason: str | None = None
    run_error: str | None = None
    deadline = time.monotonic() + timeout_seconds
    try:
        current, speed_action = _submit_and_observe(
            driver,
            f"set-speed-{speed}",
            current,
            lambda snapshot: snapshot.get("speed") == speed,
            timeout_seconds=max(0.001, deadline - time.monotonic()),
        )
        current, resume_action = _submit_and_observe(
            driver,
            "resume-map",
            current,
            lambda snapshot: snapshot.get("paused") is False,
            timeout_seconds=max(0.001, deadline - time.monotonic()),
        )
        while _date_raw(current) < target_date_raw:
            interrupt_reason = _runtime_interrupt_reason(current)
            if interrupt_reason is not None:
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                interrupt_reason = "slice_timeout_before_target"
                break
            current = driver._wait_for_life_advance_change(
                int(current["revision"]), timeout_seconds=remaining
            )
        if interrupt_reason is None:
            interrupt_reason = _runtime_interrupt_reason(current)
        if _date_raw(current) >= target_date_raw:
            first_target_observed_ns = time.perf_counter_ns()
            first_target_observed_date_raw = _date_raw(current)
    except BaseException as error:
        run_error = f"{type(error).__name__}: {error}"
    finally:
        try:
            refreshed = driver.take_internal_semantic_snapshot()
            command_timeout = getattr(driver, "command_timeout_seconds", 15.0)
            if not isinstance(command_timeout, (int, float)) or command_timeout <= 0:
                command_timeout = 15.0
            current, pause_action = _submit_and_observe(
                driver,
                "pause-map",
                refreshed,
                lambda snapshot: snapshot.get("paused") is True,
                # Progress timeout must never consume the independent pause
                # budget; a RED slice still has to make a real stop attempt.
                timeout_seconds=max(5.0, min(float(command_timeout), 30.0)),
            )
        except BaseException as error:
            detail = f"{type(error).__name__}: {error}"
            run_error = detail if run_error is None else f"{run_error}; {detail}"
            try:
                current = driver.take_internal_semantic_snapshot()
            except BaseException:
                pass
    final_observed_ns = time.perf_counter_ns()
    return {
        "requested_speed": speed,
        "requested_days": target_days,
        "starting_date_raw": starting_date_raw,
        "target_date_raw": target_date_raw,
        "first_target_observed_date_raw": first_target_observed_date_raw,
        "final_paused_date_raw": _integer(current.get("date_raw")),
        "slice_started_ns": slice_started_ns,
        "first_target_observed_ns": first_target_observed_ns,
        "final_observed_ns": final_observed_ns,
        "speed_action": speed_action,
        "resume_action": resume_action,
        "pause_action": pause_action,
        "interrupt_reason": interrupt_reason,
        "error": run_error,
        "starting": _compact_snapshot(starting, None),
        "final": _compact_snapshot(current, None),
    }


def _run_terminal_slice(
    driver: NativeHeadlessGameplayDriver,
    starting: dict[str, object],
    *,
    subject_army_id: int,
    speed: int,
    terminal_max_days: int,
    timeout_seconds: float,
) -> dict[str, object]:
    """Run until the subject leaves combat and always attempt a real pause.

    The external observation only decides when it is safe to query.  Terminal
    equivalence is bound later to the passive native journal event, including
    its exact event date, so this loop is not a 4/5 same-day decision sentinel.
    """
    if starting.get("paused") is not True or starting.get("map_ready") is not True:
        raise RuntimeError("terminal slice requires a paused, map-ready snapshot")
    subject = _subject(starting, subject_army_id)
    if not isinstance(subject, dict) or subject.get("in_combat") is not True:
        raise RuntimeError("terminal slice requires the subject in active combat")
    starting_date_raw = _date_raw(starting)
    terminal_bound_date_raw = (
        starting_date_raw + terminal_max_days * RAW_HOURS_PER_DAY
    )
    slice_started_ns = time.perf_counter_ns()
    current = starting
    speed_action: dict[str, object] | None = None
    resume_action: dict[str, object] | None = None
    pause_action: dict[str, object] | None = None
    first_terminal_observed_ns: int | None = None
    first_terminal_observed_date_raw: int | None = None
    interrupt_reason: str | None = None
    run_error: str | None = None
    deadline = time.monotonic() + timeout_seconds
    try:
        current, speed_action = _submit_and_observe(
            driver,
            f"set-speed-{speed}",
            current,
            lambda snapshot: snapshot.get("speed") == speed,
            timeout_seconds=max(0.001, deadline - time.monotonic()),
        )
        current, resume_action = _submit_and_observe(
            driver,
            "resume-map",
            current,
            lambda snapshot: snapshot.get("paused") is False,
            timeout_seconds=max(0.001, deadline - time.monotonic()),
        )
        while True:
            current_subject = _subject(current, subject_army_id)
            if not (
                isinstance(current_subject, dict)
                and current_subject.get("in_combat") is True
            ):
                first_terminal_observed_ns = time.perf_counter_ns()
                first_terminal_observed_date_raw = _date_raw(current)
                break
            interrupt_reason = _runtime_interrupt_reason(current)
            if interrupt_reason is not None:
                break
            if _date_raw(current) >= terminal_bound_date_raw:
                interrupt_reason = "terminal_max_days_exceeded"
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                interrupt_reason = "slice_timeout_before_terminal"
                break
            current = driver._wait_for_life_advance_change(
                int(current["revision"]), timeout_seconds=remaining
            )
    except BaseException as error:
        run_error = f"{type(error).__name__}: {error}"
    finally:
        try:
            refreshed = driver.take_internal_semantic_snapshot()
            command_timeout = getattr(driver, "command_timeout_seconds", 15.0)
            if not isinstance(command_timeout, (int, float)) or command_timeout <= 0:
                command_timeout = 15.0
            current, pause_action = _submit_and_observe(
                driver,
                "pause-map",
                refreshed,
                lambda snapshot: snapshot.get("paused") is True,
                timeout_seconds=max(5.0, min(float(command_timeout), 30.0)),
            )
        except BaseException as error:
            detail = f"{type(error).__name__}: {error}"
            run_error = detail if run_error is None else f"{run_error}; {detail}"
            try:
                current = driver.take_internal_semantic_snapshot()
            except BaseException:
                pass
    final_observed_ns = time.perf_counter_ns()
    return {
        "requested_speed": speed,
        "terminal_max_days": terminal_max_days,
        "starting_date_raw": starting_date_raw,
        "terminal_bound_date_raw": terminal_bound_date_raw,
        "first_terminal_observed_date_raw": first_terminal_observed_date_raw,
        "final_paused_date_raw": _integer(current.get("date_raw")),
        "slice_started_ns": slice_started_ns,
        "first_terminal_observed_ns": first_terminal_observed_ns,
        "final_observed_ns": final_observed_ns,
        "speed_action": speed_action,
        "resume_action": resume_action,
        "pause_action": pause_action,
        "interrupt_reason": interrupt_reason,
        "error": run_error,
        "starting": _compact_snapshot(starting, subject_army_id),
        "final": _compact_snapshot(current, subject_army_id),
    }


def _derive_slice_metrics(slice_result: dict[str, object]) -> dict[str, object]:
    start = _integer(slice_result.get("starting_date_raw"))
    target = _integer(slice_result.get("target_date_raw"))
    first = _integer(slice_result.get("first_target_observed_date_raw"))
    final = _integer(slice_result.get("final_paused_date_raw"))
    started_ns = _integer(slice_result.get("slice_started_ns"))
    target_ns = _integer(slice_result.get("first_target_observed_ns"))
    final_ns = _integer(slice_result.get("final_observed_ns"))
    resume = slice_result.get("resume_action")
    pause = slice_result.get("pause_action")
    resume_observed_ns = (
        _integer(resume.get("observed_ns")) if isinstance(resume, dict) else None
    )
    pause_submit_ns = (
        _integer(pause.get("submit_ns")) if isinstance(pause, dict) else None
    )
    raw_delta = final - start if start is not None and final is not None else None
    integral_days = bool(raw_delta is not None and raw_delta % RAW_HOURS_PER_DAY == 0)
    elapsed_days = (
        raw_delta // RAW_HOURS_PER_DAY
        if raw_delta is not None and raw_delta >= 0 and integral_days
        else None
    )
    observation_overshoot = (
        (first - target) / RAW_HOURS_PER_DAY
        if first is not None and target is not None
        else None
    )
    settle_overshoot = (
        (final - target) / RAW_HOURS_PER_DAY
        if final is not None and target is not None
        else None
    )
    running_wall_ms = (
        (target_ns - resume_observed_ns) / 1_000_000.0
        if target_ns is not None and resume_observed_ns is not None
        else None
    )
    pause_settle_ms = (
        (final_ns - pause_submit_ns) / 1_000_000.0
        if final_ns is not None and pause_submit_ns is not None
        else None
    )
    total_wall_ms = (
        (final_ns - started_ns) / 1_000_000.0
        if final_ns is not None and started_ns is not None
        else None
    )
    return {
        "raw_delta": raw_delta,
        "raw_delta_nonnegative": raw_delta is not None and raw_delta >= 0,
        "raw_delta_integral_days": integral_days,
        "elapsed_days": elapsed_days,
        "observation_overshoot_days": observation_overshoot,
        "settle_overshoot_days": settle_overshoot,
        "running_wall_ms": (
            round(running_wall_ms, 3) if running_wall_ms is not None else None
        ),
        "pause_settle_ms": (
            round(pause_settle_ms, 3) if pause_settle_ms is not None else None
        ),
        "total_wall_ms": (
            round(total_wall_ms, 3) if total_wall_ms is not None else None
        ),
        "game_days_per_running_second": (
            round(elapsed_days / (running_wall_ms / 1000.0), 6)
            if elapsed_days is not None
            and running_wall_ms is not None
            and running_wall_ms > 0
            else None
        ),
        "game_days_per_end_to_end_second": (
            round(elapsed_days / (total_wall_ms / 1000.0), 6)
            if elapsed_days is not None
            and total_wall_ms is not None
            and total_wall_ms > 0
            else None
        ),
    }


def _slice_postconditions(
    slice_result: dict[str, object],
    *,
    starting: dict[str, object],
    final: dict[str, object],
) -> dict[str, object]:
    requested_speed = slice_result.get("requested_speed")
    metrics = _derive_slice_metrics(slice_result)
    starting_episode = _episode_identity(starting)
    final_episode = _episode_identity(final)
    checks = {
        "no_error": slice_result.get("error") is None,
        "target_observed": (
            slice_result.get("first_target_observed_date_raw") is not None
        ),
        "final_paused": final.get("paused") is True,
        "final_map_ready": final.get("map_ready") is True,
        "final_date_matches_readback": (
            _integer(final.get("date_raw"))
            == _integer(slice_result.get("final_paused_date_raw"))
        ),
        "requested_speed_observed": final.get("speed") == requested_speed,
        "same_episode": (
            starting_episode[0] is not None
            and starting_episode[1] is not None
            and starting_episode == final_episode
        ),
        "same_connection_generation": (
            _connection_generation(starting) is not None
            and _connection_generation(starting) == _connection_generation(final)
        ),
        "raw_delta_nonnegative": metrics["raw_delta_nonnegative"],
        "raw_delta_integral_days": metrics["raw_delta_integral_days"],
        "no_runtime_interrupt": slice_result.get("interrupt_reason") is None,
        "final_uncontaminated": _runtime_interrupt_reason(final) is None,
    }
    return {"checks": checks, "ok": all(checks.values()), "metrics": metrics}


def _derive_terminal_metrics(
    slice_result: dict[str, object],
) -> dict[str, object]:
    start = _integer(slice_result.get("starting_date_raw"))
    first = _integer(slice_result.get("first_terminal_observed_date_raw"))
    final = _integer(slice_result.get("final_paused_date_raw"))
    started_ns = _integer(slice_result.get("slice_started_ns"))
    terminal_ns = _integer(slice_result.get("first_terminal_observed_ns"))
    final_ns = _integer(slice_result.get("final_observed_ns"))
    resume = slice_result.get("resume_action")
    pause = slice_result.get("pause_action")
    resume_observed_ns = (
        _integer(resume.get("observed_ns")) if isinstance(resume, dict) else None
    )
    pause_submit_ns = (
        _integer(pause.get("submit_ns")) if isinstance(pause, dict) else None
    )
    raw_delta = final - start if start is not None and final is not None else None
    integral_days = bool(raw_delta is not None and raw_delta % RAW_HOURS_PER_DAY == 0)
    elapsed_days = (
        raw_delta // RAW_HOURS_PER_DAY
        if raw_delta is not None and raw_delta >= 0 and integral_days
        else None
    )
    terminal_observed_raw_delta = (
        first - start if first is not None and start is not None else None
    )
    terminal_observed_integral_days = bool(
        terminal_observed_raw_delta is not None
        and terminal_observed_raw_delta >= 0
        and terminal_observed_raw_delta % RAW_HOURS_PER_DAY == 0
    )
    terminal_observed_elapsed_days = (
        terminal_observed_raw_delta // RAW_HOURS_PER_DAY
        if terminal_observed_integral_days
        and terminal_observed_raw_delta is not None
        else None
    )
    terminal_observation_wall_ms = (
        (terminal_ns - resume_observed_ns) / 1_000_000.0
        if terminal_ns is not None and resume_observed_ns is not None
        else None
    )
    pause_settle_ms = (
        (final_ns - pause_submit_ns) / 1_000_000.0
        if final_ns is not None and pause_submit_ns is not None
        else None
    )
    total_wall_ms = (
        (final_ns - started_ns) / 1_000_000.0
        if final_ns is not None and started_ns is not None
        else None
    )
    return {
        "raw_delta": raw_delta,
        "raw_delta_nonnegative": raw_delta is not None and raw_delta >= 0,
        "raw_delta_integral_days": integral_days,
        "elapsed_days": elapsed_days,
        "terminal_observed_raw_delta": terminal_observed_raw_delta,
        "terminal_observed_raw_delta_integral_days": (
            terminal_observed_integral_days
        ),
        "terminal_observed_elapsed_days": terminal_observed_elapsed_days,
        "terminal_observation_wall_ms": (
            round(terminal_observation_wall_ms, 3)
            if terminal_observation_wall_ms is not None
            else None
        ),
        "pause_settle_ms": (
            round(pause_settle_ms, 3) if pause_settle_ms is not None else None
        ),
        "total_wall_ms": (
            round(total_wall_ms, 3) if total_wall_ms is not None else None
        ),
        "game_days_per_running_second": (
            round(
                terminal_observed_elapsed_days
                / (terminal_observation_wall_ms / 1000.0),
                6,
            )
            if terminal_observed_elapsed_days is not None
            and terminal_observation_wall_ms is not None
            and terminal_observation_wall_ms > 0
            else None
        ),
        "game_days_per_end_to_end_second": (
            round(elapsed_days / (total_wall_ms / 1000.0), 6)
            if elapsed_days is not None
            and total_wall_ms is not None
            and total_wall_ms > 0
            else None
        ),
        "external_terminal_observation_date_raw": first,
    }


def _terminal_slice_postconditions(
    slice_result: dict[str, object],
    *,
    subject_army_id: int,
    starting: dict[str, object],
    final: dict[str, object],
) -> dict[str, object]:
    metrics = _derive_terminal_metrics(slice_result)
    starting_episode = _episode_identity(starting)
    final_episode = _episode_identity(final)
    final_subject = _subject(final, subject_army_id)
    terminal_observed = _integer(
        slice_result.get("first_terminal_observed_date_raw")
    )
    checks = {
        "no_error": slice_result.get("error") is None,
        "terminal_observed": terminal_observed is not None,
        "final_subject_left_combat": not (
            isinstance(final_subject, dict)
            and final_subject.get("in_combat") is True
        ),
        "final_paused": final.get("paused") is True,
        "final_map_ready": final.get("map_ready") is True,
        "final_date_matches_readback": (
            _integer(final.get("date_raw"))
            == _integer(slice_result.get("final_paused_date_raw"))
        ),
        "requested_speed_observed": (
            final.get("speed") == slice_result.get("requested_speed")
        ),
        "same_episode": (
            starting_episode[0] is not None
            and starting_episode[1] is not None
            and starting_episode == final_episode
        ),
        "same_connection_generation": (
            _connection_generation(starting) is not None
            and _connection_generation(starting) == _connection_generation(final)
        ),
        "raw_delta_nonnegative": metrics["raw_delta_nonnegative"],
        "raw_delta_integral_days": metrics["raw_delta_integral_days"],
        "no_preterminal_interrupt": slice_result.get("interrupt_reason") is None,
    }
    return {"checks": checks, "ok": all(checks.values()), "metrics": metrics}


def _terminal_date_within_slice_bound(
    slice_result: dict[str, object], terminal_date_raw: int | None
) -> bool:
    starting_date_raw = _integer(slice_result.get("starting_date_raw"))
    terminal_bound_date_raw = _integer(
        slice_result.get("terminal_bound_date_raw")
    )
    return bool(
        terminal_date_raw is not None
        and starting_date_raw is not None
        and terminal_bound_date_raw is not None
        and starting_date_raw <= terminal_date_raw <= terminal_bound_date_raw
    )


def _summarize_stop_envelope(
    rows: list[dict[str, object]], speeds: tuple[int, ...]
) -> dict[str, object]:
    by_speed: dict[str, object] = {}
    for speed in speeds:
        samples = [row for row in rows if row.get("requested_speed") == speed]
        valid = [row for row in samples if row.get("operational_ok") is True]
        overshoots = [
            row.get("metrics", {}).get("settle_overshoot_days")
            for row in valid
            if isinstance(row.get("metrics"), dict)
            and isinstance(
                row["metrics"].get("settle_overshoot_days"), (int, float)
            )
        ]
        by_speed[str(speed)] = {
            "sample_count": len(samples),
            "valid_sample_count": len(valid),
            "empirical_max_settle_overshoot_days": (
                max(overshoots) if overshoots else None
            ),
            "initial_guard_days": max(overshoots) + 1 if overshoots else None,
            "finite_external_stop_envelope": (
                bool(overshoots) and len(valid) == len(samples)
            ),
        }
    return {
        "by_speed": by_speed,
        "ok": bool(rows) and all(row.get("operational_ok") is True for row in rows),
    }


def _battle_group_key(row: dict[str, object]) -> tuple[object, object, object]:
    battle = row.get("battle")
    metrics = row.get("metrics")
    return (
        (
            battle.get("before_normalized_frame_sha256")
            if isinstance(battle, dict)
            else None
        ),
        metrics.get("elapsed_days") if isinstance(metrics, dict) else None,
        row.get("final_paused_date_raw"),
    )


def _summarize_battle_parity(
    rows: list[dict[str, object]], speeds: tuple[int, ...]
) -> dict[str, object]:
    groups: dict[tuple[object, object, object], list[dict[str, object]]] = {}
    for row in rows:
        battle = row.get("battle")
        if not (
            row.get("operational_ok") is True
            and isinstance(battle, dict)
            and isinstance(battle.get("after_normalized_frame_sha256"), str)
        ):
            continue
        groups.setdefault(_battle_group_key(row), []).append(row)

    rendered_groups: list[dict[str, object]] = []
    for key, members in groups.items():
        hashes = sorted(
            {
                str(member["battle"]["after_normalized_frame_sha256"])
                for member in members
                if isinstance(member.get("battle"), dict)
            }
        )
        rendered_groups.append(
            {
                "before_normalized_frame_sha256": key[0],
                "elapsed_days": key[1],
                "final_paused_date_raw": key[2],
                "speeds": [member.get("requested_speed") for member in members],
                "sample_indices": [member.get("sample_index") for member in members],
                "after_normalized_frame_sha256": hashes,
                "equivalent": len(hashes) == 1,
            }
        )

    by_speed: dict[str, object] = {}
    baseline_requested = 1 in speeds
    for speed in speeds:
        if speed == 1:
            continue
        comparable = [
            group
            for group in rendered_groups
            if 1 in group["speeds"] and speed in group["speeds"]
        ]
        mismatches = [group for group in comparable if group["equivalent"] is not True]
        status = (
            "baseline_speed_1_not_requested"
            if not baseline_requested
            else "insufficient_matched_elapsed"
            if not comparable
            else "mismatch"
            if mismatches
            else "matched"
        )
        by_speed[str(speed)] = {
            "status": status,
            "comparable_group_count": len(comparable),
            "mismatch_group_count": len(mismatches),
        }
    parity_ok = bool(by_speed) and all(
        isinstance(value, dict) and value.get("status") == "matched"
        for value in by_speed.values()
    )
    return {
        "groups": rendered_groups,
        "by_speed": by_speed,
        "all_arms_operational": bool(rows)
        and all(row.get("operational_ok") is True for row in rows),
        "parity_ok": parity_ok,
        "ok": bool(rows)
        and all(row.get("operational_ok") is True for row in rows)
        and parity_ok,
    }


def _summarize_terminal_parity(
    rows: list[dict[str, object]], speeds: tuple[int, ...]
) -> dict[str, object]:
    by_speed: dict[str, object] = {}
    for speed in speeds:
        samples = [row for row in rows if row.get("requested_speed") == speed]
        valid = [row for row in samples if row.get("operational_ok") is True]
        starting_hashes = sorted(
            {
                str(row["terminal"]["before_normalized_frame_sha256"])
                for row in valid
                if isinstance(row.get("terminal"), dict)
                and isinstance(
                    row["terminal"].get("before_normalized_frame_sha256"), str
                )
            }
        )
        outcome_hashes = sorted(
            {
                str(row["terminal"]["normalized_outcome_sha256"])
                for row in valid
                if isinstance(row.get("terminal"), dict)
                and isinstance(
                    row["terminal"].get("normalized_outcome_sha256"), str
                )
            }
        )
        non_warscore_hashes = sorted(
            {
                str(
                    row["terminal"][
                        "outcome_without_battle_warscore_sha256"
                    ]
                )
                for row in valid
                if isinstance(row.get("terminal"), dict)
                and isinstance(
                    row["terminal"].get(
                        "outcome_without_battle_warscore_sha256"
                    ),
                    str,
                )
            }
        )
        warscore_values = [
            row["terminal"].get("battle_warscore_value_raw_q100000")
            for row in valid
            if isinstance(row.get("terminal"), dict)
            and _integer(
                row["terminal"].get("battle_warscore_value_raw_q100000")
            )
            is not None
        ]
        metrics = [
            row.get("metrics")
            for row in valid
            if isinstance(row.get("metrics"), dict)
        ]
        pause_lags = [
            row["terminal"].get("pause_lag_days")
            for row in valid
            if isinstance(row.get("terminal"), dict)
            and isinstance(
                row["terminal"].get("pause_lag_days"), (int, float)
            )
        ]
        by_speed[str(speed)] = {
            "sample_count": len(samples),
            "valid_sample_count": len(valid),
            "starting_frame_sha256": starting_hashes,
            "terminal_outcome_sha256": outcome_hashes,
            "strict_terminal_outcome_reproducible": bool(
                valid and len(valid) == len(samples) and len(outcome_hashes) == 1
            ),
            "outcome_without_battle_warscore_sha256": non_warscore_hashes,
            "outcome_without_battle_warscore_reproducible": bool(
                valid
                and len(valid) == len(samples)
                and len(non_warscore_hashes) == 1
            ),
            "battle_warscore_value_raw_q100000": warscore_values,
            "battle_warscore_distribution": {
                str(value): warscore_values.count(value)
                for value in sorted(set(warscore_values))
            },
            "elapsed_days": sorted(
                {
                    metric.get("elapsed_days")
                    for metric in metrics
                    if isinstance(metric.get("elapsed_days"), int)
                }
            ),
            "mean_total_wall_ms": (
                round(
                    sum(
                        float(metric["total_wall_ms"])
                        for metric in metrics
                        if isinstance(metric.get("total_wall_ms"), (int, float))
                    )
                    / len(
                        [
                            metric
                            for metric in metrics
                            if isinstance(
                                metric.get("total_wall_ms"), (int, float)
                            )
                        ]
                    ),
                    3,
                )
                if any(
                    isinstance(metric.get("total_wall_ms"), (int, float))
                    for metric in metrics
                )
                else None
            ),
            "max_pause_lag_days": max(pause_lags) if pause_lags else None,
        }

    baseline = by_speed.get("1")
    baseline_operational = bool(
        isinstance(baseline, dict)
        and baseline.get("sample_count", 0) > 0
        and baseline.get("sample_count") == baseline.get("valid_sample_count")
        and len(baseline.get("starting_frame_sha256", [])) == 1
    )
    baseline_ready = bool(
        baseline_operational
        and baseline.get("strict_terminal_outcome_reproducible") is True
    )
    comparison: dict[str, object] = {}
    for speed in speeds:
        if speed == 1:
            continue
        arm = by_speed[str(speed)]
        arm_operational = bool(
            arm.get("sample_count", 0) > 0
            and arm.get("sample_count") == arm.get("valid_sample_count")
            and len(arm.get("starting_frame_sha256", [])) == 1
        )
        arm_ready = bool(
            arm_operational
            and arm.get("strict_terminal_outcome_reproducible") is True
        )
        same_start = bool(
            baseline_ready
            and arm.get("starting_frame_sha256")
            == baseline.get("starting_frame_sha256")
        )
        same_outcome = bool(
            baseline_ready
            and arm.get("terminal_outcome_sha256")
            == baseline.get("terminal_outcome_sha256")
        )
        status = (
            "baseline_unavailable"
            if not baseline_operational
            else "baseline_not_reproducible"
            if not baseline_ready
            else "arm_unavailable"
            if not arm_operational
            else "arm_not_reproducible"
            if not arm_ready
            else "starting_frame_mismatch"
            if not same_start
            else "terminal_outcome_mismatch"
            if not same_outcome
            else "matched"
        )
        comparison[str(speed)] = {
            "status": status,
            "same_starting_frame": same_start,
            "same_terminal_outcome": same_outcome,
        }
    parity_ok = bool(comparison) and all(
        isinstance(value, dict) and value.get("status") == "matched"
        for value in comparison.values()
    )
    all_arms_operational = bool(rows) and all(
        row.get("operational_ok") is True for row in rows
    )
    all_non_warscore_hashes = sorted(
        {
            value
            for arm in by_speed.values()
            if isinstance(arm, dict)
            for value in arm.get("outcome_without_battle_warscore_sha256", [])
            if isinstance(value, str)
        }
    )
    within_speed_not_reproducible = [
        speed
        for speed, arm in by_speed.items()
        if isinstance(arm, dict)
        and arm.get("strict_terminal_outcome_reproducible") is False
    ]
    return {
        "by_speed": by_speed,
        "comparisons_to_speed_1": comparison,
        "all_arms_operational": all_arms_operational,
        "within_speed_not_reproducible": within_speed_not_reproducible,
        "outcome_without_battle_warscore_sha256": all_non_warscore_hashes,
        "outcome_without_battle_warscore_all_equal": bool(
            rows and len(all_non_warscore_hashes) == 1
        ),
        "parity_ok": parity_ok,
        "ok": all_arms_operational and parity_ok,
    }


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started_wall = utc_now()
    started = time.monotonic()
    speeds = tuple(args.speeds)
    schedule = _balanced_speed_schedule(speeds, args.samples_per_speed)
    spec = make_spec(args.state_dir, args.game_dir)
    checkpoint_path = spec.profile_dir / "save games" / "xar_checkpoint.ck3"
    checkpoint_before = _file_identity(checkpoint_path)
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
    rows: list[dict[str, object]] = []
    restore_records: list[dict[str, object]] = []
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
                cold_start_checkpoint=True,
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
            name="xar-battle-speed-matrix-session",
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
            cold_start_checkpoint=True,
            allow_terminal=False,
        )
        action_steps = set(service.capabilities().get("action_steps", []))
        required_steps = {
            *(f"set-speed-{speed}" for speed in speeds),
            "resume-map",
            "pause-map",
        }
        if args.mode in {"battle-parity", "terminal-parity"}:
            required_steps.add("restore-checkpoint")
        missing_steps = sorted(required_steps - action_steps)
        if missing_steps:
            raise RuntimeError(
                f"native bridge lacks matrix primitives: {missing_steps}"
            )

        for sample_index, speed in enumerate(schedule, start=1):
            restore: dict[str, object] | None = None
            restore_wall_ms = 0.0
            if args.mode in {"battle-parity", "terminal-parity"} and sample_index > 1:
                restore_started_ns = time.perf_counter_ns()
                current = service.snapshot()
                restore = service.restore_checkpoint(
                    expected_revision=int(current["revision"])
                )
                restore_readiness = _wait_for_readiness(
                    driver,
                    session_done=session_done,
                    session_state=session_state,
                    timeout_seconds=float(args.readiness_timeout),
                    stable_seconds=0.5,
                    poll_interval_seconds=0.05,
                    cold_start_checkpoint=True,
                    allow_terminal=False,
                )
                restore_wall_ms = (
                    time.perf_counter_ns() - restore_started_ns
                ) / 1_000_000.0
                restore_records.append(
                    {
                        "sample_index": sample_index,
                        "speed": speed,
                        "wall_ms": round(restore_wall_ms, 3),
                        "result": restore,
                        "readiness": restore_readiness,
                    }
                )

            starting_internal = driver.take_internal_semantic_snapshot()
            if (
                args.mode == "stop-envelope"
                and args.stop_envelope_scenario == "neutral"
            ):
                start_reason = _neutral_start_reason(starting_internal)
            else:
                start_reason = _battle_start_reason(
                    starting_internal, int(args.subject_army_id)
                )
            if start_reason is not None:
                raise RuntimeError(
                    f"sample {sample_index} speed {speed} invalid start: "
                    f"{start_reason}"
                )

            before_query: dict[str, object] | None = None
            terminal_cursor: dict[str, object] | None = None
            combat_id: int | None = None
            if args.mode in {"battle-parity", "terminal-parity"}:
                starting_public = service.snapshot()
                before_query = _query_pair(
                    service, int(args.subject_army_id), starting_public
                )
                if before_query.get("ok") is not True:
                    raise RuntimeError("repeated pre-arm battle frames differ")
                if args.mode == "terminal-parity":
                    before_frame = before_query["first"].get(
                        "battle_control_snapshot"
                    )
                    combat_id = (
                        _integer(before_frame.get("combat_id"))
                        if isinstance(before_frame, dict)
                        else None
                    )
                    if combat_id is None or combat_id <= 0:
                        raise RuntimeError(
                            "pre-arm battle frame lacks a positive combat_id"
                        )
                    terminal_cursor = _terminal_cursor_pair(
                        service,
                        combat_id=combat_id,
                        subject_army_id=int(args.subject_army_id),
                        snapshot=starting_public,
                    )
                    if terminal_cursor.get("ok") is not True:
                        raise RuntimeError(
                            "terminal journal cursor was not stable before arm"
                        )
                starting_internal = driver.take_internal_semantic_snapshot()

            if args.mode == "terminal-parity":
                raw_slice = _run_terminal_slice(
                    driver,
                    starting_internal,
                    subject_army_id=int(args.subject_army_id),
                    speed=speed,
                    terminal_max_days=args.terminal_max_days,
                    timeout_seconds=float(args.slice_timeout),
                )
            else:
                raw_slice = _run_timeline_slice(
                    driver,
                    starting_internal,
                    speed=speed,
                    target_days=args.target_days,
                    timeout_seconds=float(args.slice_timeout),
                )
            final_internal = driver.take_internal_semantic_snapshot()
            if args.mode == "terminal-parity":
                postconditions = _terminal_slice_postconditions(
                    raw_slice,
                    subject_army_id=int(args.subject_army_id),
                    starting=starting_internal,
                    final=final_internal,
                )
            else:
                postconditions = _slice_postconditions(
                    raw_slice,
                    starting=starting_internal,
                    final=final_internal,
                )
            if args.mode == "stop-envelope":
                final_scenario_reason = (
                    _neutral_start_reason(final_internal)
                    if args.stop_envelope_scenario == "neutral"
                    else _battle_start_reason(
                        final_internal, int(args.subject_army_id)
                    )
                )
            else:
                final_scenario_reason = None
            row: dict[str, object] = {
                "sample_index": sample_index,
                "requested_speed": speed,
                "requested_days": (
                    args.target_days if args.mode != "terminal-parity" else None
                ),
                "terminal_max_days": (
                    args.terminal_max_days
                    if args.mode == "terminal-parity"
                    else None
                ),
                "restore_wall_ms": round(restore_wall_ms, 3),
                "starting_date_raw": raw_slice["starting_date_raw"],
                "target_date_raw": raw_slice.get("target_date_raw"),
                "terminal_bound_date_raw": raw_slice.get(
                    "terminal_bound_date_raw"
                ),
                "first_target_observed_date_raw": raw_slice.get(
                    "first_target_observed_date_raw"
                ),
                "first_terminal_observed_date_raw": raw_slice.get(
                    "first_terminal_observed_date_raw"
                ),
                "final_paused_date_raw": raw_slice["final_paused_date_raw"],
                "starting": _compact_snapshot(
                    starting_internal, args.subject_army_id
                ),
                "final": _compact_snapshot(final_internal, args.subject_army_id),
                "timeline": {
                    key: raw_slice.get(key)
                    for key in (
                        "speed_action",
                        "resume_action",
                        "pause_action",
                        "interrupt_reason",
                        "error",
                    )
                },
                "metrics": postconditions["metrics"],
                "postconditions": postconditions["checks"],
                "final_scenario_reason": final_scenario_reason,
                "operational_ok": bool(
                    postconditions["ok"] is True
                    and final_scenario_reason is None
                ),
            }
            start_hb = _heartbeat_sequence(starting_internal)
            final_hb = _heartbeat_sequence(final_internal)
            row["heartbeat_sequence_delta"] = (
                final_hb - start_hb
                if start_hb is not None and final_hb is not None
                else None
            )
            start_revision = _integer(starting_internal.get("revision"))
            final_revision = _integer(final_internal.get("revision"))
            row["semantic_revision_delta"] = (
                final_revision - start_revision
                if start_revision is not None and final_revision is not None
                else None
            )

            if args.mode == "battle-parity":
                after_query: dict[str, object] | None = None
                final_public = service.snapshot()
                after_subject = _subject(final_public, args.subject_army_id)
                battle_status = "subject_left_combat"
                if (
                    isinstance(after_subject, dict)
                    and after_subject.get("controllable") is True
                    and after_subject.get("in_combat") is True
                ):
                    after_query = _query_pair(
                        service, int(args.subject_army_id), final_public
                    )
                    battle_status = (
                        "available" if after_query.get("ok") is True else "unstable"
                    )
                row["battle"] = {
                    "status": battle_status,
                    "before_query": before_query,
                    "after_query": after_query,
                    "before_normalized_frame_sha256": (
                        before_query.get("normalized_frame_sha256")
                        if isinstance(before_query, dict)
                        else None
                    ),
                    "after_normalized_frame_sha256": (
                        after_query.get("normalized_frame_sha256")
                        if isinstance(after_query, dict)
                        else None
                    ),
                }
                row["operational_ok"] = bool(
                    row["operational_ok"] is True
                    and isinstance(after_query, dict)
                    and after_query.get("ok") is True
                )
            elif args.mode == "terminal-parity":
                if combat_id is None or terminal_cursor is None:
                    raise RuntimeError("terminal arm lost its pre-arm bindings")
                final_public = service.snapshot()
                terminal_outcome = _terminal_outcome_pair(
                    service,
                    combat_id=combat_id,
                    subject_army_id=int(args.subject_army_id),
                    after_terminal_sequence=terminal_cursor.get("cursor"),
                    snapshot=final_public,
                )
                projection = terminal_outcome.get("projection")
                battle_warscore = (
                    projection.get("battle_warscore")
                    if isinstance(projection, dict)
                    else None
                )
                battle_warscore_value_raw = (
                    _integer(battle_warscore.get("value_raw_q100000"))
                    if isinstance(battle_warscore, dict)
                    else None
                )
                terminal_date_raw = (
                    _integer(projection.get("terminal_date_raw"))
                    if isinstance(projection, dict)
                    else None
                )
                terminal_within_bound = _terminal_date_within_slice_bound(
                    raw_slice, terminal_date_raw
                )
                final_paused_date_raw = _integer(
                    raw_slice.get("final_paused_date_raw")
                )
                pause_lag_raw = (
                    final_paused_date_raw - terminal_date_raw
                    if final_paused_date_raw is not None
                    and terminal_date_raw is not None
                    else None
                )
                pause_lag_integral = bool(
                    pause_lag_raw is not None
                    and pause_lag_raw >= 0
                    and pause_lag_raw % RAW_HOURS_PER_DAY == 0
                )
                pause_lag_days = (
                    pause_lag_raw // RAW_HOURS_PER_DAY
                    if pause_lag_integral and pause_lag_raw is not None
                    else None
                )
                pause_lag_ok = bool(
                    pause_lag_days is not None
                    and pause_lag_days <= args.terminal_max_pause_lag_days
                )
                external_observed_date_raw = _integer(
                    raw_slice.get("first_terminal_observed_date_raw")
                )
                external_observation_lag_raw = (
                    external_observed_date_raw - terminal_date_raw
                    if external_observed_date_raw is not None
                    and terminal_date_raw is not None
                    else None
                )
                external_observation_lag_days = (
                    external_observation_lag_raw / RAW_HOURS_PER_DAY
                    if external_observation_lag_raw is not None
                    else None
                )
                row["terminal"] = {
                    "status": (
                        "available"
                        if terminal_outcome.get("ok") is True
                        else "unavailable"
                    ),
                    "combat_id": combat_id,
                    "before_query": before_query,
                    "before_normalized_frame_sha256": (
                        before_query.get("normalized_frame_sha256")
                        if isinstance(before_query, dict)
                        else None
                    ),
                    "journal_cursor": terminal_cursor,
                    "outcome_query": terminal_outcome,
                    "normalized_outcome_sha256": terminal_outcome.get(
                        "normalized_outcome_sha256"
                    ),
                    "outcome_without_battle_warscore_sha256": (
                        terminal_outcome.get(
                            "outcome_without_battle_warscore_sha256"
                        )
                    ),
                    "battle_warscore_value_raw_q100000": (
                        battle_warscore_value_raw
                    ),
                    "terminal_date_raw": terminal_date_raw,
                    "terminal_within_bound": terminal_within_bound,
                    "external_observation_lag_days": (
                        round(external_observation_lag_days, 6)
                        if external_observation_lag_days is not None
                        else None
                    ),
                    "pause_lag_days": pause_lag_days,
                    "pause_lag_integral_days": pause_lag_integral,
                    "pause_lag_within_bound": pause_lag_ok,
                    "max_pause_lag_days": args.terminal_max_pause_lag_days,
                }
                row["operational_ok"] = bool(
                    row["operational_ok"] is True
                    and terminal_outcome.get("ok") is True
                    and terminal_within_bound
                    and pause_lag_ok
                )
            rows.append(row)
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
    if args.mode == "stop-envelope":
        summary = _summarize_stop_envelope(rows, speeds)
    elif args.mode == "battle-parity":
        summary = _summarize_battle_parity(rows, speeds)
    else:
        summary = _summarize_terminal_parity(rows, speeds)
    checkpoint_after = _file_identity(checkpoint_path)
    checkpoint_unchanged = bool(
        checkpoint_before is not None
        and checkpoint_before == checkpoint_after
    )
    expected_samples = len(schedule)
    ok = bool(
        primary_error is None
        and len(rows) == expected_samples
        and summary.get("ok") is True
        and cleanup.get("ok") is True
        and checkpoint_unchanged
    )
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_battle_speed_matrix_live_acceptance",
        "research_only": True,
        "production_selector_changed": False,
        "started_at": started_wall,
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "mode": args.mode,
        "stop_envelope_scenario": args.stop_envelope_scenario,
        "speeds": list(speeds),
        "samples_per_speed": args.samples_per_speed,
        "target_days": args.target_days,
        "terminal_max_days": args.terminal_max_days,
        "terminal_max_pause_lag_days": args.terminal_max_pause_lag_days,
        "schedule": schedule,
        "subject_army_id": args.subject_army_id,
        "load_kind": "cold_checkpoint",
        "checkpoint": {
            "before": checkpoint_before,
            "after": checkpoint_after,
            "immutable": checkpoint_unchanged,
        },
        "identity": {
            "pipe": config.pipe_name,
            "bridge_dll": str(config.dll_path),
            "bridge_dll_sha256": _sha256_file(config.dll_path),
            "bridge_injector": str(config.injector_path),
            "bridge_injector_sha256": _sha256_file(config.injector_path),
        },
        "readiness": readiness,
        "restore_records": restore_records,
        "rows": rows,
        "summary": summary,
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": primary_error,
    }
    return payload, 0 if ok else 1


def main() -> int:
    args = _parser().parse_args()
    speeds = tuple(args.speeds)
    try:
        _validate_speed_request(
            args.mode,
            speeds,
            samples_per_speed=args.samples_per_speed,
            target_days=args.target_days,
            terminal_max_days=args.terminal_max_days,
            terminal_max_pause_lag_days=args.terminal_max_pause_lag_days,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error
    if not args.cold_start_checkpoint:
        raise SystemExit(
            "--cold-start-checkpoint is required so every matrix uses an "
            "immutable managed seed"
        )
    if (
        args.mode in {"battle-parity", "terminal-parity"}
        and args.stop_envelope_scenario != "neutral"
    ):
        raise SystemExit(
            "--stop-envelope-scenario applies only to stop-envelope"
        )
    subject_required = bool(
        args.mode in {"battle-parity", "terminal-parity"}
        or args.stop_envelope_scenario == "active-battle"
    )
    if subject_required and args.subject_army_id is None:
        raise SystemExit(
            "--subject-army-id is required for parity modes and "
            "active-battle stop-envelope"
        )
    for name in ("timeout", "readiness_timeout", "slice_timeout"):
        if getattr(args, name) <= 0:
            raise SystemExit(f"--{name.replace('_', '-')} must be positive")
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
                "mode": payload["mode"],
                "schedule": payload["schedule"],
                "summary": payload["summary"],
                "cleanup": payload["cleanup"],
                "error": payload["error"],
            },
            ensure_ascii=False,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
