"""Check ownership of the new adapter while a queue request is outstanding."""
from __future__ import annotations

import asyncio
import unittest

from tools.g2_saved_campaign.m7_ordinary_successor_async_queue import AsyncOrdinarySuccessorQueue
from tools.g2_saved_campaign.test_m7_async_successor_adoption import _AdoptedQueue, _adopt_completed
from tools.g2_saved_campaign.test_m7_async_successor_modal import inputs, typed
from tools.g2_saved_campaign.test_m7_async_successor_persistence import completed_continuation_fixture


class _HeldTimelineQueue(_AdoptedQueue):
    def __init__(self, fixture, *, close_required=False):
        super().__init__(fixture)
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self.close_required = close_required
        self.timeline_calls = 0

    async def call(self, tool, arguments, kind):
        if tool != "ck3_query_current_timeline_blocker_context_v1":
            return await super().call(tool, arguments, kind)
        self.calls.append((tool, dict(arguments), kind))
        self.timeline_calls += 1
        self.entered.set()
        await self.release.wait()
        context = {
            "status": "available",
            "identity": "death_succession_modal" if self.close_required else "none",
            "blocks_simulation": typed(self.close_required),
            "has_open_succession": typed(self.close_required),
            "can_continue": typed(self.close_required),
        }
        return {"current_timeline_blocker_context": context}, "held-timeline.json"


class AsyncSuccessorOwnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_same_adapter_serializes_handoffs_before_next_queue_request(self):
        queue = _HeldTimelineQueue(completed_continuation_fixture())
        adapter = AsyncOrdinarySuccessorQueue(queue)
        first_after, first_path, first_transition = inputs()
        second_after, second_path, second_transition = inputs()
        first = asyncio.create_task(adapter.finish_transition(
            first_after, first_path, first_transition, [],
        ))
        await queue.entered.wait()
        second = asyncio.create_task(adapter.finish_transition(
            second_after, second_path, second_transition, [],
        ))
        await asyncio.sleep(0)
        self.assertEqual(queue.timeline_calls, 1)
        queue.release.set()
        await asyncio.gather(first, second)
        self.assertEqual(queue.timeline_calls, 2)
        self.assertEqual([row[0] for row in queue.calls], [
            "ck3_query_current_timeline_blocker_context_v1",
            "ck3_query_current_timeline_blocker_context_v1",
        ])

    async def test_cancel_collects_original_query_and_starts_no_close_or_save(self):
        fixture = completed_continuation_fixture()
        queue = _HeldTimelineQueue(fixture, close_required=True)
        transitions = []
        task = asyncio.create_task(_adopt_completed(
            AsyncOrdinarySuccessorQueue(queue), fixture, transitions,
        ))
        await queue.entered.wait()
        task.cancel()
        await asyncio.sleep(0)
        self.assertFalse(task.done())
        queue.release.set()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(len(transitions), 1)
        self.assertEqual([row[0] for row in queue.calls], [
            "ck3_take_snapshot", "ck3_get_capabilities",
            "ck3_query_current_timeline_blocker_context_v1",
        ])
        self.assertEqual([kind for kind, _ in queue.observations], [
            "m7-natural-transition-pending",
        ])


if __name__ == "__main__":
    unittest.main()
