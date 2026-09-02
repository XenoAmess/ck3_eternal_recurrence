from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from xar_autoplayer.simulation.raiktor_surrender_execution_policy import (
    POLICY_VERSION,
    POSTCONDITION_REQUIREMENTS,
    project_raiktor_surrender_execution_readiness,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_policy import (
    assess_raiktor_three_way_exit,
)
from test_raiktor_continue_vs_surrender_policy import (
    _candidate,
    _current_incomplete_terms,
)
from test_raiktor_three_way_exit_policy import _complete_inputs


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "raiktor_surrender_execution_policy_v1_contract.json"
)


def _static_surrender_winner() -> tuple[dict[str, object], ...]:
    inputs = _complete_inputs(
        continue_interval=(-100, -50),
        surrender_interval=(100, 120),
        white_interval=(0, 20),
    )
    decision = assess_raiktor_three_way_exit(*inputs)
    return decision, inputs[0], inputs[1]


class RaiktorSurrenderExecutionPolicyTests(unittest.TestCase):
    def test_current_checkpoint_has_typed_decision_and_terms_blockers(
        self,
    ) -> None:
        candidate = _candidate()
        terms = _current_incomplete_terms()
        decision = assess_raiktor_three_way_exit(
            candidate, terms, None, None, None
        )

        result = project_raiktor_surrender_execution_readiness(
            decision, candidate, terms
        )

        self.assertEqual(result["policy_version"], POLICY_VERSION)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["decision"]["ready"])
        self.assertIn(
            "three_way_static_surrender_recommendation_required",
            result["decision"]["blockers"],
        )
        self.assertIn(
            "production_recommendation_not_ready",
            result["decision"]["blockers"],
        )
        self.assertIn("truce_not_ready", result["terms"]["blockers"])
        self.assertIn(
            "truce_evaluated_days_not_ready",
            result["terms"]["blockers"],
        )
        self.assertIn(
            "generic_war_bound_current_not_ready",
            result["terms"]["blockers"],
        )
        self.assertIsNone(result["action"]["literal"])
        self.assertFalse(result["postcondition"]["verified"])

    def test_static_surrender_winner_still_cannot_emit_literal(self) -> None:
        decision, candidate, terms = _static_surrender_winner()
        self.assertTrue(decision["static_recommendation_ready"])
        self.assertEqual(decision["recommended_outcome"], "surrender")

        result = project_raiktor_surrender_execution_readiness(
            decision, candidate, terms
        )

        self.assertEqual(result["decision"]["recommended_outcome"], "surrender")
        self.assertFalse(result["decision"]["ready"])
        self.assertTrue(result["terms"]["action_terms_ready"])
        self.assertTrue(result["terms"]["truce_evaluated_days_ready"])
        self.assertFalse(result["terms"]["truce_expiry_ready"])
        self.assertFalse(result["terms"]["session_provenance_ready"])
        self.assertIn(
            "six_domain_session_provenance_not_bound",
            result["terms"]["blockers"],
        )
        self.assertIn(
            "truce_expiry_not_observable", result["terms"]["blockers"]
        )
        self.assertIn(
            "source_specific_war_bound_not_ready",
            result["terms"]["blockers"],
        )
        self.assertIn(
            "typed_surrender_submit_not_enabled",
            result["action"]["blockers"],
        )
        self.assertFalse(result["action"]["ready"])
        self.assertFalse(result["action"]["automatic_surrender_ready"])
        self.assertIsNone(result["action"]["literal"])

    def test_postcondition_contract_rejects_ack_and_war_absence_shortcuts(
        self,
    ) -> None:
        decision, candidate, terms = _static_surrender_winner()
        post = project_raiktor_surrender_execution_readiness(
            decision, candidate, terms
        )["postcondition"]

        self.assertFalse(post["ack_is_postcondition"])
        self.assertFalse(post["war_id_absence_is_full_postcondition"])
        self.assertEqual(
            post["requirements"], list(POSTCONDITION_REQUIREMENTS)
        )
        self.assertEqual(len(post["requirements"]), 8)
        self.assertIn(
            "truce_expiry_post_state_observer_not_ready", post["blockers"]
        )
        self.assertIn(
            "source_specific_war_bound_cleanup_observer_not_ready",
            post["blockers"],
        )

    def test_decision_cannot_be_reused_for_another_candidate(self) -> None:
        decision, candidate, terms = _static_surrender_winner()
        other = deepcopy(candidate)
        other["player_war_score"] = -49

        with self.assertRaisesRegex(ValueError, "another candidate"):
            project_raiktor_surrender_execution_readiness(
                decision, other, terms
            )

    def test_frozen_contract_keeps_current_action_closed(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["policy_version"], POLICY_VERSION)
        current = contract["current_g2_checkpoint"]
        self.assertFalse(current["decision_ready"])
        self.assertFalse(current["action_ready"])
        self.assertIsNone(current["action_literal"])
        self.assertFalse(current["postcondition_ready"])
        self.assertFalse(current["automatic_surrender_ready"])
        self.assertEqual(
            contract["postcondition_requirements"],
            list(POSTCONDITION_REQUIREMENTS),
        )
        boundaries = contract["hard_boundaries"]
        self.assertFalse(boundaries["ack_is_postcondition"])
        self.assertFalse(boundaries["war_id_absence_is_full_postcondition"])
        self.assertFalse(boundaries["evaluated_days_implies_expiry"])
        self.assertFalse(boundaries["generic_war_bound_is_source_specific"])


if __name__ == "__main__":
    unittest.main()
