"""Exact full-state bytes across history growth, mutation and replacement."""

import json
import threading
import unittest
from unittest.mock import Mock, patch

from xar_autoplayer.bridge.driver_state_history_json import (
    DriverStateHistoryJsonCache,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.marriage_contract import arrange_marriage_step


def bare_driver():
    driver = object.__new__(NativeHeadlessGameplayDriver)
    driver.pipe_name = "test-pipe"
    driver._session_bridge_pid = 23
    driver._episode_character_id = 7
    driver._episode_run_id = "test-run"
    driver._last_checkpoint = None
    driver._command_history = []
    driver._driver_state_history_json = DriverStateHistoryJsonCache()
    driver._rollback_war_failures = []
    driver._rollback_war_failures_migration_required = False
    driver._managed_restore_transaction = None
    driver._succession_expectation = None
    driver._succession_lifecycle = {"continue_as_heir_after_death": True}
    driver._campaign_goal = {"goal": "Robert's 30 years"}
    return driver


def legacy_bytes(driver):
    return (json.dumps(
        driver._driver_state_payload_locked(), ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n")


class DriverStateHistoryJsonTest(unittest.TestCase):
    def assert_same_state(self, driver):
        actual = driver._encode_driver_state_locked()
        self.assertEqual(actual, legacy_bytes(driver))
        self.assertEqual(json.loads(actual)["command_history"],
                         driver._command_history)

    def test_empty_append_unicode_and_metadata_change(self):
        d = bare_driver()
        self.assert_same_state(d)
        d._command_history.append({"index": 1, "command": "life-advance",
                                   "ok": True, "result": {"text": "cafe é\n\\"}})
        self.assert_same_state(d)
        d._command_history.append({"index": 2, "command": "save-checkpoint",
                                   "ok": True, "result": {"checkpoint": {"size": 3}}})
        d._last_checkpoint = {"path": "D:/save.ck3", "history_index": 2}
        d._rollback_war_failures = [{"war_id": 71, "status": "lost"}]
        self.assert_same_state(d)
        d._campaign_goal = {"goal": "changed only in envelope"}
        self.assert_same_state(d)

    def test_in_place_marriage_result_requires_invalidation(self):
        d = bare_driver()
        row = {"index": 1, "command": "arrange-marriage-1", "ok": True,
               "result": {"marriage_action": {"status": "proposal_submitted"}}}
        d._command_history.append(row)
        self.assert_same_state(d)
        row["result"]["marriage_result"] = {"status": "married"}
        d._driver_state_history_json.invalidate()
        self.assert_same_state(d)

    def test_actual_marriage_observation_invalidates_prior_row(self):
        d = bare_driver()
        d._driver_state_lock = threading.RLock()
        d._history_lock = d._driver_state_lock
        d._persist_driver_state = Mock()
        d._command_history.append({
            "index": 1, "command": arrange_marriage_step("7-8"), "ok": True,
            "result": {"marriage_action": {
                "status": "proposal_submitted",
                "played_character_id": 7, "candidate_character_id": 8,
            }},
        })
        self.assert_same_state(d)
        d._observe_arrange_marriage_outcome({
            "date_raw": 123, "played_character": {
                "character_id": 7, "betrothed_id": None, "spouse_ids": [8],
            },
        })
        self.assertEqual(d._command_history[0]["result"]["marriage_result"]["status"],
                         "accepted_marriage")
        d._persist_driver_state.assert_called_once_with(
            persistence_reason="marriage_outcome_prefix_edit")
        self.assert_same_state(d)

    def test_restore_and_same_length_new_list_rebuild(self):
        d = bare_driver()
        d._command_history.append({"index": 1, "command": "old", "ok": True})
        self.assert_same_state(d)
        d._command_history = [{"index": 1, "command": "restored", "ok": True}]
        self.assert_same_state(d)
        d._command_history = []
        self.assert_same_state(d)

    def test_failed_new_row_encoding_keeps_prior_cache(self):
        d = bare_driver()
        d._command_history.append({"index": 1, "command": "good", "ok": True})
        self.assert_same_state(d)
        invalid = {"index": 2, "command": "bad", "result": object()}
        d._command_history.append(invalid)
        with self.assertRaises(TypeError):
            d._encode_driver_state_locked()
        d._command_history.pop()
        self.assert_same_state(d)
        d._command_history.append({"index": 2, "command": "good", "ok": True})
        self.assert_same_state(d)

    def test_cache_budget_falls_back_to_full_standard_bytes(self):
        d = bare_driver()
        d._command_history.append({"index": 1, "command": "large", "ok": True,
                                   "result": {"text": "x" * 100}})
        with patch(
            "xar_autoplayer.bridge.driver_state_history_json._MAX_CACHED_HISTORY_BYTES",
            20,
        ):
            self.assert_same_state(d)
            self.assertIsNone(d._driver_state_history_json._history)
            self.assert_same_state(d)


if __name__ == "__main__":
    unittest.main()
