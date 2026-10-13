from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.ordinary_player_risk_context_v1 import (
    build_ordinary_player_risk_context_v1,
)
from test_turn_bundle_v1 import _root, _snapshot


def _observed_root():
    snapshot = _snapshot()
    result = _root()
    result.update(
        queried_snapshot_id=snapshot["snapshot_id"],
        queried_revision=snapshot["revision"],
        queried_native_revision=snapshot["native_revision"],
    )
    return result


class OrdinaryPlayerRiskContextV1Tests(unittest.TestCase):
    def test_current_low_health_and_split_risk_are_compact_detached_evidence(self):
        snapshot, root = _snapshot(), _observed_root()
        before = copy.deepcopy((snapshot, root))
        context = build_ordinary_player_risk_context_v1(snapshot, root)
        self.assertEqual(context["status"], "partial")
        self.assertEqual(context["health"]["value"]["band"], "below_fine")
        self.assertTrue(context["alerts"]["succession_partition_split"]["value"])
        self.assertEqual(context["planner_signals"]["succession_preparation_priority"]["value"], "elevated")
        self.assertEqual(context["planner_signals"]["protect_legitimacy_floor"]["status"], "unavailable")
        self.assertEqual((snapshot, root), before)
        context["health"]["value"]["raw"] = 0
        self.assertEqual(root["campaign_root_context"]["player_health"]["raw"], 275000)
        self.assertNotIn("selected_step", context)
        self.assertNotIn("held_title_partition", json.dumps(context))
        self.assertLess(len(json.dumps(context).encode()), 4096)

    def test_healthy_and_dying_no_heir_use_existing_signal_rules(self):
        for raw, heirs, priority, low in (
            (300000, [88, 77], "normal", False),
            (150000, [], "critical", True),
        ):
            with self.subTest(raw=raw):
                root = _observed_root()
                root["campaign_root_context"]["player_health"]["raw"] = raw
                root["campaign_root_context"]["primary_title_succession_character_ids"] = heirs
                if not heirs:
                    root["campaign_root_context"]["held_title_partition"][0]["first_heir_character_id"] = None
                result = build_ordinary_player_risk_context_v1(_snapshot(), root)
                self.assertEqual(result["alerts"]["ruler_health_below_fine"]["value"], low)
                self.assertEqual(result["planner_signals"]["succession_preparation_priority"]["value"], priority)

    def test_missing_stress_and_partial_council_preserve_known_health(self):
        snapshot, root = _snapshot(), _observed_root()
        snapshot["played_character"].pop("stress_points")
        root["campaign_root_context"]["council"] = {
            "status": "unavailable", "unavailable_reason": "outside_standard_landed_non_nomadic_core_scope",
        }
        result = build_ordinary_player_risk_context_v1(snapshot, root)
        self.assertTrue(result["readiness"]["health_ready"])
        self.assertFalse(result["readiness"]["stress_ready"])
        self.assertEqual(result["planner_signals"]["succession_preparation_priority"]["value"], "elevated")
        self.assertEqual(result["stress"]["status"], "unavailable")

    def test_native_history_binding_uses_observed_fields_without_defaults(self):
        root = _observed_root()
        root.pop("binding")
        result = build_ordinary_player_risk_context_v1(_snapshot(), root)
        self.assertEqual(result["health"]["status"], "available")
        self.assertNotIn("binding", root)
        root.pop("queried_native_revision")
        self.assertEqual(build_ordinary_player_risk_context_v1(_snapshot(), root)["status"], "unavailable")

    def test_stale_binding_actor_generation_and_malformed_health_are_rejected(self):
        for field, wrong in (
            ("snapshot_id", "native:old"), ("revision", 99),
            ("native_revision", 99), ("date_raw", 0),
            ("character_id", 99), ("connection_generation", 3), ("health_scale", 1),
        ):
            with self.subTest(field=field):
                snapshot, root = _snapshot(), _observed_root()
                if field == "character_id":
                    snapshot["played_character"][field] = wrong
                elif field == "connection_generation":
                    snapshot["diagnostics"] = {field: wrong}
                    # This exercises only an optional supplied witness; the
                    # ordinary fixture and real Driver case never invent it.
                    root["queried_connection_generation"] = 2
                elif field == "health_scale":
                    root["campaign_root_context"]["player_health"]["scale"] = wrong
                else:
                    snapshot[field] = wrong
                result = build_ordinary_player_risk_context_v1(snapshot, root)
                self.assertEqual(result["status"], "unavailable")
                self.assertFalse(any(result["readiness"].values()))

    def test_actual_native_driver_root_history_projects_without_response_generation(self):
        from test_campaign_root_context_v1_bridge import (
            STEP, _answer_with, _native_driver, _native_result,
        )
        driver, endpoint = _native_driver()
        try:
            _answer_with(endpoint, _native_result)
            snapshot = driver.take_snapshot()
            result = driver.execute_step(STEP, expected_revision=snapshot["revision"])
            current = driver.take_snapshot()
            history_result = current["native_command_history"][-1]["result"]
            self.assertNotIn("queried_connection_generation", result)
            self.assertNotIn("queried_connection_generation", history_result)
            self.assertGreater(current["diagnostics"]["connection_generation"], 0)
            sent_before = len(endpoint.frames)
            context = build_ordinary_player_risk_context_v1(current, history_result)
            self.assertEqual(context["health"]["status"], "available")
            self.assertEqual(context["health"]["value"]["raw"], 275000)
            self.assertEqual(context["binding"]["native_revision"], current["native_revision"])
            self.assertEqual(context["current_scope"]["connection_generation"],
                             current["diagnostics"]["connection_generation"])
            self.assertFalse(context["current_scope"]["response_connection_generation_observed"])
            self.assertNotIn("connection_generation", context["binding"])
            self.assertEqual(len(endpoint.frames), sent_before)
            self.assertEqual(driver._campaign_root_context_query["cache_binding"]["connection_generation"],
                             current["diagnostics"]["connection_generation"])
        finally:
            driver.close()

    def test_absent_or_unavailable_root_never_retains_a_previous_risk(self):
        available = build_ordinary_player_risk_context_v1(_snapshot(), _observed_root())
        self.assertTrue(available["readiness"]["health_ready"])
        for root in (None, _root(available=False)):
            with self.subTest(root=root is None):
                context = build_ordinary_player_risk_context_v1(_snapshot(), root)
                self.assertEqual(context["status"], "unavailable")
                self.assertIsNone(context["binding"])
                self.assertIsNone(context["health"]["value"])


if __name__ == "__main__":
    unittest.main()
