"""Focused offline checks for explicit Root adoption of an async successor."""
from __future__ import annotations

import asyncio
import copy
import unittest

from tools.g2_saved_campaign.m7_ordinary_successor_async_queue import (
    AsyncOrdinarySuccessorQueue,
)
from tools.g2_saved_campaign.test_m7_async_successor_persistence import (
    completed_continuation_fixture,
)


def _available_boolean(value):
    return {"status": "available", "value": value, "unavailable_reason": None}


class _AdoptedQueue:
    """One existing async queue; every callback retains its owner and loop."""

    def __init__(self, fixture):
        self.fixture = fixture
        self.calls = []
        self.observations = []
        self.callback_owners = []
        self.callback_loops = []
        current = fixture["successor_snapshot"]
        self.checkpoint = {
            "status": "saved",
            "date_raw": current["date_raw"],
            "episode_character_id": current["episode_character_id"],
            "episode_run_id": current["episode_run_id"],
            "succession_lifecycle": copy.deepcopy(current["succession_lifecycle"]),
            "checkpoint_id": "offline-explicit-adoption-successor-save",
        }
        self.save_response = "offline-adopted-queue/successor-save.json"

    def _observe_callback(self):
        self.callback_owners.append(id(self))
        self.callback_loops.append(asyncio.get_running_loop())

    async def call(self, tool, arguments, kind):
        self._observe_callback()
        self.calls.append((tool, copy.deepcopy(arguments), kind))
        if tool == "ck3_take_snapshot":
            return copy.deepcopy(self.fixture["successor_snapshot"]), (
                "offline-adopted-queue/" + kind + ".json"
            )
        if tool == "ck3_get_capabilities":
            return copy.deepcopy(self.fixture["capabilities"]), (
                "offline-adopted-queue/" + kind + ".json"
            )
        if tool == "ck3_query_current_timeline_blocker_context_v1":
            return {
                "current_timeline_blocker_context": {
                    "status": "available",
                    "identity": "none",
                    "blocks_simulation": _available_boolean(False),
                    "has_open_succession": _available_boolean(False),
                }
            }, "offline-adopted-queue/already-clear-timeline.json"
        if tool == "ck3_save_checkpoint":
            return {"checkpoint": copy.deepcopy(self.checkpoint)}, self.save_response
        raise AssertionError("unexpected request after explicit adoption: " + tool)

    async def thin(self, kind, value):
        self._observe_callback()
        self.observations.append((kind, copy.deepcopy(value)))


async def _adopt_completed(adapter, fixture, transitions):
    source = fixture["source_snapshot"]
    return await adapter.adopt_successor(
        {
            "episode_character_id": source["episode_character_id"],
            "episode_run_id": source["episode_run_id"],
        },
        transitions,
        completed_turn=fixture["turn"],
        response_path=fixture["response_path"],
        source_snapshot=source,
        source_path=fixture["source_path"],
    )


class AsyncSuccessorAdoptionTests(unittest.IsolatedAsyncioTestCase):
    async def test_constructor_does_not_activate_successor_handling(self):
        queue = _AdoptedQueue(completed_continuation_fixture())

        adapter = AsyncOrdinarySuccessorQueue(queue)

        self.assertIsInstance(adapter, AsyncOrdinarySuccessorQueue)
        self.assertEqual(queue.calls, [])
        self.assertEqual(queue.observations, [])
        self.assertEqual(queue.callback_owners, [])

    async def test_explicit_adoption_returns_saved_pair_before_later_gameplay(self):
        fixture = completed_continuation_fixture()
        queue = _AdoptedQueue(fixture)
        transitions = []

        result = await _adopt_completed(
            AsyncOrdinarySuccessorQueue(queue), fixture, transitions
        )

        self.assertEqual(result["status"], "saved")
        self.assertEqual(result["successor_checkpoint"], queue.checkpoint)
        self.assertEqual(result["save_response"], queue.save_response)
        self.assertEqual(result["snapshot"], fixture["successor_snapshot"])
        self.assertIsInstance(result["snapshot_response"], str)
        self.assertEqual(result["transition"], transitions[0])
        self.assertEqual(len(transitions), 1)
        self.assertEqual(queue.calls[-1][0], "ck3_save_checkpoint")
        self.assertEqual(
            queue.calls[-1][1],
            {"expected_revision": fixture["successor_snapshot"]["revision"]},
        )
        self.assertNotIn("ck3_auto_turn", [row[0] for row in queue.calls])
        self.assertEqual(sum(row[0] == "ck3_save_checkpoint" for row in queue.calls), 1)

    async def test_adoption_uses_the_existing_queue_on_the_original_event_loop(self):
        fixture = completed_continuation_fixture()
        queue = _AdoptedQueue(fixture)
        original_loop = asyncio.get_running_loop()

        result = await _adopt_completed(
            AsyncOrdinarySuccessorQueue(queue), fixture, []
        )

        self.assertEqual(result["status"], "saved")
        self.assertTrue(queue.calls)
        self.assertTrue(queue.observations)
        self.assertTrue(queue.callback_owners)
        self.assertEqual(set(queue.callback_owners), {id(queue)})
        self.assertTrue(all(loop is original_loop for loop in queue.callback_loops))


if __name__ == "__main__":
    unittest.main()
