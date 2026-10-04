"""Caller-selected .3 owner-subset retreat and normal account writeback.

Owner callback admission is external. This primitive retains the original
observation and caller draw stream and performs no calendar/main loss carry.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, replace
from typing import Any, Literal, Mapping

from .battle_current_adapter import CurrentBattleCondition, CurrentBattleEntry, CurrentBattleSide
from .battle_current_entry_events_12003 import owner_subset_pursuit_worklist_12003
from .battle_current_next_day import CarriedBattleCondition
from .battle_current_terminal import TerminalBackingRegiment
from .combat_core import FIXED_SCALE, PursuitInitialPools, apply_pursuit_day, fixed_mul


@dataclass(frozen=True, slots=True)
class SelectedOwnerSubsetPursuitInputs12003:
    pursuit_stat_multiplier_raw: int | None = None
    base_toughness_multiplier_raw: int | None = None
    minimum_pursuit_multiplier_raw: int | None = None
    pursuit_hard_conversion_raw: int | None = None
    pursuer_efficiency_modifier_raw: int | None = None
    retreater_loss_modifier_raw: int | None = None
    source_context: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class AdmittedSelectedOwnerRetreat12003:
    """Every owner in the tuple declares an independently admitted callback.

    The tuple is neither sorted nor deduplicated. It does not declare that an
    outer native command would select the subset branch for all these owners.
    """

    combat_id: int
    side_index: int
    ordered_owner_character_ids: tuple[int, ...]
    target_province_id: int
    mixed_owner_branch_admitted: bool | None
    pursuit_inputs_by_owner: Mapping[int, SelectedOwnerSubsetPursuitInputs12003] | None = None
    source_context: Mapping[str, object] | None = None
    subset_pursuit_flag: bool = True


@dataclass(frozen=True, slots=True)
class SelectedOwnerSubsetRetreatGap12003:
    event_index: int
    owner_index: int | None
    owner_character_id: int | None
    kind: str
    implementation_entry: str


@dataclass(frozen=True, slots=True)
class SelectedOwnerSubsetRetreatResult12003:
    carried: CarriedBattleCondition
    status: Literal["available", "partial"]
    event_ledger: tuple[Mapping[str, Any], ...]
    backing_by_army: Mapping[int, tuple[TerminalBackingRegiment, ...] | None] | None
    retained_backing_by_side: Mapping[int, tuple[TerminalBackingRegiment, ...] | None]
    departed_backing_by_army: Mapping[int, tuple[TerminalBackingRegiment, ...] | None]
    typed_gaps: tuple[SelectedOwnerSubsetRetreatGap12003, ...]
    scope_kind: str = "caller_conditional_normal_selected_owner_subset_retreat_12003"
    actual_game_days_advanced: int = 0
    actual_execution_claimed: bool = False
    complete_native_transition: bool = False
    complete_monte_carlo: bool = False
    win_probability_ready: bool = False


def selected_owner_pursuit_inputs_from_current_condition_12003(
    condition: CurrentBattleCondition, *, selected_side_index: int,
) -> SelectedOwnerSubsetPursuitInputs12003:
    """Copy same-query coefficients as explicit frozen conditional operands.

    Combat6E8/6F0 pools, runtime duration and ordinary skip flags are omitted.
    Future changes of these operands still belong to the external timeline.
    """
    if selected_side_index not in (0, 1):
        raise ValueError("selected side must be an explicit native side index")
    block = condition.source_snapshot.get("current_pursuit_inputs_v1")
    block = block if isinstance(block, Mapping) else {}
    modifiers = condition.pursuit_modifier_sides
    rows = modifiers.get("sides") if isinstance(modifiers, Mapping) and modifiers.get("status") == "available" else None
    selected = opposing = None
    if isinstance(rows, (tuple, list)) and len(rows) == 2:
        selected, opposing = rows[selected_side_index], rows[1-selected_side_index]
    return SelectedOwnerSubsetPursuitInputs12003(
        block.get("pursuit_stat_multiplier_raw"),
        block.get("base_toughness_multiplier_raw"),
        block.get("minimum_pursuit_multiplier_raw"),
        None if condition.loss_inputs is None else condition.loss_inputs.runtime_pursuit_hard_conversion_raw,
        None if opposing is None else opposing.get("pursuit_efficiency_raw"),
        None if selected is None else selected.get("retreat_losses_raw"),
        {"kind": "same_query_frozen_coefficient_context",
         "snapshot_revision": condition.snapshot_revision,
         "observed_date_raw": condition.observed_date_raw,
         "combat_id": condition.combat_id, "selected_side_index": selected_side_index,
         "initial_pools_source": "selected_copied_rows_at_each_callback",
         "duration_divisor": 1, "global_pools_or_skip_flag_copied": False},
    )


def _derive(side: CurrentBattleSide, entries: tuple[CurrentBattleEntry, ...], **changes):
    indexed = []
    for bucket in ("levy", "men_at_arms"):
        indexed.extend(replace(row, bucket_index=index) for index, row in enumerate(
            row for row in entries if row.bucket == bucket))
    entries = tuple(indexed)
    return replace(side, entries=entries,
        derived_current_fighting_raw=sum(row.state.current_raw for row in entries),
        derived_soft_casualties_raw=sum(row.state.soft_casualties_raw for row in entries),
        derived_main_fighting_entry_hard_casualties_raw=sum(
            row.starting_raw-row.state.current_raw-row.state.soft_casualties_raw
            for row in entries if row.fights_in_main_phase),
        non_main_start_minus_current_minus_soft_raw=sum(
            row.starting_raw-row.state.current_raw-row.state.soft_casualties_raw
            for row in entries if not row.fights_in_main_phase), **changes)


def _regular_current(components):
    current = 0
    for component in components:
        count = component.maximum_soldiers if component.kind == 3 and component.current_soldiers == 0 else component.current_soldiers
        current = (current + count) & 0xFFFFFFFF
        if current & 0x80000000:
            current -= 0x100000000
    return current


def _whole_views(condition, backing, departed_ids):
    retained = {}
    for side in condition.sides:
        lists = None if backing is None else [backing.get(army["native_carmy_id"]) for army in side.ordered_armies]
        retained[side.side_index] = (None if lists is None or any(rows is None for rows in lists)
                                     else tuple(row for rows in lists for row in rows))
    departed = {army_id: None if backing is None else backing.get(army_id) for army_id in departed_ids}
    return retained, departed


def apply_selected_owner_subset_retreats_12003(
    carried: CarriedBattleCondition,
    events: tuple[AdmittedSelectedOwnerRetreat12003, ...],
    *,
    backing_by_army: Mapping[int, tuple[TerminalBackingRegiment, ...] | None] | None = None,
) -> SelectedOwnerSubsetRetreatResult12003:
    """Apply selected copied-row loss, owner accounting and removal once.

    Positive-soft normal losses use existing H58 rows and regular non-knight
    components. Missing numeric/admission inputs leave that callback uninstalled.
    A known Q loss with missing whole operands remains a partial Q result; its
    affected whole census is explicitly None, never an unchanged after-count.
    The all-Army census includes Regiments absent from Combat Entry arrays.
    """
    condition = carried.condition
    backing = None if backing_by_army is None else dict(backing_by_army)
    ledger, gaps, departed_ids = [], [], []

    def gap(event_index, owner_index, owner, kind, entry):
        gaps.append(SelectedOwnerSubsetRetreatGap12003(event_index, owner_index, owner, kind, entry))

    stop = False
    for event_index, event in enumerate(events):
        if event.combat_id != condition.combat_id or event.side_index not in (0, 1):
            raise ValueError("retreat event requires the same full CombatID and an explicit native side")
        if event.mixed_owner_branch_admitted is not True:
            gap(event_index, None, None, "whole_side_or_unavailable_callback_admission", "explicit admitted264F0F0 callback;258B830 separately unimplemented")
            break
        for owner_index, owner in enumerate(event.ordered_owner_character_ids):
            side = condition.sides[event.side_index]
            work = owner_subset_pursuit_worklist_12003(side, owner)
            by_bucket = work["entries_by_bucket_in_reverse_selection_order"]
            copied = (*by_bucket["levy"], *by_bucket["men_at_arms"])
            softness = work["selected_soft_raw_by_bucket"]
            toughness = sum(fixed_mul(row.state.toughness_raw, row.state.soft_casualties_raw) for row in copied)
            inputs = None if event.pursuit_inputs_by_owner is None else event.pursuit_inputs_by_owner.get(owner)
            detail = {"event_index": event_index, "owner_index": owner_index,
                "owner_character_id": owner, "selected_side_index": event.side_index,
                "opposite_side_index": 1-event.side_index, "target_province_id": event.target_province_id,
                "source_context": copy.deepcopy(event.source_context),
                "numeric_source_context": None if inputs is None else copy.deepcopy(inputs.source_context),
                "copied_entries_before": tuple(copied), "selected_soft_raw_by_bucket": softness,
                "duration_divisor": 1, "subset_pursuit_flag": event.subset_pursuit_flag,
                "side_C2_read_as_skip_gate": False, "actual_execution_claimed": False,
                "initial_baseline_A8_B0_changed": False, "phase_day_or_winner_changed": False,
                "movement_effects_complete": False, "result_attribution_effects_complete": False}
            ledger.append(detail)
            needs_loss = event.subset_pursuit_flag and toughness > 0
            if needs_loss:
                names = ("pursuit_stat_multiplier_raw", "base_toughness_multiplier_raw",
                         "minimum_pursuit_multiplier_raw", "pursuit_hard_conversion_raw",
                         "pursuer_efficiency_modifier_raw", "retreater_loss_modifier_raw")
                missing = names if inputs is None else tuple(name for name in names if getattr(inputs, name) is None)
                if missing:
                    for name in missing:
                        gap(event_index, owner_index, owner, "missing_numeric_operand:"+name, "SelectedOwnerSubsetPursuitInputs12003")
                    detail.update(branch="numeric_inputs_unavailable", installed=False, new_hard_casualties_raw=None)
                    stop = True
                    break
                unsupported = tuple(row for row in copied if row.state.soft_casualties_raw > 0 and row.knight_character_id_raw not in (None, -1))
                if unsupported:
                    gap(event_index, owner_index, owner, "occupied_knight_backing_branch_unimplemented", "26341B0->2634880 qualified early-return/count branch")
                    detail.update(branch="occupied_knight_backing_branch_unimplemented", installed=False, new_hard_casualties_raw=None)
                    stop = True
                    break
                owner_row = next((index for index, row in enumerate(side.participant_hard_ledger) if row["participant_character_id"] == owner), None)
                if owner_row is None and any(row.state.soft_casualties_raw > 0 for row in copied):
                    gap(event_index, owner_index, owner, "absent_owner_hard_row_construction_unimplemented", "264EA10 absent-row creation/order")
                    detail.update(branch="owner_hard_writer_unavailable", installed=False, new_hard_casualties_raw=None)
                    stop = True
                    break
                day = apply_pursuit_day(tuple(row.state for row in copied), condition.sides[1-event.side_index].states,
                    initial_pools=PursuitInitialPools(softness["levy"], softness["men_at_arms"]),
                    pursuer_efficiency_modifier_raw=inputs.pursuer_efficiency_modifier_raw,
                    retreater_loss_modifier_raw=inputs.retreater_loss_modifier_raw,
                    pursuit_phase_days=1, pursuit_conversion_raw=inputs.pursuit_hard_conversion_raw,
                    pursuit_stat_multiplier_raw=inputs.pursuit_stat_multiplier_raw,
                    base_toughness_multiplier_raw=inputs.base_toughness_multiplier_raw,
                    minimum_pursuit_multiplier_raw=inputs.minimum_pursuit_multiplier_raw)
                after, writebacks = [], []
                for row, state, (_, hard) in zip(copied, day.entries, day.hard_by_regiment_raw, strict=True):
                    after.append(replace(row, state=state,
                        backing_components=None if row.backing_components is None else state.components,
                        hard_casualties_raw=None if row.hard_casualties_raw is None else row.hard_casualties_raw+hard))
                    call_selected = row.state.soft_casualties_raw > 0
                    whole_after = None
                    if call_selected:
                        census = None if backing is None else backing.get(row.native_carmy_id)
                        if row.backing_components is None or census is None:
                            gap(event_index, owner_index, owner, "whole_backing_operands_unavailable", "complete ordered backing census and current regular components")
                            if backing is not None:
                                backing[row.native_carmy_id] = None
                        else:
                            found = next((index for index, item in enumerate(census) if item.regiment_id == row.state.regiment_id), None)
                            if found is None:
                                gap(event_index, owner_index, owner, "selected_regiment_absent_from_backing_census", "actual all-Army backing membership")
                                backing[row.native_carmy_id] = None
                            else:
                                whole_after = _regular_current(state.components)
                                changed = list(census)
                                changed[found] = replace(changed[found], current_soldiers=whole_after)
                                backing[row.native_carmy_id] = tuple(changed)
                    writebacks.append({"native_carmy_id": row.native_carmy_id, "regiment_id": row.state.regiment_id,
                        "new_hard_casualties_raw": hard, "whole_current_soldiers_after": whole_after,
                        "regular_backing_call_selected": call_selected,
                        "native_write_order": ("regular_backing_hard", "copied_soft_decrease", "existing_owner_H58_increment") if call_selected else (),
                        "owner_ledger_is_second_whole_debit": False})
                hard_total = day.total_hard_raw
                owner_ledger = [dict(row) for row in side.participant_hard_ledger]
                if owner_row is not None:
                    owner_ledger[owner_row]["hard_casualties_raw"] += hard_total
                detail.update(branch="selected_soft_pursuit", copied_entries_after=tuple(after),
                    new_hard_casualties_raw=hard_total, backing_writebacks=tuple(writebacks),
                    numeric_domains=day.domains, owner_hard_delta_raw=hard_total)
            else:
                hard_total = 0
                owner_ledger = side.participant_hard_ledger
                detail.update(branch="no_soft_toughness" if event.subset_pursuit_flag else "explicit_no_subset_pursuit",
                    copied_entries_after=tuple(copied), new_hard_casualties_raw=0,
                    backing_writebacks=(), numeric_domains=(), owner_hard_delta_raw=0)
            levy_debit = sum(row.state.current_raw for row in by_bucket["levy"])
            all_debit = levy_debit+sum(row.state.current_raw for row in by_bucket["men_at_arms"])
            removed = tuple(army for army in reversed(side.ordered_armies) if army["owner_character_id"] == owner)
            for army in removed:
                army_id = army["native_carmy_id"]
                departed_ids.append(army_id)
                if backing is None or backing.get(army_id) is None:
                    gap(event_index, owner_index, owner, "departed_whole_census_unavailable", "complete independent all-Army backing census")
            retained = tuple(row for row in side.entries if row.owner_character_id != owner)
            side_after = _derive(side, retained,
                ordered_armies=tuple(army for army in side.ordered_armies if army["owner_character_id"] != owner),
                stored_current_fighting_raw=side.stored_current_fighting_raw-all_debit,
                stored_levy_current_fighting_raw=side.stored_levy_current_fighting_raw-levy_debit,
                participant_hard_ledger=tuple(owner_ledger),
                participant_hard_total_raw=side.participant_hard_total_raw+hard_total)
            sides = list(condition.sides)
            sides[event.side_index] = side_after
            condition = replace(condition, sides=tuple(sides))
            detail.update(installed=True, cached_current_debit_raw=all_debit,
                cached_levy_current_debit_raw=levy_debit,
                removed_armies_in_reverse_native_order=tuple({**dict(army), "combat_backlink_id": -1} for army in removed),
                removed_native_carmy_ids=tuple(army["native_carmy_id"] for army in removed),
                backing_army_regiment_membership_removed=False, retained_rows_redebited=False,
                native_operation_order=("copy_erase_entries_and_cache_debit", "selected_pursuit_writeback", "reverse_army_removal", "army_combat_backlink_minus1"))
        if stop:
            break
    totals = tuple({"side_index": side.side_index,
        "stored_current_fighting_raw": side.stored_current_fighting_raw,
        "stored_levy_current_fighting_raw": side.stored_levy_current_fighting_raw,
        "derived_current_fighting_raw": side.derived_current_fighting_raw,
        "derived_soft_casualties_raw": side.derived_soft_casualties_raw,
        "participant_hard_total_raw": side.participant_hard_total_raw} for side in condition.sides)
    after_carry = replace(carried, condition=condition,
        scope_kind="caller_conditional_selected_owner_subset_retreat_state",
        conditional_assumptions=(*carried.conditional_assumptions,
            "ordered_owner_callbacks_explicitly_admitted_not_AI_predicted",
            "selected_copied_soft_pools_divisor1_no_main_loss_replay"), derived_side_totals=totals)
    retained_backing, departed_backing = _whole_views(condition, backing, departed_ids)
    return SelectedOwnerSubsetRetreatResult12003(after_carry, "partial" if gaps else "available",
        tuple(ledger), backing, retained_backing, departed_backing, tuple(gaps))
