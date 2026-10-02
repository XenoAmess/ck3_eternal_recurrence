"""Offline behavior tests for the recovered read-only bridge entry points."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, _action_steps
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.defender_dejure_exit_terms_v1 import CAPABILITY
from test_defender_dejure_exit_terms_v1 import _candidate
from test_h2743_preaction_existing_truce_v1 import starting_frame
from test_current_battle_knight_v1_port import REQUEST, raw_result


class RecoveredReadonlyBridgeTests(unittest.TestCase):
    def test_generic_baseline_preserves_prestate_and_unavailable_outcomes(self) -> None:
        driver = object.__new__(NativeHeadlessGameplayDriver)
        before = starting_frame(3)
        response = {
            "step": "query-defender-de-jure-exit-terms-v1-16777231",
            "accepted": True, "status": "baseline_only", "query_sequence": 1,
            "backend_id": "native-headless",
            "defender_de_jure_exit_terms_v1": _candidate(),
        }
        with (
            patch.object(driver, "take_internal_semantic_snapshot",
                         side_effect=[before, copy.deepcopy(before)]),
            patch.object(driver, "_execute_primitive_step", return_value=response) as primitive,
        ):
            result = driver._execute_native_war_step(
                response["step"], expected_revision=before["revision"])
        primitive.assert_called_once()
        baseline = result["defender_de_jure_exit_terms_v1"]
        self.assertEqual(len(baseline["primary_resource_balances"]), 14)
        self.assertFalse(baseline["material_complete"])
        self.assertIsNone(baseline["title_vassal_delta"])
        self.assertIsNone(baseline["directed_truce"])
        self.assertIsNone(baseline["action_literal"])
        self.assertEqual(result["queried_revision"], 4)
        self.assertEqual(result["queried_native_revision"], 3)

    def test_baseline_refuses_frame_drift_and_unpaused_query(self) -> None:
        for paused, drift in ((True, True), (False, False)):
            driver = object.__new__(NativeHeadlessGameplayDriver)
            before = starting_frame(3)
            before["paused"] = paused
            after = copy.deepcopy(before)
            if drift:
                after["native_revision"] += 1
            response = {
                "step": "query-defender-de-jure-exit-terms-v1-16777231",
                "accepted": True, "status": "baseline_only", "query_sequence": 1,
                "backend_id": "native-headless",
                "defender_de_jure_exit_terms_v1": _candidate(),
            }
            with (
                self.subTest(paused=paused, drift=drift),
                patch.object(driver, "take_internal_semantic_snapshot",
                             side_effect=[before, after]),
                patch.object(driver, "_execute_primitive_step", return_value=response) as primitive,
            ):
                with self.assertRaises(BridgeUnavailableError):
                    driver._execute_native_war_step(
                        response["step"], expected_revision=before["revision"])
                if not paused:
                    primitive.assert_not_called()

    def test_stock_admitted_baseline_uses_current_provenance_consumer(self) -> None:
        driver = object.__new__(NativeHeadlessGameplayDriver)
        driver._h2743_stock_predicate_admission = object()
        before = starting_frame(3)
        with patch(
            "xar_autoplayer.bridge.h2743_exit_readonly_transport.query_h2743_exit_baseline",
            return_value={"current_stock_path": True},
        ) as current:
            result = driver._execute_defender_dejure_exit_terms_v1_query(
                "query-defender-de-jure-exit-terms-v1-16777231",
                starting=before, selected_revision=4, war_id=16777231)
            self.assertEqual(result, {"current_stock_path": True})
            current.assert_called_once_with(driver, expected_frame=before)
            with self.assertRaisesRegex(BridgeUnavailableError, "expected revision"):
                driver._execute_defender_dejure_exit_terms_v1_query(
                    "query-defender-de-jure-exit-terms-v1-16777231",
                    starting=before, selected_revision=3, war_id=16777231)
            self.assertEqual(current.call_count, 1)

    def test_research_baseline_is_not_a_planner_action(self) -> None:
        before = starting_frame(3)
        steps = _action_steps(
            [CAPABILITY], active_wars=before["active_wars"], paused=True)
        self.assertFalse(any("defender-de-jure-exit-terms" in step for step in steps))

    def test_knight_service_and_mcp_facade_forward_both_revision_domains(self) -> None:
        service = object.__new__(GameplayBridgeService)
        service.driver = Mock()
        response = raw_result()
        service.driver.query_current_battle_knight_v1.return_value = response
        result = mcp_server._ck3_query_current_battle_knight_v1(service, **REQUEST)
        self.assertEqual(result, response)
        service.driver.query_current_battle_knight_v1.assert_called_once_with(**REQUEST)

    def test_private_snapshot_flag_rejects_other_drivers_and_http_before_loading(self) -> None:
        for driver, transport in (("vision-report", "stdio"),
                                  ("native-headless", "streamable-http")):
            with self.subTest(driver=driver, transport=transport), patch.object(
                mcp_server, "load_driver"
            ) as load_driver:
                with self.assertRaisesRegex(ValueError, "native-headless stdio"):
                    mcp_server.main([
                        "--driver", driver, "--transport", transport,
                        "--private-semantic-snapshot-readonly",
                    ])
                load_driver.assert_not_called()


if __name__ == "__main__":
    unittest.main()
