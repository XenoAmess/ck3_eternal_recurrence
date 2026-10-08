"""Consume measured eligibility for the ordinary planner's selected subject."""
from __future__ import annotations


def observe_siege_subject_contribution(
    province: dict[str, object], subject: dict[str, object] | None
) -> dict[str, object]:
    selection = province.get("current_besieging_army_selection")
    result: dict[str, object] = {
        "status": "unavailable", "current_besieging_army_selection": selection,
        "public_unit_id": None, "native_carmy_id": None,
        "matches_current_selection": None,
    }
    if not isinstance(subject, dict) or subject.get("controllable") is not True:
        result["reason"] = "selected_controllable_subject_unavailable"
        return result
    unit_id = subject.get("army_id")
    result["public_unit_id"] = unit_id
    if (subject.get("current_province_id") != province.get("province_id")
            or subject.get("move_target_province_id") is not None
            or subject.get("route_province_ids") != []):
        result["reason"] = "selected_subject_not_arrived_with_empty_route"
        return result
    siege = province.get("active_siege")
    occurrences = siege.get("province_unit_occurrences") if isinstance(siege, dict) else None
    if not isinstance(occurrences, list):
        result["reason"] = "current_province_qualification_unavailable"
        return result
    rows = [row for row in occurrences if isinstance(row, dict)
            and row.get("public_unit_id") == unit_id]
    if not rows or any(type(row.get("eligible")) is not bool for row in rows):
        result["reason"] = "selected_subject_native_qualification_unavailable"
        return result
    result["occurrence_indices"] = [row.get("occurrence_index") for row in rows]
    result["native_carmy_id"] = rows[0].get("native_carmy_id")
    result["status"] = "eligible" if all(row["eligible"] is True for row in rows) else "excluded"
    result["reason"] = "measured_native_province_qualification"
    if isinstance(selection, dict) and selection.get("native_carmy_id") is not None:
        result["matches_current_selection"] = (
            selection["native_carmy_id"] == result["native_carmy_id"]
        )
    return result
