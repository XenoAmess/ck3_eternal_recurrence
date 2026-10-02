"""Read-only projection of observed precontact hard-casualty operands.

Call only after strict production v3 normalization.  The local CCombatSide
shell is hypothetical; these operands cannot establish an actual battle
transition, a win probability, or permission to enter contact.
"""

from __future__ import annotations

from typing import Any, Mapping

from .combat_core import hard_casualty_conversion_raw


def _signed_raw(value: object) -> bool:
    return type(value) is int and -(2**63) <= value < 2**63


def assess_precontact_hard_conversion(
    normalized_v3: Mapping[str, Any],
    *,
    target_province_id: int,
    attacker_entry_province_id: int,
    attacker_army_ids: tuple[int, ...],
    defender_army_ids: tuple[int, ...],
) -> dict[str, object]:
    """Show the two first-frame conversion factors without promoting fidelity."""

    def unavailable(reason: str) -> dict[str, object]:
        return {
            "status": "unavailable", "reason": reason,
            "conversion_by_defending_role": None,
            "actual_combat_parity": False,
            "future_daily_refresh_modeled": False,
            "planner_usable": False,
            "active_attack_allowed": False,
        }

    base = normalized_v3.get("base_inputs")
    phase = normalized_v3.get("phase_event_inputs")
    completeness = normalized_v3.get("completeness")
    if not (
        normalized_v3.get("schema_version") == 3
        and normalized_v3.get("contract_stage") == "production_exact_132_refs"
        and isinstance(base, Mapping) and isinstance(phase, Mapping)
        and isinstance(completeness, Mapping)
        and completeness.get("input_observation_ready") is True
        and phase.get("status") == "available"
    ):
        return unavailable("production_v3_observation_unavailable")
    scenario = base.get("scenario")
    if not (
        isinstance(scenario, Mapping)
        and base.get("target_province_id") == target_province_id
        and scenario.get("attacker_entry_province_id") == attacker_entry_province_id
        and scenario.get("attacker_army_ids") == list(attacker_army_ids)
        and scenario.get("defender_army_ids") == list(defender_army_ids)
        and scenario.get("actual_route_dependency") is False
    ):
        return unavailable("precontact_encounter_identity_mismatch")

    raw = phase.get("raw")
    phase_sides = raw.get("sides") if isinstance(raw, Mapping) else None
    hard_sides = phase.get("hard_casualty_sides")
    winter = phase.get("hard_casualty_winter")
    if not (
        isinstance(phase_sides, list) and len(phase_sides) == 2
        and isinstance(hard_sides, Mapping)
        and hard_sides.get("status") == "available"
        and hard_sides.get("source_target_province_id") == target_province_id
        and hard_sides.get("scale") == 100_000
        and isinstance(hard_sides.get("sides"), list)
        and len(hard_sides["sides"]) == 2
        and isinstance(winter, Mapping)
        and winter.get("status") == "available"
        and winter.get("source_target_province_id") == target_province_id
        and winter.get("scale") == 100_000
    ):
        return unavailable("native_hard_conversion_operands_unavailable")

    if winter.get("first_original_guard") is False:
        winter_raw = 0 if winter.get("second_original_guard") is None and winter.get("raw") is None else None
    elif winter.get("first_original_guard") is True and winter.get("second_original_guard") is False:
        winter_raw = 0 if winter.get("raw") is None else None
    elif winter.get("first_original_guard") is True and winter.get("second_original_guard") is True:
        winter_raw = winter.get("raw")
    else:
        winter_raw = None
    if not _signed_raw(winter_raw):
        return unavailable("native_hard_winter_guard_or_value_invalid")

    sides: list[Mapping[str, Any]] = []
    for index, (native, expected) in enumerate(zip(hard_sides["sides"], phase_sides, strict=True)):
        if not isinstance(native, Mapping) or not isinstance(expected, Mapping):
            return unavailable("native_hard_side_identity_invalid")
        commander = expected.get("commander_character_id")
        if commander is None:
            commander = -1
        if not (
            native.get("side_index") == index
            and native.get("encounter_role") == expected.get("encounter_role")
            and native.get("ordered_army_ids") == expected.get("ordered_army_ids")
            and native.get("commander_character_id") == commander
            and native.get("ordered_army_ids") == list(
                attacker_army_ids if index == 0 else defender_army_ids
            )
            and native.get("encounter_role") == ("attacker" if index == 0 else "defender")
            and _signed_raw(native.get("own_modifier_raw"))
            and _signed_raw(native.get("enemy_modifier_raw"))
        ):
            return unavailable("native_hard_side_identity_or_value_invalid")
        sides.append(native)

    rows = []
    for defending_index in (0, 1):
        own = sides[defending_index]["own_modifier_raw"]
        enemy = sides[1 - defending_index]["enemy_modifier_raw"]
        rows.append({
            "defending_role": "attacker" if defending_index == 0 else "defender",
            "defending_army_ids": list(attacker_army_ids if defending_index == 0 else defender_army_ids),
            "defending_own_modifier_raw": own,
            "attacking_enemy_modifier_raw": enemy,
            "combat_hard_winter_raw": winter_raw,
            "conversion_raw": hard_casualty_conversion_raw(
                defending_hard_modifier_raw=own,
                attacking_enemy_hard_modifier_raw=enemy,
                combat_hard_winter_raw=winter_raw,
            ),
        })
    return {
        "status": "observed_precontact_research_only",
        "reason": None,
        "target_province_id": target_province_id,
        "attacker_entry_province_id": attacker_entry_province_id,
        "conversion_by_defending_role": rows,
        "actual_combat_parity": False,
        "future_daily_refresh_modeled": False,
        "planner_usable": False,
        "active_attack_allowed": False,
    }
