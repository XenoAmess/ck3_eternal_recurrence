from __future__ import annotations

from copy import deepcopy
import unittest

from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    canonical_policy_input_sha256,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_policy import (
    assess_raiktor_three_way_exit,
)
from xar_autoplayer.simulation.raiktor_white_peace_comparison_provider import (
    OBSERVATION_CONTRACT,
    PROVIDER_SCHEMA,
    UTILITY_CONTRACT,
    WhitePeaceComparisonProviderError,
    provide_raiktor_white_peace_comparison,
)
from test_raiktor_three_way_exit_policy import (
    _complete_campaign,
    _owner,
    _white_peace,
)
from test_raiktor_continue_vs_surrender_policy import (
    _candidate,
    _complete_terms,
)


def _provider_inputs(
    *,
    production_live: bool = False,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    candidate = _candidate()
    surrender_terms = _complete_terms()
    owner = _owner()
    if production_live:
        owner["profile_production_eligible"] = True
        owner["pairwise_limits"]["profile_production_eligible"] = True
    campaign = _complete_campaign(surrender_terms, owner)
    if production_live:
        campaign["producer"]["production_live"] = True
    white = _white_peace(candidate, surrender_terms, campaign, owner)
    observation = {
        "schema_version": 1,
        "contract": OBSERVATION_CONTRACT,
        "status": "complete",
        "frame": deepcopy(candidate["frame"]),
        "evaluated_candidate_sha256": canonical_policy_input_sha256(
            candidate
        ),
        "evaluated_surrender_terms_sha256": canonical_policy_input_sha256(
            surrender_terms
        ),
        "producer": {
            "producer_id": "synthetic-raiktor-white-terms-do-not-ship",
            "producer_version": "v1",
            "source_artifact_sha256": "A" * 64,
            "production_live": production_live,
        },
        "completeness": {
            key: white["completeness"][key]
            for key in (
                "final_recipient_response_ready",
                "claim_disposition_ready",
                "gold_transfer_ready",
                "prestige_delta_ready",
                "truce_ready",
                "prisoner_release_ready",
                "favor_hook_ready",
            )
        },
        "option": deepcopy(white["option"]),
        "terms": deepcopy(white["terms"]),
        "same_frame_stable": True,
    }
    utility = {
        "schema_version": 1,
        "contract": UTILITY_CONTRACT,
        "status": "complete",
        "frame": deepcopy(candidate["frame"]),
        "evaluated_observation_sha256": canonical_policy_input_sha256(
            observation
        ),
        "evaluated_campaign_sha256": canonical_policy_input_sha256(
            campaign
        ),
        "evaluated_owner_budget_sha256": canonical_policy_input_sha256(
            owner
        ),
        "producer": {
            "producer_id": "synthetic-owner-utility-do-not-ship",
            "producer_version": "v1",
            "source_artifact_sha256": "B" * 64,
            "utility_unit": "owner_utility_q100000",
            "production_live": production_live,
        },
        "utility_bounds": deepcopy(white["utility_bounds"]),
        "hard_budget_breaches": [],
        "model_risk_included": True,
    }
    return candidate, surrender_terms, campaign, owner, observation, utility


def _provide(
    campaign: dict[str, object],
    owner: dict[str, object],
    observation: dict[str, object],
    utility: dict[str, object],
) -> dict[str, object]:
    return provide_raiktor_white_peace_comparison(
        observation_value=observation,
        campaign_value=campaign,
        owner_budget_value=owner,
        utility_evaluation_value=utility,
    )


class RaiktorWhitePeaceComparisonProviderTests(unittest.TestCase):
    def test_complete_bound_inputs_feed_existing_three_way_policy(self) -> None:
        candidate, terms, campaign, owner, observation, utility = (
            _provider_inputs()
        )

        result = _provide(campaign, owner, observation, utility)

        self.assertEqual(result["schema"], PROVIDER_SCHEMA)
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["comparison_ready"])
        self.assertFalse(result["production_live"])
        self.assertEqual(result["blockers"], [])
        certificate = result["comparison_certificate"]
        self.assertIsInstance(certificate, dict)
        assert isinstance(certificate, dict)
        self.assertEqual(
            certificate["evaluated_campaign_sha256"],
            canonical_policy_input_sha256(campaign),
        )
        self.assertEqual(
            certificate["evaluated_owner_budget_sha256"],
            canonical_policy_input_sha256(owner),
        )
        policy = assess_raiktor_three_way_exit(
            candidate, terms, campaign, owner, certificate
        )
        self.assertEqual(policy["recommended_outcome"], "white_peace")
        self.assertTrue(policy["three_way_comparison_ready"])
        self.assertFalse(policy["production_recommendation_ready"])
        self.assertFalse(policy["action_ready"])

    def test_missing_inputs_are_typed_and_never_defaulted(self) -> None:
        result = provide_raiktor_white_peace_comparison(
            observation_value=None,
            campaign_value=None,
            owner_budget_value=None,
            utility_evaluation_value=None,
        )

        self.assertEqual(result["status"], "evidence_required")
        self.assertFalse(result["comparison_ready"])
        self.assertFalse(result["production_live"])
        self.assertIsNone(result["comparison_certificate"])
        self.assertIsNone(result["input_bundle_sha256"])
        self.assertEqual(
            result["blockers"],
            [
                "white_peace_terms_observation_unavailable",
                "campaign_dominance_certificate_unavailable",
                "owner_budget_profile_unavailable",
                "white_peace_utility_evaluation_unavailable",
            ],
        )
        self.assertIn(
            "no_default_or_fixture_utility", result["boundaries"]
        )

    def test_complete_other_inputs_do_not_synthesize_missing_utility(
        self,
    ) -> None:
        _, _, campaign, owner, observation, _ = _provider_inputs()

        result = provide_raiktor_white_peace_comparison(
            observation_value=observation,
            campaign_value=campaign,
            owner_budget_value=owner,
            utility_evaluation_value=None,
        )

        self.assertEqual(result["status"], "evidence_required")
        self.assertEqual(
            result["blockers"],
            ["white_peace_utility_evaluation_unavailable"],
        )
        self.assertFalse(result["comparison_ready"])
        self.assertFalse(result["production_live"])
        self.assertIsNone(result["comparison_certificate"])

    def test_stale_utility_hash_is_typed_evidence_blocker(self) -> None:
        _, _, campaign, owner, observation, utility = _provider_inputs()
        utility["evaluated_observation_sha256"] = "C" * 64

        result = _provide(campaign, owner, observation, utility)

        self.assertEqual(result["status"], "evidence_required")
        self.assertFalse(result["comparison_ready"])
        self.assertIsNone(result["comparison_certificate"])
        self.assertIn(
            "white_peace_utility_observation_mismatch",
            result["blockers"],
        )

    def test_cross_frame_inputs_do_not_publish_certificate(self) -> None:
        _, _, campaign, owner, observation, utility = _provider_inputs()
        utility["frame"]["snapshot_revision"] += 1

        result = _provide(campaign, owner, observation, utility)

        self.assertIn(
            "white_peace_utility_frame_mismatch", result["blockers"]
        )
        self.assertIsNone(result["comparison_certificate"])

    def test_incomplete_observation_and_campaign_stay_typed_red(self) -> None:
        _, _, campaign, owner, observation, utility = _provider_inputs()
        observation["status"] = "incomplete"
        observation["completeness"]["favor_hook_ready"] = False
        campaign["status"] = "incomplete"
        utility["evaluated_observation_sha256"] = (
            canonical_policy_input_sha256(observation)
        )
        utility["evaluated_campaign_sha256"] = canonical_policy_input_sha256(
            campaign
        )

        result = _provide(campaign, owner, observation, utility)

        self.assertIn(
            "white_peace_terms_observation_incomplete", result["blockers"]
        )
        self.assertIn(
            "white_peace_favor_hook_ready_required", result["blockers"]
        )
        self.assertIn(
            "campaign_dominance_certificate_incomplete", result["blockers"]
        )
        self.assertIsNone(result["comparison_certificate"])

    def test_malformed_observed_terms_are_rejected(self) -> None:
        _, _, campaign, owner, observation, utility = _provider_inputs()
        observation["terms"]["primary_gold_transfer_raw"] = -1
        utility["evaluated_observation_sha256"] = (
            canonical_policy_input_sha256(observation)
        )

        with self.assertRaises(WhitePeaceComparisonProviderError):
            _provide(campaign, owner, observation, utility)

    def test_inverted_or_unbound_utility_is_rejected_or_blocked(self) -> None:
        _, _, campaign, owner, observation, utility = _provider_inputs()
        inverted = deepcopy(utility)
        inverted["utility_bounds"] = {
            "white_peace_lower_raw": 2,
            "white_peace_upper_raw": 1,
        }
        with self.assertRaises(WhitePeaceComparisonProviderError):
            _provide(campaign, owner, observation, inverted)

        missing_risk = deepcopy(utility)
        missing_risk["model_risk_included"] = False
        result = _provide(campaign, owner, observation, missing_risk)
        self.assertIn(
            "white_peace_model_risk_required", result["blockers"]
        )
        self.assertIsNone(result["comparison_certificate"])

    def test_production_live_requires_all_four_production_inputs(self) -> None:
        _, _, campaign, owner, observation, utility = _provider_inputs(
            production_live=True
        )

        result = _provide(campaign, owner, observation, utility)

        self.assertTrue(result["comparison_ready"])
        self.assertTrue(result["production_live"])
        self.assertTrue(
            result["comparison_certificate"]["producer"]["production_live"]
        )

        observation["producer"]["production_live"] = False
        utility["evaluated_observation_sha256"] = (
            canonical_policy_input_sha256(observation)
        )
        result = _provide(campaign, owner, observation, utility)
        self.assertTrue(result["comparison_ready"])
        self.assertFalse(result["production_live"])


if __name__ == "__main__":
    unittest.main()
