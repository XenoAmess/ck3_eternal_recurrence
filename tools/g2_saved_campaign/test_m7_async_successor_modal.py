"""New async successor modal orchestration checks; no native or game."""
from __future__ import annotations
import copy
from pathlib import Path
import unittest
from tools.g2_saved_campaign.m7_ordinary_successor_async_queue import AsyncOrdinarySuccessorQueue

QUERY = "ck3_query_current_timeline_blocker_context_v1"

def typed(value):
    return {"status": "available", "value": value, "unavailable_reason": None}

def inputs():
    lifecycle = {"schema": "xar.ck3.succession-lifecycle-binding/v1",
                 "lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off",
                 "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
                 "source": "prepared-environment-manifest",
                 "environment_sha256": "a" * 64}
    physical = {"bridge_pid": 7001, "connection_generation": 4}
    goal = {"format_version": 1, "goal_key": "dynasty_continuity",
            "campaign_id": "fresh-modal-fixture", "origin_character_id": 100,
            "current_character_id": 301, "progress": {"reconciled_successions": 1}}
    after = {"snapshot_id": "native:81", "revision": 12, "native_revision": 81,
             "date_raw": 53290008, "paused": True, "map_ready": True,
             "played_character": {"character_id": 301, "alive": True},
             "episode_character_id": 301, "episode_run_id": "successor-run",
             "succession_lifecycle": lifecycle, "one_life_terminal": False,
             "one_life_terminal_reason": None, "diagnostics": physical, "campaign_goal": goal}
    transition = {"predecessor_binding": copy.deepcopy(physical),
                  "successor_episode_binding": copy.deepcopy(physical),
                  "successor_character_id": 301, "episode_run_id": "successor-run",
                  "succession_lifecycle": copy.deepcopy(lifecycle),
                  "campaign_goal_after": copy.deepcopy(goal),
                  "successor_checkpoint": {"status": "pending_actual_clear_successor_save"}}
    return after, Path("fixture-successor-snapshot.json"), transition

class TimelineQueue:
    """Any action or repeated query fails, even when its response is ignored."""
    def __init__(self, context):
        self.context = copy.deepcopy(context)
        self.calls = []
        self.receipts = []

    async def call(self, tool, arguments, kind):
        self.calls.append((tool, copy.deepcopy(arguments), kind))
        if tool != QUERY or len(self.calls) != 1:
            raise AssertionError("unexpected action or repeated timeline query")
        return ({"current_timeline_blocker_context": copy.deepcopy(self.context)},
                Path("fixture-timeline-query.json"))

    def thin(self, kind, payload):
        self.receipts.append((kind, copy.deepcopy(payload)))

class AsyncSuccessorModalTests(unittest.IsolatedAsyncioTestCase):
    async def test_already_clear_queries_once_and_submits_no_close(self):
        after, path, transition = inputs()
        queue = TimelineQueue({
            "status": "available", "identity": "none",
            "blocks_simulation": typed(False), "has_open_succession": typed(False),
            "can_continue": {"status": "unavailable", "value": None,
                             "unavailable_reason": "no_supported_timeline_surface_visible"}})
        transitions = []
        result = await AsyncOrdinarySuccessorQueue(queue).finish_transition(
            after, path, transition, transitions)
        self.assertEqual(result, (after, path, transition))
        self.assertEqual(transitions, [transition])
        self.assertEqual(queue.calls, [(QUERY, {"expected_revision": 12}, "m7-timeline")])
        continuation = transition["timeline_blocker_continuation"]
        self.assertEqual(continuation["status"], "already_clear")
        self.assertIsNone(continuation["close_result_response"])
        self.assertEqual(transition["current_date_raw"], 53290008)
        self.assertEqual(transition["current_snapshot_response"], str(path))
        self.assertEqual([kind for kind, _ in queue.receipts],
                         ["m7-natural-transition-pending", "m7-natural-transition"])

    async def test_unknown_timeline_retains_transition_without_resend_or_action(self):
        after, path, transition = inputs()
        unavailable = {"status": "unavailable", "value": None,
                       "unavailable_reason": "actual_gui_read_unavailable"}
        queue = TimelineQueue({
            "status": "unavailable", "identity": "unknown",
            "unavailable_reason": "actual_gui_read_unavailable",
            "blocks_simulation": unavailable, "has_open_succession": unavailable,
            "can_continue": unavailable})
        transitions = []
        with self.assertRaisesRegex(ValueError, "ambiguous/unavailable"):
            await AsyncOrdinarySuccessorQueue(queue).finish_transition(
                after, path, transition, transitions)
        self.assertEqual(transitions, [transition])
        self.assertEqual(queue.calls, [(QUERY, {"expected_revision": 12}, "m7-timeline")])
        continuation = transition["timeline_blocker_continuation"]
        self.assertIsNone(continuation["status"])
        self.assertEqual(continuation["initial_query_response"], "fixture-timeline-query.json")
        self.assertIsNone(continuation["close_result_response"])
        self.assertNotIn("current_date_raw", transition)
        self.assertEqual(len(queue.receipts), 1)
        kind, pending = queue.receipts[0]
        self.assertEqual(kind, "m7-natural-transition-pending")
        self.assertEqual(pending["successor_character_id"], 301)
        self.assertEqual(pending["successor_checkpoint"]["status"],
                         "pending_actual_clear_successor_save")

if __name__ == "__main__":
    unittest.main()
