from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    canonical_policy_input_sha256,
)
from xar_autoplayer.simulation.raiktor_owner_budget_profile_provider import (
    provide_raiktor_owner_budget_profile,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_intake import (
    PROVIDER_SCHEMA,
    provide_raiktor_three_way_exit_intake,
)
from xar_autoplayer.simulation.raiktor_white_peace_comparison_provider import (
    OBSERVATION_CONTRACT,
    UTILITY_CONTRACT,
)
from test_raiktor_continue_vs_surrender_policy import (
    _candidate,
    _complete_terms,
)
from test_raiktor_owner_budget_profile_provider import _source
from test_raiktor_three_way_exit_policy import (
    _complete_campaign,
    _white_peace,
)
from test_raiktor_surrender_session_binding_contract import _bound


def _write_owner(directory: str, *, approved: bool = True) -> Path:
    path = Path(directory) / "owner-budget.json"
    path.write_text(
        json.dumps(_source(approved=approved), sort_keys=True),
        encoding="utf-8",
    )
    return path


def _complete_inputs(owner_path: Path) -> tuple[dict[str, object], ...]:
    candidate = _candidate()
    terms = _complete_terms()
    owner_provider = provide_raiktor_owner_budget_profile(owner_path)
    owner = owner_provider["owner_budget_profile"]
    assert isinstance(owner, dict)
    campaign = _complete_campaign(terms, owner)
    white = _white_peace(candidate, terms, campaign, owner)
    observation = {
        "schema_version": 1,
        "contract": OBSERVATION_CONTRACT,
        "status": "complete",
        "frame": deepcopy(candidate["frame"]),
        "evaluated_candidate_sha256": canonical_policy_input_sha256(
            candidate
        ),
        "evaluated_surrender_terms_sha256": canonical_policy_input_sha256(
            terms
        ),
        "producer": {
            "producer_id": "synthetic-raiktor-white-terms-do-not-ship",
            "producer_version": "v1",
            "source_artifact_sha256": "A" * 64,
            "production_live": False,
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
            "production_live": False,
        },
        "utility_bounds": deepcopy(white["utility_bounds"]),
        "hard_budget_breaches": [],
        "model_risk_included": True,
    }
    return candidate, terms, campaign, observation, utility


def _provide(
    *,
    owner_path: Path | None,
    campaign: object | None = None,
    observation: object | None = None,
    utility: object | None = None,
) -> dict[str, object]:
    return provide_raiktor_three_way_exit_intake(
        candidate_value=_candidate(),
        surrender_terms_value=_complete_terms(),
        campaign_value=campaign,
        owner_budget_source_path=owner_path,
        white_peace_observation_value=observation,
        white_peace_utility_evaluation_value=utility,
    )


class RaiktorThreeWayExitIntakeTests(unittest.TestCase):
    def test_outcome_only_intake_does_not_invent_execution_inputs(self) -> None:
        result = provide_raiktor_three_way_exit_intake(
            candidate_value=None,
            surrender_terms_value=None,
            campaign_value=None,
            owner_budget_source_path=None,
            white_peace_observation_value=None,
            white_peace_utility_evaluation_value=None,
        )

        self.assertIsNone(result["surrender_execution_readiness"])
        self.assertFalse(
            result["inputs"]["surrender_aggregate_session_binding_supplied"]
        )
        self.assertFalse(result["action_ready"])
        self.assertIsNone(result["action_literal"])

    def test_missing_sources_report_one_fail_closed_intake(self) -> None:
        result = _provide(owner_path=None)

        self.assertEqual(result["schema"], PROVIDER_SCHEMA)
        self.assertEqual(result["status"], "evidence_required")
        self.assertFalse(result["static_recommendation_ready"])
        self.assertFalse(result["production_recommendation_ready"])
        self.assertFalse(result["action_ready"])
        self.assertIsNone(result["action_literal"])
        self.assertEqual(
            result["blockers"],
            [
                "owner_budget_profile_unavailable",
                "white_peace_terms_observation_unavailable",
                "campaign_dominance_certificate_unavailable",
                "white_peace_utility_evaluation_unavailable",
                "white_peace_comparison_certificate_unavailable",
            ],
        )
        execution = result["surrender_execution_readiness"]
        self.assertEqual(execution["status"], "blocked")
        self.assertIn(
            "three_way_static_surrender_recommendation_required",
            execution["decision"]["blockers"],
        )
        self.assertFalse(execution["action"]["ready"])
        self.assertIsNone(execution["action"]["literal"])

    def test_complete_bound_inputs_publish_static_recommendation_only(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            owner_path = _write_owner(directory)
            candidate, terms, campaign, observation, utility = (
                _complete_inputs(owner_path)
            )
            result = provide_raiktor_three_way_exit_intake(
                candidate_value=candidate,
                surrender_terms_value=terms,
                campaign_value=campaign,
                owner_budget_source_path=owner_path,
                white_peace_observation_value=observation,
                white_peace_utility_evaluation_value=utility,
            )

        self.assertEqual(result["status"], "static_recommendation_available")
        self.assertTrue(result["static_recommendation_ready"])
        self.assertEqual(result["recommended_outcome"], "white_peace")
        self.assertTrue(result["inputs"]["white_peace_comparison_ready"])
        self.assertFalse(result["production_recommendation_ready"])
        self.assertFalse(result["action_ready"])
        self.assertIsNone(result["action_literal"])
        self.assertEqual(result["blockers"], [])
        execution = result["surrender_execution_readiness"]
        self.assertEqual(
            execution["decision"]["recommended_outcome"], "white_peace"
        )
        self.assertFalse(execution["decision"]["ready"])
        self.assertFalse(execution["action"]["ready"])
        self.assertFalse(execution["postcondition"]["ready"])

    def test_exact_session_binding_reaches_execution_projection_only(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            owner_path = _write_owner(directory)
            candidate, terms, campaign, observation, utility = (
                _complete_inputs(owner_path)
            )
            result = provide_raiktor_three_way_exit_intake(
                candidate_value=candidate,
                surrender_terms_value=terms,
                campaign_value=campaign,
                owner_budget_source_path=owner_path,
                white_peace_observation_value=observation,
                white_peace_utility_evaluation_value=utility,
                surrender_aggregate_session_binding_value=_bound(),
            )

        execution = result["surrender_execution_readiness"]
        self.assertTrue(
            result["inputs"]["surrender_aggregate_session_binding_supplied"]
        )
        self.assertTrue(execution["terms"]["session_provenance_ready"])
        self.assertNotIn(
            "six_domain_session_provenance_not_bound",
            execution["terms"]["blockers"],
        )
        self.assertFalse(result["action_ready"])
        self.assertFalse(execution["action"]["ready"])
        self.assertIsNone(execution["action"]["literal"])

    def test_draft_owner_never_reaches_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            owner_path = _write_owner(directory, approved=False)
            result = _provide(owner_path=owner_path)

        self.assertEqual(result["status"], "evidence_required")
        self.assertTrue(result["inputs"]["owner_budget_profile_available"])
        self.assertFalse(
            result["inputs"]["owner_budget_profile_production_eligible"]
        )
        self.assertFalse(result["inputs"]["white_peace_comparison_ready"])
        self.assertIn(
            "owner_budget_profile_not_owner_approved", result["blockers"]
        )
        self.assertIn("owner_budget_profile_incomplete", result["blockers"])

    def test_stale_utility_binding_stays_typed_red(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            owner_path = _write_owner(directory)
            candidate, terms, campaign, observation, utility = (
                _complete_inputs(owner_path)
            )
            utility["evaluated_campaign_sha256"] = "C" * 64
            result = provide_raiktor_three_way_exit_intake(
                candidate_value=candidate,
                surrender_terms_value=terms,
                campaign_value=campaign,
                owner_budget_source_path=owner_path,
                white_peace_observation_value=observation,
                white_peace_utility_evaluation_value=utility,
            )

        self.assertEqual(result["status"], "evidence_required")
        self.assertFalse(result["inputs"]["white_peace_comparison_ready"])
        self.assertIn(
            "white_peace_utility_campaign_mismatch", result["blockers"]
        )
        self.assertFalse(result["action_ready"])


if __name__ == "__main__":
    unittest.main()
