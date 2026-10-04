"""Pure .3 calendar/manager scheduling projection, with explicit admission.

This models native date-stage execution, not wall-time queue admission or
observed snapshots. It provides dispatch_date_raw to existing battle kernels.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DailyDateStageInput:
    date_raw_before: int
    date_stage_executed: bool | None
    admission_source: str
    endpoint_paused: bool | None = None
    combat_resolves_in_manager: bool | None = True


@dataclass(frozen=True)
class CombatScheduleInput:
    """Current phase plus forced/strength operands at native pre-roll check.

    Stored currents must be the post26505E0 values; cadence is the value
    tested after side events. This module does not perform those refreshes.
    """
    combat_id: int
    phase_raw: int
    phase_day: int
    roll_cadence_counter: int
    forced_winner_raw: int | None = -1
    stored_side0_current_raw: int | None = None
    stored_side1_current_raw: int | None = None


@dataclass(frozen=True)
class LoadedScheduleInputs:
    maneuver_days: int | None
    roll_cadence_interval: int | None
    source: str


def _signed_remainder(value: int, divisor: int) -> int:
    quotient = abs(value) // abs(divisor)
    if (value < 0) != (divisor < 0):
        quotient = -quotient
    return value - quotient * divisor


def project_daily_battle_schedule(
    day: DailyDateStageInput,
    combat: CombatScheduleInput,
    loaded: LoadedScheduleInputs,
) -> dict[str, Any]:
    """Project one admitted date stage, retaining typed unresolved operands.

    A caller's true admission is conditional input, not a fresh live claim.
    endpoint_paused is evidence metadata only: it cannot cancel a dispatch.
    """
    out: dict[str, Any] = {
        "scope_kind": "conditional_exact_12003_daily_date_stage_schedule",
        "input": {"day": asdict(day), "combat": asdict(combat), "loaded": asdict(loaded)},
        "status": "available", "typed_gaps": [],
        "date_raw_after": day.date_raw_before,
        "calendar_raw_hours": 0, "calendar_days": 0,
        "combat_manager_invocations": 0, "accepted_combat_invocations": 0,
        "dispatch_date_raw": None, "dispatch_phase_day": None,
        "phase_raw_after": combat.phase_raw, "phase_day_after": combat.phase_day,
        "main_called": False, "main_continues": False,
        "phase_raw_at_phase_work": None, "phase_day_at_phase_work": None,
        "event_side_order": [], "roll_helpers_called": False,
        "native_rng_draws": None,
        "roll_cadence_counter_after": combat.roll_cadence_counter,
        "delegated_kernel": None,
        "source_snapshot_replaced": False,
    }
    if day.date_stage_executed is None:
        out.update(status="partial", date_raw_after=None,
                   calendar_raw_hours=None, calendar_days=None,
                   combat_manager_invocations=None, accepted_combat_invocations=None,
                   phase_raw_after=None, phase_day_after=None,
                   main_called=None, main_continues=None, roll_helpers_called=None,
                   roll_cadence_counter_after=None)
        out["typed_gaps"].append({"kind": "native_daily_date_stage_admission_unresolved",
                                  "entry": "creator25A9C50 / queueconsumer / generic29676A0"})
        return out
    if not day.date_stage_executed:
        out["branch"] = "date_stage_not_executed"
        return out
    out.update(date_raw_after=day.date_raw_before + 24, calendar_raw_hours=24,
               calendar_days=1, combat_manager_invocations=1,
               dispatch_date_raw=day.date_raw_before + 24)
    if day.combat_resolves_in_manager is None:
        out.update(status="partial", accepted_combat_invocations=None,
                   phase_raw_after=None, phase_day_after=None,
                   main_called=None, main_continues=None, roll_helpers_called=None,
                   roll_cadence_counter_after=None)
        out["typed_gaps"].append({"kind": "combat_full_id_membership_or_resolution_unresolved",
                                  "entry": "manager2AD8000 +20/+2C full ID traversal"})
        return out
    if not day.combat_resolves_in_manager:
        out["branch"] = "combat_not_resolved_in_manager"
        return out
    dispatched_day = combat.phase_day + 1
    out.update(accepted_combat_invocations=1, dispatch_phase_day=dispatched_day,
               phase_day_after=dispatched_day, phase_raw_at_phase_work=combat.phase_raw,
               phase_day_at_phase_work=dispatched_day)
    if combat.phase_raw == 0:
        if combat.forced_winner_raw is None:
            out.update(status="partial", phase_raw_after=None,
                       phase_day_after=None, main_called=None)
            out["typed_gaps"].append({"kind": "maneuver_forced_winner_unresolved", "entry": "Combat+700"})
        elif combat.forced_winner_raw != -1:
            out.update(branch="forced_maneuver_main_exit", phase_raw_after=None,
                       phase_day_after=None, main_called=True,
                       phase_raw_at_phase_work=1, phase_day_at_phase_work=0,
                       delegated_kernel="existing_main_phase_transition_forced_exit")
        elif loaded.maneuver_days is None:
            out["status"] = "partial"
            out["typed_gaps"].append({"kind": "loaded_maneuver_days_unavailable", "entry": "5C69BB0"})
            out.update(phase_raw_after=None, phase_day_after=None)
        elif dispatched_day > loaded.maneuver_days:
            out.update(branch="maneuver_crosses_threshold_no_main_call", phase_raw_after=1, phase_day_after=0)
        else:
            out["branch"] = "maneuver_remains"
        return out
    if combat.phase_raw == 2:
        out.update(branch="pursuit_dispatch", phase_raw_after=None,
                   phase_day_after=None, delegated_kernel="existing_pursuit258CA60")
        return out
    if combat.phase_raw != 1:
        out.update(status="partial", phase_raw_after=None, phase_day_after=None)
        out["typed_gaps"].append({"kind": "phase_dispatch_not_projected", "entry": "manager2AD8000"})
        return out
    out["main_called"] = True
    known_exit = (combat.forced_winner_raw is not None and combat.forced_winner_raw != -1) or any(
        value is not None and value <= 0
        for value in (combat.stored_side0_current_raw, combat.stored_side1_current_raw))
    if known_exit:
        out.update(branch="main_pre_roll_exit", phase_raw_after=None, phase_day_after=None,
                   delegated_kernel="existing_main_phase_transition")
        return out
    if any(value is None for value in (combat.forced_winner_raw,
                                      combat.stored_side0_current_raw,
                                      combat.stored_side1_current_raw)):
        out.update(status="partial", main_continues=None, roll_helpers_called=None,
                   roll_cadence_counter_after=None)
        out["typed_gaps"].append({"kind": "main_exit_operands_unavailable",
                                  "entry": "Combat+700 / side stored current+B8,+400"})
        return out
    out.update(branch="main_continues", main_continues=True,
               event_side_order=[0, 1], roll_helpers_called=combat.roll_cadence_counter == 0,
               delegated_kernel="existing_P1_refresh_phase_event_and_loss_kernels")
    if loaded.roll_cadence_interval is None:
        out.update(status="partial", roll_cadence_counter_after=None)
        out["typed_gaps"].append({"kind": "loaded_roll_cadence_interval_unavailable", "entry": "5C69B48"})
    elif loaded.roll_cadence_interval == 0:
        out.update(status="partial", roll_cadence_counter_after=None)
        out["typed_gaps"].append({"kind": "native_zero_divisor_undefined_projection", "entry": "5C69B48"})
    else:
        out["roll_cadence_counter_after"] = _signed_remainder(
            combat.roll_cadence_counter + 1, loaded.roll_cadence_interval)
    return out
