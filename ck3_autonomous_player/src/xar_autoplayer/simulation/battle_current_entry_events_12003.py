"""Conditional .3 outer join and committed knight-cleanup consequences.

Events are caller-selected model inputs, not predicted admission or observed
native execution. The original frame and caller draw stream remain unchanged.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, replace
from typing import Any, Mapping

from .battle_current_adapter import CurrentBattleEntry, CurrentBattleSide
from .battle_current_next_day import CarriedBattleCondition
from .battle_current_terminal import TerminalBackingRegiment
from .combat_core import BackingComponent, CombatRegimentState, FIXED_SCALE, RegimentKind


@dataclass(frozen=True, slots=True)
class IncomingRegiment12003:
    regiment_id: int
    current_soldiers: int
    kind: RegimentKind
    fights_in_main_phase: bool
    effective_damage_raw: int
    effective_toughness_raw: int
    effective_pursuit_raw: int = 0
    effective_screen_raw: int = 0
    effective_max_size: int | None = None
    effective_siege_raw: int | None = None
    knight_character_id_raw: int = -1
    backing_components: tuple[BackingComponent, ...] | None = None
    native_type_identity: object | None = None
    property_source: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class AdmittedArmyJoin12003:
    combat_id: int
    side_index: int
    native_carmy_id: int
    public_cunit_id: int
    owner_character_id: int
    regiments_in_source_order: tuple[IncomingRegiment12003, ...]
    refreshed_width: tuple[int, int] | None = None
    source_context: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CommittedKnightCleanup12003:
    combat_id: int
    character_id: int
    linked_regiment_id: int
    native_carmy_id: int
    death_commit_selected: bool
    cleanup_branch_selected: bool | None
    court_link_present: bool | None
    court_knight_marker_nonzero: bool | None
    store_removal_selected: bool | None = None
    source_context: Mapping[str, object] | None = None
    regiment_mapping_valid: bool | None = None
    army_mapping_valid: bool | None = None
    combat_mapping_valid: bool | None = None


@dataclass(frozen=True, slots=True)
class ConditionalEntryEventsResult12003:
    carried: CarriedBattleCondition
    event_ledger: tuple[Mapping[str, Any], ...]
    backing_by_army: Mapping[int, tuple[TerminalBackingRegiment, ...] | None] | None
    initial_baseline_deltas_by_side: Mapping[int, Mapping[str, int]]
    modeled_winner_raw: int | None
    missing_consequences: tuple[str, ...]
    scope_kind: str = "caller_conditional_native_entry_events_12003"
    actual_game_days_advanced: int = 0
    complete_transition: bool = False
    complete_monte_carlo: bool = False


def _derive(side: CurrentBattleSide, entries: tuple[CurrentBattleEntry, ...], **changes):
    # These are derived model sums, not extra native cache/ledger debits.
    return replace(side, entries=entries,
        derived_current_fighting_raw=sum(row.state.current_raw for row in entries),
        derived_soft_casualties_raw=sum(row.state.soft_casualties_raw for row in entries),
        derived_main_fighting_entry_hard_casualties_raw=sum(
            row.starting_raw-row.state.current_raw-row.state.soft_casualties_raw
            for row in entries if row.fights_in_main_phase),
        non_main_start_minus_current_minus_soft_raw=sum(
            row.starting_raw-row.state.current_raw-row.state.soft_casualties_raw
            for row in entries if not row.fights_in_main_phase), **changes)


def _ordered(entries):
    rows = []
    for bucket in ("levy", "men_at_arms"):
        rows.extend(replace(row, bucket_index=index) for index, row in enumerate(
            row for row in entries if row.bucket == bucket))
    return tuple(rows)


def _incoming(row: IncomingRegiment12003, event: AdmittedArmyJoin12003, index: int):
    if row.current_soldiers < 0:
        raise ValueError("incoming whole current soldiers must be nonnegative")
    if row.kind is RegimentKind.MEN_AT_ARMS and row.knight_character_id_raw != -1 and row.knight_character_id_raw <= 0:
        raise ValueError("occupied native knight identity must be positive or native -1")
    starting = row.current_soldiers * FIXED_SCALE
    current = starting if row.fights_in_main_phase else 0
    bucket = "levy" if row.kind is RegimentKind.LEVY else "men_at_arms"
    state = CombatRegimentState(row.regiment_id, row.kind, current, 0,
        row.effective_toughness_raw, row.effective_pursuit_raw, row.effective_screen_raw,
        () if row.backing_components is None else row.backing_components)
    source = {"model_origin": "caller_conditional_new_row", "property_source": copy.deepcopy(row.property_source),
              "effective_max_size": row.effective_max_size, "effective_siege_raw": row.effective_siege_raw}
    knight = row.knight_character_id_raw if row.kind is RegimentKind.MEN_AT_ARMS else None
    if knight is not None:
        source["knight_character_id_raw"] = knight
    return CurrentBattleEntry(state, bucket, index, event.native_carmy_id,
        event.public_cunit_id, event.owner_character_id, starting, row.effective_damage_raw,
        row.fights_in_main_phase, 0 if row.fights_in_main_phase else None,
        knight, row.backing_components, source)


def owner_subset_pursuit_worklist_12003(side: CurrentBattleSide, owner_character_id: int):
    """Expose 264F0F0's selected numeric work; do not run ordinary pursuit."""
    work = {bucket: tuple(row for row in reversed(side.entries)
                         if row.bucket == bucket and row.owner_character_id == owner_character_id)
            for bucket in ("levy", "men_at_arms")}
    soft = {bucket: sum(row.state.soft_casualties_raw for row in rows) for bucket, rows in work.items()}
    return {"scope_kind": "caller_conditional_owner_subset_pursuit_worklist",
            "selected_side_index": side.side_index, "opposite_side_index": 1-side.side_index,
            "entries_by_bucket_in_reverse_selection_order": work, "selected_soft_raw_by_bucket": soft,
            "arg4_arg6_levy_soft_raw": soft["levy"], "arg5_arg7_maa_soft_raw": soft["men_at_arms"],
            "duration_divisor": 1, "native_mixed_owner_fifth_flag": True,
            "side_C2_read_as_skip_gate": False, "numeric_writeback": None,
            "pursuit_pending": True, "membership_modified": False}


def apply_closed_entry_events_12003(
    carried: CarriedBattleCondition,
    ordered_events: tuple[AdmittedArmyJoin12003 | CommittedKnightCleanup12003, ...],
    *,
    backing_by_army: Mapping[int, tuple[TerminalBackingRegiment, ...] | None] | None = None,
    modeled_winner_raw: int | None = None,
) -> ConditionalEntryEventsResult12003:
    """Apply source-closed consequences once to caller-owned modeled state.

    Cleanup input explicitly selects the native committed CourtLink branch.
    Alive flags and script feedback are not events. Whole backing lists remain
    independent from fractional accounts; missing lists are never fabricated.
    """
    condition = carried.condition
    backing = dict(backing_by_army) if backing_by_army is not None else None
    winner = condition.source_snapshot.get("winner_raw") if modeled_winner_raw is None else modeled_winner_raw
    deltas = {index: {"side_A8_initial_raw": 0, "side_B0_levy_initial_raw": 0} for index in (0, 1)}
    ledger, gaps = [], []
    for order, event in enumerate(ordered_events):
        if event.combat_id != condition.combat_id:
            raise ValueError("conditional event belongs to another full combat")
        detail = {"order_index": order, "context_provenance": "caller_conditional",
                  "source_context": copy.deepcopy(event.source_context), "actual_execution_claimed": False}
        if isinstance(event, AdmittedArmyJoin12003):
            if event.side_index not in (0, 1):
                raise ValueError("join requires an explicitly chosen native side")
            side = condition.sides[event.side_index]
            duplicate = any(army["native_carmy_id"] == event.native_carmy_id for army in side.ordered_armies)
            added, result_rows = [], []
            if not duplicate:
                for row in event.regiments_in_source_order:
                    added.append(_incoming(row, event, 0))
                    initial = row.current_soldiers * FIXED_SCALE
                    deltas[event.side_index]["side_A8_initial_raw"] += initial
                    if row.kind is RegimentKind.LEVY:
                        deltas[event.side_index]["side_B0_levy_initial_raw"] += initial
                    result_rows.append({"regiment_id": row.regiment_id, "native_type_identity": row.native_type_identity,
                        "knight_character_id_raw": row.knight_character_id_raw if row.kind is RegimentKind.MEN_AT_ARMS else None,
                        "result_row_40_initial_increment_raw": initial})
                army = {"native_carmy_id": event.native_carmy_id, "public_cunit_id": event.public_cunit_id,
                        "owner_character_id": event.owner_character_id, "combat_backlink_id": event.combat_id}
                side = _derive(side, _ordered((*side.entries, *added)), ordered_armies=(*side.ordered_armies, army))
                if backing is not None:
                    backing[event.native_carmy_id] = tuple(TerminalBackingRegiment(
                        event.native_carmy_id, row.regiment_id, row.current_soldiers) for row in event.regiments_in_source_order)
            sides = list(condition.sides)
            sides[event.side_index] = side
            refreshed = []
            for value in sides:
                refreshed.append(replace(value,
                    stored_current_fighting_raw=sum(row.state.current_raw for row in value.entries),
                    stored_levy_current_fighting_raw=sum(row.state.current_raw for row in value.entries if row.bucket == "levy")))
            prior_phase = condition.phase_raw
            condition = replace(condition, sides=tuple(refreshed))
            if prior_phase == 2:
                condition = replace(condition, phase="main", phase_raw=1, phase_day=0)
                winner = -1
            width_called = condition.base_combat_width > 0
            if width_called and event.refreshed_width is not None:
                condition = replace(condition, base_combat_width=event.refreshed_width[0], final_combat_width=event.refreshed_width[1])
            elif width_called:
                gaps.append("join width refresh requires explicit .3 post-width operands")
            gaps.extend(("join result observer and both participant predicate effects remain separate",
                         "join absent/invalid primary fallback requires explicit caller refresh"))
            detail.update(event_kind="admitted_join", duplicate_inner_add=duplicate,
                initialized_regiment_ids_in_source_order=[row.regiment_id for row in event.regiments_in_source_order] if not duplicate else [],
                incoming_army_backlink_after=condition.combat_id, resolved_public_unit_168_clear=True,
                both_current_caches_refreshed=True, width_refresh_called=width_called,
                phase2_restart=prior_phase == 2, modeled_winner_raw_after=winner,
                result_initial_rows=result_rows, owner_hard_ledger_changed=False)
        elif isinstance(event, CommittedKnightCleanup12003):
            detail.update(event_kind="committed_death_knight_cleanup", source_cause="death_cleanup_remove_regiment")
            premises = (event.cleanup_branch_selected, event.court_link_present, event.court_knight_marker_nonzero)
            if not event.death_commit_selected or any(value is False for value in premises):
                detail["branch"] = "native_knight_cleanup_not_selected"
            elif any(value is None for value in premises):
                detail["branch"] = "conditional_knight_cleanup_premise_unavailable"
                gaps.append("cleanup branch premises must be explicit caller conditions")
            elif event.linked_regiment_id == -1:
                detail.update(branch="flag_clear_no_linked_regiment", CourtLink_16C_after=0)
            elif event.regiment_mapping_valid is not True:
                detail.update(branch="flag_clear_invalid_regiment_mapping" if event.regiment_mapping_valid is False
                              else "flag_clear_regiment_mapping_unavailable", CourtLink_16C_after=0)
                if event.regiment_mapping_valid is None:
                    gaps.append("cleanup full Regiment generation/magic mapping outcome unavailable")
            else:
                sides, removed = [], []
                for side in condition.sides:
                    if event.army_mapping_valid is not True or event.combat_mapping_valid is not True:
                        sides.append(side)
                        removed.append({"side_index": side.side_index, "invoked": False,
                                        "matched": None, "current_debit_raw": None})
                        continue
                    # Native callback searches levy first, then MAA, and erases one match.
                    index = next((index for bucket in ("levy", "men_at_arms")
                        for index, row in enumerate(side.entries)
                        if row.bucket == bucket and row.state.regiment_id == event.linked_regiment_id), None)
                    if index is None:
                        sides.append(side)
                        removed.append({"side_index": side.side_index, "matched": False, "current_debit_raw": 0})
                        continue
                    row = side.entries[index]
                    entries = _ordered((*side.entries[:index], *side.entries[index+1:]))
                    debit = row.state.current_raw
                    sides.append(_derive(side, entries,
                        stored_current_fighting_raw=side.stored_current_fighting_raw-debit,
                        stored_levy_current_fighting_raw=side.stored_levy_current_fighting_raw-(debit if row.bucket == "levy" else 0)))
                    removed.append({"side_index": side.side_index, "matched": True, "bucket": row.bucket,
                                    "regiment_id": row.state.regiment_id, "current_debit_raw": debit,
                                    "soft_native_cache_debit_raw": 0, "owner_hard_ledger_changed": False})
                condition = replace(condition, sides=tuple(sides))
                if event.army_mapping_valid is True and backing is not None and event.native_carmy_id in backing and backing[event.native_carmy_id] is not None:
                    items = list(backing[event.native_carmy_id])
                    found = next((index for index, row in enumerate(items) if row.regiment_id == event.linked_regiment_id), None)
                    if found is not None:
                        items.pop(found)
                    backing[event.native_carmy_id] = tuple(items)
                elif event.army_mapping_valid is True:
                    gaps.append("cleanup whole Army regiment-list update unavailable without independent ordered census")
                detail.update(branch="committed_cleanup_regiment_removed", CourtLink_16C_after=0,
                    CourtLink_F8_after=-1, Regiment_140_after=-1 if event.army_mapping_valid is True else None,
                    army_mapping_valid=event.army_mapping_valid, combat_mapping_valid=event.combat_mapping_valid,
                    side_callbacks_in_native_order=removed,
                    side_army_ids_removed=False, phase_or_winner_rewritten=False,
                    storage_invalidated=event.store_removal_selected,
                    destroyed_physical_Regiment_148_zero_is_live_identity=False)
                if event.store_removal_selected is None:
                    gaps.append("Regiment store-removal outcome is an explicit conditional input")
                if event.army_mapping_valid is None or (event.army_mapping_valid is True and event.combat_mapping_valid is None):
                    gaps.append("cleanup valid Army/Combat callback selection remains unavailable")
                gaps.append("cleanup destructor and later commander-role purge effects remain separate")
        else:
            raise TypeError("only source-closed join or committed cleanup events are supported")
        ledger.append(detail)
    totals = tuple({"side_index": side.side_index, "derived_current_fighting_raw": side.derived_current_fighting_raw,
        "derived_soft_casualties_raw": side.derived_soft_casualties_raw,
        "stored_current_fighting_raw": side.stored_current_fighting_raw,
        "stored_levy_current_fighting_raw": side.stored_levy_current_fighting_raw,
        "participant_hard_total_raw": side.participant_hard_total_raw} for side in condition.sides)
    carry = replace(carried, condition=condition, scope_kind="caller_conditional_entry_event_state",
                    conditional_assumptions=(*carried.conditional_assumptions,
                        "ordered_native_entry_events_are_caller_conditions_not_predicted_admission",
                        "origin_frame_and_draw_retained_no_loss_replay"), derived_side_totals=totals)
    return ConditionalEntryEventsResult12003(carry, tuple(ledger), backing, deltas, winner, tuple(dict.fromkeys(gaps)))
