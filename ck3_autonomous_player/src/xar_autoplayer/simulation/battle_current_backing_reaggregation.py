"""Pure exact .3 phase3 whole-backing count reaggregation.

Inputs are already-current qualified components and a strict count-link
witness. This module does not clear troops, apply losses, resolve native
objects, or establish normal finalization from phase3.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping, Set

from .battle_current_adapter import CurrentBattleCondition
from .battle_current_terminal import TerminalBackingRegiment
from .combat_core import BackingComponent, FIXED_SCALE


@dataclass(frozen=True, slots=True)
class CurrentPhase3BackingState:
    """Operands after any relevant P1/P2 loss carry or no-retreat clear.

    ``components`` is the complete qualified current component membership in
    native order; None is unavailable and an empty tuple is legitimate empty.
    ``valid`` means the exact 2633340 final Character count qualifier passed,
    not merely that a stored ID or an alive flag exists. ``absent`` records the
    observed -1 link; ``invalid`` records a known failed final qualifier.
    """

    components: tuple[BackingComponent, ...] | None
    knight_link_state: Literal["absent", "invalid", "valid", "unavailable"]


def _signed32(value: int) -> int:
    result = value & 0xFFFFFFFF
    return result - 0x100000000 if result & 0x80000000 else result


def _component_counts(components):
    current = maximum = 0
    rows = []
    for index, component in enumerate(components):
        fallback = component.kind == 3 and component.current_soldiers == 0
        effective = (component.maximum_soldiers if fallback else
                     component.current_soldiers)
        current = _signed32(current + effective)
        maximum = _signed32(maximum + component.maximum_soldiers)
        rows.append({
            "component_index": index, "kind": component.kind,
            "current_soldiers": component.current_soldiers,
            "maximum_soldiers": component.maximum_soldiers,
            "effective_current_soldiers": effective,
            "kind3_zero_current_uses_maximum": fallback,
        })
    return current, maximum, rows


def reaggregate_current_phase3_backing(
    condition: CurrentBattleCondition,
    *,
    current_state_by_regiment: Mapping[
        tuple[int, int], CurrentPhase3BackingState
    ],
    backing_inputs_v1: Mapping[str, object] | None = None,
    recomputed_regiments: Set[tuple[int, int]] | None = None,
    captured_maximum_by_regiment: Mapping[tuple[int, int], int] | None = None,
) -> dict[str, object]:
    """Recompute selected whole counts, preserving complete backing order.

    Membership comes only from the existing normalized complete
    ``full_backing_inputs_v1`` census, never from Combat Entry arrays.
    ``recomputed_regiments`` explicitly selects (native Army ID, Regiment ID)
    receivers; None selects all captured rows for this count context. For a
    no-retreat subset, pass the actual selected receivers: untouched rows keep
    captured whole current and optionally supplied captured whole maximum.
    Missing state on a selected receiver remains unavailable.

    The caller supplies component after-values once. Fighting current, soft,
    main-hard and owner hard-ledger quantities are not count operands here.
    Only component additions wrap signed32; side whole sums are converted to
    Q100000 at output. The terminal mapping feeds the unchanged accounting
    projector, whose normal-result intent remains independently caller-owned.
    """
    output = {
        "scope_kind": "conditional_current_phase3_whole_backing_reaggregation",
        "observed_frame": {
            "snapshot_revision": condition.snapshot_revision,
            "observed_date_raw": condition.observed_date_raw,
            "combat_id": condition.combat_id, "province_id": condition.province_id,
            "phase_raw": condition.phase_raw, "phase_day": condition.phase_day,
        },
        "status": "available", "sides": [],
        "backing_current_by_side": {0: None, 1: None},
        "whole_soldier_scale": 1, "terminal_scale": FIXED_SCALE,
        "component_addition_bits": 32,
        "owner_hard_ledger_debited": False,
        "prior_losses_reapplied": False,
        "native_membership_removal_simulated": False,
        "normal_result_intent": None,
        "actual_game_days_advanced": 0,
        "complete_monte_carlo": False,
        "named_character_outcomes_predicted": False,
    }
    if condition.phase_raw != 3:
        output.update(status="not_applicable",
                      unavailable_inputs=["explicit phase3 count context"])
        return output
    backing = (condition.source_snapshot.get("full_backing_inputs_v1")
               if backing_inputs_v1 is None else backing_inputs_v1)
    if (not isinstance(backing, Mapping)
            or backing.get("enumeration_complete") is not True):
        output.update(status="partial", unavailable_inputs=[
            "complete actual all-Army backing membership"])
        return output

    for source_side in backing["sides"]:
        side_index = source_side["side_index"]
        armies, terminal, missing = [], [], []
        currents, maxima = [], []
        for source_army in source_side["ordered_armies"]:
            native_army = source_army["native_carmy_id"]
            army = {key: source_army[key] for key in (
                "native_carmy_id", "public_cunit_id", "owner_character_id")}
            rows = []
            for source_regiment in source_army["ordered_regiments"]:
                regiment_id = source_regiment["regiment_id"]
                identity = (native_army, regiment_id)
                selected = (recomputed_regiments is None or
                            identity in recomputed_regiments)
                row_missing = []
                components = None
                link_state = None
                current = maximum = None
                count_source = None
                if not selected:
                    current = source_regiment["current_soldiers"]
                    maximum = (None if captured_maximum_by_regiment is None else
                               captured_maximum_by_regiment.get(identity))
                    count_source = "captured_unaffected_backing_whole"
                    if maximum is None:
                        row_missing.append("captured unaffected whole maximum")
                else:
                    state = current_state_by_regiment.get(identity)
                    if state is None:
                        row_missing.append("current selected backing state")
                    else:
                        link_state = state.knight_link_state
                        if link_state not in ("valid", "absent", "invalid", "unavailable"):
                            raise ValueError("knight_link_state requires its explicit four-state witness")
                        if state.components is not None:
                            current, maximum, components = _component_counts(state.components)
                        if link_state == "valid":
                            current = maximum = 1
                            count_source = "strict_valid_character_count_override"
                        elif link_state == "unavailable":
                            current = maximum = None
                            row_missing.append("strict final Character count qualifier")
                        elif state.components is None:
                            row_missing.append("complete current qualified component operands")
                        else:
                            count_source = "native_order_signed32_component_sums"
                row = {
                    "regiment_id": regiment_id,
                    "observed_census_current_soldiers": source_regiment["current_soldiers"],
                    "recomputed_in_count_context": selected,
                    "current_soldiers": current, "maximum_soldiers": maximum,
                    "knight_link_state": link_state, "component_rows": components,
                    "count_source": count_source,
                    "unavailable_inputs": row_missing,
                }
                rows.append(row)
                currents.append(current)
                maxima.append(maximum)
                missing.extend(f"Army{native_army}/Regiment{regiment_id}: {reason}"
                               for reason in row_missing)
                if current is not None:
                    terminal.append(TerminalBackingRegiment(native_army, regiment_id, current))
            army["ordered_regiments"] = rows
            armies.append(army)
        current_total = (None if any(value is None for value in currents) else
                         sum(currents))
        maximum_total = (None if any(value is None for value in maxima) else
                         sum(maxima))
        output["sides"].append({
            "side_index": side_index, "ordered_armies": armies,
            "current_soldiers": current_total, "maximum_soldiers": maximum_total,
            "terminal_current_raw_q100000": (None if current_total is None else
                                            current_total * FIXED_SCALE),
            "unavailable_inputs": missing,
        })
        if current_total is not None:
            output["backing_current_by_side"][side_index] = tuple(terminal)
        if missing:
            output["status"] = "partial"
    return output
