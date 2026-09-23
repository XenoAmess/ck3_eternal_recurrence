"""Same-frame M5 candidate intake, before any cross-domain scoring.

The observed first-heir rows have no native rank or campaign value.  This
module keeps that distinction explicit while collecting current legal war and
family alternatives for the future joint selector.  It never emits an action.
"""

from __future__ import annotations

from .bridge.declaration_contract import normalize_declarable_wars


_FAMILY_SCHEMA = "xar.ck3.observed-first-heir-marriage-legality.v1"
_MISSING_VALUE_INPUTS = [
    "candidate_marriage_outcome_and_alliance_commitment",
    "candidate_war_participants_supply_campaign_cost_and_exit",
    "shared_budget_existing_commitments_and_common_utility",
    "formal_first_heir_marriage_action_and_material_result",
]


def build_m5_same_frame_intake(
    *,
    before: dict[str, object],
    after: dict[str, object],
    first_heir_legality: dict[str, object],
    declarable_war_query: dict[str, object],
) -> dict[str, object]:
    """Inventory two native legal domains bracketed by one paused game frame.

    The caller must perform the queries between ``before`` and ``after``.
    This function consumes current observations only; it cannot turn the
    private first-heir action into a public command or infer candidate value.
    """
    before_identity = _frame_identity(before)
    if _frame_identity(after) != before_identity:
        raise ValueError("M5 observations crossed a paused native frame")
    player_id, native_revision, date_raw, snapshot_id, revision, episode_run_id = before_identity
    if (
        first_heir_legality.get("schema") != _FAMILY_SCHEMA
        or first_heir_legality.get("exact_ck3_build") != "1.19.0.6"
        or first_heir_legality.get("status") != "available"
        or first_heir_legality.get("read_only") is not True
        or first_heir_legality.get("advertised") is not False
        or first_heir_legality.get("native_revision") != native_revision
        or type(first_heir_legality.get("query_sequence")) is not int
        or first_heir_legality["query_sequence"] <= 0
    ):
        raise ValueError("current private first-heir legality observation required")
    heir_id = first_heir_legality.get("observed_first_heir_character_id")
    if type(heir_id) is not int or heir_id <= 0 or heir_id == player_id:
        raise ValueError("current first-heir identity required")
    family_rows = first_heir_legality.get("native_legal_candidates")
    if not isinstance(family_rows, list):
        raise ValueError("native final-legal family rows required")
    family: list[dict[str, object]] = []
    seen_family: set[int] = set()
    for row in family_rows:
        if not isinstance(row, dict):
            raise ValueError("family row malformed")
        candidate_id = row.get("candidate_character_id")
        if (
            type(candidate_id) is not int or candidate_id <= 0
            or candidate_id in seen_family
            or row.get("played_character_id") != player_id
            or row.get("subject_character_id") != heir_id
            or row.get("native_rank") is not None
            or row.get("complete_can_send") is not True
            or row.get("recipient_answer_allows_send") is not True
            or type(row.get("recipient_ai_accept_raw")) is not int
        ):
            raise ValueError("family row is duplicated, stale, ranked, or not final-legal")
        seen_family.add(candidate_id)
        family.append({
            "candidate_id": f"first-heir-marriage:{heir_id}-{candidate_id}",
            "domain": "first_heir_marriage",
            "candidate_character_id": candidate_id,
            "subject_character_id": heir_id,
            "native_legal": True,
            "native_rank": None,
            "public_action_available": False,
        })
    if (
        declarable_war_query.get("step") != "query-declarable-wars"
        or declarable_war_query.get("accepted") is not True
        or declarable_war_query.get("status") != "available"
    ):
        raise ValueError("current native declarable-war query required")
    wars = normalize_declarable_wars(declarable_war_query.get("declarable_wars"))
    war_candidates = [{
        "candidate_id": f'war:{row["declaration_id"]}',
        "domain": "war",
        "declaration_id": row["declaration_id"],
        "target_character_id": row["target_character_id"],
        "casus_belli_index": row["casus_belli_index"],
        "casus_belli_key": row["casus_belli_key"],
        "configuration_index": row["configuration_index"],
        "claimant_character_id": row["claimant_character_id"],
        "target_title_ids": row["target_title_ids"],
        "native_legal": True,
    } for row in wars]
    candidates = family + war_candidates
    return {
        "policy": "g2-m5-same-frame-intake-v1",
        "played_character_id": player_id,
        "first_heir_character_id": heir_id,
        "family_legality_query_sequence": first_heir_legality["query_sequence"],
        "native_revision": native_revision,
        "date_raw": date_raw,
        "snapshot_id": snapshot_id,
        "revision": revision,
        "episode_run_id": episode_run_id,
        "family_candidate_count": len(family),
        "war_candidate_count": len(war_candidates),
        "native_legal_candidate_count": len(candidates),
        "minimum_five_native_legal_candidates_observed": len(candidates) >= 5,
        "candidates": candidates,
        "joint_selection_ready": False,
        "selected_step": None,
        "missing_components": _MISSING_VALUE_INPUTS.copy(),
    }


def _frame_identity(snapshot: object) -> tuple[int, int, int, str, int, str]:
    if not isinstance(snapshot, dict) or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise ValueError("M5 intake requires a paused map frame")
    played = snapshot.get("played_character")
    player_id = played.get("character_id") if isinstance(played, dict) else None
    native_revision = snapshot.get("native_revision")
    date_raw = snapshot.get("date_raw")
    snapshot_id = snapshot.get("snapshot_id")
    revision = snapshot.get("revision")
    episode_run_id = snapshot.get("episode_run_id")
    if (
        type(player_id) is not int or player_id <= 0
        or type(native_revision) is not int or native_revision <= 0
        or type(date_raw) is not int or date_raw < 0
        or type(snapshot_id) is not str or not snapshot_id
        or type(revision) is not int or revision <= 0
        or type(episode_run_id) is not str or not episode_run_id
    ):
        raise ValueError("M5 intake frame identity incomplete")
    return player_id, native_revision, date_raw, snapshot_id, revision, episode_run_id
