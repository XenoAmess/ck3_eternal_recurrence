"""Small actual AUTO781 projection and negative pause-boundary checks."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from xar_autoplayer.war_results_scope_pause_v1 import pause_after_war_results_scope_transition_v1
from tools.g2_saved_campaign.war_results_scope_transition_outcome import classify_paused_war_results_scope_transition_v1


FIXTURE = json.loads((Path(__file__).parents[1] / "fixtures/p47_war_results_scope_transition_projection.json").read_text(encoding="utf-8"))
RESULT = FIXTURE["result"]


def frame(*, paused, revision=871, native_revision=7551, date_raw=53314512):
    return {
        "snapshot_id": f"native:{native_revision}", "revision": revision,
        "native_revision": native_revision, "date_raw": date_raw,
        "paused": paused, "map_ready": True,
        "episode_run_id": RESULT["queried_episode_run_id"],
        "played_character": {"character_id": RESULT["queried_actor_character_id"]},
        "diagnostics": {"bridge_pid": 51028,
                        "connection_generation": RESULT["queried_connection_generation"],
                        "hello": {"pid": 51028}},
    }


class Driver:
    def __init__(self, before, after, *, pause_error=None):
        self.snapshots = [before, after]
        self.calls = []
        self.pause_error = pause_error

    def take_internal_semantic_snapshot(self):
        return self.snapshots.pop(0)

    def execute_step(self, step, *, expected_revision):
        self.calls.append((step, expected_revision))
        if self.pause_error:
            raise self.pause_error
        return {"step": "pause-map", "accepted": True}


class ScopeTransitionPauseTests(unittest.TestCase):
    def test_actual_781_pending_close_pauses_and_retains_original(self):
        original = deepcopy(RESULT)
        driver = Driver(frame(paused=False), frame(paused=True))
        evidence = pause_after_war_results_scope_transition_v1(driver, original)
        self.assertEqual(driver.calls, [("pause-map", None)])
        self.assertEqual(evidence["status"], "paused_same_owner_requery_required")
        self.assertEqual(evidence["original_close"]["native_request_id"], RESULT["native_request_id"])
        self.assertFalse(evidence["close_action_credit"])
        self.assertFalse(evidence["close_replayed"])
        self.assertEqual(original, RESULT)

    def test_already_paused_only_reads(self):
        driver = Driver(frame(paused=True), frame(paused=True))
        evidence = pause_after_war_results_scope_transition_v1(driver, RESULT)
        self.assertEqual(driver.calls, [])
        self.assertEqual(evidence["status"], "paused_same_owner_requery_required")

    def test_failed_pause_preserves_pending_and_failure(self):
        driver = Driver(frame(paused=False), frame(paused=False), pause_error=RuntimeError("native unavailable"))
        evidence = pause_after_war_results_scope_transition_v1(driver, RESULT)
        self.assertEqual(evidence["status"], "pause_unverified")
        self.assertIn("native unavailable", evidence["failure"])
        self.assertFalse(evidence["close_action_credit"])

    def test_unpaused_after_pause_is_not_claimed_paused(self):
        driver = Driver(frame(paused=False), frame(paused=False))
        evidence = pause_after_war_results_scope_transition_v1(driver, RESULT)
        self.assertEqual(evidence["status"], "pause_unverified")
        self.assertEqual(driver.calls, [("pause-map", None)])

    def test_unrelated_pending_or_untrusted_owner_never_sends_pause(self):
        for key, value in (
            ("accepted", True), ("closure_verified", True),
            ("native_handled", False), ("scope_unchanged", True),
            ("unavailable_reason", "war_declared_close_not_post_verified"),
        ):
            with self.subTest(key=key):
                altered = {**RESULT, key: value}
                driver = Driver(frame(paused=False), frame(paused=True))
                self.assertIsNone(pause_after_war_results_scope_transition_v1(driver, altered))
                self.assertEqual(driver.calls, [])
        altered = deepcopy(RESULT)
        altered["native_command_result"]["war_results_window_owner_receipt"]["request_id"] = "wrong"
        driver = Driver(frame(paused=False), frame(paused=True))
        self.assertIsNone(pause_after_war_results_scope_transition_v1(driver, altered))
        self.assertEqual(driver.calls, [])

    def test_different_episode_is_not_a_same_owner_requery(self):
        after = frame(paused=True)
        after["episode_run_id"] = "different"
        driver = Driver(frame(paused=False), after)
        evidence = pause_after_war_results_scope_transition_v1(driver, RESULT)
        self.assertEqual(evidence["status"], "pause_unverified")
        self.assertEqual(evidence["failure"], "same_owner_paused_map_not_observed")

    def test_actual_781_technical_classifier_keeps_close_unverified(self):
        body = deepcopy(FIXTURE["body_projection"])
        driver = Driver(frame(paused=False), frame(paused=True, date_raw=53314536))
        body["result"]["scope_transition_pause"] = pause_after_war_results_scope_transition_v1(
            driver, body["result"])
        observed = classify_paused_war_results_scope_transition_v1(
            body, binding=body["planning_source_frame"], game_pid=51028)
        self.assertEqual(observed["category"], "war_results_scope_transition_paused_pending")
        self.assertEqual(observed["actual_elapsed_days_uncredited"], 1)
        self.assertFalse(observed["date_advance_observed"])
        self.assertFalse(observed["war_results_window_closed_verified"])
        self.assertFalse(observed["new_close_retry_authorized"])
        self.assertTrue(observed["readonly_ui_query_required"])

    def test_classifier_requires_pause_proof_same_owner(self):
        body = deepcopy(FIXTURE["body_projection"])
        with self.assertRaises(ValueError):
            classify_paused_war_results_scope_transition_v1(
                body, binding=body["planning_source_frame"], game_pid=51028)
        driver = Driver(frame(paused=False), frame(paused=True))
        body["result"]["scope_transition_pause"] = pause_after_war_results_scope_transition_v1(
            driver, body["result"])
        body["result"]["scope_transition_pause"]["after_pause"]["hello_pid"] = 999
        with self.assertRaises(ValueError):
            classify_paused_war_results_scope_transition_v1(
                body, binding=body["planning_source_frame"], game_pid=51028)


if __name__ == "__main__":
    unittest.main()
