"""Sole new registered production-route regression; Root executes the FIRST.

Transport and native War reply are deterministic fixtures. No native producer
or gameplay outcome is qualified by this Python history-export check.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

from test_native_bridge_driver import (
    FakeEndpoint, _hello, _snapshot, _termination_options, _war,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_contract import (
    QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY, query_war_termination_options_step,
)


class _CountedRetainedPayload(list):
    copies = 0

    def __deepcopy__(self, memo):
        type(self).copies += 1
        result = list(self)
        memo[id(self)] = result
        return result


def test_registered_termination_options_omits_revision_history_and_preserves_receipts(tmp_path: Path):
    from mcp import Client

    war_id = 100663329
    step = query_war_termination_options_step(war_id)
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name, endpoint=endpoint, state_dir=tmp_path,
        episode_projection="native_campaign", command_timeout_seconds=0.1,
    )
    hello = _hello("game.state.snapshot", QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY)
    hello.update(expected_ck3_version=CK3_12004.game_version,
                 expected_ck3_sha256=CK3_12004.executable_sha256)
    endpoint.publish(hello)
    endpoint.publish(_snapshot(40,
        played_character={"character_id": 707, "alive": True},
        active_wars=[_war(war_id, score=41)], player_armies=[]))
    before = driver.take_internal_semantic_snapshot()
    native_options = _termination_options(war_id, score=41)
    native_reply = {"step": step, "accepted": True, "status": "available",
                    "query_sequence": 7, "war_termination_options": native_options}
    requests = []

    def answer(request):
        if request.get("type") != "execute_step":
            return
        requests.append(deepcopy(request))
        assert request["step"] == step
        endpoint.publish({"type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": True,
            "result": deepcopy(native_reply)})

    endpoint.send_hook = answer
    retained = [{"index": index, "command": f"retained-war-history-{index}",
                 "ok": True, "result": {"values": _CountedRetainedPayload(range(32))}}
                for index in range(1, 257)]
    original = deepcopy(retained)
    with driver._history_lock:
        driver._command_history = retained
        driver._driver_state_dirty = True

    async def exercise():
        _CountedRetainedPayload.copies = 0
        with patch.object(driver, "_history_snapshot", wraps=driver._history_snapshot) as exports, \
             patch.object(driver, "_persist_driver_state", wraps=driver._persist_driver_state) as persists:
            async with Client(create_server(driver)) as client:
                response = await client.call_tool("ck3_query_war_termination_options", {
                    "war_id": war_id, "expected_revision": before["revision"],
                })
                assert not response.is_error, response.content
                actual = response.structured_content
                assert actual["war_id"] == war_id
                assert actual["war_termination_options"]["options"] == native_options["options"]
                assert actual["queried_snapshot_id"] == before["snapshot_id"]
                assert actual["queried_revision"] == before["revision"]
                assert actual["queried_native_revision"] == before["native_revision"]
                assert len(requests) == 1
                assert requests[0]["expected_revision"] == before["native_revision"]
                assert (exports.call_count, _CountedRetainedPayload.copies, persists.call_count) == (0, 0, 0)
                assert driver._command_history[:-1] == original
                assert driver._command_history[-1]["command"] == step
                assert driver._command_history[-1]["ok"] is True
                assert driver._driver_state_dirty is True

                public = driver.take_snapshot()
                assert exports.call_count == 1 and _CountedRetainedPayload.copies == 256
                assert public["native_command_history"] == driver._command_history
                public["native_command_history"][0]["result"]["values"][0] = -1
                assert driver._command_history[0]["result"]["values"][0] == 0
            driver._persist_driver_state()
            assert persists.call_count == 1
            stored = json.loads(driver._native_driver_state_path().read_bytes())
            assert stored["command_history"] == driver._command_history
            assert driver._driver_state_dirty is False

    try:
        asyncio.run(exercise())
    finally:
        driver.close()
