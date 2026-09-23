"""Bounded research preparation for one original main-phase combat tick.

This is an acceptance runner, not a gameplay policy. Its caller must verify an
official no-launch pair before cold start, persist each observation, and stop
the supervised CK3 process after return or failure. No trace detour is armed
here; the resulting checkpoint needs a separate official recovery and run.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable


_DAY_UNITS = 24
_MAX_DAYS = 3


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _identity(
    snapshot: object,
    *,
    actor: int,
    episode: str,
    paused: bool | None = None,
) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise ValueError("native snapshot is malformed")
    played = snapshot.get("played_character")
    if (
        snapshot.get("map_ready") is not True
        or snapshot.get("episode_character_id") != actor
        or snapshot.get("episode_run_id") != episode
        or not isinstance(played, dict)
        or played.get("character_id") != actor
        or snapshot.get("active_event") is not None
    ):
        raise ValueError("combat preparation crossed actor, episode, map, or event binding")
    if paused is not None and snapshot.get("paused") is not paused:
        raise ValueError("combat preparation has an unexpected pause state")
    _positive_int(snapshot.get("revision"), "revision")
    _positive_int(snapshot.get("native_revision"), "native_revision")
    _positive_int(snapshot.get("date_raw"), "date_raw")
    return snapshot


def _battle(
    driver: object,
    snapshot: dict[str, Any],
    *,
    combat_id: int,
    army_id: int,
) -> dict[str, Any]:
    result = driver.execute_step(  # type: ignore[attr-defined]
        f"query-battle-control-snapshot-v1-{army_id}",
        expected_revision=snapshot["revision"],
    )
    scope = result.get("battle_control_snapshot") if isinstance(result, dict) else None
    if (
        not isinstance(scope, dict)
        or result.get("accepted") is not True
        or result.get("status") != "available"
        or result.get("queried_native_revision") != snapshot["native_revision"]
        or scope.get("battle_control_ready") is not True
        or scope.get("status") != "available"
        or scope.get("combat_id") != combat_id
        or scope.get("subject_public_cunit_id") != army_id
        or scope.get("observed_date_raw") != snapshot["date_raw"]
        or scope.get("winner_raw") != -1
        or scope.get("forced_winner_raw") != -1
        or scope.get("finalized") is not False
    ):
        raise ValueError("fresh same-CombatID undecided battle-control proof is absent")
    for side in ("attacker", "defender"):
        row = scope.get(side)
        fighting = row.get("stored_current_fighting_raw") if isinstance(row, dict) else None
        if (
            not isinstance(row, dict)
            or row.get("stored_current_matches_derived") is not True
            or isinstance(fighting, bool)
            or not isinstance(fighting, int)
            or fighting <= 0
        ):
            raise ValueError(f"{side} fighting scope is unavailable")
    phase = scope.get("phase_raw")
    day = scope.get("phase_day")
    if isinstance(phase, bool) or not isinstance(phase, int) or phase not in (0, 1):
        raise ValueError("combat phase is not maneuver or main")
    if isinstance(day, bool) or not isinstance(day, int) or day < 0:
        raise ValueError("combat phase day is unavailable")
    return {"result": result, "scope": scope}


def _accepted(driver: object, step: str) -> dict[str, Any]:
    result = driver.execute_step(step)  # type: ignore[attr-defined]
    if (
        not isinstance(result, dict)
        or result.get("step") != step
        or result.get("accepted") is not True
        or result.get("status") != "submitted"
    ):
        raise ValueError(f"{step} was not submitted")
    return result


def _next_paused_day(
    driver: object,
    *,
    actor: int,
    episode: str,
    date_raw: int,
    deadline_seconds: float,
) -> dict[str, Any]:
    _accepted(driver, "set-speed-1")
    _accepted(driver, "resume-map")
    deadline = time.monotonic() + deadline_seconds
    running_seen = False
    while time.monotonic() < deadline:
        frame = _identity(driver.take_snapshot(), actor=actor, episode=episode)  # type: ignore[attr-defined]
        current_date = frame["date_raw"]
        if current_date not in (date_raw, date_raw + _DAY_UNITS):
            raise ValueError("single-day preparation overshot or changed date unexpectedly")
        if frame.get("paused") is False:
            running_seen = True
            if current_date == date_raw + _DAY_UNITS:
                break
        elif current_date != date_raw or running_seen:
            raise ValueError("map paused before the declared one-day boundary")
        time.sleep(0.1)
    else:
        raise ValueError("single-day preparation timed out before the date boundary")
    if not running_seen:
        raise ValueError("resume-map never produced a running native frame")
    _accepted(driver, "pause-map")
    pause_deadline = time.monotonic() + min(deadline_seconds, 10.0)
    while time.monotonic() < pause_deadline:
        frame = _identity(driver.take_snapshot(), actor=actor, episode=episode)  # type: ignore[attr-defined]
        if frame["date_raw"] != date_raw + _DAY_UNITS:
            raise ValueError("pause crossed the one-day date bound")
        if frame.get("paused") is True:
            return frame
        time.sleep(0.1)
    raise ValueError("pause-map lacks an independent paused postcondition")


def run_to_main_phase_checkpoint(
    driver: object,
    *,
    official_index: dict[str, Any],
    combat_id: int,
    subject_army_id: int,
    daily_observation_sink: Callable[[dict[str, Any]], None],
    deadline_seconds: float = 30.0,
) -> dict[str, Any]:
    """Advance at most three exact days and save only a proven main frame."""
    _positive_int(combat_id, "combat_id")
    _positive_int(subject_army_id, "subject_army_id")
    if not 0 < deadline_seconds <= 60:
        raise ValueError("bounded deadline must be in (0, 60] seconds")
    if not callable(daily_observation_sink):
        raise ValueError("a persistent daily observation sink is required")
    actor = _positive_int(official_index.get("actor"), "official actor")
    episode = official_index.get("episode")
    if not isinstance(episode, str) or not episode:
        raise ValueError("official episode is absent")
    control = driver.capabilities().get("native_session_control")  # type: ignore[attr-defined]
    if (
        not isinstance(control, dict)
        or control.get("driver_state_restored") is not True
        or control.get("driver_state_restore_kind") != "cold_checkpoint"
        or control.get("driver_state_error") is not None
    ):
        raise ValueError("official cold checkpoint restore is not confirmed")
    current = _identity(driver.take_snapshot(), actor=actor, episode=episode, paused=True)  # type: ignore[attr-defined]
    if current["date_raw"] != official_index.get("date_raw"):
        raise ValueError("cold restored date differs from official pair")
    proof = _battle(driver, current, combat_id=combat_id, army_id=subject_army_id)
    scope = proof["scope"]
    if (scope["phase_raw"], scope["phase_day"]) != (0, 1):
        raise ValueError("this bounded preparation requires maneuver day 1")

    observations: list[dict[str, Any]] = []
    expected = ((0, 2), (0, 3), (1, 0))
    for day_index in range(_MAX_DAYS):
        prior_date = current["date_raw"]
        prior_revision = current["revision"]
        prior_native_revision = current["native_revision"]
        current = _next_paused_day(
            driver,
            actor=actor,
            episode=episode,
            date_raw=prior_date,
            deadline_seconds=deadline_seconds,
        )
        if (
            current["revision"] <= prior_revision
            or current["native_revision"] <= prior_native_revision
        ):
            raise ValueError("one-day boundary lacks a fresh native revision")
        proof = _battle(driver, current, combat_id=combat_id, army_id=subject_army_id)
        scope = proof["scope"]
        observation = {
            "day_index": day_index + 1,
            "starting_date_raw": prior_date,
            "ending_snapshot": current,
            "battle_control": proof["result"],
        }
        daily_observation_sink(observation)
        observations.append(observation)
        if (scope["phase_raw"], scope["phase_day"]) != expected[day_index]:
            raise ValueError("daily combat phase transition differs from exact build")
        if scope["phase_raw"] == 1:
            saved = driver.execute_step(  # type: ignore[attr-defined]
                "save-checkpoint", expected_revision=current["revision"]
            )
            after_save = _identity(driver.take_snapshot(), actor=actor, episode=episode, paused=True)  # type: ignore[attr-defined]
            if after_save["date_raw"] != current["date_raw"]:
                raise ValueError("checkpoint crossed the proven main frame")
            prepared_save = official_index.get("files", {}).get("prepared_save", {})
            save_path = prepared_save.get("path") if isinstance(prepared_save, dict) else None
            if not isinstance(save_path, str) or not save_path:
                raise ValueError("official prepared save path is absent")
            from xar_autoplayer.native_auto_run import _verify_checkpoint_result

            checkpoint = _verify_checkpoint_result(
                saved,
                snapshot=after_save,
                expected_save_dir=Path(save_path).parent,
            )
            return {
                "status": "main_phase_checkpoint_saved",
                "production_trace_ready": False,
                "combat_id": combat_id,
                "subject_army_id": subject_army_id,
                "days_advanced": day_index + 1,
                "date_raw": current["date_raw"],
                "phase_raw": scope["phase_raw"],
                "phase_day": scope["phase_day"],
                "checkpoint": checkpoint,
                "daily_observations": observations,
                "requires_official_new_pid_recovery": True,
            }
    raise ValueError("main phase was not reached in three bounded days")
