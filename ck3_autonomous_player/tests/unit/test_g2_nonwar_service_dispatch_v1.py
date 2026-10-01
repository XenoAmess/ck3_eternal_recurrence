"""Production nonwar service/MCP dispatch with preserved Council SDK DTOs."""

from __future__ import annotations

import asyncio
import copy
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

import pytest

from test_private_council_formal_consumer_v1 import ActualCouncilDriver
from xar_autoplayer import strategy
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.succession_transition_contract import (
    CONTINUE_AS_RECONCILED_SUCCESSOR_STEP, SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
)
from xar_autoplayer.private_council_formal_consumer_v1 import (
    LEDGER_FILENAME, RECEIPT_STEP, SUBMIT_STEP, read_council_ledger,
)


class NonwarActualCouncilDriver(ActualCouncilDriver):
    """Existing nine actual DTOs; ordinary advance is a recorded fixture seam."""

    nonwar_only = False

    def __init__(self, state_dir):
        super().__init__(state_dir)
        self.advance_calls = []

    def capabilities(self):
        return {"action_steps": ["life-advance"], "bridge_capabilities": []}

    def execute_step(self, step, *, expected_revision):
        if step == "life-advance":
            assert expected_revision == self.take_snapshot()["revision"]
            self.advance_calls.append((step, expected_revision))
            # This records dispatch only. It neither rewrites the real DTOs
            # nor claims a native date advance or subsequent frame capture.
            return {"step": step, "status": "recorded_fixture_advance"}
        return super().execute_step(step, expected_revision=expected_revision)


@contextmanager
def forbid_legacy_planning():
    with ExitStack() as stack:
        for target in (
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            "xar_autoplayer.strategy.choose_one_life_turn",
            "xar_autoplayer.bridge.service.plan_m5_formal_query_only",
            "xar_autoplayer.bridge.service.plan_m5_wartime_query_only",
        ):
            stack.enter_context(patch(target, side_effect=AssertionError(f"nonwar called {target}")))
        yield


def test_real_council_submit_once_pending_advance_later_receipt_and_cold_consumption(tmp_path):
    driver = NonwarActualCouncilDriver(tmp_path)
    service = GameplayBridgeService(driver)
    actual_wars = copy.deepcopy(driver.data["pre_snapshot"]["active_wars"])
    with forbid_legacy_planning():
        submitted = service.auto_nonwar_turn()
        assert submitted["status"] == "executed"
        assert submitted["selected_step"] == SUBMIT_STEP
        decision = submitted["plan"]["council_decision"]
        assert (decision["native_candidate_count"], decision["legal_candidate_count"]) == (13, 10)
        assert decision["selected_candidate"]["character_id"] == 33433
        assert decision["skill_gain"] == 4
        assert driver.submit_calls == driver.query_calls == 1
        assert submitted["result"]["stage"] == "receipt_pending"
        assert read_council_ledger(tmp_path)["applied"] is None

        pending = service.plan_nonwar_turn()["plan"]
        assert pending["selected_step"] == "life-advance"
        assert pending["phase"] == "council_pending_later_frame"
        advanced = service.auto_nonwar_turn()
        assert advanced["selected_step"] == "life-advance"
        assert driver.advance_calls == [("life-advance", driver.data["pre_snapshot"]["revision"])]
        assert (driver.submit_calls, driver.query_calls, driver.receipt_calls) == (1, 1, 0)
        assert driver.take_snapshot()["active_wars"] == actual_wars

        # A preserved independent native6 frame, not the fixture advance ACK,
        # makes the assignment eligible for material receipt readback.
        driver.phase = "post"
        applied = service.auto_nonwar_turn()
        assert applied["selected_step"] == RECEIPT_STEP
        assert applied["result"]["status"] == "applied"
        position = applied["result"]["independent_position"]
        assert position["incumbent_character_id"] == 33433
        assert position["task_key"] == "task_collect_taxes"
        assert read_council_ledger(tmp_path)["pending"] is None
        assert (driver.submit_calls, driver.receipt_calls, driver.root_calls) == (1, 1, 1)

        # A fresh service/driver consumes the actual R10 current holder/task,
        # whose native revision restarts at one, using the existing ledger.
        cold_driver = NonwarActualCouncilDriver(tmp_path)
        cold_driver.phase = "current"
        current = GameplayBridgeService(cold_driver).plan_nonwar_turn()["plan"]
        assert current["selected_step"] == "life-advance"
        assert current["council_decision"]["outcome"] == "NO_CHANGE"
        assert current["council_decision"]["incumbent_character_id"] == 33433
        assert current["council_decision"]["incumbent_main_skill"]["value"] == 15
        consumed = current["council_receipt_consumed"]
        assert consumed["next_turn_consumed"] is True
        assert consumed["next_turn_native_revision"] == 1
        assert consumed["next_turn_position"]["task_key"] == "task_collect_taxes"
        assert read_council_ledger(tmp_path)["applied"]["next_turn_consumed"] is True
        assert cold_driver.submit_calls == cold_driver.receipt_calls == 0
        assert cold_driver.root_calls == 1
        assert cold_driver.take_snapshot()["active_wars"] == cold_driver.data["current_snapshot"]["active_wars"]


def test_council_off_and_default_inactive_government_leave_no_ledger_and_advance(tmp_path):
    driver = NonwarActualCouncilDriver(tmp_path)
    driver.allow_private_council_action = False
    service = GameplayBridgeService(driver)
    with forbid_legacy_planning():
        plan = service.plan_nonwar_turn()["plan"]
        assert plan["selected_step"] == "life-advance"
        assert plan["campaign_government_context_used"]["status"] == "inactive"
        assert plan["campaign_government_context_used"]["query_permitted"] is False
        advanced = service.auto_nonwar_turn()
    assert advanced["selected_step"] == "life-advance"
    assert len(driver.advance_calls) == 1
    assert (driver.query_calls, driver.submit_calls, driver.receipt_calls, driver.root_calls) == (0, 0, 0, 0)
    assert not (tmp_path / LEDGER_FILENAME).exists()


def test_public_mcp_nonwar_flag_runs_real_service_and_preserves_actual_wars(tmp_path):
    async def run():
        from mcp import Client

        driver = NonwarActualCouncilDriver(tmp_path)
        driver.nonwar_only = True
        driver.allow_private_council_action = False
        driver.allow_private_m5_joint_collector = True
        actual_wars = copy.deepcopy(driver.data["pre_snapshot"]["active_wars"])
        with forbid_legacy_planning(), patch.object(GameplayBridgeService, "plan_turn", side_effect=AssertionError("legacy plan")), patch.object(GameplayBridgeService, "auto_turn", side_effect=AssertionError("legacy auto")):
            async with Client(create_server(driver)) as client:
                planned = await client.call_tool("ck3_plan_turn", {})
                assert not planned.is_error, planned.content
                assert planned.structured_content["plan"]["selected_step"] == "life-advance"
                assert planned.structured_content["plan"]["active_wars"] == actual_wars
                advanced = await client.call_tool("ck3_auto_turn", {})
                assert not advanced.is_error, advanced.content
                assert advanced.structured_content["selected_step"] == "life-advance"
                assert advanced.structured_content["plan"]["active_wars"] == actual_wars
        assert driver.take_snapshot()["active_wars"] == actual_wars
        assert len(driver.advance_calls) == 1
        assert driver.query_calls == driver.root_calls == 0

    asyncio.run(run())


def test_public_mcp_default_flag_keeps_legacy_plan_and_auto_contract(tmp_path):
    async def run():
        from mcp import Client

        assert parser().parse_args([]).nonwar_only is False
        assert parser().parse_args(["--nonwar-only"]).nonwar_only is True
        driver = NonwarActualCouncilDriver(tmp_path)
        driver.allow_private_council_action = False
        plan_contract = {"snapshot_id": "legacy:1", "revision": 1, "plan": {"selected_step": "legacy-step"}}
        auto_contract = {"status": "executed", "selected_step": "legacy-step", "plan": plan_contract["plan"], "result": {"legacy": True}}
        with patch.object(GameplayBridgeService, "plan_turn", return_value=plan_contract) as old_plan, patch.object(GameplayBridgeService, "auto_turn", return_value=auto_contract) as old_auto, patch.object(GameplayBridgeService, "plan_nonwar_turn", side_effect=AssertionError("default routed nonwar plan")), patch.object(GameplayBridgeService, "auto_nonwar_turn", side_effect=AssertionError("default routed nonwar auto")):
            async with Client(create_server(driver)) as client:
                planned = await client.call_tool("ck3_plan_turn", {})
                assert not planned.is_error, planned.content
                assert planned.structured_content == plan_contract
                advanced = await client.call_tool("ck3_auto_turn", {})
                assert not advanced.is_error, advanced.content
                assert advanced.structured_content == auto_contract
        old_plan.assert_called_once_with()
        old_auto.assert_called_once_with()
        assert not driver.advance_calls

    asyncio.run(run())


@pytest.mark.parametrize("case", ["forced_terminal", "ordinary_matched_successor", "operator_event", "resolved_notification"])
def test_nonwar_strategy_preserves_shared_lifecycle_and_modal_priority(case):
    snapshot = {"snapshot_id": "fixture:1", "revision": 1, "native_revision": 1,
                "paused": True, "map_ready": True, "date_raw": 53169072,
                "played_character": {"character_id": 29829, "alive": True},
                "active_event": None, "pending_character_interaction": None,
                "active_wars": [{"war_id": 16777290}]}
    available = {"life-advance", "death-terminal", CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
                 "acknowledge-pending-character-interaction"}
    if case == "forced_terminal":
        snapshot["one_life_terminal_reason"] = "forced_terminal"
        expected_step, expected_phase = "death-terminal", "terminal_native"
    elif case == "ordinary_matched_successor":
        snapshot["one_life_terminal_reason"] = "played_character_changed"
        snapshot["succession_lifecycle"] = {
            "schema": SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
            "lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off",
            "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
            "source": "explicit_fixture_profile", "environment_sha256": "1" * 64,
        }
        snapshot["succession_reconciliation"] = {"status": "available", "verdict": "matched",
                                                  "successor_match": True, "title_distribution_match": True}
        expected_step, expected_phase = CONTINUE_AS_RECONCILED_SUCCESSOR_STEP, "ordinary_successor_continuation_ready"
    elif case == "operator_event":
        snapshot["active_event"] = {"instance_id": 73, "option_count": 3}
        expected_step, expected_phase = None, "active_event_operator_choice"
    else:
        snapshot["pending_character_interaction"] = {"instance_id": 74, "auto_accept_notification": True}
        expected_step, expected_phase = "acknowledge-pending-character-interaction", "pending_character_interaction_acknowledge"
    preserved = copy.deepcopy(snapshot)
    with forbid_legacy_planning(), patch.object(strategy, "_plan_one_life_terminal_v1", wraps=strategy._plan_one_life_terminal_v1) as terminal:
        selected = strategy.choose_nonwar_turn_v1([], snapshot=snapshot, action_steps=available)
    terminal.assert_called_once()
    assert selected["selected_step"] == expected_step
    assert selected["phase"] == expected_phase
    assert snapshot == preserved
    assert not any(key.startswith("war_") for key in selected)
