"""Bounded .3 current pursuit transfer with frozen observed operands."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

from .battle_current_adapter import CurrentBattleCondition, CurrentBattleSide
from .combat_core import (
    FIXED_SCALE, PursuitInitialPools, apply_pursuit_day, fixed_mul,
)


@dataclass(frozen=True, slots=True)
class CurrentPursuitSourceContext:
    """Explicit observed supplements for an older absent/null rule block."""

    winner_side: int | None = None
    initial_pools: PursuitInitialPools | None = None
    pursuit_phase_days: int | None = None
    pursuit_stat_multiplier_raw: int | None = None
    base_toughness_multiplier_raw: int | None = None
    minimum_pursuit_multiplier_raw: int | None = None
    skip_pursuit: bool | None = None
    source_context: Mapping[str, object] | None = None


def _source_inputs(condition, explicit):
    block = condition.source_snapshot.get("current_pursuit_inputs_v1")
    block = block if isinstance(block, Mapping) else {}
    values = {}
    sources = {}
    for name in ("pursuit_phase_days", "pursuit_stat_multiplier_raw",
                 "base_toughness_multiplier_raw", "minimum_pursuit_multiplier_raw"):
        value = block.get(name)
        sources[name] = "current_pursuit_inputs_v1" if value is not None else "explicit_context"
        values[name] = value if value is not None else getattr(explicit, name)
    losing_side = block.get("losing_side_index")
    if losing_side in (0, 1):
        winner = 1 - losing_side
        sources["winner_side"] = "current_pursuit_inputs_v1.losing_side_index"
    elif explicit.winner_side is not None:
        winner = explicit.winner_side
        sources["winner_side"] = "explicit_context"
    else:
        winner = condition.source_snapshot.get("winner_raw")
        sources["winner_side"] = "source_snapshot.winner_raw"
    levy = block.get("initial_loser_levy_soft_raw")
    maa = block.get("initial_loser_maa_soft_raw")
    if losing_side in (0, 1) and levy is not None and maa is not None:
        pools = PursuitInitialPools(levy, maa)
        sources["initial_pools"] = "current_pursuit_inputs_v1"
    else:
        pools = explicit.initial_pools
        sources["initial_pools"] = "explicit_context"
    skip = block.get("losing_side_skip_pursuit")
    if skip is not None:
        sources["skip_pursuit"] = "current_pursuit_inputs_v1.losing_side_skip_pursuit"
    elif explicit.skip_pursuit is not None:
        skip = explicit.skip_pursuit
        sources["skip_pursuit"] = "explicit_context"
    elif winner in (0, 1) and condition.subject_side_index == 1 - winner:
        flags = condition.source_snapshot.get("side_flags")
        skip = flags.get("skip_pursuit") if isinstance(flags, Mapping) else None
        sources["skip_pursuit"] = "source_snapshot.side_flags.skip_pursuit (subject is loser)"
    else:
        sources["skip_pursuit"] = "unavailable_actual_loser_flag"
    return CurrentPursuitSourceContext(winner_side=winner, initial_pools=pools,
                                      skip_pursuit=skip, source_context=explicit.source_context,
                                      **values), sources


def _apply_result(side: CurrentBattleSide, day):
    updated_entries = []
    rows = []
    owner_deltas: dict[int, int] = {}
    for entry, after, (_, hard) in zip(side.entries, day.entries,
                                       day.hard_by_regiment_raw, strict=True):
        known_backing = entry.backing_components is not None
        backing_after = after.components if known_backing else None
        updated_entries.append(replace(
            entry, state=after, backing_components=backing_after,
            hard_casualties_raw=(None if entry.hard_casualties_raw is None else
                                 entry.hard_casualties_raw + hard),
        ))
        owner_deltas[entry.owner_character_id] = owner_deltas.get(entry.owner_character_id, 0) + hard
        rows.append({
            "bucket": entry.bucket, "bucket_index": entry.bucket_index,
            "regiment_id": entry.state.regiment_id,
            "native_carmy_id": entry.native_carmy_id,
            "public_cunit_id": entry.public_cunit_id,
            "owner_character_id": entry.owner_character_id,
            "current_fighting_raw_before": entry.state.current_raw,
            "current_fighting_raw_after": after.current_raw,
            "soft_casualties_raw_before": entry.state.soft_casualties_raw,
            "soft_casualties_raw_after": after.soft_casualties_raw,
            "new_hard_casualties_raw": hard,
            "backing_components": (None if not known_backing else [
                {"component_index": index, "kind": before.kind,
                 "maximum_soldiers": before.maximum_soldiers,
                 "current_soldiers_before": before.current_soldiers,
                 "current_soldiers_after": current.current_soldiers}
                for index, (before, current) in enumerate(
                    zip(entry.backing_components, after.components, strict=True))
            ]),
        })
    remaining = dict(owner_deltas)
    ledger = []
    for observed in side.participant_hard_ledger:
        row = dict(observed)
        amount = remaining.pop(row["participant_character_id"], 0)
        row["hard_casualties_raw"] += amount
        ledger.append(row)
    updated = replace(
        side, entries=tuple(updated_entries), participant_hard_ledger=tuple(ledger),
        participant_hard_total_raw=side.participant_hard_total_raw + day.total_hard_raw,
        derived_soft_casualties_raw=sum(entry.state.soft_casualties_raw for entry in updated_entries),
        derived_main_fighting_entry_hard_casualties_raw=(
            side.derived_main_fighting_entry_hard_casualties_raw +
            sum(row["new_hard_casualties_raw"] for entry, row in zip(side.entries, rows, strict=True)
                if entry.fights_in_main_phase)),
        non_main_start_minus_current_minus_soft_raw=(
            side.non_main_start_minus_current_minus_soft_raw +
            sum(row["new_hard_casualties_raw"] for entry, row in zip(side.entries, rows, strict=True)
                if not entry.fights_in_main_phase)),
    )
    return updated, rows, owner_deltas, remaining


def run_current_pursuit_ticks(
    condition: CurrentBattleCondition,
    *,
    inputs: CurrentPursuitSourceContext | None = None,
    max_ticks: int = 1,
    dispatched_phase_days: tuple[int, ...] | None = None,
) -> dict[str, object]:
    """Run bounded manager invocations, including the separate zero-loss finish.

    Exact .3 manager increments phase_day before 258CA60. The tick applies at
    d<=runtimeDays and finishes only at d>runtimeDays, or actual loser skip.
    Explicit dispatched days instead expose that tick primitive without an
    extra increment. Caller-supplied pools are frozen initial pools, never a
    reconstruction from a current declining soft pool.

    The .3 tree closes the old core's particular pursuit arithmetic. It does
    not certify the whole 1.19 kernel, overflow parity, loaded event feedback,
    outer calendar admission, AI retreat or complete Monte Carlo.
    """
    context, sources = _source_inputs(condition, inputs or CurrentPursuitSourceContext())
    output = {
        "scope_kind": "frozen_current_pursuit_transfer",
        "observed_frame": {"snapshot_revision": condition.snapshot_revision,
                           "observed_date_raw": condition.observed_date_raw,
                           "combat_id": condition.combat_id, "province_id": condition.province_id,
                           "phase_raw": condition.phase_raw, "phase_day": condition.phase_day},
        "input_sources": sources, "explicit_source_context": context.source_context,
        "status": "available", "ticks": [], "new_hard_casualties_raw": 0,
        "phase_raw_after": condition.phase_raw, "phase_day_after": condition.phase_day,
        "stop_reason": "tick_budget_exhausted", "normal_result_intent": None,
        "normal_result_intent_conditions": ["normal manager branch with no overriding invalidation sweep"],
        "updated_condition": condition, "complete_monte_carlo": False,
        "ai_retreat_decision_predicted": False, "actual_game_days_advanced": 0,
    }
    if condition.phase_raw != 2:
        output.update(status="not_applicable", stop_reason="observed_phase_is_not_pursuit")
        return output
    if context.winner_side is None:
        output.update(status="partial", stop_reason="recorded_winner_unobserved",
                      new_hard_casualties_raw=None, updated_condition=None)
        return output
    current = condition
    winner = context.winner_side
    output["winner_side"] = winner
    output["loser_side"] = 1 - winner if winner in (0, 1) else None
    for invocation in range(max_ticks):
        if dispatched_phase_days is not None and invocation >= len(dispatched_phase_days):
            output["stop_reason"] = "supplied_dispatch_schedule_exhausted"
            break
        presented = (current.phase_day + 1 if dispatched_phase_days is None else
                     dispatched_phase_days[invocation])
        tick = {"phase_day_before": current.phase_day,
                "dispatched_phase_day": presented,
                "new_hard_casualties_raw": 0, "entries": [], "domains": []}
        current = replace(current, phase_day=presented)
        if winner not in (0, 1):
            tick["branch"] = "native_winner_without_pursuit_application"
        else:
            loser = 1 - winner
            if context.skip_pursuit is None or (
                context.skip_pursuit is not True and context.pursuit_phase_days is None
            ):
                output.update(status="partial", stop_reason="loser_skip_or_runtime_days_unobserved",
                              new_hard_casualties_raw=None, updated_condition=None)
                return output
            if context.skip_pursuit or presented > context.pursuit_phase_days:
                tick["branch"] = "pursuit_finished"
                tick["finish_reason"] = "loser_skip_pursuit" if context.skip_pursuit else "phase_day_exceeds_runtime_days"
                current = replace(current, phase="done", phase_raw=3, phase_day=0)
                output.update(stop_reason="normal_result", normal_result_intent=True)
            else:
                retreater = current.sides[loser]
                toughness = sum(fixed_mul(entry.state.toughness_raw, entry.state.soft_casualties_raw)
                                for entry in retreater.entries)
                if toughness <= 0:
                    tick.update(branch="no_soft_toughness", toughness_soft_raw=toughness)
                else:
                    missing = [name for name in ("initial_pools", "pursuit_stat_multiplier_raw",
                               "base_toughness_multiplier_raw", "minimum_pursuit_multiplier_raw")
                               if getattr(context, name) is None]
                    modifiers = current.pursuit_modifier_sides
                    if not isinstance(modifiers, Mapping) or modifiers.get("status") != "available":
                        missing.append("pursuit_modifier_sides")
                    if current.loss_inputs is None:
                        missing.append("current_loss_inputs_v1.runtime_pursuit_hard_conversion_raw")
                    if missing:
                        output.update(status="partial", stop_reason="pursuit_operands_unobserved",
                                      unavailable_inputs=missing, new_hard_casualties_raw=None,
                                      updated_condition=None)
                        return output
                    modifier_rows = modifiers["sides"]
                    day = apply_pursuit_day(
                        retreater.states, current.sides[winner].states,
                        initial_pools=context.initial_pools,
                        pursuer_efficiency_modifier_raw=modifier_rows[winner]["pursuit_efficiency_raw"],
                        retreater_loss_modifier_raw=modifier_rows[loser]["retreat_losses_raw"],
                        pursuit_phase_days=context.pursuit_phase_days,
                        pursuit_conversion_raw=current.loss_inputs.runtime_pursuit_hard_conversion_raw,
                        pursuit_stat_multiplier_raw=context.pursuit_stat_multiplier_raw,
                        base_toughness_multiplier_raw=context.base_toughness_multiplier_raw,
                        minimum_pursuit_multiplier_raw=context.minimum_pursuit_multiplier_raw,
                    )
                    updated, entry_rows, owner_deltas, unmatched = _apply_result(retreater, day)
                    sides = list(current.sides)
                    sides[loser] = updated
                    current = replace(current, sides=tuple(sides))
                    tick.update(
                        branch="pursuit_casualties", new_hard_casualties_raw=day.total_hard_raw,
                        entries=entry_rows, toughness_soft_raw=day.toughness_soft_raw,
                        pursuit_damage_raw=day.pursuit_damage_raw, screen_raw=day.screen_raw,
                        base_raw=day.base_raw, minimum_raw=day.minimum_raw,
                        extra_raw=day.extra_raw, floor_component_raw=day.floor_component_raw,
                        domains=[{"kind": domain.kind.value, "current_soft_raw": domain.current_soft_raw,
                                  "extra_daily_raw": domain.extra_daily_raw, "floor_daily_raw": domain.floor_daily_raw,
                                  "hard_raw": domain.hard_raw, "allocation_remainder_raw": domain.allocation_remainder_raw}
                                 for domain in day.domains],
                        participant_hard_ledger=[dict(row) for row in updated.participant_hard_ledger],
                        owner_hard_ledger_deltas=[{"owner_character_id": owner, "hard_casualties_raw_delta": amount}
                                                 for owner, amount in owner_deltas.items()],
                        unmatched_owner_hard_deltas=[{"owner_character_id": owner, "hard_casualties_raw_delta": amount}
                                                     for owner, amount in unmatched.items()],
                        ledger_is_an_additional_fighting_deduction=False,
                    )
        tick["phase_raw_after"] = current.phase_raw
        tick["phase_day_after"] = current.phase_day
        output["ticks"].append(tick)
        output["new_hard_casualties_raw"] += tick["new_hard_casualties_raw"]
        output.update(phase_raw_after=current.phase_raw, phase_day_after=current.phase_day,
                      updated_condition=current)
        if current.phase_raw == 3:
            break
    return output
