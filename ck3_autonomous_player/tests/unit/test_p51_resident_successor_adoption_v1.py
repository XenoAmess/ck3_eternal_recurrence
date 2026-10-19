"""One registered-App compound for the isolated P51 source adapter."""
import asyncio
import copy
from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
sys.path.insert(0, str(REPO / "tools"))

from mcp import Client
import test_successor_ui_app_owner_v1 as fixture
from g2_saved_campaign.p51_resident_successor_adoption_v1 import (
    classify_ui_auto_result_v1, observe_app_ui_v1,
)


class ResidentAdoptionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.context = fixture.AppOwnerTests()
        self.context.setUp()

    def tearDown(self):
        self.context.tearDown()

    async def test_registered_app_deferred_event_auto_close_zero_credit_and_no_replay(self):
        context, calls = self.context, []
        async with Client(fixture.mcp_server.create_server(context.driver)) as client:
            async def call(name, arguments):
                calls.append(name)
                return await context.call(client, name, arguments), context.root / f"original-{len(calls)}.json"

            turn, _ = await call("ck3_auto_turn", {})
            continued = turn["result"]
            before = copy.deepcopy(context.driver.frame)
            current, path, deferred, _ = await observe_app_ui_v1(
                call, {"SEMANTIC": "ck3_take_snapshot"}, before, None, continued, require_proof=True)
            self.assertTrue(deferred)
            self.assertEqual(current["active_event"], before["active_event"])
            self.assertEqual((context.driver.continues, context.driver.closes, context.driver.saves), (1, 0, 0))
            state = {"resident_successor_ui_pending": {"continued": continued,
                     "campaign_goal_after": copy.deepcopy(current["campaign_goal"])}}
            # The ordinary App planner handles the old-root event without a new
            # Continue. Its following AUTO closes the retained UI separately.
            event_turn, _ = await call("ck3_auto_turn", {})
            self.assertEqual(event_turn["selected_step"], "select-event-option-1")
            ui_turn, _ = await call("ck3_auto_turn", {})
            observation = classify_ui_auto_result_v1(ui_turn, queue_state=state)
            self.assertTrue(observation["resident_ui_only"])
            self.assertEqual((observation["ordinary_cycle_credit"], observation["new_natural_succession_credit"]), (0, 0))
            with self.assertRaisesRegex(ValueError, "retained handoff"):
                classify_ui_auto_result_v1(ui_turn, queue_state={})
            after = copy.deepcopy(context.driver.frame)
            _, _, deferred, _ = await observe_app_ui_v1(
                call, {"SEMANTIC": "ck3_take_snapshot"}, after, path, continued)
            self.assertFalse(deferred)
            self.assertEqual((context.driver.continues, context.driver.closes, context.driver.saves), (1, 1, 0))
            self.assertNotIn("ck3_save_checkpoint", calls)

    async def test_required_close_uses_held_auto_publication_before_original_close(self):
        context, calls, held = self.context, [], [None]
        def display(candidate):
            self.assertEqual(held[0], "ck3_auto_turn", "actual-style held AUTO publication required")
            context.driver.order.append("display-ack:" + candidate["selected_step"])
            if candidate["selected_step"] == "continue-death-succession-modal-v1":
                self.assertEqual(context.driver.closes, 0)
                self.assertEqual(list(context.root.glob("successor-ui-close-*.json")), [])
        server = fixture.mcp_server.create_server(context.driver, before_auto_turn_submit=display)
        async with Client(server) as client:
            async def call(name, arguments):
                calls.append(name)
                held[0] = name
                return await context.call(client, name, arguments), context.root / f"original-{len(calls)}.json"
            first, _ = await call("ck3_auto_turn", {})
            continued = first["result"]
            event, _ = await call("ck3_auto_turn", {})
            self.assertEqual(event["selected_step"], "select-event-option-1")
            before = copy.deepcopy(context.driver.frame)
            current, _, deferred, ui = await observe_app_ui_v1(
                call, {"SEMANTIC": "ck3_take_snapshot"}, before, None, continued, require_proof=True)
            self.assertFalse(deferred)
            self.assertFalse(ui["pending"])
            self.assertTrue(ui["date_advanced"])
            self.assertEqual((context.driver.continues, context.driver.closes, context.driver.saves), (1, 1, 0))
            self.assertEqual(calls[-4:], ["ck3_resume_successor_ui_v1", "ck3_take_snapshot", "ck3_auto_turn", "ck3_take_snapshot"])
            self.assertNotIn("ck3_continue_death_succession_modal_v1", calls)
            self.assertLess(context.driver.order.index("display-ack:continue-death-succession-modal-v1"),
                            context.driver.order.index("close-intent-observed-before-driver"))
            self.assertEqual(current["episode_run_id"], continued["episode_run_id"])

    async def test_close_display_interception_defers_without_another_auto_or_close(self):
        context, calls, held = self.context, [], [None]
        def display(candidate):
            self.assertEqual(held[0], "ck3_auto_turn")
            if candidate["selected_step"] == "continue-death-succession-modal-v1":
                return {"reason": "synthetic real display interception"}
        server = fixture.mcp_server.create_server(context.driver, before_auto_turn_submit=display)
        async with Client(server) as client:
            async def call(name, arguments):
                calls.append(name)
                held[0] = name
                return await context.call(client, name, arguments), context.root / f"original-{len(calls)}.json"
            first, _ = await call("ck3_auto_turn", {})
            await call("ck3_auto_turn", {})
            _, _, deferred, ui = await observe_app_ui_v1(call, {"SEMANTIC": "ck3_take_snapshot"},
                copy.deepcopy(context.driver.frame), None, first["result"], require_proof=True)
            self.assertTrue(deferred)
            self.assertTrue(ui["pending"])
            self.assertFalse(ui["date_advanced"])
            self.assertEqual(calls.count("ck3_auto_turn"), 3)
            self.assertNotIn("ck3_continue_death_succession_modal_v1", calls)
            self.assertEqual((context.driver.continues, context.driver.closes, context.driver.saves), (1, 0, 0))
            self.assertEqual(list(context.root.glob("successor-ui-close-*.json")), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
