"""Private M5 comparison of current legal and domain-approved opportunities.

The 657 unranked first-heir rows are an intake, not valuations.  A caller may
price a bounded subset only after it has obtained the missing marriage and war
outcomes on the same paused frame.  No price is inferred from native legality,
recipient acceptance, troop count, or the order of the native result.
"""

from __future__ import annotations

from copy import deepcopy
from .m5_joint_dispatch import M5FrameDispatcher
from .m5_observed_opportunity_selector import _normalize_proposal, observed_frame


_MISSING_BY_DOMAIN = {
    "first_heir_marriage": (
        "marriage_or_betrothal_outcome",
        "alliance_value_and_long_term_obligation",
    ),
    "marriage": ("marriage_outcome_and_long_term_obligation",),
    "war": (
        "declaration_bound_participants_and_allies",
        "future_route_supply_campaign_cost_and_exit_terms",
    ),
    "council": ("common_policy_value",),
    "building": ("common_policy_value_and_payback",),
    "diplomacy": ("common_policy_value_and_faction_deadline",),
    "lifestyle": ("common_policy_value_and_perk_opportunity_cost",),
}


def compare_m5_joint_shortlist(
    *, snapshot: dict[str, object], intake: dict[str, object],
    observed_proposals: list[dict[str, object]],
    assessments: list[dict[str, object]],
    marriage_projection: dict[str, object] | None = None,
    war_current: dict[str, object] | None = None,
    existing_commitments: dict[str, object],
    gold_reserve_raw: int, max_active_wars: int,
) -> dict[str, object]:
    """Compare a priced subset, reserving at most one analytic opportunity.

    ``intake`` comes from the current native-final-legal family/war inventory;
    ``observed_proposals`` come from existing domain policies.  Assessments use
    one explicit campaign-value unit and must carry observed shared resource
    claims.  Missing prices remain visible and never become zero-valued rows.
    """
    if intake.get("policy") != "g2-m5-same-frame-intake-v1":
        raise ValueError("current M5 legal intake required")
    frame = observed_frame(snapshot)
    if any(intake.get(key) != value for key, value in frame.items()):
        raise ValueError("M5 shortlist crossed the paused frame")
    rows = intake.get("candidates")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("M5 legal candidates are unavailable")
    legal = deepcopy(rows)
    known = {row.get("candidate_id") for row in legal}
    if len(known) != len(legal) or any(type(key) is not str for key in known):
        raise ValueError("M5 legal candidate identities are duplicated")
    if not isinstance(observed_proposals, list):
        raise ValueError("M5 observed proposals must be a list")
    for raw in observed_proposals:
        proposal = _normalize_proposal(raw, frame)
        candidate_id = proposal["candidate_id"]
        if candidate_id in known:
            raise ValueError("M5 proposal duplicates a native legal candidate")
        known.add(candidate_id)
        legal.append({
            "candidate_id": candidate_id,
            "domain": proposal["domain"],
            "observed_proposal": proposal,
        })
    if not isinstance(assessments, list):
        raise ValueError("M5 common-value assessments must be a list")
    quoted = {row.get("candidate_id") for row in assessments
              if isinstance(row, dict)}
    if len(quoted) != len(assessments) or not quoted <= known:
        raise ValueError("M5 assessment identity is absent or duplicated")
    scales = {row.get("common_value_policy") for row in assessments}
    if assessments and (
        len(scales) != 1
        or any(type(value) is not str or not value for value in scales)
    ):
        raise ValueError("M5 shortlist requires one explicit common-value policy")
    by_id = {row["candidate_id"]: row for row in legal}
    priced_family = [by_id[key] for key in quoted
                     if by_id[key]["domain"] == "first_heir_marriage"]
    if priced_family:
        _require_marriage_projection(marriage_projection, intake, priced_family)
    priced_war = [by_id[key] for key in quoted
                  if by_id[key]["domain"] == "war"
                  and "observed_proposal" not in by_id[key]]
    current_war_resources = None
    if priced_war:
        current_war_resources = _require_current_war_readback(
            war_current, snapshot, priced_war
        )
    missing = [
        {"candidate_id": row["candidate_id"], "domain": row["domain"],
         "needed": list(_MISSING_BY_DOMAIN[row["domain"]])}
        for row in legal if row["candidate_id"] not in quoted
    ]
    if len(assessments) < 5:
        return {
            "policy": "g2-m5-joint-shortlist-v1",
            "status": "fewer_than_five_priced_legal_candidates",
            "frame": frame,
            "legal_candidate_count": len(legal),
            "priced_candidate_count": len(assessments),
            "unpriced_candidates": missing,
            "current_war_resources": current_war_resources,
            "selected_candidate_id": None,
            "reservation": None,
            "selected_step": None,
            "formal_action_ready": False,
        }
    combined = {**deepcopy(intake), "candidates": legal}
    dispatcher = M5FrameDispatcher(
        snapshot=deepcopy(snapshot),
        existing_commitments=deepcopy(existing_commitments),
    )
    decision = dispatcher.choose(
        intake=combined, snapshot=deepcopy(snapshot),
        assessments=deepcopy(assessments),
        gold_reserve_raw=gold_reserve_raw,
        max_active_wars=max_active_wars,
    )
    return {
        "policy": "g2-m5-joint-shortlist-v1",
        "status": decision["status"],
        "frame": frame,
        "legal_candidate_count": len(legal),
        "priced_candidate_count": len(assessments),
        "unpriced_candidates": missing,
        "current_war_resources": current_war_resources,
        "selected_candidate_id": decision["selected_candidate_id"],
        "reservation": decision["reservation"],
        "analysis": decision["analysis"],
        "selected_step": None,
        "formal_action_ready": False,
    }


def _require_marriage_projection(
    projection: object, intake: dict[str, object],
    priced_family: list[dict[str, object]],
) -> None:
    if not isinstance(projection, dict) or (
        projection.get("schema")
        != "xar.ck3.first-heir-candidate-alliance-projection.v1"
        or projection.get("status") != "available"
        or projection.get("native_revision") != intake["native_revision"]
        or projection.get("legality_query_sequence")
        != intake.get("family_legality_query_sequence")
        or type(projection.get("legality_query_sequence")) is not int
        or not isinstance(projection.get("rows"), list)
    ):
        raise ValueError("M5 priced family requires current five-row projection")
    rows = projection["rows"]
    identities = [row.get("candidate_character_id")
                  for row in rows if isinstance(row, dict)
                  and row.get("status") == "available"
                  and row.get("actor_character_id") == intake["played_character_id"]
                  and row.get("heir_character_id") == intake["first_heir_character_id"]]
    if (len(rows) != 5 or len(identities) != 5
            or len(set(identities)) != 5
            or any(row["candidate_character_id"] not in identities
                   for row in priced_family)):
        raise ValueError("M5 priced family is absent from the five current projections")


def _require_current_war_readback(
    readback: object, snapshot: dict[str, object],
    priced_wars: list[dict[str, object]],
) -> dict[str, object]:
    if not isinstance(readback, dict):
        raise ValueError("M5 priced war requires current private resource readback")
    readiness = readback.get("readiness")
    current = readback.get("m5_war_primary_current")
    if (
        readback.get("status") != "available"
        or readback.get("read_only") is not True
        or readback.get("advertised") is not False
        or readback.get("queried_snapshot_id") != snapshot["snapshot_id"]
        or readback.get("queried_revision") != snapshot["revision"]
        or readback.get("queried_native_revision") != snapshot["native_revision"]
        or readback.get("date_raw") != snapshot["date_raw"]
        or not isinstance(readiness, dict)
        or readiness.get("current_treasury_ready") is not True
        or readiness.get("current_raised_armies_ready") is not True
        or readiness.get("current_raised_supply_ready") is not True
        or not isinstance(current, dict)
        or current.get("actor_character_id") != snapshot["played_character_id"]
        or current.get("current_treasury") != snapshot.get("played_character_gold")
        or current.get("active_war_ids") != [
            war.get("war_id") for war in snapshot.get("active_wars", [])
        ]
    ):
        raise ValueError("M5 current war resources crossed the paused frame")
    declaration = current.get("declaration")
    if not isinstance(declaration, dict):
        raise ValueError("M5 current war declaration is unavailable")
    for row in priced_wars:
        if any(declaration.get(key) != row.get(key) for key in (
            "target_character_id", "casus_belli_index", "casus_belli_key",
            "configuration_index", "claimant_character_id", "target_title_ids",
        )):
            raise ValueError("M5 priced war differs from current declaration")
    supply = current.get("actor_current_raised_supply")
    army_ids = {row.get("army_id") for row in snapshot.get("player_armies", [])
               if isinstance(row, dict)}
    if (not isinstance(supply, list)
            or any(not isinstance(row, dict)
                   or type(row.get("army_id")) is not int
                   or row["army_id"] not in army_ids
                   or type(row.get("current_supply_raw")) is not int
                   or row["current_supply_raw"] < 0
                   or row.get("current_supply_scale") != 100_000
                   for row in supply)
            or len({row["army_id"] for row in supply}) != len(supply)):
        raise ValueError("M5 current raised supply is unavailable")
    return {
        "current_treasury_raw": current["current_treasury"]["raw"],
        "active_war_ids": list(current["active_war_ids"]),
        "actor_current_raised_supply": deepcopy(supply),
        "future_supply_ready": readiness.get("future_supply_ready") is True,
        "campaign_cost_ready": readiness.get("campaign_cost_ready") is True,
    }
