"""Read-only native quality comparison attached to the existing Army query.

This consumes the production-normalized current role and player CanAssign
rows. It supplies a queried proposal; plan_turn/M5 do not consume it and no
assignment is executed here. Native base quality is distinct from martial,
generic advantage and the selected CombatSide commander's contextual inputs.
"""

from __future__ import annotations

from collections.abc import Mapping

from .bridge.army_commander_assignment import assign_army_commander_v1_step


def propose_commander_quality_v1(
    candidates: Mapping[str, object],
    *,
    snapshot: Mapping[str, object],
    query_sequence: int,
) -> dict[str, object]:
    """Compare one normalized assigned-role score with observed eligible rows.

    The existing native pool order breaks candidate ties. Retain an assigned
    commander unless an observed player-eligible alternative is strictly
    better. An unavailable current score is not a zero or a candidate score.
    """
    current = candidates["current_commander"]
    current_id = current["character_id"]
    current_leaf = current.get("current_native_ai_base_quality")
    current_quality = (
        current_leaf["value"]
        if current["status"] == "available"
        and isinstance(current_leaf, Mapping)
        and current_leaf.get("status") == "available"
        else None
    )
    eligible = [
        row for row in candidates["candidates"]
        if row["available"] is True
        and row["final_eligibility_observable"] is True
        and row["can_assign"] is True
        and row["quality_observable"] is True
        and row["character_id"] != current_id
    ]
    best = max(eligible, key=lambda row: row["native_ai_base_quality"], default=None)
    proposal = {
        "schema": "xar.ck3.commander-quality-proposal.v1",
        "policy": "native_base_quality_current_baseline_v1",
        "status": "keep_current",
        "read_only": True,
        "scope": "existing_mcp_queried_proposal",
        "automatic_consumption": False,
        "assignment_executed": False,
        "source": "native_ai_base_quality",
        "army_id": candidates["army_id"],
        "native_carmy_id": candidates["native_carmy_id"],
        "owner_character_id": candidates["owner_character_id"],
        "frame": {
            "snapshot_id": snapshot["snapshot_id"],
            "revision": snapshot["revision"],
            "native_revision": snapshot["native_revision"],
            "date_raw": snapshot["date_raw"],
            "query_sequence": query_sequence,
        },
        "current_commander_character_id": current_id,
        "current_native_ai_base_quality": current_quality,
        "best_eligible_candidate_character_id": best["character_id"] if best else None,
        "best_eligible_candidate_native_ai_base_quality": best["native_ai_base_quality"] if best else None,
        "quality_gain": None,
        "proposed_commander_character_id": None,
        "selected_step": None,
        "unavailable_reason": None,
    }
    if current["status"] != "absent" and current_quality is None:
        proposal["status"] = "current_quality_unavailable"
        proposal["unavailable_reason"] = "current_native_ai_base_quality_unavailable"
        return proposal
    if best is None:
        if current["status"] == "absent":
            proposal["status"] = "no_eligible_candidate"
            proposal["unavailable_reason"] = "no_available_can_assign_candidate"
        return proposal
    if current["status"] == "absent":
        proposal["status"] = "assign_candidate_for_empty_role"
    else:
        proposal["quality_gain"] = best["native_ai_base_quality"] - current_quality
        if proposal["quality_gain"] <= 0:
            return proposal
        proposal["status"] = "assign_better_candidate"
    proposal["proposed_commander_character_id"] = best["character_id"]
    proposal["selected_step"] = assign_army_commander_v1_step(
        candidates["army_id"], best["character_id"],
    )
    return proposal
