"""Read the current first heir beside a bounded child pending observation."""

from __future__ import annotations

from copy import deepcopy
from typing import Mapping


def observe_first_heir_companion_after_child(
    driver: object,
    service: object,
    *,
    before: Mapping[str, object],
    child_observation: Mapping[str, object],
    first_heir_resolved: Mapping[str, object] | None,
    turn_index: int,
) -> dict[str, object]:
    """Classify one native heir relationship without evaluating another proposal."""
    revision = before.get("native_revision")
    actor = before.get("played_character_id")
    if (child_observation.get("same_frame") is not True
            or type(revision) is not int or revision <= 0
            or type(actor) is not int or actor <= 0
            or before.get("paused") is not True
            or before.get("map_ready") is not True):
        raise ValueError("first-heir companion lacks a paused child result frame")
    relation = driver.query_current_first_heir_relationship_private_v1(
        expected_native_revision=revision)
    after = service.snapshot()
    played = after.get("played_character") if isinstance(after, dict) else None
    if (not isinstance(relation, dict)
            or relation.get("schema") != "xar.ck3.current-first-heir-relationship.v1"
            or relation.get("status") not in {"available", "unavailable"}
            or relation.get("native_revision") != revision
            or relation.get("read_only") is not True
            or relation.get("advertised") is not False
            or not isinstance(after, dict)
            or any(before.get(key) != after.get(key) for key in (
                "snapshot_id", "revision", "native_revision", "date_raw",
                "episode_run_id", "episode_character_id"))
            or after.get("paused") is not True
            or after.get("map_ready") is not True
            or not isinstance(played, dict)
            or played.get("character_id") != actor
            or played.get("alive") != before.get("played_character_alive")):
        raise ValueError("first-heir companion crossed its paused child frame")

    value_status = "unavailable"
    proposal_eligible: bool | None = None
    resolved_pair_matches_native = False
    if relation["status"] == "available":
        heir = relation.get("heir_character_id")
        betrothed = relation.get("betrothed_character_id")
        spouse = relation.get("primary_spouse_character_id")
        spouses = relation.get("spouse_character_ids")
        if (type(heir) is not int or heir <= 0
                or relation.get("bilateral_verified") is not True
                or not isinstance(spouses, list)
                or any(type(value) is not int or value <= 0 for value in spouses)
                or any(value is not None and (type(value) is not int or value <= 0)
                       for value in (betrothed, spouse))):
            raise ValueError("first-heir companion relationship is incomplete")
        partnered = betrothed is not None or spouse is not None or bool(spouses)
        if partnered:
            proposal_eligible = False
            value_status = "existing_partner_no_new_proposal_value"
            if isinstance(first_heir_resolved, Mapping):
                candidate = first_heir_resolved.get("candidate_character_id")
                resolved_pair_matches_native = bool(
                    first_heir_resolved.get("status") in {"betrothal", "marriage"}
                    and first_heir_resolved.get("material_result") is True
                    and first_heir_resolved.get("heir_character_id") == heir
                    and first_heir_resolved.get("episode_run_id") ==
                    before.get("episode_run_id")
                    and (betrothed == candidate or spouse == candidate
                         or candidate in spouses)
                )
        else:
            # Being unpartnered does not prove final Can Send or positive value.
            value_status = "unpartnered_requires_final_legality_and_value"
    return {
        "status": "observed", "turn_index": turn_index,
        "same_frame": True,
        "source_native_revision": revision,
        "first_heir_relationship": deepcopy(relation),
        "new_proposal_eligible": proposal_eligible,
        "new_proposal_value_status": value_status,
        "resolved_pair_matches_native": resolved_pair_matches_native,
        "read_only": True, "advertised": False,
    }
