"""M5 candidate intake before a calibrated family/diplomacy/war choice.

Native legality is counted separately from action readiness and campaign value.
The current war-entry EU and marriage alliance value are incomplete, so this
ledger deliberately produces no cross-domain action recommendation.
"""

from __future__ import annotations

from .bridge.declaration_contract import declare_war_step, normalize_declarable_wars
from .bridge.marriage_contract import arrange_marriage_step


def build_joint_candidate_ledger(
    *,
    ranked_marriage: dict[str, object],
    declarable_wars: object,
    available_steps: set[str],
    active_wars: object,
) -> dict[str, object]:
    """Count distinct native-legal candidates and expose decision dependencies."""
    if not isinstance(ranked_marriage, dict) or not isinstance(ranked_marriage.get("candidates"), list):
        raise ValueError("ranked marriage observation must be normalized first")
    if not isinstance(available_steps, set) or any(type(step) is not str for step in available_steps):
        raise ValueError("available_steps must be a set of typed commands")
    if not isinstance(active_wars, list) or any(not isinstance(war, dict) for war in active_wars):
        raise ValueError("active_wars must be a normalized array")
    war_rows = normalize_declarable_wars(declarable_wars)
    candidates: list[dict[str, object]] = []
    for row in ranked_marriage["candidates"]:
        if row["complete_can_send"] is not True or row["recipient_answer_allows_send"] is not True:
            continue
        choice_id = f'{ranked_marriage["played_character_id"]}-{row["candidate_character_id"]}'
        step = arrange_marriage_step(choice_id)
        candidates.append({
            "candidate_id": f"marriage:{choice_id}",
            "domain": "marriage",
            "native_legal": True,
            "typed_step_available": step in available_steps,
            "native_rank": row["rank"],
            "native_candidate_score": row["native_candidate_score"],
            "recipient_ai_accept_raw": row["recipient_ai_accept_raw"],
            "predicted_outcome": row["predicted_outcome"],
        })
    for row in war_rows:
        step = declare_war_step(str(row["declaration_id"]))
        candidates.append({
            "candidate_id": f'war:{row["declaration_id"]}',
            "domain": "war",
            "native_legal": True,
            "typed_step_available": step in available_steps,
            "target_character_id": row["target_character_id"],
            "casus_belli_key": row["casus_belli_key"],
            "target_title_ids": row["target_title_ids"],
            "existing_war_count": len(active_wars),
        })
    missing = [
        "common_campaign_utility_scale",
        "marriage_alliance_and_long_commitment_value",
        "war_participant_and_supply_bounds",
        "war_campaign_cost_and_exit_assessment",
        "shared_budget_and_multiwar_opportunity_cost",
    ]
    return {
        "policy": "g2-m5-joint-candidate-intake-v1",
        "native_legal_candidate_count": len(candidates),
        "minimum_five_native_legal_candidates_observed": len(candidates) >= 5,
        "candidates": candidates,
        "joint_selection_ready": False,
        "selected_step": None,
        "missing_components": missing,
    }
