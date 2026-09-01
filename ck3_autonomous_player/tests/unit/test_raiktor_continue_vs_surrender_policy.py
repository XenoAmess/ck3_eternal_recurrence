from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    CAMPAIGN_CERTIFICATE_CONTRACT,
    POLICY_VERSION,
    assess_raiktor_continue_vs_surrender,
    canonical_policy_input_sha256,
)
from test_raiktor_surrender_six_domain_contract import (
    _aggregate as _six_domain_aggregate,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "raiktor_continue_vs_surrender_policy_v1_contract.json"
)


def _frame() -> dict[str, object]:
    return {
        "snapshot_id": "fixture-native:91",
        "snapshot_revision": 91,
        "native_revision": 7,
        "date_raw": 53_175_816,
        "connection_id": "fixture-connection-1",
        "episode_id": "fixture-native-29829-episode",
        "ck3_pid": 51_268,
        "paused": True,
        "war_id": 50_331_699,
        "active_casus_belli_database_index": 411,
        "active_casus_belli_key": "raiktor_claim_cb",
        "primary_attacker_character_id": 29_829,
        "primary_defender_character_id": 17_116,
        "claimant_character_id": 41_001,
    }


def _candidate() -> dict[str, object]:
    return {
        "schema_version": 1,
        "frame": _frame(),
        "played_character_id": 29_829,
        "player_is_primary_attacker": True,
        "player_war_score": -50,
        "war_duration_days": 1_281,
        "hostage_variant": "none",
        "surrender": {
            "context_constructed": True,
            "native_validator": True,
            "available": True,
            "auto_accept": True,
            "recipient_response": {
                "decision_status_raw": 0,
                "would_accept_now": True,
            },
        },
        "same_frame_stable": True,
    }


def _complete_terms() -> dict[str, object]:
    return deepcopy(_six_domain_aggregate())


def _current_incomplete_terms() -> dict[str, object]:
    return deepcopy(
        _six_domain_aggregate(
            missing=("truce", "generic_war_bound_current")
        )
    )


def _limits() -> dict[str, object]:
    return {
        "schema_version": 1,
        "profile_id": "synthetic-fixture-owner-budget-do-not-ship",
        "profile_provenance": "synthetic test fixture; not owner approved",
        "profile_production_eligible": False,
        "maximum_surrender_gold_transfer_raw": 30_000_000,
        "maximum_surrender_prestige_loss_raw": 100_000_000,
        "maximum_surrender_claims_removed": 1,
        "allow_surrender_favor_hook": True,
        "maximum_surrender_truce_days": 1_825,
        "maximum_continue_tail_loss_raw": 100,
        "minimum_switch_margin_raw": 10,
    }


def _campaign(
    terms: dict[str, object],
    limits: dict[str, object],
    *,
    safe_objective: bool,
    credible_reinforcement: bool,
    tail_loss_upper: int,
    continue_interval: tuple[int, int],
    surrender_interval: tuple[int, int],
    continue_breaches: list[str] | None = None,
    surrender_breaches: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract": CAMPAIGN_CERTIFICATE_CONTRACT,
        "status": "complete",
        "frame": _frame(),
        "evaluated_candidate_sha256": canonical_policy_input_sha256(
            _candidate()
        ),
        "evaluated_terms_sha256": canonical_policy_input_sha256(terms),
        "evaluated_limits_sha256": canonical_policy_input_sha256(limits),
        "producer": {
            "producer_id": "synthetic-fixture-campaign-evaluator",
            "producer_version": "v1",
            "source_artifact_sha256": "C" * 64,
            "utility_unit": "owner_utility_q100000",
            "tail_loss_unit": "owner_loss_q100000",
            "production_live": False,
        },
        "completeness": {
            "campaign_outcome_distribution_ready": True,
            "all_reasonable_encounters_evaluated": True,
            "mobilized_and_reserve_strength_ready": True,
            "reinforcement_and_siege_eta_ready": True,
            "finance_endurance_ready": True,
            "model_risk_included": True,
            "tail_risk_included": True,
            "sunk_cost_excluded": True,
            "all_six_domains_valued": True,
            "claims_base_valued": True,
        },
        "military_state": {
            "safe_objective_path_exists": safe_objective,
            "credible_reinforcement_before_next_decision": (
                credible_reinforcement
            ),
            "continue_tail_loss_upper_raw": tail_loss_upper,
        },
        "utility_bounds": {
            "continue_lower_raw": continue_interval[0],
            "continue_upper_raw": continue_interval[1],
            "surrender_lower_raw": surrender_interval[0],
            "surrender_upper_raw": surrender_interval[1],
        },
        "hard_budget_breaches": {
            "continue": list(continue_breaches or []),
            "surrender": list(surrender_breaches or []),
        },
        "same_frame_stable": True,
    }


class RaiktorContinueVsSurrenderPolicyTests(unittest.TestCase):
    def test_current_checkpoint_has_no_recommendation(self) -> None:
        result = assess_raiktor_continue_vs_surrender(
            _candidate(), _current_incomplete_terms(), None, _limits()
        )
        self.assertEqual(result["status"], "evidence_required")
        self.assertIsNone(result["suggested_action"])
        self.assertFalse(result["automatic_surrender_ready"])
        self.assertIsNone(result["action_literal"])
        self.assertIn("six_domain_terms_incomplete", result["terms_blockers"])
        self.assertIn(
            "campaign_dominance_certificate_unavailable",
            result["campaign_blockers"],
        )

    def test_explicit_certificate_only_prefers_surrender_pairwise(self) -> None:
        terms = _complete_terms()
        limits = _limits()
        campaign = _campaign(
            terms,
            limits,
            safe_objective=False,
            credible_reinforcement=False,
            tail_loss_upper=1_000,
            continue_interval=(-100, -50),
            surrender_interval=(0, 20),
            continue_breaches=["catastrophic_loss_budget"],
        )
        result = assess_raiktor_continue_vs_surrender(
            _candidate(), terms, campaign, limits
        )
        self.assertEqual(result["status"], "prefer_surrender_over_continue")
        self.assertEqual(
            result["pairwise_preference"],
            "prefer_surrender_over_continue",
        )
        self.assertTrue(result["pairwise_preference_ready"])
        self.assertFalse(result["full_exit_decision_ready"])
        self.assertFalse(result["white_peace_evaluated"])
        self.assertFalse(result["recommendation_ready"])
        self.assertIsNone(result["suggested_action"])
        self.assertEqual(result["surrender_margin_raw"], 50)
        self.assertFalse(result["automatic_surrender_ready"])
        self.assertIsNone(result["action_literal"])
        self.assertFalse(result["native_ai_equivalent"])
        self.assertFalse(result["semantic_optimal"])

    def test_explicit_certificate_only_prefers_continue_pairwise(self) -> None:
        terms = _complete_terms()
        limits = _limits()
        campaign = _campaign(
            terms,
            limits,
            safe_objective=True,
            credible_reinforcement=True,
            tail_loss_upper=50,
            continue_interval=(100, 150),
            surrender_interval=(0, 20),
        )
        result = assess_raiktor_continue_vs_surrender(
            _candidate(), terms, campaign, limits
        )
        self.assertEqual(result["status"], "prefer_continue_over_surrender")
        self.assertEqual(
            result["pairwise_preference"],
            "prefer_continue_over_surrender",
        )
        self.assertEqual(result["continue_margin_raw"], 80)
        self.assertFalse(result["automatic_surrender_ready"])
        self.assertFalse(result["production_pairwise_ready"])

    def test_overlapping_intervals_hold(self) -> None:
        terms = _complete_terms()
        limits = _limits()
        campaign = _campaign(
            terms,
            limits,
            safe_objective=False,
            credible_reinforcement=False,
            tail_loss_upper=1_000,
            continue_interval=(-10, 20),
            surrender_interval=(0, 30),
        )
        result = assess_raiktor_continue_vs_surrender(
            _candidate(), terms, campaign, limits
        )
        self.assertEqual(result["status"], "pairwise_underdetermined")
        self.assertIsNone(result["suggested_action"])
        self.assertIn(
            "surrender_utility_margin_not_met", result["surrender_blockers"]
        )
        self.assertIn(
            "continue_utility_margin_not_met", result["continue_blockers"]
        )

    def test_candidate_score_and_duration_are_hash_bound_not_hard_gates(
        self,
    ) -> None:
        terms = _complete_terms()
        limits = _limits()
        candidate = _candidate()
        candidate["player_war_score"] = -20
        candidate["war_duration_days"] = 100
        campaign = _campaign(
            terms,
            limits,
            safe_objective=False,
            credible_reinforcement=False,
            tail_loss_upper=1_000,
            continue_interval=(-100, -50),
            surrender_interval=(0, 20),
        )
        result = assess_raiktor_continue_vs_surrender(
            candidate, terms, campaign, limits
        )
        self.assertEqual(result["status"], "evidence_required")
        self.assertIn(
            "campaign_candidate_fingerprint_mismatch",
            result["campaign_blockers"],
        )

    def test_explicit_surrender_term_budget_blocks_pairwise_preference(
        self,
    ) -> None:
        terms = _complete_terms()
        limits = _limits()
        limits["maximum_surrender_gold_transfer_raw"] = 14_999_999
        campaign = _campaign(
            terms,
            limits,
            safe_objective=False,
            credible_reinforcement=False,
            tail_loss_upper=1_000,
            continue_interval=(-100, -50),
            surrender_interval=(0, 20),
        )
        result = assess_raiktor_continue_vs_surrender(
            _candidate(), terms, campaign, limits
        )
        self.assertEqual(result["status"], "pairwise_underdetermined")
        self.assertIsNone(result["suggested_action"])
        self.assertIn(
            "surrender_gold_budget_breached", result["surrender_blockers"]
        )

    def test_missing_campaign_field_fails_closed(self) -> None:
        terms = _complete_terms()
        limits = _limits()
        campaign = _campaign(
            terms,
            limits,
            safe_objective=False,
            credible_reinforcement=False,
            tail_loss_upper=1_000,
            continue_interval=(-100, -50),
            surrender_interval=(0, 20),
        )
        campaign["completeness"]["finance_endurance_ready"] = False
        campaign["status"] = "incomplete"
        result = assess_raiktor_continue_vs_surrender(
            _candidate(), terms, campaign, limits
        )
        self.assertEqual(result["status"], "evidence_required")
        self.assertIsNone(result["suggested_action"])
        self.assertIn(
            "finance_endurance_ready_required", result["campaign_blockers"]
        )

    def test_stale_terms_or_limits_fingerprint_fails_closed(self) -> None:
        terms = _complete_terms()
        limits = _limits()
        campaign = _campaign(
            terms,
            limits,
            safe_objective=False,
            credible_reinforcement=False,
            tail_loss_upper=1_000,
            continue_interval=(-100, -50),
            surrender_interval=(0, 20),
        )
        campaign["evaluated_terms_sha256"] = "A" * 64
        campaign["evaluated_limits_sha256"] = "B" * 64
        result = assess_raiktor_continue_vs_surrender(
            _candidate(), terms, campaign, limits
        )
        self.assertEqual(result["status"], "evidence_required")
        self.assertIn(
            "campaign_terms_fingerprint_mismatch",
            result["campaign_blockers"],
        )
        self.assertIn(
            "campaign_limits_fingerprint_mismatch",
            result["campaign_blockers"],
        )

    def test_cross_frame_campaign_fails_closed(self) -> None:
        terms = _complete_terms()
        limits = _limits()
        campaign = _campaign(
            terms,
            limits,
            safe_objective=False,
            credible_reinforcement=False,
            tail_loss_upper=1_000,
            continue_interval=(-100, -50),
            surrender_interval=(0, 20),
        )
        campaign["frame"]["date_raw"] += 24
        result = assess_raiktor_continue_vs_surrender(
            _candidate(), terms, campaign, limits
        )
        self.assertEqual(result["status"], "evidence_required")
        self.assertIn("campaign_frame_mismatch", result["campaign_blockers"])

    def test_played_character_must_match_primary_attacker(self) -> None:
        candidate = _candidate()
        candidate["played_character_id"] = 17_116
        result = assess_raiktor_continue_vs_surrender(
            candidate, _current_incomplete_terms(), None, _limits()
        )
        self.assertEqual(result["status"], "evidence_required")
        self.assertIsNone(result["suggested_action"])
        self.assertIn(
            "played_character_must_be_primary_attacker",
            result["candidate_blockers"],
        )

    def test_terms_cannot_promote_unproven_readiness(self) -> None:
        for key in (
            "automatic_surrender_ready",
            "source_specific_war_bound_ready",
            "pre_soldiers_ready",
            "proven_soldier_loss_ready",
        ):
            with self.subTest(key=key):
                terms = _complete_terms()
                terms["readiness"][key] = True
                with self.assertRaises(ValueError):
                    assess_raiktor_continue_vs_surrender(
                        _candidate(), terms, None, _limits()
                    )

    def test_terms_must_preserve_attacker_defeat_claim_semantics(self) -> None:
        terms = _complete_terms()
        terms["claims_base"]["payload"]["attacker_defeat"][
            "claim_disposition"
        ] = "retain_declared_target_claims"
        with self.assertRaises(ValueError):
            assess_raiktor_continue_vs_surrender(
                _candidate(), terms, None, _limits()
            )

    def test_inverted_utility_interval_is_rejected(self) -> None:
        terms = _complete_terms()
        limits = _limits()
        campaign = _campaign(
            terms,
            limits,
            safe_objective=False,
            credible_reinforcement=False,
            tail_loss_upper=1_000,
            continue_interval=(10, -10),
            surrender_interval=(0, 20),
        )
        with self.assertRaises(ValueError):
            assess_raiktor_continue_vs_surrender(
                _candidate(), terms, campaign, limits
            )

    def test_frozen_contract_keeps_current_action_closed(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["policy_version"], POLICY_VERSION)
        self.assertEqual(
            contract["campaign_certificate_contract"],
            CAMPAIGN_CERTIFICATE_CONTRACT,
        )
        current = contract["current_g2_checkpoint"]
        self.assertIsNone(current["pairwise_preference"])
        self.assertFalse(current["full_exit_decision_ready"])
        self.assertFalse(current["white_peace_evaluated"])
        self.assertIsNone(current["suggested_action"])
        self.assertFalse(current["automatic_surrender_ready"])
        boundaries = contract["hard_boundaries"]
        self.assertTrue(boundaries["pairwise_preference_only"])
        self.assertFalse(boundaries["recommendation_ready"])
        self.assertFalse(boundaries["full_exit_decision_ready"])
        self.assertFalse(boundaries["white_peace_evaluated"])
        self.assertIsNone(boundaries["action_literal"])
        self.assertFalse(boundaries["automatic_surrender_ready"])
        self.assertFalse(boundaries["native_ai_equivalent"])
        self.assertFalse(boundaries["semantic_optimal"])
        self.assertFalse(contract["readiness"]["gen_034_resolved"])
        repository_root = ROOT.parent
        for entry in contract["frozen_inputs"]:
            with self.subTest(path=entry["path"]):
                digest = hashlib.sha256(
                    (repository_root / entry["path"]).read_bytes()
                ).hexdigest().upper()
                self.assertEqual(digest, entry["sha256"])


if __name__ == "__main__":
    unittest.main()
