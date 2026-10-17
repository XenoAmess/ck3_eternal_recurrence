"""Portable exact-rejection tests; no SDK, process, campaign, or disk mutation."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from tools.g2_saved_campaign.construction_paused_frame_readonly_v1 import classify_construction_paused_frame_readonly_v1 as qualify

FIXTURE = json.loads((Path(__file__).resolve().parent / "actual185-projection.json").read_bytes())


class ExactConstructionRead(unittest.TestCase):
    def test_actual_retained_rejection_and_other_request_sequence(self):
        for sequence in (1, 185, 9123):
            row = deepcopy(FIXTURE)
            row["request"]["sequence"] = sequence
            result = qualify(row)
            self.assertTrue(result["read_only_precondition"])
            self.assertFalse(result["business_submission"])
            self.assertFalse(result["construction_query_executor_submitted"])
            self.assertFalse(result["original_action_replay_allowed"])

    def test_timeout_business_wrong_identity_and_returned_data_do_not_qualify(self):
        changes = (("classification", "result_absent_cause_unknown"),
            ("classification", "invalid_envelope"),
            ("step", "g2_player_world_building_action_private_v1"),
            ("native_error", "prior private building command material state unresolved"),
            ("native_error", "private construction probe revision is stale"),
            ("request_id", "construction-write-" + "0" * 32),
            ("received_request_id", "construction-read-" + "0" * 32),
            ("gate_request_id", False), ("gate_protocol", False),
            ("gate_type", False), ("gate_mapping", False),
            ("received_ok", True), ("diagnostic_only", False),
            ("expected_native_revision", 0), ("expected_native_revision", True),
            ("gate_result_mapping", True), ("model_status", "available"),
            ("probe_status", "available"), ("world_status", "available"))
        for key, value in changes:
            with self.subTest(key=key, value=value):
                row = deepcopy(FIXTURE)
                row["result"]["structured_content"]["diagnostics"]["construction_transport_v1"][key] = value
                self.assertIsNone(qualify(row))
        row = deepcopy(FIXTURE); row["client_error"] = "timeout"
        self.assertIsNone(qualify(row))
        row = deepcopy(FIXTURE); row["request"]["tool"] = "ck3_execute_step"
        self.assertIsNone(qualify(row))


if __name__ == "__main__": unittest.main()
