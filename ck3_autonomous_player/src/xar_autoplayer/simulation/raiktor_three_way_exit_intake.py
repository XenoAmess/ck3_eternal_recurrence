"""Compose the existing Raiktor exit providers into one fail-closed intake.

This module is deliberately side-effect free.  It loads only the explicitly
supplied owner budget source, delegates evidence validation to the existing
white-peace provider and three-way policy, and never manufactures a missing
campaign, terms observation, utility evaluation, or action authorization.
"""

from __future__ import annotations

from pathlib import Path

from xar_autoplayer.simulation.raiktor_owner_budget_profile_provider import (
    provide_raiktor_owner_budget_profile,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_policy import (
    assess_raiktor_three_way_exit,
)
from xar_autoplayer.simulation.raiktor_white_peace_comparison_provider import (
    provide_raiktor_white_peace_comparison,
)


PROVIDER_SCHEMA = "xar.ck3.raiktor_three_way_exit_intake.v1"
PROVIDER_ID = "raiktor-three-way-exit-intake-provider-v1"


def provide_raiktor_three_way_exit_intake(
    *,
    candidate_value: object,
    surrender_terms_value: object,
    campaign_value: object | None,
    owner_budget_source_path: str | Path | None,
    white_peace_observation_value: object | None,
    white_peace_utility_evaluation_value: object | None,
    observed_surrender_outcome_value: object | None = None,
) -> dict[str, object]:
    """Return one composed static assessment and all typed provider blockers."""

    owner_provider = provide_raiktor_owner_budget_profile(
        owner_budget_source_path
    )
    owner_budget = (
        owner_provider["owner_budget_profile"]
        if owner_provider["profile_available"] is True
        else None
    )
    white_provider = provide_raiktor_white_peace_comparison(
        observation_value=white_peace_observation_value,
        campaign_value=campaign_value,
        owner_budget_value=owner_budget,
        utility_evaluation_value=white_peace_utility_evaluation_value,
    )
    white_peace = white_provider["comparison_certificate"]
    assessment = assess_raiktor_three_way_exit(
        candidate_value,
        surrender_terms_value,
        campaign_value,
        owner_budget,
        white_peace,
        observed_surrender_outcome_value,
    )

    blockers = _ordered_unique(
        [
            *owner_provider["blockers"],
            *white_provider["blockers"],
            *[
                item["reason"]
                for item in assessment["provider_blockers"]
            ],
            *assessment["owner_blockers"],
            *assessment["white_peace_blockers"],
            *assessment["white_peace_budget_blockers"],
            *assessment["observed_surrender_outcome"]["blockers"],
        ]
    )
    return {
        "schema": PROVIDER_SCHEMA,
        "provider": PROVIDER_ID,
        "status": assessment["status"],
        "inputs": {
            "campaign_certificate_supplied": campaign_value is not None,
            "owner_budget_profile_available": owner_provider[
                "profile_available"
            ],
            "owner_budget_profile_production_eligible": owner_provider[
                "profile_production_eligible"
            ],
            "white_peace_terms_observation_supplied": (
                white_peace_observation_value is not None
            ),
            "white_peace_utility_evaluation_supplied": (
                white_peace_utility_evaluation_value is not None
            ),
            "white_peace_comparison_ready": white_provider[
                "comparison_ready"
            ],
            "observed_surrender_outcome_supplied": (
                observed_surrender_outcome_value is not None
            ),
        },
        "static_recommendation_ready": assessment[
            "static_recommendation_ready"
        ],
        "recommended_outcome": assessment["recommended_outcome"],
        "production_recommendation_ready": False,
        "action_ready": False,
        "action_literal": None,
        "blockers": blockers,
        "providers": {
            "owner_budget": owner_provider,
            "white_peace_comparison": white_provider,
        },
        "assessment": assessment,
        "boundaries": [
            "offline_side_effect_free_composition_only",
            "no_default_owner_budget_or_utility_values",
            "missing_evidence_remains_typed_and_unavailable",
            "static_recommendation_does_not_authorize_an_action",
            "provider_does_not_start_query_or_mutate_ck3",
        ],
    }


def _ordered_unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


__all__ = [
    "PROVIDER_ID",
    "PROVIDER_SCHEMA",
    "provide_raiktor_three_way_exit_intake",
]
