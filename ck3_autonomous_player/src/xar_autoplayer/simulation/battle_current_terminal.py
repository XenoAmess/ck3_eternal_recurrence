"""Current .3 terminal accounting, separate from hero outcomes and fighting Q."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .battle_current_adapter import CurrentBattleCondition
from .combat_core import FIXED_SCALE, RegimentKind


@dataclass(frozen=True, slots=True)
class TerminalBackingRegiment:
    """One genuine Army backing Regiment's integer current count."""

    native_carmy_id: int
    regiment_id: int
    current_soldiers: int


def project_current_terminal_accounting(
    condition: CurrentBattleCondition,
    *,
    stop_reason: str,
    winner_side: int | None,
    normal_result_intent: bool | None = None,
    wipe_raw: bool | None = None,
    backing_current_by_side: Mapping[
        int, tuple[TerminalBackingRegiment, ...] | None
    ] | None = None,
    side_baseline_raw_by_side: Mapping[int, int | None] | None = None,
) -> dict[str, object]:
    """Project known terminal inputs without inventing final survivor counts.

    Native 2652B50 uses Side+A8 baseline, cached Side+98 current and both soft
    buckets. Native 2667E90 separately sums actual Army backing Regiment+38
    integer current soldiers. ``backing_current_by_side`` is that complete,
    native-ordered caller-supplied list; a missing side is unavailable and a
    supplied empty complete list is genuine zero. Entry starting sums and
    fractional cached fighting current do not replace either source.
    """
    rows: list[dict[str, object]] = []
    for index, side in enumerate(condition.sides):
        source_side = condition.source_snapshot.get(side.role)
        baseline = (source_side.get("stored_terminal_loss_baseline_raw")
                    if isinstance(source_side, Mapping) else None)
        baseline_source = (
            f"source_snapshot.{side.role}.stored_terminal_loss_baseline_raw"
            if baseline is not None else None
        )
        if baseline is None and side_baseline_raw_by_side is not None:
            baseline = side_baseline_raw_by_side.get(index)
            if baseline is not None:
                baseline_source = "caller_observed_native_side_A8"
        levy_soft = sum(entry.state.soft_casualties_raw for entry in side.entries
                        if entry.state.kind is RegimentKind.LEVY)
        maa_soft = sum(entry.state.soft_casualties_raw for entry in side.entries
                       if entry.state.kind is RegimentKind.MEN_AT_ARMS)
        hard = (None if baseline is None else
                max(baseline - side.stored_current_fighting_raw - levy_soft - maa_soft, 0))
        backing = (backing_current_by_side.get(index)
                   if backing_current_by_side is not None else None)
        backing_current = (None if backing is None else
                           sum(regiment.current_soldiers for regiment in backing) * FIXED_SCALE)
        final_survivors = backing_current if normal_result_intent is True else None
        missing = []
        if baseline is None:
            missing.append("native Side+A8 baseline / stored_terminal_loss_baseline_raw")
        if backing is None:
            missing.append("complete actual Army backing Regiment+38 integer current counts / native 2667E90 output+18")
        if normal_result_intent is None:
            missing.append("normal-result intent: current accounting alone does not establish normal finalization")
        rows.append({
            "side_index": index, "role": side.role,
            "primary_participant_character_id": side.primary_participant_character_id,
            "ordered_armies": [dict(army) for army in side.ordered_armies],
            "baseline_raw_q100000": baseline,
            "baseline_source": baseline_source,
            "stored_current_fighting_raw_q100000": side.stored_current_fighting_raw,
            "levy_soft_raw_q100000": levy_soft,
            "men_at_arms_soft_raw_q100000": maa_soft,
            "hard_loss_raw_q100000": hard,
            "participant_hard_ledger": [dict(row) for row in side.participant_hard_ledger],
            "participant_hard_total_raw_q100000": side.participant_hard_total_raw,
            "final_survivors_raw_q100000": final_survivors,
            "backing_current_raw_q100000": backing_current,
            "final_survivors_source": (None if final_survivors is None else
                                       "complete_actual_army_backing_regiment_integer_current"),
            "backing_regiments": (None if backing is None else [
                {"native_carmy_id": regiment.native_carmy_id,
                 "regiment_id": regiment.regiment_id,
                 "current_soldiers": regiment.current_soldiers}
                for regiment in backing
            ]),
            "unavailable_inputs": missing,
        })
    return {
        "scope_kind": "deterministic_current_terminal_accounting",
        "observed_frame": {"snapshot_revision": condition.snapshot_revision,
                           "observed_date_raw": condition.observed_date_raw,
                           "combat_id": condition.combat_id,
                           "province_id": condition.province_id,
                           "subject_side_index": condition.subject_side_index,
                           "phase": condition.phase, "phase_day": condition.phase_day},
        "stop_reason": stop_reason,
        "normal_result_intent": normal_result_intent,
        "wipe_raw": wipe_raw,
        "winner_side": winner_side,
        "loser_side": 1 - winner_side if winner_side in (0, 1) else None,
        "scale": FIXED_SCALE,
        "sides": rows,
        "hard_summary_is_participant_ledger_or_named_deaths": False,
        "final_survivors_are_cached_fighting_current": False,
        "complete_monte_carlo": False,
        "ai_retreat_decision_predicted": False,
        "named_character_outcomes_predicted": False,
    }
