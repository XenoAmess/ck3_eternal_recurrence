"""M5 same-frame resource arbitration for externally assessed alternatives.

This is an analytic selector, not a production action source.  Native legality
and recipient acceptance do not provide campaign value.  The caller must
obtain the missing marriage/war outcome observations and supply policy values
on the same frame before it can provide complete assessments.
"""

from __future__ import annotations


_VALUE_FIELDS = (
    "benefit_units", "war_cost_units", "family_cost_units",
    "diplomacy_cost_units", "supply_cost_units", "long_term_cost_units",
)
_CLAIM_FIELDS = ("army_ids", "ally_character_ids", "character_ids", "commitment_keys")
_OBSERVED_DOMAINS = {"council", "building", "diplomacy", "lifestyle"}


def select_m5_assessed_candidate(
    *, intake: dict[str, object], snapshot: dict[str, object],
    assessments: list[dict[str, object]], commitments: dict[str, object],
    gold_reserve_raw: int, max_active_wars: int,
) -> dict[str, object]:
    """Choose one positive, feasible assessed alternative or an explicit wait.

    ``units`` are one caller-defined campaign utility scale, never native
    acceptance or native military power.  This function never emits a step.
    A shortlist can be compared only within its stated scope.
    """
    identity = _identity(intake)
    if _identity(snapshot) != identity:
        raise ValueError("M5 assessment crossed the paused native frame")
    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise ValueError("M5 assessment requires a paused map frame")
    if intake.get("policy") != "g2-m5-same-frame-intake-v1":
        raise ValueError("M5 same-frame legal intake required")
    if not isinstance(commitments, dict):
        raise ValueError("existing commitments required")
    rows = intake.get("candidates")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("M5 intake candidates missing")
    legal = {row.get("candidate_id"): row for row in rows}
    if len(legal) != len(rows) or any(type(key) is not str for key in legal):
        raise ValueError("M5 intake candidate identity duplicated")
    if not assessments:
        return _result(identity, [], None, "missing_assessments", len(rows))
    if not isinstance(assessments, list) or len(assessments) < 5:
        raise ValueError("M5 comparison requires at least five assessed legal rows")
    gold = snapshot.get("played_character_gold")
    if (
        not isinstance(gold, dict) or type(gold.get("raw")) is not int
        or gold.get("scale") != 100_000
    ):
        raise ValueError("same-frame played_character_gold raw/scale required")
    wars = snapshot.get("active_wars")
    armies = snapshot.get("player_armies")
    if not isinstance(wars, list) or any(not isinstance(row, dict) or type(row.get("war_id")) is not int for row in wars):
        raise ValueError("same-frame active_wars required")
    if not isinstance(armies, list) or any(not isinstance(row, dict) or type(row.get("army_id")) is not int or type(row.get("controllable")) is not bool for row in armies):
        raise ValueError("same-frame player_armies required")
    if len({row["war_id"] for row in wars}) != len(wars) or len({row["army_id"] for row in armies}) != len(armies):
        raise ValueError("current war or army identities duplicated")
    _nonnegative(gold_reserve_raw, "gold_reserve_raw")
    _nonnegative(max_active_wars, "max_active_wars")
    reserved_gold = _nonnegative(commitments.get("gold_raw"), "commitments.gold_raw")
    pending_wars = _nonnegative(
        commitments.get("pending_war_slots", 0), "commitments.pending_war_slots"
    )
    occupied = {key: _claim_set(commitments.get(key), key) for key in _CLAIM_FIELDS}
    usable_armies = {row["army_id"] for row in armies if row["controllable"] is True}
    seen: set[str] = set()
    evaluated: list[dict[str, object]] = []
    for assessment in assessments:
        if not isinstance(assessment, dict):
            raise ValueError("M5 assessment must be an object")
        candidate_id = assessment.get("candidate_id")
        if type(candidate_id) is not str or candidate_id not in legal or candidate_id in seen:
            raise ValueError("M5 assessment candidate is absent or duplicated")
        seen.add(candidate_id)
        if _identity(assessment) != identity:
            raise ValueError("M5 assessment crossed the paused native frame")
        values = {key: _nonnegative(assessment.get(key), key) for key in _VALUE_FIELDS}
        gold_claim = _nonnegative(assessment.get("gold_raw"), "gold_raw")
        supply_margin = assessment.get("projected_supply_margin_units")
        if type(supply_margin) is not int:
            raise ValueError("projected_supply_margin_units must be measured")
        claims = {key: _claim_set(assessment.get(key), key) for key in _CLAIM_FIELDS}
        domain = legal[candidate_id].get("domain")
        proposal = legal[candidate_id].get("observed_proposal")
        if domain == "first_heir_marriage":
            heir = legal[candidate_id].get("subject_character_id")
            spouse = legal[candidate_id].get("candidate_character_id")
            if not {heir, spouse} <= claims["character_ids"]:
                raise ValueError("family assessment must claim both marriage roles")
        elif domain in _OBSERVED_DOMAINS or proposal is not None:
            if not isinstance(proposal, dict) or (
                proposal.get("candidate_id") != candidate_id
                or proposal.get("domain") != domain
                or proposal.get("domain_policy_ready") is not True
                or proposal.get("frame") != {
                    key: intake.get(key) for key in (
                        "played_character_id", "native_revision", "date_raw",
                        "snapshot_id", "revision", "episode_run_id",
                    )
                }
            ):
                raise ValueError("observed domain proposal is not bound to intake")
            if (
                gold_claim != proposal.get("gold_cost_raw")
                or any(claims[key] != _claim_set(proposal.get(key), key)
                       for key in _CLAIM_FIELDS)
            ):
                raise ValueError("assessed shared resource claims differ from observation")
            observed_supply = proposal.get("projected_supply_margin_raw")
            if domain == "war":
                if supply_margin != observed_supply:
                    raise ValueError("assessed war supply differs from observation")
            elif supply_margin != 0:
                raise ValueError("non-war assessment cannot claim route supply")
        elif domain != "war":
            raise ValueError("unknown M5 candidate domain")
        war_slot_claim = (
            _nonnegative(proposal.get("war_slot_claim"), "war_slot_claim")
            if isinstance(proposal, dict) else int(domain == "war")
        )
        minimum_reserve = (
            _nonnegative(proposal.get("minimum_gold_reserve_raw"),
                         "minimum_gold_reserve_raw")
            if isinstance(proposal, dict) else 0
        )
        net = values["benefit_units"] - sum(
            values[key] for key in _VALUE_FIELDS if key != "benefit_units"
        )
        reason = "eligible"
        if net <= 0:
            reason = "nonpositive_net_value"
        elif gold_claim + reserved_gold + max(gold_reserve_raw, minimum_reserve) > gold["raw"]:
            reason = "shared_gold_budget"
        elif supply_margin < 0:
            reason = "projected_supply_deficit"
        elif claims["army_ids"] - usable_armies:
            reason = "army_not_controllable"
        elif any(claims[key] & occupied[key] for key in _CLAIM_FIELDS):
            reason = "existing_commitment_conflict"
        elif war_slot_claim and len(wars) + pending_wars + war_slot_claim > max_active_wars:
            reason = "war_slot_budget"
        evaluated.append({
            "candidate_id": candidate_id, "domain": domain,
            "net_units": net, "reason": reason,
            "value_components": values, "gold_raw": gold_claim,
            "war_slot_claim": war_slot_claim,
            "minimum_gold_reserve_raw": minimum_reserve,
            "projected_supply_margin_units": supply_margin,
            "claims": {key: sorted(claims[key]) for key in _CLAIM_FIELDS},
        })
    eligible = [row for row in evaluated if row["reason"] == "eligible"]
    selected = min(eligible, key=lambda row: (-row["net_units"], row["candidate_id"])) if eligible else None
    return _result(identity, evaluated, selected, "selected" if selected else "wait", len(rows))


def _identity(value: object) -> tuple[int, int, int]:
    if not isinstance(value, dict):
        raise ValueError("M5 frame object required")
    player = value.get("played_character_id")
    if player is None and isinstance(value.get("played_character"), dict):
        player = value["played_character"].get("character_id")
    revision = value.get("native_revision")
    date = value.get("date_raw")
    if any(type(item) is not int or item <= 0 for item in (player, revision)) or type(date) is not int or date < 0:
        raise ValueError("M5 frame identity incomplete")
    return player, revision, date


def _nonnegative(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _claim_set(value: object, name: str) -> set[int] | set[str]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    kind = str if name == "commitment_keys" else int
    if any(type(item) is not kind or (item <= 0 if kind is int else not item) for item in value):
        raise ValueError(f"{name} has an invalid claim")
    result = set(value)
    if len(result) != len(value):
        raise ValueError(f"{name} contains duplicate claims")
    return result


def _result(
    identity: tuple[int, int, int], evaluated: list[dict[str, object]],
    selected: dict[str, object] | None, status: str, total: int,
) -> dict[str, object]:
    return {
        "policy": "g2-m5-assessed-budget-selector-v1", "status": status,
        "played_character_id": identity[0], "native_revision": identity[1],
        "date_raw": identity[2], "assessed_candidate_count": len(evaluated),
        "unassessed_legal_candidate_count": total - len(evaluated),
        "evaluated": evaluated,
        "selected_candidate_id": selected["candidate_id"] if selected else None,
        "selected_step": None, "formal_action_ready": False,
    }
