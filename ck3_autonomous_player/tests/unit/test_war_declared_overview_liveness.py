"""Unpaused ordinary plans must pause before any popup read or close."""
import pytest

from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_declared_overview_contract import QUERY_CAPABILITY, CLOSE_CAPABILITY
from xar_autoplayer.strategy import choose_one_life_turn
from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot


@pytest.mark.parametrize("can_pause", [True, False], ids=["pause-map", "no-pause-map"])
def test_unpaused_popup_scope_uses_existing_pause_route_or_stays_blocked_without_rpc(can_pause):
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
        command_timeout_seconds=.1)
    capabilities = ["game.state.snapshot", QUERY_CAPABILITY, CLOSE_CAPABILITY,
        "game.command.declare-war-N"]
    if can_pause:
        capabilities.append("game.command.pause-map")
    hello = _hello(*capabilities)
    hello.update(bridge_version="0.1.0.4", expected_ck3_version=CK3_12004.game_version,
        expected_ck3_sha256=CK3_12004.executable_sha256, connection_generation=17)
    endpoint.publish(hello)
    endpoint.publish(_snapshot(40, played_character={"character_id":707,"alive":True},
        paused=False, map_ready=True))
    try:
        snapshot = driver.take_internal_semantic_snapshot()
        current_caps = driver.capabilities()
        assert snapshot["paused"] is False and snapshot["map_ready"] is True
        assert QUERY_CAPABILITY in current_caps["bridge_capabilities"]
        assert CLOSE_CAPABILITY in current_caps["bridge_capabilities"]
        assert ("pause-map" in current_caps["action_steps"]) is can_pause
        assert all(frame["type"] == "ping" for frame in endpoint.frames)
        endpoint.frames.clear()  # Separate observed constructor handshake from planning.
        strategy_plan = choose_one_life_turn(snapshot["history"], snapshot=snapshot,
            action_steps=current_caps["action_steps"],
            bridge_capabilities=current_caps["bridge_capabilities"])
        service_plan = GameplayBridgeService(driver).plan_turn()["plan"]
        for plan in (strategy_plan, service_plan):
            assert plan["policy"] == "ordinary-war-declared-overview-v1"
            assert plan["selected_step"] == ("pause-map" if can_pause else None)
            assert plan["status"] == ("ready" if can_pause else "blocked")
            assert plan["pending_actions"] == (["pause-map"] if can_pause else [])
        assert endpoint.frames == []  # Planning does not submit pause, popup or war actions.
    finally:
        driver.close()
