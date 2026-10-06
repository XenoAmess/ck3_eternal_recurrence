"""Independent county culture input in the existing player faction alert.

The caller validates the existing paused alert and player targeting identities.
This module exposes grievance inputs, not a complete populist validity predicate
or an action/outcome guarantee.
"""

from __future__ import annotations

from typing import Final


COUNTY_CULTURE_RELATION_FIELDS_V1: Final = frozenset(
    {
        "county_culture_id",
        "target_culture_id",
        "same_culture_as_target",
        "culture_relation_status",
    }
)


def _culture_id(value: object, field: str) -> int | None:
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(2**31) <= value <= 2**31 - 1
        or value == -1
    ):
        raise ValueError(f"{field} must be a signed int32 full CultureID other than -1, or null")
    return value


def normalize_county_culture_relation_v1(
    value: dict[str, object], *, field: str
) -> dict[str, object]:
    """Validate the optional all-four-field addition on a county observation.

    A legacy row has none of these fields and retains its original shape. The
    enclosing county normalizer continues to validate its existing ten fields.
    """

    present = COUNTY_CULTURE_RELATION_FIELDS_V1.intersection(value)
    if not present:
        return {}
    if present != COUNTY_CULTURE_RELATION_FIELDS_V1:
        raise ValueError(f"{field} must publish all four culture relation fields together")

    county = _culture_id(value["county_culture_id"], f"{field}.county_culture_id")
    target = _culture_id(value["target_culture_id"], f"{field}.target_culture_id")
    relation = value["same_culture_as_target"]
    status = value["culture_relation_status"]
    if not isinstance(status, str) or status not in {"available", "unavailable"}:
        raise ValueError(f"{field}.culture_relation_status is invalid")
    if relation is not None and not isinstance(relation, bool):
        raise ValueError(f"{field}.same_culture_as_target must be boolean or null")

    if status == "available":
        if county is None or target is None or not isinstance(relation, bool):
            raise ValueError(f"{field} available culture relation requires both full IDs and a boolean")
        if relation is not (county == target):
            raise ValueError(f"{field}.same_culture_as_target disagrees with the full IDs")
    elif relation is not None or (county is not None and target is not None):
        raise ValueError(f"{field} unavailable culture relation requires a missing ID and null relation")

    return {
        "county_culture_id": county,
        "target_culture_id": target,
        "same_culture_as_target": relation,
        "culture_relation_status": status,
    }


def project_player_faction_county_culture_context_v1(
    alert: dict[str, object],
) -> dict[str, object]:
    """Project culture grievance inputs from the normalized same-frame alert.

    Call only after the existing alert readiness and player/frame checks. This
    local readiness does not alter the alert's dangerous/watch classification,
    war entry eligibility, native county score, or action selection.
    """

    rows: list[dict[str, object]] = []
    ready_count = 0
    for faction in alert["targeting_factions"]:
        observations = {
            county["county_title_id"]: county
            for county in faction.get("county_member_observations", [])
        }
        for county_id in faction["county_member_title_ids"]:
            material = observations.get(county_id)
            culture = (
                normalize_county_culture_relation_v1(
                    material, field="normalized county_member_observation"
                )
                if material is not None
                else {}
            )
            relation_ready = culture.get("culture_relation_status") == "available"
            if relation_ready:
                ready_count += 1
            rows.append(
                {
                    "faction_id": faction["faction_id"],
                    "faction_type_key": faction["faction_type_key"],
                    "target_character_id": faction["target_character_id"],
                    "county_title_id": county_id,
                    "county_culture_id": culture.get("county_culture_id"),
                    "target_culture_id": culture.get("target_culture_id"),
                    "same_culture_as_target": culture.get("same_culture_as_target"),
                    "culture_relation_status": culture.get("culture_relation_status", "unavailable"),
                    "relation_input_ready": relation_ready,
                    "unavailable_reason": (
                        None
                        if relation_ready
                        else "culture_relation_unavailable"
                        if culture
                        else "culture_fields_not_published"
                        if material is not None
                        else "county_member_observation_not_published"
                    ),
                }
            )
    status = (
        "not_applicable"
        if not rows
        else "available"
        if ready_count == len(rows)
        else "partial"
        if ready_count
        else "unavailable"
    )
    return {
        "status": status,
        "relation_input_ready": bool(rows) and ready_count == len(rows),
        "source": "query-player-faction-alerts-v1",
        "snapshot_revision": alert["snapshot_revision"],
        "date_raw": alert["date_raw"],
        "player_character_id": alert["player_character_id"],
        "provenance": dict(alert["provenance"]),
        "county_row_count": len(rows),
        "available_relation_count": ready_count,
        "rows": rows,
    }


__all__ = [
    "COUNTY_CULTURE_RELATION_FIELDS_V1",
    "normalize_county_culture_relation_v1",
    "project_player_faction_county_culture_context_v1",
]
