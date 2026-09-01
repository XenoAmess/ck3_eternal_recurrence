"""Fail-closed Raiktor continue-versus-surrender pairwise policy core.

This module is deliberately independent from the production bridge and action
planner.  It consumes already-normalized evidence certificates and may emit a
pairwise preference, but never a complete war-exit recommendation, action
literal, or automatic-surrender readiness.  White peace is intentionally not
an input to this narrow core, so even ``prefer_surrender_over_continue`` cannot
authorize surrender.  The current G2 checkpoint therefore remains blocked.
"""

from __future__ import annotations

import hashlib
import json
import re

from xar_autoplayer.bridge.raiktor_surrender_six_domain_contract import (
    normalize_raiktor_surrender_six_domain,
)


POLICY_VERSION = "raiktor-continue-vs-surrender-policy-v1"
CAMPAIGN_CERTIFICATE_CONTRACT = "raiktor-campaign-dominance-certificate-v1"

_FRAME_KEYS = {
    "snapshot_id",
    "snapshot_revision",
    "native_revision",
    "date_raw",
    "connection_id",
    "episode_id",
    "ck3_pid",
    "paused",
    "war_id",
    "active_casus_belli_database_index",
    "active_casus_belli_key",
    "primary_attacker_character_id",
    "primary_defender_character_id",
    "claimant_character_id",
}
_CANDIDATE_KEYS = {
    "schema_version",
    "frame",
    "played_character_id",
    "player_is_primary_attacker",
    "player_war_score",
    "war_duration_days",
    "hostage_variant",
    "surrender",
    "same_frame_stable",
}
_SURRENDER_KEYS = {
    "context_constructed",
    "native_validator",
    "available",
    "auto_accept",
    "recipient_response",
}
_RECIPIENT_KEYS = {"decision_status_raw", "would_accept_now"}
_LIMIT_KEYS = {
    "schema_version",
    "profile_id",
    "profile_provenance",
    "profile_production_eligible",
    "maximum_surrender_gold_transfer_raw",
    "maximum_surrender_prestige_loss_raw",
    "maximum_surrender_claims_removed",
    "allow_surrender_favor_hook",
    "maximum_surrender_truce_days",
    "maximum_continue_tail_loss_raw",
    "minimum_switch_margin_raw",
}
_CAMPAIGN_KEYS = {
    "schema_version",
    "contract",
    "status",
    "frame",
    "evaluated_candidate_sha256",
    "evaluated_terms_sha256",
    "evaluated_limits_sha256",
    "producer",
    "completeness",
    "military_state",
    "utility_bounds",
    "hard_budget_breaches",
    "same_frame_stable",
}
_COMPLETENESS_KEYS = {
    "campaign_outcome_distribution_ready",
    "all_reasonable_encounters_evaluated",
    "mobilized_and_reserve_strength_ready",
    "reinforcement_and_siege_eta_ready",
    "finance_endurance_ready",
    "model_risk_included",
    "tail_risk_included",
    "sunk_cost_excluded",
    "all_six_domains_valued",
    "claims_base_valued",
}
_PRODUCER_KEYS = {
    "producer_id",
    "producer_version",
    "source_artifact_sha256",
    "utility_unit",
    "tail_loss_unit",
    "production_live",
}
_MILITARY_KEYS = {
    "safe_objective_path_exists",
    "credible_reinforcement_before_next_decision",
    "continue_tail_loss_upper_raw",
}
_UTILITY_KEYS = {
    "continue_lower_raw",
    "continue_upper_raw",
    "surrender_lower_raw",
    "surrender_upper_raw",
}
_BUDGET_BREACH_KEYS = {
    "continue",
    "surrender",
}
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


def assess_raiktor_continue_vs_surrender(
    candidate_value: object,
    terms_value: object,
    campaign_value: object,
    limits_value: object,
) -> dict[str, object]:
    """Return a deterministic pairwise preference without an action.

    A preference is possible only when all inputs are explicit and bound to the
    same paused frame.  Missing evidence is a normal fail-closed result;
    malformed evidence raises ``ValueError``.  White peace, pending/cooldown
    checks, a typed submit surface, and action-boundary postconditions are all
    outside this independent core, so no result is an action recommendation.
    """

    candidate = _normalize_candidate(candidate_value)
    candidate_frame = candidate["frame"]
    terms = _normalize_terms(terms_value, candidate_frame)
    limits = _normalize_limits(limits_value)

    candidate_blockers = _candidate_blockers(candidate)
    terms_blockers = _terms_blockers(terms)

    candidate_sha256 = _canonical_sha256(candidate)
    terms_sha256 = _canonical_sha256(terms)
    limits_sha256 = _canonical_sha256(limits)
    campaign: dict[str, object] | None = None
    campaign_blockers: list[str] = []
    if campaign_value is None:
        campaign_blockers.append("campaign_dominance_certificate_unavailable")
    else:
        campaign = _normalize_campaign(campaign_value)
        campaign_blockers.extend(
            _campaign_blockers(
                campaign,
                expected_frame=candidate_frame,
                expected_candidate_sha256=candidate_sha256,
                expected_terms_sha256=terms_sha256,
                expected_limits_sha256=limits_sha256,
            )
        )

    evidence_ready = not (
        candidate_blockers or terms_blockers or campaign_blockers
    )
    surrender_blockers: list[str] = []
    continue_blockers: list[str] = []
    surrender_margin_raw: int | None = None
    continue_margin_raw: int | None = None
    surrender_robustly_dominates: bool | None = None
    continue_robustly_dominates: bool | None = None
    pairwise_preference: str | None = None

    if evidence_ready:
        assert campaign is not None
        military = campaign["military_state"]
        utility = campaign["utility_bounds"]
        breaches = campaign["hard_budget_breaches"]
        minimum_margin = limits["minimum_switch_margin_raw"]
        claims_base = terms["claims_base"]["payload"]
        domains = terms["domains"]
        gold = domains["gold"]["payload"]
        prestige = domains["prestige"]["payload"]
        favor = domains["favor_hook"]["payload"]
        truce = domains["truce"]["payload"]

        surrender_margin_raw = (
            utility["surrender_lower_raw"] - utility["continue_upper_raw"]
        )
        continue_margin_raw = (
            utility["continue_lower_raw"] - utility["surrender_upper_raw"]
        )
        surrender_robustly_dominates = surrender_margin_raw >= minimum_margin
        continue_robustly_dominates = continue_margin_raw >= minimum_margin

        if military["safe_objective_path_exists"] is not False:
            surrender_blockers.append("safe_objective_path_still_exists")
        if (
            military["credible_reinforcement_before_next_decision"]
            is not False
        ):
            surrender_blockers.append("credible_reinforcement_still_pending")
        if (
            military["continue_tail_loss_upper_raw"]
            <= limits["maximum_continue_tail_loss_raw"]
        ):
            surrender_blockers.append("continue_tail_loss_budget_not_breached")
        if breaches["surrender"]:
            surrender_blockers.append("surrender_hard_budget_breached")
        if (
            gold["actual_transfer"]["value"]["raw"]
            > limits["maximum_surrender_gold_transfer_raw"]
        ):
            surrender_blockers.append("surrender_gold_budget_breached")
        if (
            -prestige["attacker_prestige_delta"]["value"]["raw"]
            > limits["maximum_surrender_prestige_loss_raw"]
        ):
            surrender_blockers.append("surrender_prestige_budget_breached")
        if (
            len(claims_base["target_title_ids"])
            > limits["maximum_surrender_claims_removed"]
        ):
            surrender_blockers.append("surrender_claim_budget_breached")
        if (
            favor["will_apply"] is True
            and limits["allow_surrender_favor_hook"] is not True
        ):
            surrender_blockers.append("surrender_favor_hook_budget_breached")
        if (
            truce["evaluated_days"]
            > limits["maximum_surrender_truce_days"]
        ):
            surrender_blockers.append("surrender_truce_budget_breached")
        if not surrender_robustly_dominates:
            surrender_blockers.append("surrender_utility_margin_not_met")

        if military["safe_objective_path_exists"] is not True:
            continue_blockers.append("safe_objective_path_not_proven")
        if (
            military["continue_tail_loss_upper_raw"]
            > limits["maximum_continue_tail_loss_raw"]
        ):
            continue_blockers.append("continue_tail_loss_budget_breached")
        if breaches["continue"]:
            continue_blockers.append("continue_hard_budget_breached")
        if not continue_robustly_dominates:
            continue_blockers.append("continue_utility_margin_not_met")

        if not surrender_blockers:
            pairwise_preference = "prefer_surrender_over_continue"
        elif not continue_blockers:
            pairwise_preference = "prefer_continue_over_surrender"

    status = "evidence_required"
    if evidence_ready:
        status = pairwise_preference or "pairwise_underdetermined"

    return {
        "policy_version": POLICY_VERSION,
        "status": status,
        "pairwise_evidence_ready": evidence_ready,
        "surrender_candidate_ready": not candidate_blockers
        and not terms_blockers,
        "campaign_evidence_ready": not campaign_blockers,
        "pairwise_preference_ready": pairwise_preference is not None,
        "pairwise_preference": pairwise_preference,
        "production_pairwise_ready": (
            evidence_ready
            and campaign is not None
            and campaign["producer"]["production_live"] is True
            and limits["profile_production_eligible"] is True
        ),
        "full_exit_decision_ready": False,
        "white_peace_evaluated": False,
        "recommendation_ready": False,
        "suggested_action": None,
        "automatic_surrender_ready": False,
        "action_literal": None,
        "native_ai_equivalent": False,
        "semantic_optimal": False,
        "candidate_sha256": candidate_sha256,
        "terms_sha256": terms_sha256,
        "limits_sha256": limits_sha256,
        "campaign_sha256": (
            _canonical_sha256(campaign) if campaign is not None else None
        ),
        "surrender_margin_raw": surrender_margin_raw,
        "continue_margin_raw": continue_margin_raw,
        "surrender_robustly_dominates": surrender_robustly_dominates,
        "continue_robustly_dominates": continue_robustly_dominates,
        "candidate_blockers": candidate_blockers,
        "terms_blockers": terms_blockers,
        "campaign_blockers": campaign_blockers,
        "surrender_blockers": surrender_blockers,
        "continue_blockers": continue_blockers,
        "explicit_boundaries": [
            "pairwise_preference_only_not_full_exit_decision",
            "white_peace_not_evaluated",
            "no_recommendation_or_command",
            "pending_submission_and_cooldown_not_evaluated",
            "action_boundary_postconditions_not_evaluated",
            "generic_war_bound_current_is_not_source_attribution",
            "generic_war_bound_current_is_not_proven_loss",
            "score_and_duration_are_model_inputs_not_surrender_validators",
            "native_ai_equivalent_false",
            "semantic_optimal_false",
        ],
    }


def canonical_policy_input_sha256(value: object) -> str:
    """Expose the exact canonical hash used by campaign certificates."""

    return _canonical_sha256(value)


def _normalize_candidate(value: object) -> dict[str, object]:
    item = _exact_dict(value, _CANDIDATE_KEYS, "candidate")
    if item["schema_version"] != 1:
        raise ValueError("candidate schema_version must be 1")
    frame = _normalize_frame(item["frame"], "candidate.frame")
    surrender = _exact_dict(item["surrender"], _SURRENDER_KEYS, "surrender")
    response = _exact_dict(
        surrender["recipient_response"], _RECIPIENT_KEYS, "recipient_response"
    )
    decision_status = _nonnegative_int32(
        response["decision_status_raw"], "decision_status_raw"
    )
    if decision_status > 3:
        raise ValueError("decision_status_raw is outside the frozen enum")
    war_score = _signed_int32(item["player_war_score"], "player_war_score")
    if war_score < -100 or war_score > 100:
        raise ValueError("player_war_score is outside -100..100")
    duration = _nonnegative_int32(
        item["war_duration_days"], "war_duration_days"
    )
    hostage_variant = item["hostage_variant"]
    if not isinstance(hostage_variant, str) or not hostage_variant:
        raise ValueError("hostage_variant must be a nonempty string")
    return {
        "schema_version": 1,
        "frame": frame,
        "played_character_id": _full_id(
            item["played_character_id"], "played_character_id"
        ),
        "player_is_primary_attacker": _strict_bool(
            item["player_is_primary_attacker"], "player_is_primary_attacker"
        ),
        "player_war_score": war_score,
        "war_duration_days": duration,
        "hostage_variant": hostage_variant,
        "surrender": {
            "context_constructed": _strict_bool(
                surrender["context_constructed"], "context_constructed"
            ),
            "native_validator": _strict_bool(
                surrender["native_validator"], "native_validator"
            ),
            "available": _strict_bool(surrender["available"], "available"),
            "auto_accept": _strict_bool(
                surrender["auto_accept"], "auto_accept"
            ),
            "recipient_response": {
                "decision_status_raw": decision_status,
                "would_accept_now": _strict_bool(
                    response["would_accept_now"], "would_accept_now"
                ),
            },
        },
        "same_frame_stable": _strict_bool(
            item["same_frame_stable"], "candidate.same_frame_stable"
        ),
    }


def _candidate_blockers(candidate: dict[str, object]) -> list[str]:
    frame = candidate["frame"]
    surrender = candidate["surrender"]
    response = surrender["recipient_response"]
    blockers: list[str] = []
    if frame["paused"] is not True:
        blockers.append("paused_frame_required")
    if frame["active_casus_belli_key"] != "raiktor_claim_cb":
        blockers.append("exact_raiktor_claim_cb_required")
    if candidate["played_character_id"] != frame["primary_attacker_character_id"]:
        blockers.append("played_character_must_be_primary_attacker")
    if candidate["player_is_primary_attacker"] is not True:
        blockers.append("player_primary_attacker_required")
    if candidate["hostage_variant"] != "none":
        blockers.append("hostage_variant_not_supported")
    if candidate["same_frame_stable"] is not True:
        blockers.append("candidate_same_frame_stability_required")
    for key, reason in (
        ("context_constructed", "surrender_context_not_constructed"),
        ("native_validator", "surrender_native_validator_false"),
        ("available", "surrender_not_available"),
        ("auto_accept", "surrender_auto_accept_not_proven"),
    ):
        if surrender[key] is not True:
            blockers.append(reason)
    if (
        response["would_accept_now"] is not True
        or response["decision_status_raw"] not in {0, 1}
    ):
        blockers.append("typed_recipient_acceptance_not_proven")
    return blockers


def _normalize_terms(
    value: object, candidate_frame: dict[str, object]
) -> dict[str, object]:
    return normalize_raiktor_surrender_six_domain(
        value,
        expected_war_id=candidate_frame["war_id"],
        expected_snapshot_revision=candidate_frame["snapshot_revision"],
        expected_native_revision=candidate_frame["native_revision"],
        expected_date_raw=candidate_frame["date_raw"],
        expected_attacker_character_id=candidate_frame[
            "primary_attacker_character_id"
        ],
        expected_defender_character_id=candidate_frame[
            "primary_defender_character_id"
        ],
        expected_claimant_character_id=candidate_frame[
            "claimant_character_id"
        ],
    )


def _terms_blockers(terms: dict[str, object]) -> list[str]:
    blockers: list[str] = []
    frame = terms["frame"]
    readiness = terms["readiness"]
    if frame["paused"] is not True:
        blockers.append("terms_paused_frame_required")
    if frame["active_casus_belli_key"] != "raiktor_claim_cb":
        blockers.append("terms_exact_raiktor_claim_cb_required")
    if terms["status"] != "complete":
        blockers.append("six_domain_terms_incomplete")
    if readiness["action_terms_ready"] is not True:
        blockers.append("six_domain_action_terms_not_ready")
    return blockers


def _normalize_limits(value: object) -> dict[str, object]:
    item = _exact_dict(value, _LIMIT_KEYS, "limits")
    if item["schema_version"] != 1:
        raise ValueError("limits schema_version must be 1")
    profile = item["profile_id"]
    if not isinstance(profile, str) or not profile.strip():
        raise ValueError("profile_id must be a nonempty string")
    provenance = _nonempty_string(
        item["profile_provenance"], "profile_provenance"
    )
    production_eligible = _strict_bool(
        item["profile_production_eligible"], "profile_production_eligible"
    )
    minimum_margin = _positive_int64(
        item["minimum_switch_margin_raw"], "minimum_switch_margin_raw"
    )
    return {
        "schema_version": 1,
        "profile_id": profile,
        "profile_provenance": provenance,
        "profile_production_eligible": production_eligible,
        "maximum_surrender_gold_transfer_raw": _nonnegative_int64(
            item["maximum_surrender_gold_transfer_raw"],
            "maximum_surrender_gold_transfer_raw",
        ),
        "maximum_surrender_prestige_loss_raw": _nonnegative_int64(
            item["maximum_surrender_prestige_loss_raw"],
            "maximum_surrender_prestige_loss_raw",
        ),
        "maximum_surrender_claims_removed": _nonnegative_int32(
            item["maximum_surrender_claims_removed"],
            "maximum_surrender_claims_removed",
        ),
        "allow_surrender_favor_hook": _strict_bool(
            item["allow_surrender_favor_hook"],
            "allow_surrender_favor_hook",
        ),
        "maximum_surrender_truce_days": _nonnegative_int32(
            item["maximum_surrender_truce_days"],
            "maximum_surrender_truce_days",
        ),
        "maximum_continue_tail_loss_raw": _nonnegative_int64(
            item["maximum_continue_tail_loss_raw"],
            "maximum_continue_tail_loss_raw",
        ),
        "minimum_switch_margin_raw": minimum_margin,
    }


def _normalize_campaign(value: object) -> dict[str, object]:
    item = _exact_dict(value, _CAMPAIGN_KEYS, "campaign")
    if item["schema_version"] != 1:
        raise ValueError("campaign schema_version must be 1")
    if item["contract"] != CAMPAIGN_CERTIFICATE_CONTRACT:
        raise ValueError("campaign certificate contract drifted")
    if item["status"] not in {"complete", "incomplete"}:
        raise ValueError("campaign status must be complete or incomplete")
    completeness_item = _exact_dict(
        item["completeness"], _COMPLETENESS_KEYS, "campaign.completeness"
    )
    completeness = {
        key: _strict_bool(completeness_item[key], f"completeness.{key}")
        for key in sorted(_COMPLETENESS_KEYS)
    }
    military_item = _exact_dict(
        item["military_state"], _MILITARY_KEYS, "campaign.military_state"
    )
    military = {
        "safe_objective_path_exists": _strict_bool(
            military_item["safe_objective_path_exists"],
            "safe_objective_path_exists",
        ),
        "credible_reinforcement_before_next_decision": _strict_bool(
            military_item["credible_reinforcement_before_next_decision"],
            "credible_reinforcement_before_next_decision",
        ),
        "continue_tail_loss_upper_raw": _nonnegative_int64(
            military_item["continue_tail_loss_upper_raw"],
            "continue_tail_loss_upper_raw",
        ),
    }
    utility_item = _exact_dict(
        item["utility_bounds"], _UTILITY_KEYS, "campaign.utility_bounds"
    )
    utility = {
        key: _signed_int64(utility_item[key], f"utility_bounds.{key}")
        for key in sorted(_UTILITY_KEYS)
    }
    if (
        utility["continue_lower_raw"] > utility["continue_upper_raw"]
        or utility["surrender_lower_raw"] > utility["surrender_upper_raw"]
    ):
        raise ValueError("campaign utility interval is inverted")
    breach_item = _exact_dict(
        item["hard_budget_breaches"],
        _BUDGET_BREACH_KEYS,
        "campaign.hard_budget_breaches",
    )
    breaches = {
        key: _string_list(breach_item[key], f"hard_budget_breaches.{key}")
        for key in sorted(_BUDGET_BREACH_KEYS)
    }
    producer_item = _exact_dict(
        item["producer"], _PRODUCER_KEYS, "campaign.producer"
    )
    producer = {
        "producer_id": _nonempty_string(
            producer_item["producer_id"], "producer.producer_id"
        ),
        "producer_version": _nonempty_string(
            producer_item["producer_version"], "producer.producer_version"
        ),
        "source_artifact_sha256": _sha256(
            producer_item["source_artifact_sha256"],
            "producer.source_artifact_sha256",
        ),
        "utility_unit": _nonempty_string(
            producer_item["utility_unit"], "producer.utility_unit"
        ),
        "tail_loss_unit": _nonempty_string(
            producer_item["tail_loss_unit"], "producer.tail_loss_unit"
        ),
        "production_live": _strict_bool(
            producer_item["production_live"], "producer.production_live"
        ),
    }
    if producer["utility_unit"] != "owner_utility_q100000":
        raise ValueError("campaign utility unit drifted")
    if producer["tail_loss_unit"] != "owner_loss_q100000":
        raise ValueError("campaign tail-loss unit drifted")
    return {
        "schema_version": 1,
        "contract": CAMPAIGN_CERTIFICATE_CONTRACT,
        "status": item["status"],
        "frame": _normalize_frame(item["frame"], "campaign.frame"),
        "evaluated_candidate_sha256": _sha256(
            item["evaluated_candidate_sha256"],
            "evaluated_candidate_sha256",
        ),
        "evaluated_terms_sha256": _sha256(
            item["evaluated_terms_sha256"], "evaluated_terms_sha256"
        ),
        "evaluated_limits_sha256": _sha256(
            item["evaluated_limits_sha256"], "evaluated_limits_sha256"
        ),
        "producer": producer,
        "completeness": completeness,
        "military_state": military,
        "utility_bounds": utility,
        "hard_budget_breaches": breaches,
        "same_frame_stable": _strict_bool(
            item["same_frame_stable"], "campaign.same_frame_stable"
        ),
    }


def _campaign_blockers(
    campaign: dict[str, object],
    *,
    expected_frame: dict[str, object],
    expected_candidate_sha256: str,
    expected_terms_sha256: str,
    expected_limits_sha256: str,
) -> list[str]:
    blockers: list[str] = []
    if campaign["status"] != "complete":
        blockers.append("campaign_dominance_certificate_incomplete")
    if campaign["frame"] != expected_frame:
        blockers.append("campaign_frame_mismatch")
    if campaign["evaluated_candidate_sha256"] != expected_candidate_sha256:
        blockers.append("campaign_candidate_fingerprint_mismatch")
    if campaign["evaluated_terms_sha256"] != expected_terms_sha256:
        blockers.append("campaign_terms_fingerprint_mismatch")
    if campaign["evaluated_limits_sha256"] != expected_limits_sha256:
        blockers.append("campaign_limits_fingerprint_mismatch")
    if campaign["same_frame_stable"] is not True:
        blockers.append("campaign_same_frame_stability_required")
    for key in sorted(_COMPLETENESS_KEYS):
        if campaign["completeness"][key] is not True:
            blockers.append(f"{key}_required")
    return blockers


def _normalize_frame(value: object, name: str) -> dict[str, object]:
    frame = _exact_dict(value, _FRAME_KEYS, name)
    normalized = {
        "snapshot_id": _nonempty_string(
            frame["snapshot_id"], f"{name}.snapshot_id"
        ),
        "snapshot_revision": _positive_uint64(
            frame["snapshot_revision"], f"{name}.snapshot_revision"
        ),
        "native_revision": _positive_uint64(
            frame["native_revision"], f"{name}.native_revision"
        ),
        "date_raw": _signed_int32(frame["date_raw"], f"{name}.date_raw"),
        "connection_id": _nonempty_string(
            frame["connection_id"], f"{name}.connection_id"
        ),
        "episode_id": _nonempty_string(
            frame["episode_id"], f"{name}.episode_id"
        ),
        "ck3_pid": _positive_int32(frame["ck3_pid"], f"{name}.ck3_pid"),
        "paused": _strict_bool(frame["paused"], f"{name}.paused"),
        "war_id": _full_id(frame["war_id"], f"{name}.war_id"),
        "active_casus_belli_database_index": _nonnegative_int32(
            frame["active_casus_belli_database_index"],
            f"{name}.active_casus_belli_database_index",
        ),
        "active_casus_belli_key": _nonempty_string(
            frame["active_casus_belli_key"], f"{name}.active_casus_belli_key"
        ),
        "primary_attacker_character_id": _full_id(
            frame["primary_attacker_character_id"],
            f"{name}.primary_attacker_character_id",
        ),
        "primary_defender_character_id": _full_id(
            frame["primary_defender_character_id"],
            f"{name}.primary_defender_character_id",
        ),
        "claimant_character_id": _full_id(
            frame["claimant_character_id"], f"{name}.claimant_character_id"
        ),
    }
    if (
        normalized["primary_attacker_character_id"]
        == normalized["primary_defender_character_id"]
    ):
        raise ValueError(f"{name} primary roles cannot be the same character")
    return normalized


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _exact_dict(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} has a malformed schema")
    return value


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _string_list(value: object, name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    result = [_nonempty_string(item, f"{name}[]") for item in value]
    if len(result) != len(set(result)):
        raise ValueError(f"{name} contains duplicates")
    return result


def _positive_unique_ids(
    value: object, name: str, *, require_nonempty: bool
) -> list[int]:
    if not isinstance(value, list) or (require_nonempty and not value):
        raise ValueError(f"{name} must be a nonempty list")
    result = [_positive_int32(item, f"{name}[]") for item in value]
    if len(result) != len(set(result)):
        raise ValueError(f"{name} contains duplicates")
    return result


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be an uppercase SHA-256")
    return value


def _full_id(value: object, name: str) -> int:
    result = _signed_int32(value, name)
    if result == -1:
        raise ValueError(f"{name} is the invalid sentinel")
    return result


def _positive_int32(value: object, name: str) -> int:
    result = _signed_int32(value, name)
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _nonnegative_int32(value: object, name: str) -> int:
    result = _signed_int32(value, name)
    if result < 0:
        raise ValueError(f"{name} must be nonnegative")
    return result


def _signed_int32(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < -(2**31) or value > 2**31 - 1:
        raise ValueError(f"{name} is outside signed int32")
    return value


def _positive_int64(value: object, name: str) -> int:
    result = _signed_int64(value, name)
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _nonnegative_int64(value: object, name: str) -> int:
    result = _signed_int64(value, name)
    if result < 0:
        raise ValueError(f"{name} must be nonnegative")
    return result


def _signed_int64(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < -(2**63) or value > 2**63 - 1:
        raise ValueError(f"{name} is outside signed int64")
    return value


def _positive_uint64(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value <= 0 or value > 2**64 - 1:
        raise ValueError(f"{name} is outside positive uint64")
    return value


__all__ = [
    "CAMPAIGN_CERTIFICATE_CONTRACT",
    "POLICY_VERSION",
    "assess_raiktor_continue_vs_surrender",
    "canonical_policy_input_sha256",
]
