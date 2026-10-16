"""Private AUTO Army scalar view through real synthetic Driver/Service routes."""

from __future__ import annotations

from copy import deepcopy

import pytest

from test_army_profile_cache_regression import make_scenario
from xar_autoplayer.bridge.army_strengths_manager_shared_wire import (
    SHARED_KEY, pack_army_strengths_manager_inputs,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.service import GameplayBridgeService


def _planned(before: dict[str, object]) -> dict[str, object]:
    return {
        "revision": before["revision"], "snapshot_id": before["snapshot_id"],
        "plan": {"selected_step": "query-army-strengths-v1", "phase": "war_tactical_query"},
    }


def test_auto_scalar_result_and_cache_keep_frame_and_direct_query_keeps_rich_inputs(tmp_path):
    scenario = make_scenario(tmp_path / "state")
    original_publish = scenario.endpoint.publish

    def packed(frame):
        if frame.get("type") == "command_result":
            frame = {**frame, "result": pack_army_strengths_manager_inputs(frame["result"])}
        original_publish(frame)

    scenario.endpoint.publish = packed
    service = GameplayBridgeService(scenario.driver)
    try:
        outcome = service._execute_planned_turn_without_unhandled_capture(_planned(scenario.before))
        result = outcome["result"]
        assert outcome["status"] == "executed"
        assert result["army_strengths_profile"] == "ordinary_core_v1"
        assert result["queried_revision"] == scenario.before["revision"]
        assert result["queried_native_revision"] == scenario.before["native_revision"]
        assert result["queried_episode_run_id"] == scenario.before["episode_run_id"]
        assert SHARED_KEY not in result
        assert "fixed_chunk0_preparation_inputs_v1" not in result["army_strengths"][0]
        cached = deepcopy(scenario.driver.take_snapshot()["army_strengths"])
        result["army_strengths"][0]["war_ids"].append(99)
        assert scenario.driver.take_snapshot()["army_strengths"] == cached
        assert scenario.driver._command_history[-1]["ok"] is True

        direct = service.execute_step("query-army-strengths-v1", expected_revision=scenario.before["revision"])
        assert "fixed_chunk0_preparation_inputs_v1" in direct["army_strengths"][0]
        assert direct["army_strengths_profile"] == "ordinary_core_v1"
        count = len(scenario.endpoint.frames)
        with pytest.raises(ValueError, match="complete ordinary scope"):
            scenario.driver.query_army_strengths(
                army_ids=[82], expected_revision=scenario.before["revision"], _auto_core_only=True,
            )
        assert len(scenario.endpoint.frames) == count
    finally:
        scenario.driver.close()


def test_malformed_auto_scalar_rejects_without_publishing_or_business_action(tmp_path):
    scenario = make_scenario(tmp_path / "state")
    original_publish = scenario.endpoint.publish

    def malformed(frame):
        if frame.get("type") == "command_result":
            frame = deepcopy(frame)
            frame["result"]["army_strengths"][0]["current_soldiers"] = True
        original_publish(frame)

    scenario.endpoint.publish = malformed
    service = GameplayBridgeService(scenario.driver)
    try:
        with pytest.raises(BridgeUnavailableError, match="malformed rows"):
            service._execute_planned_turn_without_unhandled_capture(_planned(scenario.before))
        assert scenario.driver._army_strength_query is None
        assert scenario.driver._command_history[-1]["ok"] is False
        assert [frame["step"] for frame in scenario.endpoint.frames if frame.get("type") == "execute_step"] == ["query-army-strengths-v1"]
    finally:
        scenario.driver.close()
