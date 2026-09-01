"""Conservative, side-effect-free Raiktor three-way exit policy core.

The core composes the existing six-domain surrender contract and the existing
continue-versus-surrender pairwise evaluator with two explicit inputs:

* an owner-authored budget profile; and
* a same-frame white-peace comparison certificate.

It can publish a static outcome recommendation.  It deliberately cannot emit
an action literal, advertise a submit capability, or prove an action applied.
Missing real providers are returned as typed evidence blockers; no score,
duration, authored troop count, or fixture threshold is substituted for them.
"""

from __future__ import annotations

import re

from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    assess_raiktor_continue_vs_surrender,
    canonical_policy_input_sha256,
)


POLICY_VERSION = "raiktor-three-way-exit-policy-v1"
OWNER_BUDGET_PROFILE_CONTRACT = "raiktor-owner-budget-profile-v1"
WHITE_PEACE_COMPARISON_CONTRACT = (
    "raiktor-white-peace-comparison-certificate-v1"
)

CAMPAIGN_PROVIDER = "raiktor-campaign-dominance-certificate-provider-v1"
OWNER_BUDGET_PROVIDER = "raiktor-owner-budget-profile-provider-v1"
WHITE_PEACE_PROVIDER = "raiktor-white-peace-comparison-provider-v1"

_OWNER_KEYS = {
    "schema_version",
    "contract",
    "status",
    "profile_id",
    "profile_provenance",
    "profile_source_sha256",
    "profile_production_eligible",
    "pairwise_limits",
    "white_peace_limits",
}
_WHITE_LIMIT_KEYS = {
    "maximum_gold_transfer_raw",
    "maximum_prestige_loss_raw",
    "maximum_claims_removed",
    "allow_favor_hook",
    "maximum_truce_days",
}
_PAIRWISE_LIMIT_KEYS = {
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
_WHITE_KEYS = {
    "schema_version",
    "contract",
    "status",
    "frame",
    "evaluated_candidate_sha256",
    "evaluated_surrender_terms_sha256",
    "evaluated_campaign_sha256",
    "evaluated_owner_budget_sha256",
    "producer",
    "completeness",
    "option",
    "terms",
    "utility_bounds",
    "hard_budget_breaches",
    "same_frame_stable",
}
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
_PRODUCER_KEYS = {
    "producer_id",
    "producer_version",
    "source_artifact_sha256",
    "utility_unit",
    "production_live",
}
_COMPLETENESS_KEYS = {
    "final_recipient_response_ready",
    "claim_disposition_ready",
    "gold_transfer_ready",
    "prestige_delta_ready",
    "truce_ready",
    "prisoner_release_ready",
    "favor_hook_ready",
    "utility_bounds_ready",
    "model_risk_included",
}
_OPTION_KEYS = {
    "context_constructed",
    "native_validator",
    "available",
    "auto_accept",
    "recipient_response",
}
_RECIPIENT_KEYS = {"decision_status_raw", "would_accept_now"}
_TERMS_KEYS = {
    "declared_target_title_ids",
    "retained_target_title_ids",
    "claim_disposition",
    "title_holder_change_count",
    "primary_gold_transfer_raw",
    "attacker_prestige_delta_raw",
    "truce_evaluated_days",
    "prisoner_release_pairs",
    "favor_hook_will_apply",
    "hostage_variant",
}
_PAIR_KEYS = {"jailer_character_id", "prisoner_character_id"}
_UTILITY_KEYS = {"white_peace_lower_raw", "white_peace_upper_raw"}
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


def assess_raiktor_three_way_exit(
    candidate_value: object,
    surrender_terms_value: object,
    campaign_value: object | None,
    owner_budget_value: object | None,
    white_peace_value: object | None,
) -> dict[str, object]:
    """Assess continue, white peace, and surrender without authorizing action.

    ``None`` is the canonical representation of a provider which has not yet
    supplied evidence.  A malformed value on an evaluable dependency path
    raises ``ValueError``; an absent prerequisite yields a deterministic typed
    RED result without guessing a replacement.
    """

    provider_blockers: list[dict[str, str]] = []
    if campaign_value is None:
        provider_blockers.append(
            _missing_provider(
                CAMPAIGN_PROVIDER,
                "campaign_dominance_certificate_unavailable",
            )
        )
    if owner_budget_value is None:
        provider_blockers.append(
            _missing_provider(
                OWNER_BUDGET_PROVIDER,
                "owner_budget_profile_unavailable",
            )
        )
    if white_peace_value is None:
        provider_blockers.append(
            _missing_provider(
                WHITE_PEACE_PROVIDER,
                "white_peace_comparison_certificate_unavailable",
            )
        )

    if owner_budget_value is None:
        return _red_result(
            provider_blockers=provider_blockers,
            owner_blockers=["owner_budget_profile_unavailable"],
        )

    owner = _normalize_owner_budget(owner_budget_value)
    owner_blockers = _owner_blockers(owner)
    if owner_blockers:
        return _red_result(
            provider_blockers=provider_blockers,
            owner_blockers=owner_blockers,
            owner_budget_sha256=canonical_policy_input_sha256(owner),
        )

    pairwise = assess_raiktor_continue_vs_surrender(
        candidate_value,
        surrender_terms_value,
        campaign_value,
        owner["pairwise_limits"],
    )
    owner_sha256 = canonical_policy_input_sha256(owner)

    if campaign_value is None or white_peace_value is None:
        return _red_result(
            provider_blockers=provider_blockers,
            owner_blockers=[],
            owner_budget_sha256=owner_sha256,
            pairwise=pairwise,
        )

    white = _normalize_white_peace(white_peace_value)
    white_blockers = _white_certificate_blockers(
        white,
        expected_frame=_candidate_frame(candidate_value),
        expected_candidate_sha256=pairwise["candidate_sha256"],
        expected_terms_sha256=pairwise["terms_sha256"],
        expected_campaign_sha256=pairwise["campaign_sha256"],
        expected_owner_sha256=owner_sha256,
        expected_target_title_ids=_surrender_target_title_ids(
            surrender_terms_value
        ),
    )

    evidence_ready = (
        pairwise["pairwise_evidence_ready"] is True and not white_blockers
    )
    white_budget_blockers: list[str] = []
    recommendation: str | None = None
    margins: dict[str, int | None] = {
        "continue": None,
        "white_peace": None,
        "surrender": None,
    }
    eligible_candidates: list[str] = []

    if evidence_ready:
        white_budget_blockers = _white_budget_blockers(white, owner)
        campaign = campaign_value
        assert isinstance(campaign, dict)
        utility = campaign["utility_bounds"]
        white_utility = white["utility_bounds"]
        intervals = {
            "continue": (
                utility["continue_lower_raw"],
                utility["continue_upper_raw"],
            ),
            "white_peace": (
                white_utility["white_peace_lower_raw"],
                white_utility["white_peace_upper_raw"],
            ),
            "surrender": (
                utility["surrender_lower_raw"],
                utility["surrender_upper_raw"],
            ),
        }
        non_utility_blockers = {
            "continue": [
                item
                for item in pairwise["continue_blockers"]
                if item != "continue_utility_margin_not_met"
            ],
            "white_peace": white_budget_blockers,
            "surrender": [
                item
                for item in pairwise["surrender_blockers"]
                if item != "surrender_utility_margin_not_met"
            ],
        }
        eligible_candidates = [
            name for name in intervals if not non_utility_blockers[name]
        ]
        minimum_margin = owner["pairwise_limits"][
            "minimum_switch_margin_raw"
        ]
        for name in eligible_candidates:
            other_uppers = [
                intervals[other][1]
                for other in eligible_candidates
                if other != name
            ]
            margins[name] = (
                intervals[name][0] - max(other_uppers)
                if other_uppers
                else minimum_margin
            )
        winners = [
            name
            for name in eligible_candidates
            if margins[name] is not None and margins[name] >= minimum_margin
        ]
        if len(winners) == 1:
            recommendation = winners[0]

    status = "evidence_required"
    if evidence_ready:
        status = (
            "static_recommendation_available"
            if recommendation is not None
            else "three_way_underdetermined"
        )

    return {
        "policy_version": POLICY_VERSION,
        "status": status,
        "three_way_evidence_ready": evidence_ready,
        "three_way_comparison_ready": evidence_ready,
        "static_recommendation_ready": recommendation is not None,
        "recommended_outcome": recommendation,
        # This package has no public wire or paused artifact and therefore
        # cannot promote even fully shaped inputs to production readiness.
        "production_recommendation_ready": False,
        "full_exit_decision_ready": False,
        "action_ready": False,
        "suggested_action": None,
        "action_literal": None,
        "automatic_surrender_ready": False,
        "native_ai_equivalent": False,
        "semantic_optimal": False,
        "pairwise": pairwise,
        "owner_budget_sha256": owner_sha256,
        "white_peace_sha256": canonical_policy_input_sha256(white),
        "provider_blockers": provider_blockers,
        "owner_blockers": owner_blockers,
        "white_peace_blockers": white_blockers,
        "white_peace_budget_blockers": white_budget_blockers,
        "eligible_candidates": eligible_candidates,
        "robust_margin_raw": margins,
        "explicit_boundaries": _explicit_boundaries(),
    }


def _red_result(
    *,
    provider_blockers: list[dict[str, str]],
    owner_blockers: list[str],
    owner_budget_sha256: str | None = None,
    pairwise: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "policy_version": POLICY_VERSION,
        "status": "evidence_required",
        "three_way_evidence_ready": False,
        "three_way_comparison_ready": False,
        "static_recommendation_ready": False,
        "recommended_outcome": None,
        "production_recommendation_ready": False,
        "full_exit_decision_ready": False,
        "action_ready": False,
        "suggested_action": None,
        "action_literal": None,
        "automatic_surrender_ready": False,
        "native_ai_equivalent": False,
        "semantic_optimal": False,
        "pairwise": pairwise,
        "owner_budget_sha256": owner_budget_sha256,
        "white_peace_sha256": None,
        "provider_blockers": provider_blockers,
        "owner_blockers": owner_blockers,
        "white_peace_blockers": [],
        "white_peace_budget_blockers": [],
        "eligible_candidates": [],
        "robust_margin_raw": {
            "continue": None,
            "white_peace": None,
            "surrender": None,
        },
        "explicit_boundaries": _explicit_boundaries(),
    }


def _explicit_boundaries() -> list[str]:
    return [
        "static_outcome_recommendation_only",
        "no_action_literal_or_submit_capability",
        "pending_submission_and_cooldown_not_evaluated",
        "action_boundary_postconditions_not_evaluated",
        "generic_war_bound_current_is_not_source_attribution",
        "generic_war_bound_current_is_not_proven_loss",
        "authored_3000_is_not_measured_pre_soldiers_or_loss",
        "six_domain_v1_does_not_carry_connection_episode_or_pid",
        "static_core_never_promotes_provider_flags_to_production_live",
        "score_and_duration_are_model_inputs_not_exit_reasons",
        "native_ai_equivalent_false",
        "semantic_optimal_false",
    ]


def _missing_provider(provider: str, reason: str) -> dict[str, str]:
    return {"provider": provider, "status": "unavailable", "reason": reason}


def _normalize_owner_budget(value: object) -> dict[str, object]:
    item = _exact_dict(value, _OWNER_KEYS, "owner_budget")
    if item["schema_version"] != 1:
        raise ValueError("owner budget schema_version must be 1")
    if item["contract"] != OWNER_BUDGET_PROFILE_CONTRACT:
        raise ValueError("owner budget contract drifted")
    if item["status"] not in {"complete", "incomplete"}:
        raise ValueError("owner budget status must be complete or incomplete")
    profile_id = _nonempty_string(item["profile_id"], "profile_id")
    provenance = _nonempty_string(
        item["profile_provenance"], "profile_provenance"
    )
    production_eligible = _strict_bool(
        item["profile_production_eligible"], "profile_production_eligible"
    )
    pairwise = _exact_dict(
        item["pairwise_limits"], _PAIRWISE_LIMIT_KEYS, "pairwise_limits"
    )
    if (
        pairwise["schema_version"] != 1
        or pairwise["profile_id"] != profile_id
        or pairwise["profile_provenance"] != provenance
        or pairwise["profile_production_eligible"] != production_eligible
    ):
        raise ValueError("owner budget and pairwise profile identity drifted")
    white_item = _exact_dict(
        item["white_peace_limits"],
        _WHITE_LIMIT_KEYS,
        "white_peace_limits",
    )
    white = {
        "maximum_gold_transfer_raw": _nonnegative_int64(
            white_item["maximum_gold_transfer_raw"],
            "maximum_gold_transfer_raw",
        ),
        "maximum_prestige_loss_raw": _nonnegative_int64(
            white_item["maximum_prestige_loss_raw"],
            "maximum_prestige_loss_raw",
        ),
        "maximum_claims_removed": _nonnegative_int32(
            white_item["maximum_claims_removed"],
            "maximum_claims_removed",
        ),
        "allow_favor_hook": _strict_bool(
            white_item["allow_favor_hook"], "allow_favor_hook"
        ),
        "maximum_truce_days": _nonnegative_int32(
            white_item["maximum_truce_days"], "maximum_truce_days"
        ),
    }
    return {
        "schema_version": 1,
        "contract": OWNER_BUDGET_PROFILE_CONTRACT,
        "status": item["status"],
        "profile_id": profile_id,
        "profile_provenance": provenance,
        "profile_source_sha256": _sha256(
            item["profile_source_sha256"], "profile_source_sha256"
        ),
        "profile_production_eligible": production_eligible,
        "pairwise_limits": dict(pairwise),
        "white_peace_limits": white,
    }


def _owner_blockers(owner: dict[str, object]) -> list[str]:
    return (
        []
        if owner["status"] == "complete"
        else ["owner_budget_profile_incomplete"]
    )


def _normalize_white_peace(value: object) -> dict[str, object]:
    item = _exact_dict(value, _WHITE_KEYS, "white_peace")
    if item["schema_version"] != 1:
        raise ValueError("white-peace schema_version must be 1")
    if item["contract"] != WHITE_PEACE_COMPARISON_CONTRACT:
        raise ValueError("white-peace comparison contract drifted")
    if item["status"] not in {"complete", "incomplete"}:
        raise ValueError("white-peace status must be complete or incomplete")

    producer_item = _exact_dict(
        item["producer"], _PRODUCER_KEYS, "white_peace.producer"
    )
    producer = {
        "producer_id": _nonempty_string(
            producer_item["producer_id"], "producer_id"
        ),
        "producer_version": _nonempty_string(
            producer_item["producer_version"], "producer_version"
        ),
        "source_artifact_sha256": _sha256(
            producer_item["source_artifact_sha256"],
            "source_artifact_sha256",
        ),
        "utility_unit": _nonempty_string(
            producer_item["utility_unit"], "utility_unit"
        ),
        "production_live": _strict_bool(
            producer_item["production_live"], "producer.production_live"
        ),
    }
    if producer["utility_unit"] != "owner_utility_q100000":
        raise ValueError("white-peace utility unit drifted")

    completeness_item = _exact_dict(
        item["completeness"],
        _COMPLETENESS_KEYS,
        "white_peace.completeness",
    )
    completeness = {
        key: _strict_bool(completeness_item[key], f"completeness.{key}")
        for key in sorted(_COMPLETENESS_KEYS)
    }

    option_item = _exact_dict(item["option"], _OPTION_KEYS, "white_peace.option")
    response_item = _exact_dict(
        option_item["recipient_response"],
        _RECIPIENT_KEYS,
        "white_peace.recipient_response",
    )
    decision_status = _nonnegative_int32(
        response_item["decision_status_raw"], "decision_status_raw"
    )
    if decision_status > 3:
        raise ValueError("white-peace decision status is outside frozen enum")
    option = {
        "context_constructed": _strict_bool(
            option_item["context_constructed"], "context_constructed"
        ),
        "native_validator": _strict_bool(
            option_item["native_validator"], "native_validator"
        ),
        "available": _strict_bool(option_item["available"], "available"),
        "auto_accept": _strict_bool(
            option_item["auto_accept"], "auto_accept"
        ),
        "recipient_response": {
            "decision_status_raw": decision_status,
            "would_accept_now": _strict_bool(
                response_item["would_accept_now"], "would_accept_now"
            ),
        },
    }

    terms_item = _exact_dict(item["terms"], _TERMS_KEYS, "white_peace.terms")
    declared = _id_list(
        terms_item["declared_target_title_ids"],
        "declared_target_title_ids",
        require_nonempty=True,
    )
    retained = _id_list(
        terms_item["retained_target_title_ids"],
        "retained_target_title_ids",
        require_nonempty=True,
    )
    pairs_value = terms_item["prisoner_release_pairs"]
    if not isinstance(pairs_value, list):
        raise ValueError("prisoner_release_pairs must be a list")
    pairs: list[dict[str, int]] = []
    seen_pairs: set[tuple[int, int]] = set()
    for index, pair_value in enumerate(pairs_value):
        pair = _exact_dict(pair_value, _PAIR_KEYS, f"prisoner_pairs[{index}]")
        jailer = _full_id(pair["jailer_character_id"], "jailer_character_id")
        prisoner = _full_id(
            pair["prisoner_character_id"], "prisoner_character_id"
        )
        if jailer == prisoner or (jailer, prisoner) in seen_pairs:
            raise ValueError("white-peace prisoner release pairs drifted")
        seen_pairs.add((jailer, prisoner))
        pairs.append(
            {
                "jailer_character_id": jailer,
                "prisoner_character_id": prisoner,
            }
        )
    terms = {
        "declared_target_title_ids": declared,
        "retained_target_title_ids": retained,
        "claim_disposition": _nonempty_string(
            terms_item["claim_disposition"], "claim_disposition"
        ),
        "title_holder_change_count": _nonnegative_int32(
            terms_item["title_holder_change_count"],
            "title_holder_change_count",
        ),
        "primary_gold_transfer_raw": _nonnegative_int64(
            terms_item["primary_gold_transfer_raw"],
            "primary_gold_transfer_raw",
        ),
        "attacker_prestige_delta_raw": _signed_int64(
            terms_item["attacker_prestige_delta_raw"],
            "attacker_prestige_delta_raw",
        ),
        "truce_evaluated_days": _nonnegative_int32(
            terms_item["truce_evaluated_days"], "truce_evaluated_days"
        ),
        "prisoner_release_pairs": pairs,
        "favor_hook_will_apply": _strict_bool(
            terms_item["favor_hook_will_apply"], "favor_hook_will_apply"
        ),
        "hostage_variant": _nonempty_string(
            terms_item["hostage_variant"], "hostage_variant"
        ),
    }
    utility_item = _exact_dict(
        item["utility_bounds"], _UTILITY_KEYS, "white_peace.utility_bounds"
    )
    utility = {
        "white_peace_lower_raw": _signed_int64(
            utility_item["white_peace_lower_raw"], "white_peace_lower_raw"
        ),
        "white_peace_upper_raw": _signed_int64(
            utility_item["white_peace_upper_raw"], "white_peace_upper_raw"
        ),
    }
    if utility["white_peace_lower_raw"] > utility["white_peace_upper_raw"]:
        raise ValueError("white-peace utility interval is inverted")

    return {
        "schema_version": 1,
        "contract": WHITE_PEACE_COMPARISON_CONTRACT,
        "status": item["status"],
        "frame": _normalize_frame(item["frame"]),
        "evaluated_candidate_sha256": _sha256(
            item["evaluated_candidate_sha256"],
            "evaluated_candidate_sha256",
        ),
        "evaluated_surrender_terms_sha256": _sha256(
            item["evaluated_surrender_terms_sha256"],
            "evaluated_surrender_terms_sha256",
        ),
        "evaluated_campaign_sha256": _sha256(
            item["evaluated_campaign_sha256"],
            "evaluated_campaign_sha256",
        ),
        "evaluated_owner_budget_sha256": _sha256(
            item["evaluated_owner_budget_sha256"],
            "evaluated_owner_budget_sha256",
        ),
        "producer": producer,
        "completeness": completeness,
        "option": option,
        "terms": terms,
        "utility_bounds": utility,
        "hard_budget_breaches": _string_list(
            item["hard_budget_breaches"], "hard_budget_breaches"
        ),
        "same_frame_stable": _strict_bool(
            item["same_frame_stable"], "same_frame_stable"
        ),
    }


def _white_certificate_blockers(
    white: dict[str, object],
    *,
    expected_frame: dict[str, object],
    expected_candidate_sha256: str,
    expected_terms_sha256: str,
    expected_campaign_sha256: str,
    expected_owner_sha256: str,
    expected_target_title_ids: list[int],
) -> list[str]:
    blockers: list[str] = []
    if white["status"] != "complete":
        blockers.append("white_peace_comparison_certificate_incomplete")
    if white["frame"] != expected_frame:
        blockers.append("white_peace_frame_mismatch")
    for key, expected, reason in (
        (
            "evaluated_candidate_sha256",
            expected_candidate_sha256,
            "white_peace_candidate_fingerprint_mismatch",
        ),
        (
            "evaluated_surrender_terms_sha256",
            expected_terms_sha256,
            "white_peace_surrender_terms_fingerprint_mismatch",
        ),
        (
            "evaluated_campaign_sha256",
            expected_campaign_sha256,
            "white_peace_campaign_fingerprint_mismatch",
        ),
        (
            "evaluated_owner_budget_sha256",
            expected_owner_sha256,
            "white_peace_owner_budget_fingerprint_mismatch",
        ),
    ):
        if white[key] != expected:
            blockers.append(reason)
    if white["same_frame_stable"] is not True:
        blockers.append("white_peace_same_frame_stability_required")
    for key in sorted(_COMPLETENESS_KEYS):
        if white["completeness"][key] is not True:
            blockers.append(f"white_peace_{key}_required")

    option = white["option"]
    response = option["recipient_response"]
    for key, reason in (
        ("context_constructed", "white_peace_context_not_constructed"),
        ("native_validator", "white_peace_native_validator_false"),
        ("available", "white_peace_not_available"),
    ):
        if option[key] is not True:
            blockers.append(reason)
    if (
        response["would_accept_now"] is not True
        or response["decision_status_raw"] not in {0, 1}
    ):
        blockers.append("white_peace_typed_recipient_acceptance_not_proven")

    terms = white["terms"]
    if terms["declared_target_title_ids"] != expected_target_title_ids:
        blockers.append("white_peace_declared_targets_mismatch")
    if terms["retained_target_title_ids"] != expected_target_title_ids:
        blockers.append("white_peace_claim_retention_not_proven")
    if terms["claim_disposition"] != "retain_declared_target_claims":
        blockers.append("white_peace_claim_disposition_not_proven")
    if terms["title_holder_change_count"] != 0:
        blockers.append("white_peace_title_holder_change_present")
    if terms["attacker_prestige_delta_raw"] > 0:
        blockers.append("white_peace_prestige_gain_shape_unexpected")
    if terms["hostage_variant"] != "none":
        blockers.append("white_peace_hostage_variant_not_supported")
    return blockers


def _white_budget_blockers(
    white: dict[str, object], owner: dict[str, object]
) -> list[str]:
    terms = white["terms"]
    limits = owner["white_peace_limits"]
    blockers = list(white["hard_budget_breaches"])
    if terms["primary_gold_transfer_raw"] > limits["maximum_gold_transfer_raw"]:
        blockers.append("white_peace_gold_budget_breached")
    if -terms["attacker_prestige_delta_raw"] > limits[
        "maximum_prestige_loss_raw"
    ]:
        blockers.append("white_peace_prestige_budget_breached")
    removed = len(
        set(terms["declared_target_title_ids"])
        - set(terms["retained_target_title_ids"])
    )
    if removed > limits["maximum_claims_removed"]:
        blockers.append("white_peace_claim_budget_breached")
    if (
        terms["favor_hook_will_apply"] is True
        and limits["allow_favor_hook"] is not True
    ):
        blockers.append("white_peace_favor_hook_budget_breached")
    if terms["truce_evaluated_days"] > limits["maximum_truce_days"]:
        blockers.append("white_peace_truce_budget_breached")
    return blockers


def _candidate_frame(candidate: object) -> dict[str, object]:
    if not isinstance(candidate, dict) or "frame" not in candidate:
        raise ValueError("candidate frame is unavailable")
    return _normalize_frame(candidate["frame"])


def _surrender_target_title_ids(terms: object) -> list[int]:
    try:
        target_ids = terms["claims_base"]["payload"]["target_title_ids"]
    except (KeyError, TypeError) as error:
        raise ValueError("surrender target titles are unavailable") from error
    return _id_list(
        target_ids, "surrender_target_title_ids", require_nonempty=True
    )


def _normalize_frame(value: object) -> dict[str, object]:
    frame = _exact_dict(value, _FRAME_KEYS, "frame")
    result = {
        "snapshot_id": _nonempty_string(frame["snapshot_id"], "snapshot_id"),
        "snapshot_revision": _positive_uint64(
            frame["snapshot_revision"], "snapshot_revision"
        ),
        "native_revision": _positive_uint64(
            frame["native_revision"], "native_revision"
        ),
        "date_raw": _signed_int32(frame["date_raw"], "date_raw"),
        "connection_id": _nonempty_string(
            frame["connection_id"], "connection_id"
        ),
        "episode_id": _nonempty_string(frame["episode_id"], "episode_id"),
        "ck3_pid": _positive_int32(frame["ck3_pid"], "ck3_pid"),
        "paused": _strict_bool(frame["paused"], "paused"),
        "war_id": _full_id(frame["war_id"], "war_id"),
        "active_casus_belli_database_index": _nonnegative_int32(
            frame["active_casus_belli_database_index"],
            "active_casus_belli_database_index",
        ),
        "active_casus_belli_key": _nonempty_string(
            frame["active_casus_belli_key"], "active_casus_belli_key"
        ),
        "primary_attacker_character_id": _full_id(
            frame["primary_attacker_character_id"],
            "primary_attacker_character_id",
        ),
        "primary_defender_character_id": _full_id(
            frame["primary_defender_character_id"],
            "primary_defender_character_id",
        ),
        "claimant_character_id": _full_id(
            frame["claimant_character_id"], "claimant_character_id"
        ),
    }
    if (
        result["paused"] is not True
        or result["active_casus_belli_key"] != "raiktor_claim_cb"
        or result["primary_attacker_character_id"]
        == result["primary_defender_character_id"]
    ):
        raise ValueError("frame is not an exact paused Raiktor frame")
    return result


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


def _id_list(value: object, name: str, *, require_nonempty: bool) -> list[int]:
    if not isinstance(value, list) or (require_nonempty and not value):
        raise ValueError(f"{name} must be a nonempty list")
    result = [_full_id(item, f"{name}[]") for item in value]
    if len(result) != len(set(result)):
        raise ValueError(f"{name} contains duplicate generations")
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
        raise ValueError(f"{name} is outside int32")
    return value


def _signed_int64(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < -(2**63) or value > 2**63 - 1:
        raise ValueError(f"{name} is outside int64")
    return value


def _nonnegative_int64(value: object, name: str) -> int:
    result = _signed_int64(value, name)
    if result < 0:
        raise ValueError(f"{name} must be nonnegative")
    return result


def _positive_uint64(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value <= 0 or value > 2**64 - 1:
        raise ValueError(f"{name} is outside positive uint64")
    return value
