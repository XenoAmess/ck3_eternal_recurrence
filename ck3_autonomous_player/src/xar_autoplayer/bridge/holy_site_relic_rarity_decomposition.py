"""Explain already sampled slot values without repeating any native evaluation.

The recognition matrix is evaluated separately from the original rarity getter.
This arithmetic projection is neither that getter's call trace nor a cache or
beneficiary observation. Call only after the existing parent/matrix validators.
"""
from __future__ import annotations

from collections.abc import Mapping


def project_holy_site_relic_rarity_v1(parent: Mapping[str, object]) -> dict[str, object]:
    """Preserve raw slot order, including repeated artifact contributions."""
    matrix = parent.get("recognition_matrix")
    inventory = parent["inventory"]
    county = parent["county_context"]
    current = parent["current_relic_evaluation"]
    holder = county.get("county_holder_faith_id")
    count = current.get("inventory_artifact_count_raw")
    association = current.get("county_holder_faith_associated")
    reported = current.get("active_artifact_rarity_sum") if current["available"] else None
    result = {
        "schema": "ck3_12004_holy_site_relic_rarity_decomposition_v1",
        "available": False, "complete_for_equipped_slots": False,
        "method": "independent_matrix_projection",
        "same_native_evaluation_as_total": False, "native_slot_trace_observed": False,
        "evaluation_atomic": False, "source_arrays_stable": False,
        **{key: parent.get(key) for key in
           ("capture_epoch", "date_raw", "played_character_id", "holy_site_id")},
        "county_holder_faith_id": holder,
        "inventory_artifact_count_raw": count,
        "county_holder_faith_associated": association,
        "reported_native_sum": reported, "projected_sum": None,
        "projected_current_is_active": None, "numerically_matches_reported_total": None,
        "slots": None, "additional_native_getter_calls": 0,
        "script_rng_effects_verified": False, "script_rng_effects": "unknown",
        "benefits_observed": False, "world_cache_written": False, "read_only": True,
        "unavailable_reason": None,
    }
    reason = None
    if parent["available"] is not True:
        reason = "parent_scope_unavailable"
    elif inventory["available"] is not True or not isinstance(matrix, Mapping):
        reason = "source_shape_unavailable"
    elif matrix["available"] is not True or matrix["source_arrays_stable"] is not True:
        reason = "matrix_unavailable_or_unstable"
    if reason is not None:
        result["unavailable_reason"] = reason
        return result

    slots = inventory["slots"]
    sources, artifact_sources = matrix["faith_sources"], matrix["artifact_sources"]
    associated_available = parent["associated_faith_ids_available"]
    if (artifact_sources["slots_available"] is not True
            or artifact_sources["slot_artifact_ids"] != [slot["artifact_id"] for slot in slots]
            or sources["county_holder_faith_id"] != holder
            or sources["player_faith_id"] != parent.get("player_faith_id")
            or sources["associated_available"] is not associated_available
            or sources["associated_faith_ids"] != parent.get("associated_faith_ids")):
        result["unavailable_reason"] = "source_identity_mismatch"
        return result
    if holder is not None and associated_available:
        membership = holder in parent["associated_faith_ids"]
        if association is not None and association is not membership:
            result["unavailable_reason"] = "source_identity_mismatch"
            return result
        association = membership
        result["county_holder_faith_associated"] = membership
    result["source_arrays_stable"] = True

    objects = {item["artifact_id"]: item for item in inventory["artifact_objects"]}
    cells = {(item["artifact_id"], item["faith_id"]): (index, item)
             for index, item in enumerate(matrix["cells"])}
    rows = []
    for slot in slots:
        artifact = slot["artifact_id"]
        obj = objects.get(artifact)
        rarity = obj["rarity_level"] if obj is not None and obj["available"] else None
        cell_index, cell = cells.get((artifact, holder), (None, None))
        recognized = cell["value"] if cell is not None and cell["available"] else None
        contribution = None
        if artifact is None:
            contribution, reason = 0, "empty_slot"
        elif count == 0:
            contribution, reason = 0, "inventory_count_zero"
        elif association is False:
            contribution, reason = 0, "holder_faith_not_associated"
        elif count is None:
            reason = "inventory_count_unavailable"
        elif holder is None:
            reason = "holder_faith_unavailable"
        elif association is None:
            reason = "association_unavailable"
        elif obj is None or obj["available"] is not True or rarity is None:
            reason = "artifact_unavailable"
        elif recognized is None:
            reason = "recognition_unavailable"
        elif recognized is False:
            contribution, reason = 0, "not_recognized"
        else:
            contribution, reason = rarity, "contributes"
        rows.append({"slot_index": slot["slot_index"], "artifact_id": artifact,
            "available": contribution is not None, "rarity_level": rarity,
            "matrix_cell_index": cell_index, "recognized": recognized,
            "contribution": contribution, "reason": reason,
            "reason_provenance": "projection_from_separately_sampled_inputs"})
    result["slots"] = rows
    complete = all(row["available"] for row in rows) and count is not None
    if not complete:
        result["unavailable_reason"] = "one_or_more_required_slot_inputs_unavailable"
        return result
    total = sum(row["contribution"] for row in rows)
    if not -(2**31) <= total <= 2**31 - 1:
        result["unavailable_reason"] = "projected_sum_outside_int32"
        return result
    result.update(available=True, complete_for_equipped_slots=True,
        projected_sum=total, projected_current_is_active=total > 0,
        numerically_matches_reported_total=(total == reported if reported is not None else None))
    return result
