"""One new CampaignRoot omission/ownership compound on the real Driver path.

The existing fixture supplies synthetic hello, paused state and native response.
Only this new test runs; it adds no native producer, current-build or live credit.
"""
from __future__ import annotations

from copy import deepcopy
import unittest
from unittest.mock import patch

import test_campaign_root_context_v1_bridge as fixture


class CampaignRootHistoryOmissionOwnershipTests(unittest.TestCase):
    def test_root_query_omits_history_copy_but_records_detached_result(self) -> None:
        driver, endpoint = fixture._native_driver()
        before = driver.take_snapshot_without_native_command_history()
        old_history = [{
            "index": 1,
            "command": "query-synthetic-retained-history",
            "ok": True,
            "result": {
                "ordered_rows": [{"value": 7}, {"value": None}, {"value": 7}],
                "unresolved_intent": {"status": "action_state_unknown", "ack": None},
            },
        }]
        with driver._history_lock:
            driver._command_history = deepcopy(old_history)
        fixture._answer_with(endpoint, fixture._native_result)

        with patch.object(
            driver, "_history_snapshot",
            side_effect=AssertionError("campaign-root copied the full command history"),
        ) as history_copy:
            result = driver.execute_step(
                fixture.STEP, expected_revision=before["revision"],
            )
        self.assertEqual(history_copy.call_count, 0)

        requests = [
            frame for frame in endpoint.frames if frame.get("type") == "execute_step"
        ]
        self.assertEqual(len(requests), 1)
        request = requests[0]
        self.assertEqual(set(request), {
            "type", "protocol_version", "request_id", "step", "expected_revision",
        })
        self.assertEqual(request["protocol_version"], 1)
        self.assertEqual(request["step"], fixture.STEP)
        self.assertEqual(request["expected_revision"], before["native_revision"])
        self.assertIsInstance(request["request_id"], str)
        self.assertTrue(request["request_id"].startswith("step-"))

        expected_native = fixture._native_result()
        self.assertEqual(
            result["campaign_root_context"], expected_native["campaign_root_context"],
        )
        self.assertEqual(result["query_sequence"], expected_native["query_sequence"])
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["campaign_root_context_ready"])
        self.assertEqual(result["queried_snapshot_id"], before["snapshot_id"])
        self.assertEqual(result["queried_revision"], before["revision"])
        self.assertEqual(result["queried_native_revision"], before["native_revision"])
        self.assertEqual(result["date_raw"], before["date_raw"])

        cached = driver._campaign_root_context_query
        self.assertIsInstance(cached, dict)
        self.assertEqual(cached["cache_binding"], {
            "snapshot_id": before["snapshot_id"],
            "revision": before["revision"],
            "native_revision": before["native_revision"],
            "date_raw": before["date_raw"],
            "actor_character_id": before["played_character"]["character_id"],
            "bridge_pid": before["diagnostics"]["bridge_pid"],
            "connection_generation": before["diagnostics"]["connection_generation"],
        })
        with driver._history_lock:
            self.assertEqual(len(driver._command_history), len(old_history) + 1)
            self.assertEqual(driver._command_history[:-1], old_history)
            recorded = driver._command_history[-1]
            self.assertEqual(recorded["index"], 2)
            self.assertEqual(recorded["command"], fixture.STEP)
            self.assertIs(recorded["ok"], True)
            history_result = recorded["result"]
        self.assertEqual(history_result, result)
        self.assertEqual(cached["campaign_root_context"], result["campaign_root_context"])

        cached_before = deepcopy(cached)
        history_before = deepcopy(history_result)
        result["campaign_root_context"]["readiness"]["ready"] = False
        result["selected_game_rule_tokens"].append("mutated-return-mirror")
        self.assertTrue(result["readiness"]["ready"])
        self.assertEqual(cached, cached_before)
        self.assertEqual(history_result, history_before)
        mutated_result = deepcopy(result)

        cached["campaign_root_context"]["selected_game_rule_tokens"].append(
            "mutated-private-cache",
        )
        self.assertEqual(result, mutated_result)
        self.assertEqual(history_result, history_before)
        mutated_cache = deepcopy(cached)

        history_result["campaign_root_context"]["government"]["flags"].append(
            "mutated-recorded-history",
        )
        self.assertEqual(result, mutated_result)
        self.assertEqual(cached, mutated_cache)
        self.assertEqual(driver._command_history[:-1], old_history)


if __name__ == "__main__":
    unittest.main()
