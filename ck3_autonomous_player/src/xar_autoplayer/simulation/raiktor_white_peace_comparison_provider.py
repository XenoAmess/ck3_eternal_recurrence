"""Compose evidence-bound Raiktor white-peace comparison certificates.

The provider publishes the existing three-way policy input only when a
same-frame terms observation, campaign certificate, owner-authored budget,
and explicit utility evaluation agree by identity and SHA-256. It never
derives observed terms from scripts or supplies default utility values.
"""

from __future__ import annotations

from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    canonical_policy_input_sha256,
    normalize_raiktor_campaign_certificate,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_policy import (
    WHITE_PEACE_COMPARISON_CONTRACT,
    WHITE_PEACE_PROVIDER,
    normalize_raiktor_owner_budget_profile,
    normalize_raiktor_white_peace_comparison_certificate,
)
from xar_autoplayer.simulation.raiktor_white_peace_comparison_contracts import (
    OBSERVATION_COMPLETENESS_KEYS,
    OBSERVATION_CONTRACT,
    UTILITY_CONTRACT,
    WhitePeaceComparisonProviderError,
    normalize_white_peace_terms_observation,
    normalize_white_peace_utility_evaluation,
)


PROVIDER_SCHEMA = "xar.ck3.raiktor_white_peace_comparison_provider.v1"
_CAMPAIGN_COMPLETENESS_KEYS = {
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


def provide_raiktor_white_peace_comparison(
    *,
    observation_value: object | None,
    campaign_value: object | None,
    owner_budget_value: object | None,
    utility_evaluation_value: object | None,
) -> dict[str, object]:
    """Return one comparison certificate or typed missing-evidence result."""

    missing = [
        reason
        for value, reason in (
            (
                observation_value,
                "white_peace_terms_observation_unavailable",
            ),
            (campaign_value, "campaign_dominance_certificate_unavailable"),
            (owner_budget_value, "owner_budget_profile_unavailable"),
            (
                utility_evaluation_value,
                "white_peace_utility_evaluation_unavailable",
            ),
        )
        if value is None
    ]
    if missing:
        return _result(
            status="evidence_required",
            blockers=missing,
            certificate=None,
            input_sha256=None,
        )

    try:
        observation = normalize_white_peace_terms_observation(
            observation_value
        )
        campaign = normalize_raiktor_campaign_certificate(campaign_value)
        owner = normalize_raiktor_owner_budget_profile(owner_budget_value)
        utility = normalize_white_peace_utility_evaluation(
            utility_evaluation_value
        )
    except ValueError as exc:
        if isinstance(exc, WhitePeaceComparisonProviderError):
            raise
        raise WhitePeaceComparisonProviderError(str(exc)) from exc

    observation_sha = canonical_policy_input_sha256(observation)
    campaign_sha = canonical_policy_input_sha256(campaign)
    owner_sha = canonical_policy_input_sha256(owner)
    utility_sha = canonical_policy_input_sha256(utility)
    input_sha = canonical_policy_input_sha256(
        {
            "observation_sha256": observation_sha,
            "campaign_sha256": campaign_sha,
            "owner_budget_sha256": owner_sha,
            "utility_evaluation_sha256": utility_sha,
        }
    )
    blockers = _input_blockers(
        observation=observation,
        observation_sha256=observation_sha,
        campaign=campaign,
        campaign_sha256=campaign_sha,
        owner=owner,
        owner_sha256=owner_sha,
        utility=utility,
    )
    complete = not blockers
    production_live = (
        complete
        and observation["producer"]["production_live"] is True
        and campaign["producer"]["production_live"] is True
        and owner["profile_production_eligible"] is True
        and utility["producer"]["production_live"] is True
    )
    candidate = {
        "schema_version": 1,
        "contract": WHITE_PEACE_COMPARISON_CONTRACT,
        "status": "complete" if complete else "incomplete",
        "frame": dict(observation["frame"]),
        "evaluated_candidate_sha256": observation[
            "evaluated_candidate_sha256"
        ],
        "evaluated_surrender_terms_sha256": observation[
            "evaluated_surrender_terms_sha256"
        ],
        "evaluated_campaign_sha256": campaign_sha,
        "evaluated_owner_budget_sha256": owner_sha,
        "producer": {
            "producer_id": WHITE_PEACE_PROVIDER,
            "producer_version": "v1",
            "source_artifact_sha256": input_sha,
            "utility_unit": "owner_utility_q100000",
            "production_live": production_live,
        },
        "completeness": {
            **dict(observation["completeness"]),
            "utility_bounds_ready": utility["status"] == "complete",
            "model_risk_included": utility["model_risk_included"],
        },
        "option": dict(observation["option"]),
        "terms": dict(observation["terms"]),
        "utility_bounds": dict(utility["utility_bounds"]),
        "hard_budget_breaches": list(utility["hard_budget_breaches"]),
        "same_frame_stable": (
            observation["same_frame_stable"] is True
            and observation["frame"] == campaign["frame"]
            and observation["frame"] == utility["frame"]
        ),
    }
    try:
        normalized = normalize_raiktor_white_peace_comparison_certificate(
            candidate
        )
    except ValueError as exc:
        raise WhitePeaceComparisonProviderError(str(exc)) from exc
    return _result(
        status="available" if complete else "evidence_required",
        blockers=blockers,
        certificate=normalized if complete else None,
        input_sha256=input_sha,
    )


def _input_blockers(
    *,
    observation: dict[str, object],
    observation_sha256: str,
    campaign: dict[str, object],
    campaign_sha256: str,
    owner: dict[str, object],
    owner_sha256: str,
    utility: dict[str, object],
) -> list[str]:
    blockers: list[str] = []
    if observation["status"] != "complete":
        blockers.append("white_peace_terms_observation_incomplete")
    for key in sorted(OBSERVATION_COMPLETENESS_KEYS):
        if observation["completeness"][key] is not True:
            blockers.append(f"white_peace_{key}_required")
    if observation["same_frame_stable"] is not True:
        blockers.append("white_peace_observation_same_frame_required")
    if campaign["status"] != "complete":
        blockers.append("campaign_dominance_certificate_incomplete")
    for key in sorted(_CAMPAIGN_COMPLETENESS_KEYS):
        if campaign["completeness"][key] is not True:
            blockers.append(f"campaign_{key}_required")
    if campaign["same_frame_stable"] is not True:
        blockers.append("campaign_same_frame_stability_required")
    if owner["status"] != "complete":
        blockers.append("owner_budget_profile_incomplete")
    if utility["status"] != "complete":
        blockers.append("white_peace_utility_evaluation_incomplete")
    if utility["model_risk_included"] is not True:
        blockers.append("white_peace_model_risk_required")

    for actual, expected, reason in (
        (
            campaign["frame"],
            observation["frame"],
            "white_peace_campaign_frame_mismatch",
        ),
        (
            utility["frame"],
            observation["frame"],
            "white_peace_utility_frame_mismatch",
        ),
        (
            campaign["evaluated_candidate_sha256"],
            observation["evaluated_candidate_sha256"],
            "white_peace_campaign_candidate_mismatch",
        ),
        (
            campaign["evaluated_terms_sha256"],
            observation["evaluated_surrender_terms_sha256"],
            "white_peace_campaign_surrender_terms_mismatch",
        ),
        (
            campaign["evaluated_limits_sha256"],
            canonical_policy_input_sha256(owner["pairwise_limits"]),
            "white_peace_campaign_owner_limits_mismatch",
        ),
        (
            utility["evaluated_observation_sha256"],
            observation_sha256,
            "white_peace_utility_observation_mismatch",
        ),
        (
            utility["evaluated_campaign_sha256"],
            campaign_sha256,
            "white_peace_utility_campaign_mismatch",
        ),
        (
            utility["evaluated_owner_budget_sha256"],
            owner_sha256,
            "white_peace_utility_owner_budget_mismatch",
        ),
    ):
        if actual != expected:
            blockers.append(reason)
    return blockers


def _result(
    *,
    status: str,
    blockers: list[str],
    certificate: dict[str, object] | None,
    input_sha256: str | None,
) -> dict[str, object]:
    return {
        "schema": PROVIDER_SCHEMA,
        "provider": WHITE_PEACE_PROVIDER,
        "status": status,
        "comparison_ready": certificate is not None,
        "production_live": (
            certificate is not None
            and certificate["producer"]["production_live"] is True
        ),
        "input_bundle_sha256": input_sha256,
        "comparison_certificate": certificate,
        "blockers": blockers,
        "boundaries": [
            "no_static_script_direction_promoted_to_observed_terms",
            "no_default_or_fixture_utility",
            "same_frame_identity_and_all_input_hashes_required",
            "provider_does_not_query_or_start_ck3",
            "provider_does_not_authorize_or_submit_an_action",
        ],
    }


__all__ = [
    "OBSERVATION_CONTRACT",
    "PROVIDER_SCHEMA",
    "UTILITY_CONTRACT",
    "WhitePeaceComparisonProviderError",
    "provide_raiktor_white_peace_comparison",
]
