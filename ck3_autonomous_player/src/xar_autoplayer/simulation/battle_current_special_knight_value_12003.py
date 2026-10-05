"""Independent current-input special-knight values from a normalized query.

Exact .3 initial special branch: 264E099 -> 2657AC0 -> 26344C0.
This adapter reuses the existing C1..C9 kernel. It does not select admission,
replace observed stats, or infer the constructor's later Character stage.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Mapping

from .battle_first_contact_final_stat_refresh_12003 import (
    compute_knight_stat_cache_at_stage_12003,
    knight_inputs_from_current_observation_12003,
    vars_six_stats,
)


def estimate_current_special_knight_initial_stats_12003(
    combat_inputs: Mapping[str, object], *,
    source_provenance: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Calculate each observed member and retain partial, independent outputs.

    ``all_observed_member_inputs_ready`` covers this numeric slice only. Sums
    include ready members and explicitly report missing members/Army coverage;
    they are analysis totals, not native Entry aggregation or a battle forecast.
    The input must be the existing production-normalized combat query leaf.
    """
    rows, missing = [], []
    sums = {role: {"ready_member_count": 0, "partial_member_count": 0,
                   "ready_member_damage_raw_sum": 0,
                   "ready_member_toughness_raw_sum": 0}
            for role in ("attacker", "defender")}
    armies = combat_inputs.get("armies")
    if not isinstance(armies, (list, tuple)):
        armies = ()
        missing.append("armies")
    for army_index, army in enumerate(armies):
        role = army.get("encounter_role")
        army_key = f"armies[{army_index}]"
        knights = army.get("knights")
        if army.get("status") != "available":
            missing.append(army_key + ".available")
        if not isinstance(knights, Mapping) or knights.get("status") != "available":
            missing.append(army_key + ".knights.available")
            continue
        for member_index, member in enumerate(knights["members"]):
            member_key = army_key + f".knights.members[{member_index}]"
            calculated = compute_knight_stat_cache_at_stage_12003(
                knight_inputs_from_current_observation_12003(
                    knights, member, source_provenance=source_provenance))
            gaps = tuple(member_key + "." + key for key in calculated.missing_inputs)
            missing.extend(gaps)
            stats = (dict(vars_six_stats(calculated.stat_cache))
                     if calculated.stat_cache is not None else None)
            observed = {key: member[key] for key in (
                "knight_effectiveness_raw", "effective_damage_raw", "effective_toughness_raw")}
            raw_context = member.get("effectiveness_context")
            comparisons = {
                "effectiveness_raw": (None if calculated.effectiveness_raw is None else
                                      calculated.effectiveness_raw == observed["knight_effectiveness_raw"]),
                **{key: None if stats is None else stats[key] == observed[key]
                   for key in ("effective_damage_raw", "effective_toughness_raw")},
            }
            rows.append({
                "army_index": army_index, "member_index": member_index,
                "encounter_role": role, "public_cunit_id": army.get("army_id"),
                "native_carmy_id": army.get("native_carmy_id"),
                "regiment_id": member["source_regiment_id"],
                "linked_character_full_id": calculated.linked_character_full_id,
                "selected_character_full_id": calculated.selected_character_full_id,
                "read_stage": calculated.ledger["selected_stage"],
                "modeled_stage": "caller_conditional_initial_special_knight_cache",
                "ready": calculated.ready, "missing_inputs": list(gaps),
                "effectiveness_raw": calculated.effectiveness_raw,
                "initial_stat_cache": stats, "current_observation": deepcopy(observed),
                "raw_context_status": (raw_context.get("status")
                                       if isinstance(raw_context, Mapping) else "absent"),
                "observed_matches_calculation": comparisons,
                "calculation_ledger": deepcopy(calculated.ledger),
            })
            if role in sums:
                summary = sums[role]
                summary["ready_member_count" if calculated.ready else "partial_member_count"] += 1
                if stats is not None:
                    summary["ready_member_damage_raw_sum"] += stats["effective_damage_raw"]
                    summary["ready_member_toughness_raw_sum"] += stats["effective_toughness_raw"]
    return {
        "schema": "ck3_12003_current_special_knight_initial_value_v1",
        "scope": "observed_current_inputs_conditional_initial_special_knight",
        "source": "264E099->2657AC0->26344C0->2C06D30->28BFC70->2C06B00",
        "target_province_id": combat_inputs.get("target_province_id"),
        "all_observed_member_inputs_ready": not missing,
        "observed_member_count": len(rows),
        "ready_member_count": sum(row["ready"] for row in rows),
        "missing_inputs": missing, "members_in_query_order": rows,
        "ready_member_contributions_by_role": sums,
        "source_provenance": deepcopy(source_provenance),
        "province_used_by_special_formula": False,
        "current_observations_modified": False,
        "admission_predicted": False, "constructor_final_stage_inferred": False,
        "full_person_preparation_ready": False, "full_entry_ready": False,
        "native_write_performed": False, "actual_game_days_advanced": 0,
    }
