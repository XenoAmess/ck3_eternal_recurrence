"""Conditional exact .3 manager dispatch and normal numerical subset.

Manager operands are source inputs, not user authorization. Phase3 by itself
does not select a normal finalizer. Current components already include the
relevant loss carry; this adapter never applies losses or native effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping, Set

from .battle_current_adapter import CurrentBattleCondition
from .battle_current_backing_reaggregation import (
    CurrentPhase3BackingState, reaggregate_current_phase3_backing,
)
from .battle_current_terminal import project_current_terminal_accounting
from .combat_core import FIXED_SCALE


@dataclass(frozen=True, slots=True)
class CurrentNormalFinalizerManagerInputs:
    """Explicit manager row context; None is an unresolved reached operand.

    ``combat_manager_row_admitted`` records the native lookup/fallback tag and
    ID checks. Primary hostility includes the native Character fallback; it
    does not require an invented strict-primary-success guard. ``daily_row``
    is the post-phase-work context where 2AD8148 has cleared processing+705.
    ``result_present`` is metadata only and never admission.
    """

    entry_kind: Literal["daily_row", "suppression_sweep"]
    combat_manager_row_admitted: bool | None
    pending_suppression_sweep: bool | None = None
    primary_hostile: bool | None = None
    finalized: bool | None = None
    processing: bool | None = None
    result_present: bool | None = None
    source_context: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CurrentNormalFinalizerGap:
    stage: str
    missing_input: str
    native_entry: str


def _signed(value: int, bits: int) -> int:
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def _whole_result_field(raw: int | None) -> int | None:
    if raw is None:
        return None
    whole = abs(raw) // FIXED_SCALE
    return _signed(-whole if raw < 0 else whole, 32)


def _dispatch(condition, manager):
    dispatch = {
        "status": "available", "branch": "no_invocation",
        "normal_result_intent": False, "suppression_argument": None,
        "finalizer_invoked_conditionally": False, "removal_intent": False,
        "manager_pending_after": None,
        "processing_for_selected_row": (
            False if manager.entry_kind == "daily_row" else manager.processing),
    }
    gaps = []

    def unresolved(name, entry):
        gaps.append(CurrentNormalFinalizerGap("manager_dispatch", name, entry))
        dispatch.update(status="partial", branch="unknown_reached_operand",
                        normal_result_intent=None,
                        finalizer_invoked_conditionally=None,
                        removal_intent=None)

    if manager.entry_kind not in ("daily_row", "suppression_sweep"):
        raise ValueError("entry_kind requires daily_row or suppression_sweep")
    if manager.combat_manager_row_admitted is None:
        unresolved("combat_manager_row_admitted", "2AD8000 / 2AD8880")
        return dispatch, gaps
    if manager.combat_manager_row_admitted is False:
        dispatch["branch"] = "manager_row_not_admitted"
        return dispatch, gaps
    if manager.entry_kind == "daily_row":
        if manager.pending_suppression_sweep is None:
            unresolved("pending_suppression_sweep", "2AD814F / manager+60")
            return dispatch, gaps
        if manager.pending_suppression_sweep is False:
            if condition.phase_raw == 3:
                dispatch.update(branch="normal", normal_result_intent=True,
                                suppression_argument=False,
                                finalizer_invoked_conditionally=True,
                                removal_intent=True)
            else:
                dispatch["branch"] = "phase_not_done"
            return dispatch, gaps
    # The pending sweep takes precedence and never resumes the daily normal
    # branch. Only reached operands matter; later None values are not gaps.
    if manager.primary_hostile is None:
        unresolved("primary_hostile", "2AD8992 / 2C09640 false-mode")
    elif manager.primary_hostile is True:
        dispatch["branch"] = "hostile_sweep_skip"
    elif manager.finalized is None:
        unresolved("finalized", "2AD899B / Combat+704")
    elif manager.finalized is True:
        dispatch["branch"] = "already_finalized_sweep_skip"
    elif dispatch["processing_for_selected_row"] is None:
        unresolved("processing", "2AD89A4 / Combat+705")
    elif dispatch["processing_for_selected_row"] is True:
        dispatch.update(branch="deferred", manager_pending_after=True)
    else:
        dispatch.update(branch="suppressed", suppression_argument=True,
                        finalizer_invoked_conditionally=True,
                        removal_intent=True)
    return dispatch, gaps


def _normal_numeric(condition, backing, side_baselines, winner, wipe):
    account = project_current_terminal_accounting(
        condition, stop_reason="caller_conditional_normal_finalizer",
        winner_side=winner, normal_result_intent=True, wipe_raw=wipe,
        backing_current_by_side=backing["backing_current_by_side"],
        side_baseline_raw_by_side=side_baselines,
    )
    by_side = {row["side_index"]: row for row in backing.get("sides", ())}
    for row in account["sides"]:
        # Native raw accounts are signed64, whereas result-row whole fields
        # independently truncate toward zero and retain their signed32 bits.
        levy = _signed(row["levy_soft_raw_q100000"], 64)
        maa = _signed(row["men_at_arms_soft_raw_q100000"], 64)
        baseline = row["baseline_raw_q100000"]
        hard = (None if baseline is None else max(_signed(
            baseline - row["stored_current_fighting_raw_q100000"] - levy - maa,
            64), 0))
        row.update(levy_soft_raw_q100000=levy,
                   men_at_arms_soft_raw_q100000=maa,
                   hard_loss_raw_q100000=hard,
                   result_row_baseline_whole_signed32=_whole_result_field(baseline),
                   result_row_hard_whole_signed32=_whole_result_field(hard))
        source = by_side.get(row["side_index"])
        whole = None
        if source is not None and source["current_soldiers"] is not None:
            whole = 0
            for army in source["ordered_armies"]:
                army_whole = 0
                for regiment in army["ordered_regiments"]:
                    army_whole = _signed(army_whole + regiment["current_soldiers"], 32)
                whole = _signed(whole + army_whole, 32)
        raw = None if whole is None else whole * FIXED_SCALE
        row.update(backing_current_whole_signed32=whole,
                   backing_current_raw_q100000=raw,
                   final_survivors_raw_q100000=raw,
                   final_survivors_source=(None if raw is None else
                       "complete_actual_army_backing_native_signed32_accumulation"))
    account.update(backing_accumulation_bits=32,
                   raw_account_arithmetic_bits=64,
                   result_row_whole_conversion="truncate_toward_zero_then_signed32",
                   actual_native_effects_executed=False,
                   participant_hard_ledger_debited=False,
                   current_components_debited=False)
    return account


def project_current_normal_finalizer(
    condition: CurrentBattleCondition, *,
    manager: CurrentNormalFinalizerManagerInputs,
    current_state_by_regiment: Mapping[
        tuple[int, int], CurrentPhase3BackingState
    ] | None = None,
    backing_inputs_v1: Mapping[str, object] | None = None,
    recomputed_regiments: Set[tuple[int, int]] | None = None,
    captured_maximum_by_regiment: Mapping[tuple[int, int], int] | None = None,
    side_baseline_raw_by_side: Mapping[int, int | None] | None = None,
    winner_raw: Literal[-1, 0, 1] | None = None,
    wipe_raw: bool | None = None,
) -> dict[str, object]:
    """Compose covered manager intent and normal numerics without mutations.

    The count helper receives already-current components once, plus genuine
    complete census membership. Unaffected receiver counts are retained. A
    suppressed, deferred, skipped or unresolved invocation produces no normal
    numerical output; None does not mean zero. Supported-subset availability
    is separate from the still-partial complete native effects model.
    """
    if winner_raw not in (None, -1, 0, 1):
        raise ValueError("winner_raw requires -1, 0, 1 or unavailable None")
    dispatch, gaps = _dispatch(condition, manager)
    winner = winner_raw if winner_raw in (0, 1) else None
    output = {
        "scope_kind": "caller_conditional_manager_and_normal_numeric_subset",
        "status": dispatch["status"], "dispatch": dispatch,
        "source_context": dict(manager.source_context),
        "observed_frame": {
            "snapshot_revision": condition.snapshot_revision,
            "observed_date_raw": condition.observed_date_raw,
            "combat_id": condition.combat_id, "province_id": condition.province_id,
            "phase_raw": condition.phase_raw, "phase_day": condition.phase_day,
        },
        "winner_raw": winner_raw, "winner_side": winner,
        "loser_side": 1 - winner if winner is not None else None,
        "wipe_raw": wipe_raw, "result_present_input": manager.result_present,
        "backing_reaggregation": None, "normal_numeric_accounting": None,
        "losing_side_hard_raw_q100000": None,
        "war_battle_row_projection": {
            "status": "not_produced" if dispatch["normal_result_intent"] is False
                      else "partial",
            "row_created_conditionally": (
                False if dispatch["normal_result_intent"] is False or winner_raw == -1
                else None),
            "attacker_relative_delta_raw_q100000": None,
        },
        "unmodeled_effect_branches": (
            CurrentNormalFinalizerGap("normal_summary", "financial/prestige/piety and script envelope effects", "258BF70"),
            CurrentNormalFinalizerGap("war_row", "strict relation War/guard, memberships, mode2 buckets, actual CB scale and live cap", "249A940 / 2868690"),
            CurrentNormalFinalizerGap("person_and_retreat", "named person and retreat writeback outcomes", "separate native producers"),
            CurrentNormalFinalizerGap("war_settlement", "independent peace, truce, titles and current WarID observations", "separate war/interaction producers"),
            CurrentNormalFinalizerGap("result_lifetime", "genuine Result and relevant player count", "258DAEB..258DB24"),
        ),
        "complete_native_finalizer": False,
        "actual_native_effects_executed": False,
        "old_combat_removed_observed": False,
        "war_settlement_observed": False,
        "named_character_outcomes_predicted": False,
        "prior_losses_reapplied": False,
        "owner_hard_ledger_debited": False,
        "actual_game_days_advanced": 0,
        "complete_monte_carlo": False,
        "win_probability_ready": False,
    }
    if dispatch["normal_result_intent"] is True:
        backing = reaggregate_current_phase3_backing(
            condition, current_state_by_regiment=current_state_by_regiment or {},
            backing_inputs_v1=backing_inputs_v1,
            recomputed_regiments=recomputed_regiments,
            captured_maximum_by_regiment=captured_maximum_by_regiment,
        )
        account = _normal_numeric(condition, backing, side_baseline_raw_by_side,
                                  winner, wipe_raw)
        output.update(backing_reaggregation=backing,
                      normal_numeric_accounting=account)
        for missing in backing.get("unavailable_inputs", ()):
            gaps.append(CurrentNormalFinalizerGap("backing_count", missing, "2633340"))
        for row in backing.get("sides", ()):
            for missing in row["unavailable_inputs"]:
                gaps.append(CurrentNormalFinalizerGap(
                    f"side{row['side_index']}_backing_count", missing, "2633340"))
        for row in account["sides"]:
            for missing in row["unavailable_inputs"]:
                gaps.append(CurrentNormalFinalizerGap(
                    f"side{row['side_index']}_normal_numeric", missing,
                    "2652B50 / 2667E90"))
        if winner is not None:
            output["losing_side_hard_raw_q100000"] = account["sides"][1 - winner]["hard_loss_raw_q100000"]
        if winner_raw == -1:
            output["war_battle_row_projection"]["status"] = "not_produced"
    output["typed_gaps"] = tuple(gaps)
    if gaps:
        output["status"] = "partial"
    return output
