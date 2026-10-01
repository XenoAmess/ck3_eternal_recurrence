"""Actual 1.20 Feast counter reader/serializer output through Python reads."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from test_ck3_12002_feast_wire import FixtureDriver, actual_wire
from xar_autoplayer.bridge.activity_feast_stage5_start_private_transport import (
    INPUT_STEP, query_activity_feast_stage5_start_inputs_private_v1,
    query_activity_feast_hosted_post_private_v1,
)


class CounterFixtureDriver(FixtureDriver):
    def wait_for_command_result(self, request_id: str, timeout: float) -> dict[str, object]:
        if self.requests[-1]["step"] != INPUT_STEP:
            return super().wait_for_command_result(request_id, timeout)
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": {
                "step": INPUT_STEP, "accepted": True, "status": "available",
                "private_build": True, "read_only": True,
                "advertised": False, "backend_id": "native-headless",
                "activity_feast_stage5_start_inputs": self.payload,
            },
        }


class FeastOutcomeValuesWireTests(unittest.TestCase):
    def test_actual_start_baseline_keeps_negative_prestige_and_native_stress_units(self):
        payload = actual_wire("ck3_12002_feast_outcome_values_wire_baseline.json")
        driver = CounterFixtureDriver(payload)
        read = query_activity_feast_stage5_start_inputs_private_v1(driver, expected_revision=5)
        self.assertEqual(read["outcome_values"], {
            "prestige_raw": -500000, "stress_points": 48,
            "reveler_present": True, "reveler_xp_raw": 6500000,
        })
        self.assertIs(read["native_guest_route_qualified"], False)
        self.assertEqual(read["guest_join_status"], "exact_build_rejected")
        self.assertEqual(read["exact_ck3_build"], "1.20.0.2")
        # The caller can persist an immutable pre-submit baseline independently
        # from later provider buffer reuse.
        driver.payload["outcome_values"]["prestige_raw"] = 0
        self.assertEqual(read["outcome_values"]["prestige_raw"], -500000)

    def test_actual_post_counter_trace_survives_terminal_and_manager_release(self):
        payloads = actual_wire("ck3_12002_feast_outcome_values_wire.json")
        reads = [query_activity_feast_hosted_post_private_v1(
            CounterFixtureDriver(deepcopy(payload)), expected_revision=5,
        ) for payload in payloads]
        self.assertEqual([read["outcome_values"] for read in reads],
                         [payload["outcome_values"] for payload in payloads])
        self.assertEqual(reads[1]["outcome_values"]["prestige_raw"] -
                         reads[0]["outcome_values"]["prestige_raw"], 10000000)
        self.assertEqual(reads[1]["outcome_values"]["stress_points"] -
                         reads[0]["outcome_values"]["stress_points"], -20)
        self.assertEqual(reads[1]["outcome_values"]["reveler_xp_raw"] -
                         reads[0]["outcome_values"]["reveler_xp_raw"], 500000)
        self.assertIs(reads[1]["hosted_activities"][0]["native_completed"], True)
        self.assertIs(reads[2]["outcome_values"]["reveler_present"], False)
        self.assertIsNone(reads[2]["outcome_values"]["reveler_xp_raw"])
        self.assertEqual(reads[3]["hosted_activities"], [])
        self.assertEqual(reads[3]["outcome_values"]["stress_points"], 28)
        self.assertIsNone(reads[3]["outcome_values"]["reveler_xp_raw"])


if __name__ == "__main__":
    unittest.main()
