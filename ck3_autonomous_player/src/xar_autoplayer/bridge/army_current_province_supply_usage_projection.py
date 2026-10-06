"""Conditional selected-refill usage over the native ordered Province roster."""
from __future__ import annotations

from collections.abc import Mapping

from .army_associated_refill_current_projection import (
    project_conditional_associated_refill_current,
)


def _signed32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def project_conditional_current_province_supply_usage(
    army: Mapping[str, object],
) -> dict[str, object]:
    """Refill physical DATA once, then count every admitted roster occurrence.

    Scope is one explicit core invocation per observed persistent/cache. Native
    current ownership, supply eligibility, and roster are retained inputs, not
    reconstructed future manager dispatch or post-monthly observations.
    """
    result: dict[str, object] = {
        "projection_kind": "conditional_current_province_supply_usage",
        "source_contract_game_version": "1.20.0.3",
        "input_basis": "observed_Province_mode0_roster_admission_and_eligibility; "
                       "one_explicit_core_invocation_per_observed_persistent_cache",
        "status": "unavailable", "current_usage_ready": False,
        "contributors_ready": False, "native_supply_usage_soldiers": None,
        "native_supply_limit_soldiers": None, "soldiers_scale": 1,
        "current_contributor_sum_ready": False,
        "current_contributor_sum_soldiers": None,
        "conditional_usage_ready": False,
        "conditional_supply_usage_soldiers": None,
        "occurrences": [], "physical_refill": None, "missing_inputs": [],
        "actual_replenishment": False, "actual_loss": False,
        "actual_post_stage_current": None, "actual_post_supply_usage_soldiers": None,
        "full_regular_refill_ready": False, "full_monthly_ready": False,
        "excluded_stages": ["manager_roster_order_and_preparation",
                            "post_refill_supply_rate_and_stock",
                            "actual_monthly_entry_and_loss_application"],
    }
    family = army.get("current_province_supply_contributors_v1")
    if not isinstance(family, Mapping):
        result["missing_inputs"] = ["current_province_supply_contributors_v1"]
        return result
    source_occurrences = family["occurrences"]
    observed = {
        "current_usage_ready": family["current_usage_ready"],
        "contributors_ready": family["contributors_ready"],
        "province_id": family["province_id"],
        "subject_army_id": family["subject_army_id"],
        "subject_carmy_id": family["subject_carmy_id"],
        "owner_character_id": family["owner_character_id"],
        "native_province_unit_count": family["native_province_unit_count"],
        "native_supply_usage_soldiers": family["native_supply_usage_soldiers"],
        "native_supply_limit_soldiers": family["native_supply_limit_soldiers"],
        "native_observation_status": family["status"],
        "native_observation_unavailable_reason": family["unavailable_reason"],
    }

    # Full ArRg identities identify physical refresh receivers. Province and
    # DATA occurrences are preserved separately from this unique refill frame.
    by_regiment: dict[int, list[Mapping[str, object]]] = {}
    locations: dict[int, list[dict[str, int]]] = {}
    for occurrence in source_occurrences:
        if occurrence["included"] is not True:
            continue
        for regiment in occurrence["regiments"]:
            if regiment["native_supply_loss_eligible"] is not True:
                continue
            identity = regiment["army_regiment_id"]
            by_regiment.setdefault(identity, []).append(regiment)
            locations.setdefault(identity, []).append({
                "province_stored_index": occurrence["stored_index"],
                "army_id": occurrence["army_id"],
                "regiment_stored_index": regiment["stored_index"],
            })
    snapshots = []
    strengths = []
    unavailable: dict[int, str] = {}
    for identity, aliases in by_regiment.items():
        candidates = [row["replenishment_records_v1"] for row in aliases
                      if row["replenishment_records_v1"] is not None]
        complete = [row for row in candidates if row["status"] == "available"]
        selected = complete[0] if complete else candidates[0] if candidates else None
        if selected is None:
            unavailable[identity] = "observed_associated_DATA"
            continue
        if complete and any(row != selected for row in complete[1:]):
            unavailable[identity] = "consistent_same_physical_ArRg_DATA"
            continue
        snapshots.append(selected)
        strengths.append({"army_regiment_id": identity,
                          "current_soldiers": aliases[0]["current_soldiers"],
                          "maximum_soldiers": aliases[0]["maximum_soldiers"]})
    subject = family["subject_army_id"]
    refill = project_conditional_associated_refill_current({
        "status": "available", "army_id": subject if type(subject) is int else 0,
        "regiment_replenishment_records_v1": snapshots,
        "regiment_strengths": strengths,
    })
    refreshes = {row["army_regiment_id"]: row for row in refill["regiment_refreshes"]}
    coverage = [{"army_regiment_id": identity, "occurrences": aliases}
                for identity, aliases in locations.items()]

    missing = []
    modeled_occurrences = []
    conditional_sum = current_sum = 0
    conditional_rows_ready = current_rows_ready = True
    for occurrence in source_occurrences:
        included = occurrence["included"]
        modeled: dict[str, object] = {
            "stored_index": occurrence["stored_index"],
            "army_id": occurrence["army_id"],
            "native_carmy_id": occurrence["native_carmy_id"],
            "owner_character_id": occurrence["owner_character_id"],
            "included": included, "inclusion_basis": occurrence["inclusion_basis"],
            "native_eligible_current_soldiers": occurrence["native_eligible_current_soldiers"],
            "conditional_ready": False,
            "conditional_eligible_current_soldiers": None,
            "regiments": [], "missing_inputs": [],
        }
        current = 0 if included is False else occurrence["native_eligible_current_soldiers"]
        if included is None or type(current) is not int:
            current_rows_ready = False
        else:
            current_sum = _signed32(current_sum + current)
        if included is False:
            modeled.update({"conditional_ready": True,
                            "conditional_eligible_current_soldiers": 0})
        elif included is None:
            modeled["missing_inputs"] = ["native_owner_admission"]
        else:
            eligible_sum = 0
            regiments_ready = True
            for regiment in occurrence["regiments"]:
                identity = regiment["army_regiment_id"]
                eligible = regiment["native_supply_loss_eligible"]
                row: dict[str, object] = {
                    "stored_index": regiment["stored_index"],
                    "army_regiment_id": identity,
                    "native_supply_loss_eligible": eligible,
                    "current_soldiers_before": regiment["current_soldiers"],
                    "maximum_soldiers_before": regiment["maximum_soldiers"],
                    "conditional_ready": False,
                    "conditional_current_soldiers": None,
                    "conditional_maximum_soldiers": None,
                    "conditional_supply_contribution": None,
                    "missing_inputs": [],
                }
                if eligible is False:
                    row.update({"conditional_ready": True,
                                "conditional_current_soldiers": regiment["current_soldiers"],
                                "conditional_maximum_soldiers": regiment["maximum_soldiers"],
                                "conditional_supply_contribution": 0})
                elif eligible is None:
                    row["missing_inputs"] = ["native_supply_loss_eligibility"]
                elif identity in unavailable:
                    row["missing_inputs"] = [unavailable[identity]]
                else:
                    refresh = refreshes.get(identity)
                    if refresh is not None and refresh["current_maximum_ready"]:
                        contribution = refresh["current_soldiers"]
                        row.update({"conditional_ready": True,
                                    "conditional_current_soldiers": contribution,
                                    "conditional_maximum_soldiers": refresh["maximum_soldiers"],
                                    "conditional_supply_contribution": contribution})
                    else:
                        row["missing_inputs"] = (refresh["missing_inputs"] if refresh
                                                 else ["conditional_ArRg_refresh"])
                if row["conditional_ready"]:
                    eligible_sum = _signed32(eligible_sum + row["conditional_supply_contribution"])
                else:
                    regiments_ready = False
                modeled["regiments"].append(row)
            # An unavailable occurrence may contain only its readable prefix.
            if occurrence["status"] != "available":
                regiments_ready = False
                modeled["missing_inputs"].append("complete_native_ArRg_roster")
            if regiments_ready:
                modeled.update({"conditional_ready": True,
                                "conditional_eligible_current_soldiers": eligible_sum})
            else:
                modeled["missing_inputs"].extend({
                    "regiment_stored_index": row["stored_index"],
                    "army_regiment_id": row["army_regiment_id"],
                    "inputs": row["missing_inputs"],
                } for row in modeled["regiments"] if not row["conditional_ready"])
        if modeled["conditional_ready"]:
            conditional_sum = _signed32(conditional_sum + modeled["conditional_eligible_current_soldiers"])
        else:
            conditional_rows_ready = False
            missing.append({"province_stored_index": occurrence["stored_index"],
                            "army_id": occurrence["army_id"],
                            "inputs": modeled["missing_inputs"]})
        modeled_occurrences.append(modeled)

    count = family["native_province_unit_count"]
    roster_ready = family["contributors_ready"] and type(count) is int and (
        count >= 0 and count == len(source_occurrences))
    if not roster_ready:
        missing.append("complete_native_Province_occurrence_roster")
    conditional_ready = bool(roster_ready and conditional_rows_ready)
    current_ready = bool(roster_ready and current_rows_ready)
    any_ready = family["current_usage_ready"] or current_ready or any(
        row["conditional_ready"] for row in modeled_occurrences)
    return {
        **result, **observed,
        "status": "available" if conditional_ready else "partial" if any_ready else "unavailable",
        "current_contributor_sum_ready": current_ready,
        "current_contributor_sum_soldiers": current_sum if current_ready else None,
        "conditional_usage_ready": conditional_ready,
        "conditional_supply_usage_soldiers": conditional_sum if conditional_ready else None,
        "occurrences": modeled_occurrences, "physical_refill": refill,
        "physical_regiment_coverage": coverage, "missing_inputs": missing,
    }
