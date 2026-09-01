from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    canonical_policy_input_sha256,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_policy import (
    CAMPAIGN_PROVIDER,
    OWNER_BUDGET_PROFILE_CONTRACT,
    OWNER_BUDGET_PROVIDER,
    POLICY_VERSION,
    WHITE_PEACE_COMPARISON_CONTRACT,
    WHITE_PEACE_PROVIDER,
    assess_raiktor_three_way_exit,
)
from test_raiktor_continue_vs_surrender_policy import (
    _campaign,
    _candidate,
    _complete_terms,
    _current_incomplete_terms,
    _limits,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "raiktor_three_way_exit_policy_v1_contract.json"
)


def _owner() -> dict[str, object]:
    limits = _limits()
    return {
        "schema_version": 1,
        "contract": OWNER_BUDGET_PROFILE_CONTRACT,
        "status": "complete",
        "profile_id": limits["profile_id"],
        "profile_provenance": limits["profile_provenance"],
        "profile_source_sha256": "D" * 64,
        "profile_production_eligible": False,
        "pairwise_limits": limits,
        "white_peace_limits": {
            "maximum_gold_transfer_raw": 0,
            "maximum_prestige_loss_raw": 10_000_000,
            "maximum_claims_removed": 0,
            "allow_favor_hook": False,
            "maximum_truce_days": 1_825,
        },
    }


def _complete_campaign(
    terms: dict[str, object],
    owner: dict[str, object],
    *,
    safe_objective: bool = False,
    credible_reinforcement: bool = False,
    tail_loss_upper: int = 1_000,
    continue_interval: tuple[int, int] = (-100, -50),
    surrender_interval: tuple[int, int] = (0, 20),
    continue_breaches: list[str] | None = None,
    surrender_breaches: list[str] | None = None,
) -> dict[str, object]:
    return _campaign(
        terms,
        owner["pairwise_limits"],
        safe_objective=safe_objective,
        credible_reinforcement=credible_reinforcement,
        tail_loss_upper=tail_loss_upper,
        continue_interval=continue_interval,
        surrender_interval=surrender_interval,
        continue_breaches=continue_breaches,
        surrender_breaches=surrender_breaches,
    )


def _white_peace(
    candidate: dict[str, object],
    terms: dict[str, object],
    campaign: dict[str, object],
    owner: dict[str, object],
    *,
    interval: tuple[int, int] = (40, 50),
) -> dict[str, object]:
    target_ids = list(terms["claims_base"]["payload"]["target_title_ids"])
    return {
        "schema_version": 1,
        "contract": WHITE_PEACE_COMPARISON_CONTRACT,
        "status": "complete",
        "frame": deepcopy(candidate["frame"]),
        "evaluated_candidate_sha256": canonical_policy_input_sha256(
            candidate
        ),
        "evaluated_surrender_terms_sha256": canonical_policy_input_sha256(
            terms
        ),
        "evaluated_campaign_sha256": canonical_policy_input_sha256(
            campaign
        ),
        "evaluated_owner_budget_sha256": canonical_policy_input_sha256(owner),
        "producer": {
            "producer_id": "synthetic-white-peace-fixture-do-not-ship",
            "producer_version": "v1",
            "source_artifact_sha256": "E" * 64,
            "utility_unit": "owner_utility_q100000",
            "production_live": False,
        },
        "completeness": {
            "final_recipient_response_ready": True,
            "claim_disposition_ready": True,
            "gold_transfer_ready": True,
            "prestige_delta_ready": True,
            "truce_ready": True,
            "prisoner_release_ready": True,
            "favor_hook_ready": True,
            "utility_bounds_ready": True,
            "model_risk_included": True,
        },
        "option": {
            "context_constructed": True,
            "native_validator": True,
            "available": True,
            "auto_accept": False,
            "recipient_response": {
                "decision_status_raw": 0,
                "would_accept_now": True,
            },
        },
        "terms": {
            "declared_target_title_ids": target_ids,
            "retained_target_title_ids": list(target_ids),
            "claim_disposition": "retain_declared_target_claims",
            "title_holder_change_count": 0,
            "primary_gold_transfer_raw": 0,
            "attacker_prestige_delta_raw": -5_000_000,
            "truce_evaluated_days": 1_825,
            "prisoner_release_pairs": [],
            "favor_hook_will_apply": False,
            "hostage_variant": "none",
        },
        "utility_bounds": {
            "white_peace_lower_raw": interval[0],
            "white_peace_upper_raw": interval[1],
        },
        "hard_budget_breaches": [],
        "same_frame_stable": True,
    }


def _complete_inputs(
    *,
    safe_objective: bool = False,
    credible_reinforcement: bool = False,
    tail_loss_upper: int = 1_000,
    continue_interval: tuple[int, int] = (-100, -50),
    surrender_interval: tuple[int, int] = (0, 20),
    white_interval: tuple[int, int] = (40, 50),
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    candidate = _candidate()
    terms = _complete_terms()
    owner = _owner()
    campaign = _complete_campaign(
        terms,
        owner,
        safe_objective=safe_objective,
        credible_reinforcement=credible_reinforcement,
        tail_loss_upper=tail_loss_upper,
        continue_interval=continue_interval,
        surrender_interval=surrender_interval,
    )
    white = _white_peace(
        candidate, terms, campaign, owner, interval=white_interval
    )
    return candidate, terms, campaign, owner, white


class RaiktorThreeWayExitPolicyTests(unittest.TestCase):
    def test_current_checkpoint_reports_exact_missing_providers(self) -> None:
        result = assess_raiktor_three_way_exit(
            _candidate(), _current_incomplete_terms(), None, None, None
        )
        self.assertEqual(result["status"], "evidence_required")
        self.assertFalse(result["static_recommendation_ready"])
        self.assertIsNone(result["recommended_outcome"])
        providers = {
            row["provider"]: row["reason"]
            for row in result["provider_blockers"]
        }
        self.assertEqual(
            providers,
            {
                CAMPAIGN_PROVIDER: (
                    "campaign_dominance_certificate_unavailable"
                ),
                OWNER_BUDGET_PROVIDER: "owner_budget_profile_unavailable",
                WHITE_PEACE_PROVIDER: (
                    "white_peace_comparison_certificate_unavailable"
                ),
            },
        )
        self.assertFalse(result["full_exit_decision_ready"])
        self.assertFalse(result["action_ready"])
        self.assertIsNone(result["action_literal"])

    def test_missing_campaign_and_white_keep_pairwise_evidence_red(self) -> None:
        owner = _owner()
        result = assess_raiktor_three_way_exit(
            _candidate(), _complete_terms(), None, owner, None
        )
        self.assertEqual(result["status"], "evidence_required")
        self.assertIsNotNone(result["pairwise"])
        self.assertIn(
            "campaign_dominance_certificate_unavailable",
            result["pairwise"]["campaign_blockers"],
        )
        self.assertIsNone(result["recommended_outcome"])

    def test_pairwise_preference_does_not_bypass_missing_white_peace(self) -> None:
        candidate, terms, campaign, owner, _ = _complete_inputs()
        result = assess_raiktor_three_way_exit(
            candidate, terms, campaign, owner, None
        )
        self.assertEqual(
            result["pairwise"]["pairwise_preference"],
            "prefer_surrender_over_continue",
        )
        self.assertEqual(result["status"], "evidence_required")
        self.assertIsNone(result["recommended_outcome"])

    def test_white_peace_robustly_wins_three_way(self) -> None:
        candidate, terms, campaign, owner, white = _complete_inputs()
        result = assess_raiktor_three_way_exit(
            candidate, terms, campaign, owner, white
        )
        self.assertEqual(result["status"], "static_recommendation_available")
        self.assertEqual(result["recommended_outcome"], "white_peace")
        self.assertEqual(result["robust_margin_raw"]["white_peace"], 20)
        self.assertTrue(result["static_recommendation_ready"])
        self.assertFalse(result["production_recommendation_ready"])
        self.assertFalse(result["action_ready"])
        self.assertIsNone(result["suggested_action"])

    def test_surrender_robustly_wins_three_way(self) -> None:
        inputs = _complete_inputs(
            surrender_interval=(60, 70), white_interval=(0, 20)
        )
        result = assess_raiktor_three_way_exit(*inputs)
        self.assertEqual(result["recommended_outcome"], "surrender")
        self.assertEqual(result["robust_margin_raw"]["surrender"], 40)
        self.assertFalse(result["automatic_surrender_ready"])
        self.assertIsNone(result["action_literal"])

    def test_continue_robustly_wins_three_way(self) -> None:
        inputs = _complete_inputs(
            safe_objective=True,
            credible_reinforcement=True,
            tail_loss_upper=50,
            continue_interval=(100, 120),
            surrender_interval=(0, 20),
            white_interval=(30, 50),
        )
        result = assess_raiktor_three_way_exit(*inputs)
        self.assertEqual(result["recommended_outcome"], "continue")
        self.assertEqual(result["robust_margin_raw"]["continue"], 50)

    def test_overlapping_three_way_intervals_are_underdetermined(self) -> None:
        inputs = _complete_inputs(
            continue_interval=(-10, 20),
            surrender_interval=(0, 30),
            white_interval=(10, 40),
        )
        result = assess_raiktor_three_way_exit(*inputs)
        self.assertEqual(result["status"], "three_way_underdetermined")
        self.assertIsNone(result["recommended_outcome"])
        self.assertTrue(result["three_way_evidence_ready"])

    def test_white_peace_hard_budget_breach_excludes_only_that_candidate(
        self,
    ) -> None:
        candidate, terms, campaign, owner, white = _complete_inputs(
            surrender_interval=(60, 70), white_interval=(100, 120)
        )
        white["terms"]["primary_gold_transfer_raw"] = 1
        white["evaluated_owner_budget_sha256"] = canonical_policy_input_sha256(
            owner
        )
        result = assess_raiktor_three_way_exit(
            candidate, terms, campaign, owner, white
        )
        self.assertIn(
            "white_peace_gold_budget_breached",
            result["white_peace_budget_blockers"],
        )
        self.assertNotIn("white_peace", result["eligible_candidates"])
        self.assertEqual(result["recommended_outcome"], "surrender")

    def test_stale_white_peace_hash_fails_closed(self) -> None:
        candidate, terms, campaign, owner, white = _complete_inputs()
        white["evaluated_campaign_sha256"] = "A" * 64
        result = assess_raiktor_three_way_exit(
            candidate, terms, campaign, owner, white
        )
        self.assertEqual(result["status"], "evidence_required")
        self.assertIn(
            "white_peace_campaign_fingerprint_mismatch",
            result["white_peace_blockers"],
        )
        self.assertIsNone(result["recommended_outcome"])

    def test_incomplete_white_peace_domain_fails_closed(self) -> None:
        candidate, terms, campaign, owner, white = _complete_inputs()
        white["status"] = "incomplete"
        white["completeness"]["truce_ready"] = False
        result = assess_raiktor_three_way_exit(
            candidate, terms, campaign, owner, white
        )
        self.assertIn(
            "white_peace_truce_ready_required",
            result["white_peace_blockers"],
        )
        self.assertFalse(result["three_way_comparison_ready"])

    def test_unproven_claim_retention_fails_closed(self) -> None:
        candidate, terms, campaign, owner, white = _complete_inputs()
        white["terms"]["retained_target_title_ids"] = [1_801]
        result = assess_raiktor_three_way_exit(
            candidate, terms, campaign, owner, white
        )
        self.assertIn(
            "white_peace_claim_retention_not_proven",
            result["white_peace_blockers"],
        )
        self.assertIsNone(result["recommended_outcome"])

    def test_owner_and_embedded_pairwise_profile_cannot_drift(self) -> None:
        owner = _owner()
        owner["pairwise_limits"]["profile_id"] = "different-profile"
        with self.assertRaises(ValueError):
            assess_raiktor_three_way_exit(
                _candidate(), _complete_terms(), None, owner, None
            )

    def test_score_and_duration_do_not_replace_bound_certificates(self) -> None:
        candidate, terms, campaign, owner, white = _complete_inputs()
        candidate["player_war_score"] = -100
        candidate["war_duration_days"] = 99_999
        campaign["evaluated_candidate_sha256"] = canonical_policy_input_sha256(
            candidate
        )
        white["evaluated_candidate_sha256"] = canonical_policy_input_sha256(
            candidate
        )
        white["evaluated_campaign_sha256"] = canonical_policy_input_sha256(
            campaign
        )
        result = assess_raiktor_three_way_exit(
            candidate, terms, campaign, owner, white
        )
        self.assertEqual(result["recommended_outcome"], "white_peace")

    def test_authored_3000_is_explicitly_not_a_loss_input(self) -> None:
        result = assess_raiktor_three_way_exit(
            _candidate(), _current_incomplete_terms(), None, None, None
        )
        self.assertIn(
            "authored_3000_is_not_measured_pre_soldiers_or_loss",
            result["explicit_boundaries"],
        )

    def test_static_core_never_promotes_claimed_provider_flags_to_live(
        self,
    ) -> None:
        candidate = _candidate()
        terms = _complete_terms()
        owner = _owner()
        owner["profile_production_eligible"] = True
        owner["pairwise_limits"]["profile_production_eligible"] = True
        campaign = _complete_campaign(terms, owner)
        campaign["producer"]["production_live"] = True
        white = _white_peace(candidate, terms, campaign, owner)
        white["producer"]["production_live"] = True
        result = assess_raiktor_three_way_exit(
            candidate, terms, campaign, owner, white
        )
        self.assertEqual(result["recommended_outcome"], "white_peace")
        self.assertTrue(result["pairwise"]["production_pairwise_ready"])
        self.assertFalse(result["production_recommendation_ready"])
        self.assertIn(
            "six_domain_v1_does_not_carry_connection_episode_or_pid",
            result["explicit_boundaries"],
        )
        self.assertFalse(result["action_ready"])

    def test_frozen_contract_keeps_current_checkpoint_typed_red(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["policy_version"], POLICY_VERSION)
        self.assertEqual(
            contract["owner_budget_profile_contract"],
            OWNER_BUDGET_PROFILE_CONTRACT,
        )
        self.assertEqual(
            contract["white_peace_comparison_contract"],
            WHITE_PEACE_COMPARISON_CONTRACT,
        )
        current = contract["current_g2_checkpoint"]
        self.assertEqual(current["status"], "evidence_required")
        self.assertIsNone(current["recommended_outcome"])
        self.assertFalse(current["action_ready"])
        self.assertIsNone(current["action_literal"])
        self.assertFalse(contract["readiness"]["production_live"])
        self.assertFalse(contract["readiness"]["gen_034_resolved"])


if __name__ == "__main__":
    unittest.main()
