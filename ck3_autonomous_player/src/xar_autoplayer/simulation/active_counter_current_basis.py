"""Conditional current-frame counter projection for an actual battle.

Inputs must already be normalized by ``normalize_battle_control_snapshot_v1``.
The result is a same-frame diagnostic, not a next-tick retention or forecast.
"""

from __future__ import annotations

from typing import Any, Mapping

from .combat_core import FIXED_SCALE, fixed_div, fixed_mul


def project_current_counter_attack_raw(
    frame: Mapping[str, Any],
) -> tuple[tuple[int, int], tuple[tuple[int, ...], tuple[int, ...]]]:
    counter = frame.get("active_counter_inputs_v1")
    if not (
        isinstance(counter, dict)
        and counter.get("status") == "available"
        and counter.get("operand_census_complete") is True
        and frame.get("side_scope") == "full_side"
    ):
        raise ValueError("complete actual current-frame counter census required")
    class_count = counter["class_count"]
    counter_sides = counter["sides"]
    contexts = counter["contexts"]
    battle_sides = (frame["attacker"], frame["defender"])
    if (not isinstance(class_count, int) or not 0 < class_count <= 4096
            or len(counter_sides) != 2 or len(contexts) != 2):
        raise ValueError("current-frame counter shape is incomplete")

    retentions: list[tuple[int, ...]] = []
    for index, context in enumerate(contexts):
        if (context["countered_side_index"] != index
                or context["countering_side_index"] != 1 - index):
            raise ValueError("directional counter context disagrees")
        own = [0] * class_count
        pressure = [0] * class_count
        for entry in counter_sides[index]["men_at_arms_entries"]:
            if entry["status"] == "available":
                own[entry["class_index"]] += entry["current_chunk_raw"]
        for entry in counter_sides[1 - index]["men_at_arms_entries"]:
            if entry["status"] != "available":
                continue
            for target in entry["targets"]:
                pressure[target["class_index"]] += fixed_mul(
                    fixed_mul(entry["current_chunk_raw"], target["effectiveness_raw"]),
                    context["context_scale_raw"],
                )
        retentions.append(tuple(
            FIXED_SCALE if own_chunk == 0 else
            FIXED_SCALE - fixed_mul(
                min(FIXED_SCALE, fixed_div(fixed_div(incoming, own_chunk), 200_000)),
                90_000,
            )
            for own_chunk, incoming in zip(own, pressure, strict=True)
        ))

    attacks: list[int] = []
    for index, battle_side in enumerate(battle_sides):
        total = sum(
            fixed_mul(entry["effective_damage_raw"], entry["current_fighting_raw"])
            for entry in battle_side["levy_entries"]
            if entry["fights_in_main_phase"] is True
        )
        maa_entries = battle_side["men_at_arms_entries"]
        counter_entries = counter_sides[index]["men_at_arms_entries"]
        if len(maa_entries) != len(counter_entries):
            raise ValueError("MAA counter census disagrees with battle entries")
        for entry, operand in zip(maa_entries, counter_entries, strict=True):
            if (entry["regiment_id"] != operand["regiment_id"]
                    or entry["current_fighting_raw"] != operand["current_fighting_raw"]):
                raise ValueError("MAA counter entry differs from current battle entry")
            if entry["fights_in_main_phase"] is not True:
                continue
            damage_raw = entry["effective_damage_raw"]
            if operand["status"] == "available":
                damage_raw = fixed_mul(damage_raw, retentions[index][operand["class_index"]])
            total += fixed_mul(damage_raw, entry["current_fighting_raw"])
        attacks.append(total)
    return (attacks[0], attacks[1]), (retentions[0], retentions[1])
