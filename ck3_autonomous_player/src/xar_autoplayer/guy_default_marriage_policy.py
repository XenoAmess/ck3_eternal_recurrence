"""Bounded default-line marriage value for a verified child title successor.

This private policy values an early, zero-upfront-cost betrothal for a child
who will succeed to a separate title.  It does not assign a value to an
unobserved alliance, future children, or the recipient's acceptance score.
"""

from __future__ import annotations

from typing import Mapping, Sequence


_COST_TERMS = (
    "gold_raw", "prestige_raw", "piety_raw", "renown_raw", "influence_raw",
    "herd_raw", "treasury_raw", "treasury_or_gold_raw", "merit_raw",
    "barter_goods_raw",
)
_MAX_CHILD_WAIT_RAW = 3
_NATIVE_REVERSE_FERTILE_AGE_CUTOFF = 43
_BOUNDED_FULL_VALUE_COMPARISON = 2


def _positive(value: object) -> bool:
    return type(value) is int and 0 < value < 2**31


def _empty_relationship(row: Mapping[str, object], prefix: str) -> bool:
    return (
        row.get(prefix + "_betrothed_character_id") is None
        and row.get(prefix + "_primary_spouse_character_id") is None
        and row.get(prefix + "_spouse_character_ids") == []
    )


def _native_fertility_available(value: object) -> bool:
    return (
        isinstance(value, dict)
        and value.get("source") == "native_marriage_fertility_input"
        and value.get("extension_present") is True
        and value.get("native_gate_evaluated") is True
        and value.get("native_gate_allows") is True
        and _positive(value.get("effective_raw"))
    )


def shortlist_specified_child_default_candidates(
    legality: Mapping[str, object], *, limit: int = _BOUNDED_FULL_VALUE_COMPARISON,
) -> list[int]:
    """Pick bounded full-value reads from native final-legal compact rows.

    The compact adult threshold is only a shortlist filter.  The full value
    must confirm the candidate's own threshold and all action conditions.
    """
    if type(limit) is not int or not 1 <= limit <= 5:
        raise ValueError("child default shortlist limit must be 1..5")
    age = legality.get("adult_measure_raw")
    threshold = legality.get("adult_threshold_raw")
    dynasty = legality.get("dynasty_id")
    rows = legality.get("native_legal_candidates")
    if (legality.get("schema") != "xar.ck3.player-child-marriage-subject.v1"
            or legality.get("status") != "available"
            or legality.get("player_child_verified") is not True
            or legality.get("betrothed_character_id") is not None
            or legality.get("primary_spouse_character_id") is not None
            or legality.get("spouse_character_ids") != []
            or type(age) is not int or type(threshold) is not int
            or not _positive(dynasty) or not isinstance(rows, list)):
        return []
    child_wait = threshold - age
    if not 1 <= child_wait <= _MAX_CHILD_WAIT_RAW:
        return []
    ranked: list[tuple[int, int, int]] = []
    seen: set[int] = set()
    duplicates: set[int] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        candidate_id = row.get("candidate_character_id")
        if _positive(candidate_id):
            if candidate_id in seen:
                duplicates.add(candidate_id)
            seen.add(candidate_id)
        candidate_age = row.get("candidate_adult_measure_raw")
        candidate_dynasty = row.get("candidate_dynasty_id")
        accept = row.get("recipient_ai_accept_raw")
        if (not _positive(candidate_id) or not _positive(candidate_dynasty)
                or candidate_dynasty == dynasty
                or type(candidate_age) is not int
                or candidate_age < threshold
                or candidate_age + child_wait >= _NATIVE_REVERSE_FERTILE_AGE_CUTOFF
                or row.get("heir_adult_measure_raw") != age
                or row.get("played_character_id") != legality.get("played_character_id")
                or row.get("subject_character_id") != legality.get("subject_character_id")
                or row.get("complete_can_send") is not True
                or row.get("recipient_answer_allows_send") is not True
                or not _positive(accept)):
            continue
        ranked.append((candidate_age + child_wait, -accept, candidate_id))
    return [candidate_id for _, _, candidate_id in sorted(ranked)
            if candidate_id not in duplicates][:limit]


def _reason(legality: Mapping[str, object], value: Mapping[str, object],
            legal_rows: Mapping[int, Mapping[str, object]]) -> str:
    row = value.get("row")
    candidate_id = value.get("candidate_character_id")
    legal_row = legal_rows.get(candidate_id) if _positive(candidate_id) else None
    if not isinstance(row, dict) or not isinstance(legal_row, dict):
        return "missing_exact_legal_value"
    if (value.get("schema") != "xar.ck3.player-child-marriage-value.v1"
            or value.get("status") != "available"
            or value.get("read_only") is not True
            or value.get("request_matrilineal_option") is not False
            or value.get("subject_character_id") != legality.get("subject_character_id")
            or value.get("played_character_id") != legality.get("played_character_id")
            or value.get("native_revision") != legality.get("native_revision")
            or value.get("legality_query_sequence") != legality.get("query_sequence")
            or row.get("actor_character_id") != legality.get("played_character_id")
            or row.get("heir_character_id") != legality.get("subject_character_id")
            or row.get("candidate_character_id") != candidate_id
            or row.get("recipient_character_id") != legal_row.get(
                "recipient_matchmaker_character_id")
            or row.get("final_legality_sampled") is not True
            or row.get("complete_can_send") is not True
            or legal_row.get("complete_can_send") is not True
            or legal_row.get("recipient_answer_allows_send") is not True
            or row.get("recipient_answer_status_raw") not in {0, 1}
            or not _positive(row.get("recipient_ai_accept_raw"))
            or row.get("recipient_ai_accept_raw") != legal_row.get(
                "recipient_ai_accept_raw")
            or row.get("heir_adult_measure_raw") != legal_row.get(
                "heir_adult_measure_raw")
            or row.get("candidate_adult_measure_raw") != legal_row.get(
                "candidate_adult_measure_raw")):
        return "native_final_or_frame_unavailable"
    if (row.get("heir_sex_selector_raw") != 0
            or row.get("candidate_sex_selector_raw") != 1
            or row.get("effective_matrilineal_if_accepted") is not
                bool(row.get("heir_sex_selector_raw"))):
        return "sex_lineality_mismatch"
    if (row.get("requested_matrilineal_option") is not False
            or row.get("matrilineal_option_selected") is not False
            or row.get("effective_matrilineal_if_accepted") is not False
            or row.get("predicted_outcome_if_accepted") != "betrothal"
            or row.get("grand_wedding_option_selected") is not False
            or row.get("heir_is_adult") is not False
            or row.get("heir_house_id") != legality.get("house_id")
            or row.get("heir_dynasty_id") != legality.get("dynasty_id")
            or row.get("played_house_id") != legality.get("house_id")
            or row.get("played_dynasty_id") != legality.get("dynasty_id")
            or not _positive(row.get("candidate_dynasty_id"))
            or row.get("candidate_dynasty_id") == legality.get("dynasty_id")
            or not _empty_relationship(row, "heir")
            or not _empty_relationship(row, "candidate")):
        return "family_relation_or_lineality_not_valued"
    heir_age = row.get("heir_adult_measure_raw")
    heir_threshold = row.get("heir_adult_threshold_raw")
    candidate_age = row.get("candidate_adult_measure_raw")
    candidate_threshold = row.get("candidate_adult_threshold_raw")
    if (not all(type(v) is int for v in (
            heir_age, heir_threshold, candidate_age, candidate_threshold))
            or heir_age != legality.get("adult_measure_raw")
            or heir_threshold != legality.get("adult_threshold_raw")):
        return "adult_timing_unavailable"
    if candidate_age < candidate_threshold:
        return "candidate_not_adult"
    if row.get("candidate_is_adult") is not True:
        return "adult_timing_unavailable"
    child_wait = heir_threshold - heir_age
    if (child_wait < 1 or child_wait > _MAX_CHILD_WAIT_RAW
            or candidate_age + child_wait >= _NATIVE_REVERSE_FERTILE_AGE_CUTOFF):
        return "betrothal_wait_or_future_age_too_high"
    if (not _native_fertility_available(row.get("heir_native_fertility"))
            or not _native_fertility_available(row.get("candidate_native_fertility"))):
        return "native_fertility_gate_unavailable"
    costs = row.get("generic_costs")
    if (not isinstance(costs, dict)
            or costs.get("payer_role") != "actor"
            or costs.get("application_timing") != "on_send"
            or not all(type(costs.get(term)) is int and costs[term] == 0
                       for term in _COST_TERMS)):
        return "upfront_cost_unpriced"
    alliances = row.get("possible_alliance_pairs")
    if (not isinstance(alliances, list) or not alliances
            or any(not isinstance(pair, dict)
                   or pair.get("would_attempt_if_accepted") is not False
                   for pair in alliances)):
        return "alliance_obligation_unpriced"
    return "positive_early_split_successor_betrothal"


def choose_specified_child_default_value(
    legality: Mapping[str, object], values: Sequence[Mapping[str, object]], *,
    split_successor_verified: bool,
) -> dict[str, object]:
    """Choose a same-frame native value; caller retains and submits its object.

    A true split-successor proof must come from the title partition on this
    paused frame.  Candidate IDs are deliberately absent from this policy.
    """
    if (split_successor_verified is not True
            or legality.get("schema") != "xar.ck3.player-child-marriage-subject.v1"
            or legality.get("status") != "available"
            or legality.get("player_child_verified") is not True
            or not _positive(legality.get("subject_character_id"))
            or not _positive(legality.get("played_character_id"))
            or not _positive(legality.get("native_revision"))
            or not _positive(legality.get("query_sequence"))
            or legality.get("betrothed_character_id") is not None
            or legality.get("primary_spouse_character_id") is not None
            or legality.get("spouse_character_ids") != []):
        return {"status": "no_positive_value", "selected_candidate_character_id": None,
                "evaluated": [], "reason": "split_child_subject_not_verified"}
    raw_rows = legality.get("native_legal_candidates")
    if not isinstance(raw_rows, list):
        return {"status": "no_positive_value", "selected_candidate_character_id": None,
                "evaluated": [], "reason": "final_legal_candidates_unavailable"}
    legal_rows: dict[int, Mapping[str, object]] = {}
    duplicates: set[int] = set()
    for row in raw_rows:
        if isinstance(row, dict) and _positive(row.get("candidate_character_id")):
            candidate_id = row["candidate_character_id"]
            if candidate_id in legal_rows:
                duplicates.add(candidate_id)
            legal_rows[candidate_id] = row
    shortlist = shortlist_specified_child_default_candidates(legality)
    evaluated: list[dict[str, object]] = []
    value_by_id: dict[int, Mapping[str, object]] = {}
    for value in values:
        candidate_id = value.get("candidate_character_id")
        if not _positive(candidate_id):
            continue
        if candidate_id in value_by_id:
            return {"status": "no_positive_value", "selected_candidate_character_id": None,
                    "evaluated": evaluated, "reason": "duplicate_full_value"}
        value_by_id[candidate_id] = value
        reason = ("duplicate_final_legal_candidate" if candidate_id in duplicates
                  else _reason(legality, value, legal_rows))
        row = value.get("row")
        item: dict[str, object] = {"candidate_character_id": candidate_id,
                                   "reason": reason}
        if reason == "positive_early_split_successor_betrothal" and isinstance(row, dict):
            child_wait = row["heir_adult_threshold_raw"] - row["heir_adult_measure_raw"]
            future_age = row["candidate_adult_measure_raw"] + child_wait
            item.update({"child_wait_raw": child_wait,
                         "candidate_age_at_child_adulthood_raw": future_age,
                         "recipient_ai_accept_raw": row["recipient_ai_accept_raw"]})
        evaluated.append(item)
    reasons = {item["candidate_character_id"]: item["reason"]
               for item in evaluated}
    if any(candidate_id not in value_by_id for candidate_id in shortlist):
        return {"status": "no_positive_value", "selected_candidate_character_id": None,
                "evaluated": evaluated,
                "reason": "incomplete_top_two_full_value_comparison"}
    if any(reasons[candidate_id] in {
            "missing_exact_legal_value", "native_final_or_frame_unavailable",
            "adult_timing_unavailable", "duplicate_final_legal_candidate",
            "sex_lineality_mismatch"}
            for candidate_id in shortlist):
        return {"status": "no_positive_value", "selected_candidate_character_id": None,
                "evaluated": evaluated, "reason": "incomplete_same_frame_full_value"}
    for candidate_id in shortlist:
        if reasons[candidate_id] == "positive_early_split_successor_betrothal":
            return {"status": "selected",
                    "selected_candidate_character_id": candidate_id,
                    "evaluated": evaluated,
                    "reason": "early_zero_upfront_cost_split_successor_betrothal"}
    return {"status": "no_positive_value", "selected_candidate_character_id": None,
            "evaluated": evaluated, "reason": "no_bounded_positive_pair"}
