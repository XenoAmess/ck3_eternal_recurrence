"""One registered normal-MCP Council compound; no native or game execution.

Reuse the preserved Council SDK DTOs and their existing outer Driver seam.
The baseline chooser is the sole planner seam so this fixture isolates the
previously unreachable normal Service consumer without simulating war AI.
"""
import asyncio
import copy
from unittest.mock import patch

from test_private_council_formal_consumer_v1 import ActualCouncilDriver
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.private_council_formal_consumer_v1 import (
    RECEIPT_STEP, SUBMIT_STEP, read_council_ledger,
)


class NormalCouncilDriver(ActualCouncilDriver):
    nonwar_only = False

    def __init__(self, state_dir):
        super().__init__(state_dir)
        self.advance_calls = []

    def capabilities(self):
        return {"action_steps": ["life-advance", "query-army-strengths-v1"], "bridge_capabilities": []}

    def execute_step(self, step, *, expected_revision):
        if step == "life-advance":
            self.advance_calls.append((step, expected_revision))
            return {"status": "recorded_fixture_advance"}
        if self.phase == "pre":
            # The fail-gate branch uses the retained actual root structure at
            # the positive quote's frame; these binding edits are synthetic.
            value = copy.deepcopy(self.data["current_root"])
            snapshot = self.take_snapshot()
            root = value["campaign_root_context"]
            root.update(snapshot_revision=snapshot["native_revision"], date_raw=snapshot["date_raw"])
            self.root_calls += 1
            return value
        return super().execute_step(step, expected_revision=expected_revision)


def test_registered_normal_council_submit_receipt_following_failgate_and_war_priority(tmp_path):
    async def run():
        from mcp import Client

        baseline = {"policy": "normal-baseline-fixture", "phase": "life_advance", "selected_step": "life-advance"}
        driver = NormalCouncilDriver(tmp_path / "positive")
        wars = copy.deepcopy(driver.take_snapshot()["active_wars"])
        with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline), \
                patch.object(GameplayBridgeService, "plan_nonwar_turn", side_effect=AssertionError("normal MCP must not call nonwar planner")), \
                patch.object(GameplayBridgeService, "auto_nonwar_turn", side_effect=AssertionError("normal MCP must not call nonwar executor")):
            async with Client(create_server(driver)) as client:
                planned = await client.call_tool("ck3_plan_turn", {})
                assert not planned.is_error, planned.content
                assert planned.structured_content["plan"]["selected_step"] == SUBMIT_STEP
                assert planned.structured_content["plan"]["council_decision"]["skill_gain"] == 4
                submitted = await client.call_tool("ck3_auto_turn", {})
                assert not submitted.is_error, submitted.content
                assert submitted.structured_content["selected_step"] == SUBMIT_STEP
                assert submitted.structured_content["result"]["stage"] == "receipt_pending"
                assert driver.submit_calls == 1
                pending = await client.call_tool("ck3_plan_turn", {})
                assert not pending.is_error, pending.content
                assert pending.structured_content["plan"]["selected_step"] is None
                assert pending.structured_content["plan"]["phase"] == "council_pending_later_frame"
                assert driver.receipt_calls == 0 and not driver.advance_calls
                # Actual retained later DTO supplies independent material;
                # the submit ACK and fixture dispatch do not manufacture it.
                driver.phase = "post"
                applied = await client.call_tool("ck3_auto_turn", {})
                assert not applied.is_error, applied.content
                assert applied.structured_content["selected_step"] == RECEIPT_STEP
                material = applied.structured_content["result"]
                assert material["status"] == "applied"
                assert material["independent_position"]["incumbent_character_id"] == 33433
                assert material["receipt"]["council_assign_councillor_receipt"]["postcondition_verified"] is True
                assert (driver.submit_calls, driver.receipt_calls) == (1, 1)
                driver.phase = "current"
                following = await client.call_tool("ck3_plan_turn", {})
                assert not following.is_error, following.content
                after = following.structured_content["plan"]
                assert after["selected_step"] == "life-advance"
                assert after["council_decision"]["outcome"] == "NO_CHANGE"
                assert after["council_receipt_consumed"]["next_turn_consumed"] is True
                assert read_council_ledger(driver.state_dir)["applied"]["next_turn_consumed"] is True
                assert not driver.advance_calls and driver.submit_calls == 1
            assert driver.data["pre_snapshot"]["active_wars"] == wars
            assert driver.take_snapshot()["active_wars"] == driver.data["current_snapshot"]["active_wars"]

            blocked = NormalCouncilDriver(tmp_path / "native-failgate")
            # One final native gate rejects every replacement, leaving the
            # observed baseline. No fake quote or submitted ACK is introduced.
            for gate in blocked.data["positive_query"]["council_final_gates"]["rows"]:
                gate["incumbent_can_be_fired"] = False
            async with Client(create_server(blocked)) as client:
                observed = await client.call_tool("ck3_plan_turn", {})
                assert not observed.is_error, observed.content
                decision = observed.structured_content["plan"]["council_decision"]
                assert decision["legal_candidate_count"] == 0
                assert observed.structured_content["plan"]["selected_step"] == "life-advance"
                assert blocked.submit_calls == blocked.receipt_calls == 0

        urgent = NormalCouncilDriver(tmp_path / "urgent-war")
        war_plan = {"policy": "normal-war-fixture", "phase": "native_war_army_query", "selected_step": "query-army-strengths-v1"}
        with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=war_plan):
            async with Client(create_server(urgent)) as client:
                planned = await client.call_tool("ck3_plan_turn", {})
                assert not planned.is_error, planned.content
                assert planned.structured_content["plan"]["selected_step"] == "query-army-strengths-v1"
        assert (urgent.query_calls, urgent.submit_calls, urgent.receipt_calls, urgent.root_calls) == (0, 0, 0, 0)

    asyncio.run(run())
