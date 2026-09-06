#!/usr/bin/env python3
"""Focused contracts for the Phase2 exact full-tree completion gate."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_zhongguo_acceptance as capture  # noqa: E402


def _green_evidence() -> dict[str, object]:
    incident_checks = {
        "entry_event_identity_bound": True,
        "entry_option_materialized": True,
        "ack_not_used_as_result": True,
        "xyz_terminal_same_frame_ready": True,
        "xyz_profile_probe_receipts_frozen": True,
        "xyz_mixed_na_incident_matrix": True,
        "wrong_owner_acl_typed_red": True,
    }
    provider_postcondition = {
        "result": "GREEN",
        "provider_observed": True,
    }
    return {
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "completed_gameplay_action_cells": list(
            capture.PHASE2_REQUIRED_GAMEPLAY_ACTION_CELLS
        ),
        "completed_observation_only_cells": list(
            capture.PHASE2_REQUIRED_OBSERVATION_ONLY_CELLS
        ),
        "domain_restore_consistency": {"result": "GREEN"},
        "incident_gameplay_action_cell": {
            "result": "GREEN",
            "checks": incident_checks,
        },
        "b2_pip_gameplay_action_cell": {
            "result": "GREEN",
            "postcondition_query_green": True,
            "ack_is_postcondition": False,
            "postcondition": {"same_immutable_case": True},
        },
        "ai_owned_case_gameplay_action_cell": {
            "result": "GREEN",
            "gameplay_action_complete": True,
            "background_business_complete": True,
            "action_ack_is_business_postcondition": False,
        },
        "workforce_collective_gameplay_action_cell": {
            "result": "GREEN",
            "stage": "complete_and_baseline_restored",
            "checks": {"three_routes_green": True},
            "session_lineage": {
                "result": "GREEN",
                "baseline_restored": True,
            },
        },
        "promotion_compensation_gameplay_action_cell": {
            "result": "GREEN",
            "mcp_only": True,
            "action_ack_is_business_postcondition": False,
            "business_postcondition": provider_postcondition,
        },
        "manager_governance_gameplay_action_cell": {
            "result": "GREEN",
            "gameplay_action_complete": True,
            "action_ack_is_business_postcondition": False,
            "provider_observed_postcondition": {
                "status": "available",
                "readiness": {"ready": True},
            },
            "runner_checks": {"provider_checks_green": True},
        },
        "scoreboard_gameplay_action_cell": {
            "result": "GREEN",
            "gameplay_action_complete": True,
            "candidate_batch_complete": True,
            "all_postconditions_verified": True,
            "all_expected_acl_denials_verified": True,
            "per_surface_single_session_binding_verified": True,
            "cross_surface_clean_restart_verified": True,
            "production_capability_advertised": True,
            "promotion_eligible": True,
            "provider_observed_postcondition": provider_postcondition,
            "action_ack_is_business_postcondition": False,
        },
    }


class Phase2FullTreeCompletionGateTests(unittest.TestCase):
    def test_exact_full_tree_is_green(self) -> None:
        gate = capture._phase2_full_tree_completion_gate(_green_evidence())
        self.assertEqual(gate["result"], "GREEN")
        self.assertEqual(gate["missing_gameplay_action_cells"], [])
        self.assertEqual(gate["missing_observation_only_cells"], [])
        self.assertEqual(gate["incomplete_gameplay_action_evidence"], [])

    def test_missing_or_duplicate_cell_is_red(self) -> None:
        evidence = _green_evidence()
        actions = evidence["completed_gameplay_action_cells"]
        assert isinstance(actions, list)
        actions.remove("workforce_collective_gameplay_action_and_postcondition_matrix")
        actions.append("incident_xyz_gameplay_action_and_postcondition_matrix")
        gate = capture._phase2_full_tree_completion_gate(evidence)
        self.assertEqual(gate["result"], "RED")
        self.assertEqual(
            gate["missing_gameplay_action_cells"],
            ["workforce_collective_gameplay_action_and_postcondition_matrix"],
        )
        self.assertEqual(
            gate["duplicate_gameplay_action_cells"],
            ["incident_xyz_gameplay_action_and_postcondition_matrix"],
        )

    def test_ack_or_completed_label_cannot_replace_product_evidence(self) -> None:
        evidence = copy.deepcopy(_green_evidence())
        promotion = evidence[
            "promotion_compensation_gameplay_action_cell"
        ]
        assert isinstance(promotion, dict)
        promotion["business_postcondition"] = {
            "result": "GREEN",
            "provider_observed": False,
            "action_acknowledged": True,
        }
        gate = capture._phase2_full_tree_completion_gate(evidence)
        self.assertEqual(gate["result"], "RED")
        self.assertEqual(
            gate["incomplete_gameplay_action_evidence"],
            ["promotion_compensation_gameplay_action_and_postcondition_matrix"],
        )


if __name__ == "__main__":
    unittest.main()
