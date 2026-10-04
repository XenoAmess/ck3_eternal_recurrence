"""Replace a caller-carried battle condition with a fresh observed frame.

This is an observed refresh boundary, not a native future-day simulation. It
does not run native refresh getters, infer event effects, advance the calendar,
or apply earlier predicted losses to the fresh quantities. Constructor-context
advantage details remain a separate diagnostic from stored actual advantage.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Mapping

from .active_counter_current_basis import project_current_counter_attack_raw
from .battle_current_adapter import (
    CurrentBattleCondition,
    CurrentBattleEntry,
    CurrentBattleSide,
    adapt_current_battle_condition,
)
from .battle_current_next_day import CarriedBattleCondition, NextMainTickContext, prepare_next_main_tick
from .combat_core import BackingComponent, DrawState


@dataclass(frozen=True, slots=True)
class DynamicRefreshContext:
    context: NextMainTickContext
    ledger: Mapping[str, Any]
    component_ledger: tuple[Mapping[str, Any], ...]
    scope_kind: str = "fresh_observed_current_condition_refresh"
    complete_transition: bool = False
    complete_monte_carlo: bool = False
    actual_next_draw_claimed: bool = False

    @property
    def condition(self) -> CurrentBattleCondition:
        return self.context.condition

    @property
    def draw_state(self) -> DrawState:
        return self.context.draw_state

    @property
    def missing_inputs(self) -> tuple[str, ...]:
        return tuple(self.ledger["missing_inputs"])


def _frame(condition: CurrentBattleCondition) -> dict[str, Any]:
    return {key: getattr(condition, key) for key in (
        "snapshot_revision", "observed_date_raw", "combat_id", "province_id",
        "subject_side_index", "phase", "phase_raw", "phase_day",
    )}


def _account(source: Mapping[str, Any], carried: Any, fresh: Any, key: str) -> dict[str, Any]:
    return {
        "source_observed_present": key in source,
        "source_observed": copy.deepcopy(source.get(key)),
        "caller_carried": copy.deepcopy(carried),
        "fresh_observed": copy.deepcopy(fresh),
        "changed_since_carry": carried != fresh,
    }


def _counts(side: CurrentBattleSide) -> dict[str, int]:
    return {key: getattr(side, key) for key in (
        "stored_current_fighting_raw", "stored_levy_current_fighting_raw",
        "derived_current_fighting_raw", "derived_soft_casualties_raw",
        "derived_main_fighting_entry_hard_casualties_raw",
        "non_main_start_minus_current_minus_soft_raw", "participant_hard_total_raw",
    )}


def _entry_identity(entry: CurrentBattleEntry) -> dict[str, Any]:
    return {
        "bucket": entry.bucket, "bucket_index": entry.bucket_index,
        "regiment_id": entry.state.regiment_id,
        "native_carmy_id": entry.native_carmy_id,
        "public_cunit_id": entry.public_cunit_id,
        "owner_character_id": entry.owner_character_id,
    }


def _entry_state(entry: CurrentBattleEntry) -> dict[str, Any]:
    return dict(_entry_identity(entry),
        starting_raw=entry.starting_raw,
        current_fighting_raw=entry.state.current_raw,
        soft_casualties_raw=entry.state.soft_casualties_raw,
        hard_casualties_raw=entry.hard_casualties_raw,
        fights_in_main_phase=entry.fights_in_main_phase,
        effective_damage_raw=entry.effective_damage_raw,
        effective_toughness_raw=entry.state.toughness_raw,
        effective_pursuit_raw=entry.state.pursuit_raw,
        effective_screen_raw=entry.state.screen_raw,
        knight_character_id_raw=entry.knight_character_id_raw,
    )


def _components(value: tuple[BackingComponent, ...] | None) -> list[dict[str, int]] | None:
    if value is None:
        return None
    return [{"component_index": index, "maximum_soldiers": row.maximum_soldiers,
             "current_soldiers": row.current_soldiers, "kind": row.kind}
            for index, row in enumerate(value)]


def _side_ledger(previous: CurrentBattleSide, fresh: CurrentBattleSide,
                 source_side: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    prior_entries = {(row.bucket, row.state.regiment_id): row for row in previous.entries}
    entries, components = [], []
    for entry in fresh.entries:
        old = prior_entries.pop((entry.bucket, entry.state.regiment_id), None)
        entries.append({
            "identity": _entry_identity(entry),
            "membership": "retained" if old is not None else "new_in_fresh_frame",
            "source_observed": None if old is None else copy.deepcopy(dict(old.source_entry)),
            "caller_carried": None if old is None else _entry_state(old),
            "fresh_observed": copy.deepcopy(dict(entry.source_entry)),
        })
        components.append({
            "side_index": fresh.side_index, "identity": _entry_identity(entry),
            "caller_carried_components": None if old is None else _components(old.backing_components),
            "fresh_caller_supplied_components": _components(entry.backing_components),
            "fresh_component_status": "unavailable" if entry.backing_components is None else "caller_supplied",
            "fractional_accounts_used_to_infer_components": False,
            "previous_predicted_component_losses_reapplied": False,
        })
    prior_counts, fresh_counts = _counts(previous), _counts(fresh)
    source_counts = {key: copy.deepcopy(source_side[key]) for key in prior_counts if key in source_side}
    return {
        "side_index": fresh.side_index, "role": fresh.role,
        "selected_commander": _account(source_side, previous.selected_commander_character_id,
                                       fresh.selected_commander_character_id, "selected_commander_character_id"),
        "primary_participant": _account(source_side, previous.primary_participant_character_id,
                                        fresh.primary_participant_character_id, "primary_participant_character_id"),
        "ordered_armies": _account(source_side, previous.ordered_armies,
                                   fresh.ordered_armies, "ordered_armies"),
        "counts": {"source_observed": source_counts, "caller_carried": prior_counts,
                   "fresh_observed": fresh_counts,
                   "stored_caches_replaced_by_derived_sums": False},
        "entries": entries,
        "removed_entries": [_entry_identity(row) for row in prior_entries.values()],
        "participant_hard_ledger": _account(source_side, previous.participant_hard_ledger,
                                           fresh.participant_hard_ledger, "participant_hard_ledger"),
        "owner_hard_ledger_is_additional_fighting_debit": False,
    }, components


def _counter_projection(condition: CurrentBattleCondition) -> dict[str, Any]:
    try:
        _, retentions = project_current_counter_attack_raw(condition.source_snapshot)
    except ValueError as error:
        return {"status": "unavailable", "retention_raw_by_side": None,
                "reason": str(error), "native_outgoing_damage_claimed": False}
    # The helper's eligibility-filtered attack total is intentionally discarded.
    # Actual .3 outgoing loops all retained MAA rows, as the P1 runner records.
    return {"status": "available", "scope_kind": "conditional_current_frame_counter_retention",
            "retention_raw_by_side": [list(row) for row in retentions],
            "reason": None, "native_outgoing_damage_claimed": False}


def _contextual_ledger(envelope: Mapping[str, Any] | None,
                       battle_source: Mapping[str, Any] | None,
                       condition: CurrentBattleCondition) -> dict[str, Any]:
    if envelope is None:
        return {"status": "not_supplied", "binding": {"status": "not_supplied"},
                "source": None, "contextual_advantage": None,
                "used_to_replace_actual_advantage": False}
    source = envelope.get("source")
    inputs = envelope.get("combat_simulation_inputs")
    leaf = inputs.get("contextual_advantage") if isinstance(inputs, Mapping) else None
    checks: dict[str, bool | None] = {}
    checks["date_matches_control_leaf"] = (
        source.get("date_raw") == condition.observed_date_raw if isinstance(source, Mapping) else None)
    checks["query_paused"] = source.get("paused") is True if isinstance(source, Mapping) else None
    if isinstance(leaf, Mapping):
        checks["target_province_matches"] = leaf.get("target_province_id") == condition.province_id
        query_sides = leaf.get("sides")
        if isinstance(query_sides, (list, tuple)) and len(query_sides) == 2:
            for side, row in zip(condition.sides, query_sides, strict=True):
                if isinstance(row, Mapping):
                    checks[f"side_{side.side_index}_selected_commander_matches"] = (
                        row.get("selected_commander_character_id") == side.selected_commander_character_id)
                    checks[f"side_{side.side_index}_ordered_participants_match"] = (
                        row.get("ordered_public_cunit_ids") == [army["public_cunit_id"] for army in side.ordered_armies])
    native_checks: dict[str, bool | None] = {}
    if isinstance(source, Mapping) and isinstance(battle_source, Mapping):
        for key in ("native_revision", "date_raw", "paused", "player_character_id", "actor_character_id"):
            native_checks[key] = (
                source[key] == battle_source[key]
                if key in source and key in battle_source else None)
        core_available = all(native_checks[key] is not None for key in ("native_revision", "date_raw", "paused"))
        matched = (core_available and all(value is not False for value in native_checks.values())
                   and source.get("paused") is True and battle_source.get("paused") is True
                   and all(value is not False for value in checks.values()))
        binding = "same_paused_native_sample_coordinates" if matched else "native_sample_coordinates_unbound_or_mismatched"
    else:
        binding = "native_frame_identity_not_comparable_from_control_leaf"
    return {
        "status": "missing_leaf" if not isinstance(leaf, Mapping) else leaf.get("status"),
        "source": copy.deepcopy(source), "battle_control_source": copy.deepcopy(battle_source),
        "query_identity": {key: copy.deepcopy(envelope[key]) for key in (
            "queried_snapshot_id", "queried_revision", "queried_native_revision", "query_sequence") if key in envelope},
        "binding": {"status": binding, "participant_and_date_checks": checks,
                    "native_source_checks": native_checks, "is_runtime_gate": False,
                    "proves_actual_combat_source_cache": False},
        # Retain complete seven-stage/helper shape, including absent/null/zero.
        # Rows attribute aggregates; summing them beside aggregates would double count.
        "contextual_advantage": copy.deepcopy(leaf),
        "contextual_leaf_present": isinstance(inputs, Mapping) and "contextual_advantage" in inputs,
        "scope_kind": "independent_hypothetical_constructor_context_diagnostic",
        "source_rows_added_again_to_aggregates": False,
        "used_to_replace_actual_advantage": False,
    }


def refresh_current_battle_condition(
    carried: CarriedBattleCondition,
    normalized_snapshot: Mapping[str, object],
    *,
    active_resume_inputs: Mapping[str, object] | None = None,
    contextual_advantage_inputs: Mapping[str, object] | None = None,
    battle_control_source: Mapping[str, object] | None = None,
    backing_components_by_regiment_id: Mapping[int, tuple[BackingComponent, ...]] | None = None,
    levy_damage_raw_by_side: Mapping[int, int] | None = None,
) -> DynamicRefreshContext:
    """Adapt an authoritative observation without reapplying modeled losses.

    Snapshot and resume inputs use the existing production normalizers. The
    optional contextual argument is the existing registered query envelope;
    both query-source mappings may diagnose a same paused native sample, but
    constructor details never become an actual ongoing nonroll cache. Integer
    backing tuples are caller-supplied operands for this refresh, not inferred
    from Entry Q quantities. Earlier backing tuples are not silently reused.
    """
    fresh = adapt_current_battle_condition(
        normalized_snapshot,
        active_resume_inputs=active_resume_inputs,
        backing_components_by_regiment_id=backing_components_by_regiment_id,
        levy_damage_raw_by_side=levy_damage_raw_by_side,
    )
    context = prepare_next_main_tick(carried, refreshed_condition=fresh)
    previous, source = carried.condition, carried.condition.source_snapshot
    sides, components = [], []
    for old_side, new_side, role in zip(previous.sides, fresh.sides, ("attacker", "defender"), strict=True):
        side_ledger, component_rows = _side_ledger(old_side, new_side, source[role])
        sides.append(side_ledger)
        components.extend(component_rows)
    resume_source = active_resume_inputs.get("source") if active_resume_inputs is not None else None
    resume_same_frame = (
        all(resume_source.get(key) == fresh.source_snapshot[key] for key in (
            "snapshot_revision", "observed_date_raw", "combat_id", "province_id"))
        if isinstance(resume_source, Mapping) else None)
    counter = _counter_projection(fresh)
    missing = list(fresh.missing_inputs)
    # Existing control publishes stored actual advantage, not its source rows.
    missing.append("actual_ongoing_nonroll_advantage_component_sources")
    ledger = {
        "observed_frame": _frame(fresh),
        "previous_origin_observed_frame": copy.deepcopy(carried.origin_observed_frame),
        "state_policy": "authoritative_replacement_no_prior_loss_reapply",
        "previous_simulated_main_ticks": carried.simulated_main_ticks,
        "previous_predicted_losses_reapplied": False,
        "native_calendar_or_refresh_admission_inferred": False,
        "sides": sides,
        "native_order": [{"side_index": side.side_index,
                          "entries": [_entry_identity(entry) for entry in side.entries]}
                         for side in fresh.sides],
        "counter": {
            "source_observed_present": "active_counter_inputs_v1" in source,
            "source_observed": copy.deepcopy(source.get("active_counter_inputs_v1")),
            "fresh_observed_present": "active_counter_inputs_v1" in fresh.source_snapshot,
            "fresh_observed": copy.deepcopy(fresh.active_counter_inputs),
            "current_projection": counter,
            "prediction_carry_used_as_current_counter_census": False,
        },
        "advantage": {
            "observed_actual": {key: _account(source, getattr(previous, key), getattr(fresh, key), key)
                                for key in ("base_advantage_raw", "resolved_advantage_raw")},
            "contextual_query": _contextual_ledger(contextual_advantage_inputs, battle_control_source, fresh),
            "caller_rolls_used_to_infer_nonroll_components": False,
        },
        "roll_resume": {
            "roll_cadence_counter": _account(source, previous.roll_cadence_counter,
                                            fresh.roll_cadence_counter, "roll_cadence_counter"),
            "roll_cadence_interval_present": "roll_cadence_interval" in fresh.source_snapshot,
            "roll_cadence_interval": copy.deepcopy(fresh.source_snapshot.get("roll_cadence_interval")),
            "native_current_roll_points": [side.current_roll_points for side in fresh.sides],
            "resume_source": copy.deepcopy(resume_source), "active_resume_same_frame": resume_same_frame,
            "active_resume_observed": copy.deepcopy(active_resume_inputs.get("observed")) if active_resume_inputs is not None else None,
            "caller_draw_state": {"counter": context.draw_state.counter, "salt": context.draw_state.salt},
            "draw_consumed": False, "cadence_advanced": False, "default_interval_inserted": False,
        },
        "loss_inputs": {
            "source_observed_present": "current_loss_inputs_v1" in source,
            "source_observed": copy.deepcopy(source.get("current_loss_inputs_v1")),
            "fresh_observed_present": "current_loss_inputs_v1" in fresh.source_snapshot,
            "fresh_observed": copy.deepcopy(fresh.source_snapshot.get("current_loss_inputs_v1")),
            "factor_recomputed_from_sampled_rolls": False,
        },
        "missing_inputs": list(dict.fromkeys(missing)),
    }
    return DynamicRefreshContext(context=context, ledger=ledger, component_ledger=tuple(components))
