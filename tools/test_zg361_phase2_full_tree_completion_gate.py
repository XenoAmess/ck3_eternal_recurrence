#!/usr/bin/env python3
"""Focused contracts for the Phase2 P1 critical-path completion gate."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


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
    digest = "a" * 64
    return {
        "loaded_candidate_tree_sha256": digest,
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
        "p1_acceptance_evidence": {
            "b1_fix_live": {
                "result": "GREEN",
                "production_live": True,
                "fix_verified": True,
                "product_red": False,
            },
            "af5_terminal_authored_42_native_41": {
                "result": "GREEN",
                "event_definition_key": "zg361comp.1",
                "selected_option_number": 42,
                "selected_native_option_index": 41,
                "provider_observed": True,
                "terminal_postcondition_verified": True,
                "action_ack_is_business_postcondition": False,
            },
            "central_stage_terminals": {
                str(stage): {
                    "result": "GREEN",
                    "stage": stage,
                    "event_definition_key": (
                        capture.PHASE2_P1_STAGE_TERMINAL_EVENTS.get(
                            stage, "zg361we.360"
                        )
                    ),
                    "provider_domain": "workforce" if stage == 11 else "central",
                    "terminal_state": "closed" if stage == 11 else "complete",
                    "provider_observed": True,
                    "terminal_postcondition_verified": True,
                }
                for stage in (9, 10, 11)
            },
            "representative_terminal_cold_restore": {
                "result": "GREEN",
                "save_result": {
                    "accepted": True,
                    "checkpoint": {
                        "status": "saved",
                        "sha256": digest,
                    },
                },
                "restore_result": {
                    "accepted": True,
                    "status": "restored",
                },
                "pid_lineage": [372, 373],
                "connection_generation_lineage": [7, 8],
                "before_readback": {
                    domain: {
                        "identity": {"key": f"{domain}-terminal"},
                        "state": {"terminal": True},
                        "receipt": {"revision": 101 + offset},
                    }
                    for offset, domain in enumerate(
                        ("b1", "af5", "central", "workforce")
                    )
                },
            },
            "runtime_error_scan": {
                "result": "GREEN",
                "full_gameplay_window_scanned": True,
                "blocking_diagnostics": [],
            },
            "managed_cleanup": {
                "result": "GREEN",
                "cleanup_proven": True,
                "contract_errors": [],
            },
            "final_candidate_l0": {
                "result": "GREEN",
                "full_l0": True,
                "candidate_sha256": digest,
                "tested_candidate_sha256": digest,
            },
        },
        # Explicitly incomplete historical/P2-only counters do not belong to
        # the P1 critical-path decision.
        "canonical_source_registry_count": 3,
        "canonical_source_registry_total": 4,
        "third_zg361we_356_observed": False,
        "workforce_cycle_count": 1,
        "promo_footage_count": 0,
        "promo_footage_total": 8,
    }


def _finish_restore_readback(evidence: dict[str, object]) -> None:
    p1 = evidence["p1_acceptance_evidence"]
    assert isinstance(p1, dict)
    restore = p1["representative_terminal_cold_restore"]
    assert isinstance(restore, dict)
    restore["after_readback"] = copy.deepcopy(restore["before_readback"])


class Phase2FullTreeCompletionGateTests(unittest.TestCase):
    def test_complete_critical_path_is_green(self) -> None:
        evidence = _green_evidence()
        _finish_restore_readback(evidence)
        gate = capture._phase2_full_tree_completion_gate(evidence)
        self.assertEqual(gate["result"], "GREEN")
        self.assertEqual(gate["missing_p1_evidence"], [])
        self.assertEqual(gate["missing_gameplay_action_cells"], [])
        self.assertEqual(gate["missing_observation_only_cells"], [])
        self.assertEqual(gate["incomplete_gameplay_action_evidence"], [])
        self.assertTrue(gate["coverage_non_blocking"])

    def test_missing_duplicate_and_unknown_legacy_cells_are_non_blocking(self) -> None:
        evidence = _green_evidence()
        _finish_restore_readback(evidence)
        actions = evidence["completed_gameplay_action_cells"]
        assert isinstance(actions, list)
        actions.remove("workforce_collective_gameplay_action_and_postcondition_matrix")
        actions.append("incident_xyz_gameplay_action_and_postcondition_matrix")
        actions.append("retained_historical_action")
        observations = evidence["completed_observation_only_cells"]
        assert isinstance(observations, list)
        observations.pop()
        gate = capture._phase2_full_tree_completion_gate(evidence)
        self.assertEqual(gate["result"], "GREEN")
        self.assertEqual(
            gate["missing_gameplay_action_cells"],
            ["workforce_collective_gameplay_action_and_postcondition_matrix"],
        )
        self.assertEqual(
            gate["duplicate_gameplay_action_cells"],
            ["incident_xyz_gameplay_action_and_postcondition_matrix"],
        )
        self.assertEqual(
            gate["unknown_gameplay_action_cells"],
            ["retained_historical_action"],
        )
        self.assertFalse(gate["coverage"]["exact_legacy_inventory_complete"])

    def test_each_p1_hard_item_remains_blocking(self) -> None:
        mutators = {
            "b1_fix_live": lambda p1: p1.pop("b1_fix_live"),
            "af5_terminal_authored_42_native_41": lambda p1: p1[
                "af5_terminal_authored_42_native_41"
            ].update(selected_native_option_index=39),
            "central_stage_9_terminal": lambda p1: p1[
                "central_stage_terminals"
            ].pop("9"),
            "central_stage_10_terminal": lambda p1: p1[
                "central_stage_terminals"
            ]["10"].update(provider_observed=False),
            "central_stage_11_terminal": lambda p1: p1[
                "central_stage_terminals"
            ]["11"].update(terminal_postcondition_verified=False),
            "representative_terminal_cold_restore": lambda p1: p1[
                "representative_terminal_cold_restore"
            ]["after_readback"]["central"]["state"].update(terminal=False),
            "runtime_error_scan": lambda p1: p1[
                "runtime_error_scan"
            ].update(blocking_diagnostics=["script_error"]),
            "managed_cleanup": lambda p1: p1[
                "managed_cleanup"
            ].update(cleanup_proven=False),
            "final_candidate_l0": lambda p1: p1[
                "final_candidate_l0"
            ].update(tested_candidate_sha256="b" * 64),
        }
        self.assertEqual(
            tuple(mutators), capture.PHASE2_P1_REQUIRED_EVIDENCE
        )
        for missing_name, mutate in mutators.items():
            with self.subTest(missing_name=missing_name):
                evidence = copy.deepcopy(_green_evidence())
                _finish_restore_readback(evidence)
                p1 = evidence["p1_acceptance_evidence"]
                assert isinstance(p1, dict)
                mutate(p1)
                gate = capture._phase2_full_tree_completion_gate(evidence)
                self.assertEqual(gate["result"], "RED")
                self.assertEqual(gate["missing_p1_evidence"], [missing_name])

    def test_ack_cannot_replace_af5_terminal_postcondition(self) -> None:
        evidence = copy.deepcopy(_green_evidence())
        _finish_restore_readback(evidence)
        p1 = evidence["p1_acceptance_evidence"]
        assert isinstance(p1, dict)
        af5 = p1["af5_terminal_authored_42_native_41"]
        assert isinstance(af5, dict)
        af5.update(
            provider_observed=False,
            terminal_postcondition_verified=False,
            action_acknowledged=True,
        )
        gate = capture._phase2_full_tree_completion_gate(evidence)
        self.assertEqual(gate["result"], "RED")
        self.assertEqual(
            gate["missing_p1_evidence"],
            ["af5_terminal_authored_42_native_41"],
        )

    def test_stage_11_requires_workforce_terminal_but_not_361(self) -> None:
        evidence = copy.deepcopy(_green_evidence())
        _finish_restore_readback(evidence)
        p1 = evidence["p1_acceptance_evidence"]
        assert isinstance(p1, dict)
        stage_11 = p1["central_stage_terminals"]["11"]
        assert isinstance(stage_11, dict)
        self.assertEqual(stage_11["event_definition_key"], "zg361we.360")
        gate = capture._phase2_full_tree_completion_gate(evidence)
        self.assertEqual(gate["result"], "GREEN")

        stage_11["provider_domain"] = "central"
        gate = capture._phase2_full_tree_completion_gate(evidence)
        self.assertEqual(gate["result"], "RED")
        self.assertEqual(
            gate["missing_p1_evidence"], ["central_stage_11_terminal"]
        )

    def test_default_scenario_skips_legacy_full_tree_cells(self) -> None:
        evidence_packet = _green_evidence()
        _finish_restore_readback(evidence_packet)
        p1 = evidence_packet["p1_acceptance_evidence"]
        assert isinstance(p1, dict)
        paused_binding = {
            "bridge_pid": 372,
            "connection_generation": 7,
            "player_character_id": 9001,
            "revision": 101,
            "date_raw": 5000,
        }

        class ManifestService:
            def query_loaded_feature_manifest_v1(
                self, *, expected_revision: int
            ) -> dict[str, object]:
                self.expected_revision = expected_revision
                return {"loaded_feature_manifest_ready": True}

        service = ManifestService()
        with tempfile.TemporaryDirectory() as raw_directory:
            artifacts = Path(raw_directory)
            with (
                mock.patch.object(
                    capture,
                    "wait_for_phase2_paused_snapshot",
                    return_value={"snapshot": "unit"},
                ),
                mock.patch.object(
                    capture,
                    "_phase2_paused_binding",
                    return_value=paused_binding,
                ),
                mock.patch.object(
                    capture,
                    "prove_phase2_loaded_seed",
                    return_value={"result": "GREEN"},
                ),
                mock.patch.object(
                    capture, "run_phase2_incident_gameplay_action_cell"
                ) as legacy_incident,
                mock.patch.object(
                    capture,
                    "run_phase2_manager_governance_gameplay_action_cell",
                ) as legacy_manager,
                mock.patch.object(
                    capture, "run_phase2_scoreboard_gameplay_action_cell"
                ) as legacy_scoreboard,
                mock.patch.object(
                    capture,
                    "run_phase2_workforce_m360_gameplay_action_cell",
                ) as legacy_workforce,
                mock.patch.object(
                    capture,
                    "run_phase2_full_tree_promotion_compensation_cell",
                ) as legacy_promotion,
            ):
                result = capture.run_phase2_live_scenario(
                    service,
                    artifacts,
                    tracked_ck3_pid=372,
                    seed_contract={"kind": "unit"},
                    bootstrap={"tree_sha256": {"product": "a" * 64}},
                    p1_acceptance_evidence=p1,
                )

        self.assertEqual(service.expected_revision, 101)
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["execution_mode"], "p1_critical_path")
        self.assertTrue(result["phase2_acceptance_complete"])
        self.assertFalse(
            result["full_tree_completion_gate"]["coverage"][
                "exact_legacy_inventory_complete"
            ]
        )
        for legacy_call in (
            legacy_incident,
            legacy_manager,
            legacy_scoreboard,
            legacy_workforce,
            legacy_promotion,
        ):
            legacy_call.assert_not_called()

    def test_capability_preflight_uses_narrow_default_and_opt_in_legacy(self) -> None:
        capability_packet = {
            "mode": "native-headless",
            "backend_id": "native-headless",
            "visual_fallback": False,
            "snapshot": True,
            "bridge_capabilities": [
                capture.PHASE2_REQUIRED_BRIDGE_CAPABILITIES[label]
                for label in capture.PHASE2_P1_REQUIRED_BRIDGE_CAPABILITY_LABELS
            ],
            "action_steps": [
                capture.PHASE2_REQUIRED_ACTION_STEPS[label]
                for label in capture.PHASE2_P1_REQUIRED_ACTION_STEP_LABELS
            ],
            **{
                capture.PHASE2_REQUIRED_QUERY_FLAGS[label]: True
                for label in capture.PHASE2_P1_REQUIRED_QUERY_FLAG_LABELS
            },
            "diagnostics": {
                "connected": True,
                "bridge_pid": 372,
                "connection_generation": 7,
            },
        }

        class CapabilityService:
            def capabilities(self) -> dict[str, object]:
                return copy.deepcopy(capability_packet)

        with tempfile.TemporaryDirectory() as raw_directory:
            artifacts = Path(raw_directory)
            critical = capture.phase2_runtime_capability_preflight(
                CapabilityService(),
                artifacts,
                tracked_ck3_pid=372,
            )
            self.assertEqual(critical["result"], "GREEN")
            self.assertEqual(
                critical["scope"],
                "p1_critical_path_mcp_capability_profile",
            )

        with tempfile.TemporaryDirectory() as raw_directory:
            with self.assertRaises(capture.acceptance.RunnerError):
                capture.phase2_runtime_capability_preflight(
                    CapabilityService(),
                    Path(raw_directory),
                    tracked_ck3_pid=372,
                    managed_restore_supervisor=True,
                    legacy_full_tree_coverage=True,
                )


if __name__ == "__main__":
    unittest.main()
