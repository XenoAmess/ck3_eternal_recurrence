"""One new registered read-only compound using two retained actual4 packets.

Only endpoint transport and matching paused contexts are synthetic. Native
bodies are unchanged; no producer, game, or previous qualification is rerun.
Root supplies both CK3_SWAY_READONLY_*_PACKET paths for the sole FIRST.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge.g2_private_query_transport import read_private_g2_native_query_v1
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.sway_formal_consumer import LEDGER_FILE, SCHEMA, read_sway_ledger


class _CountedPayload(list):
    copies = 0

    def __deepcopy__(self, memo):
        type(self).copies += 1
        detached = list(self)
        memo[id(self)] = detached
        return detached


class _PacketEndpoint:
    pipe_name = "offline-sway-readonly-history"

    def __init__(self, packet):
        self.packet = deepcopy(packet)
        self.requests = []
        self.after_send = None

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, frame):
        self.on_frame(frame)

    def send(self, request):
        if request["type"] == "ping":
            return
        assert request["type"] == "execute_step"
        assert request["step"] == self.packet["result"]["step"]
        self.requests.append(deepcopy(request))
        response = deepcopy(self.packet)
        response["request_id"] = request["request_id"]
        self.publish(response)
        if self.after_send is not None:
            self.publish(self.after_send)

    def close(self):
        pass


def _original_ledger(native, role):
    """The opinion fixture has an independent synthetic original-instance input."""
    resolved = {
        "status": "applied", "postcondition_verified": True,
        "actor_character_id": native["actor_character_id"],
        "target_character_id": native["target_character_id"],
        "action_id": "synthetic-original-sway-" + role,
        "post_native_revision": native["snapshot_revision"],
        "post_date_raw": native["date_raw"], "next_turn_consumed": True,
        "native_receipt": {
            "scheme_instance_id": native.get("scheme_instance_id", 1),
            "scheme_instance_generation": native.get("scheme_instance_generation", 0),
        },
    }
    if role == "opinion":
        resolved["latest_instance_observation"] = {
            "actor_character_id": native["actor_character_id"],
            "target_character_id": native["target_character_id"],
            "exact_ck3_build": CK3_12004.game_version,
            "exe_sha256": CK3_12004.executable_sha256,
            "source_date_raw": native["date_raw"],
            "tracked_instance_active": True,
            "instance_terminal_outcome_observed": False,
        }
    return {"schema": SCHEMA, "pending": None, "resolved": resolved}


def test_registered_sway_reads_omit_unused_history_and_preserve_durable_facts(tmp_path: Path):
    from mcp import Client

    roles = (
        ("completion", "sway_completion", "allow_private_active_scheme_sway_completion_query"),
        ("opinion", "sway_outcome_opinion", "allow_private_active_scheme_sway_outcome_opinion_query"),
    )
    for role, field, permission in roles:
        packet_path = Path(os.environ[f"CK3_SWAY_READONLY_{role.upper()}_PACKET"])
        packet = json.loads(packet_path.read_bytes())
        original_packet = deepcopy(packet)
        assert packet["type"] == "command_result" and packet["ok"] is True
        native = packet["result"][field]
        endpoint = _PacketEndpoint(packet)
        driver = NativeHeadlessGameplayDriver(
            endpoint=endpoint, episode_projection="native_campaign",
            command_timeout_seconds=0.1,
        )
        setattr(driver, permission, True)
        endpoint.publish({
            "type": "hello", "protocol_version": 1, "pid": 80808,
            "capabilities": ["game.state.snapshot"],
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
        })
        snapshot_packet = {
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": f"native:{native['snapshot_revision']}",
            "revision": native["snapshot_revision"],
            "state": {
                "phase": "map_hud", "date": "synthetic:sway-readonly-history",
                "date_raw": native["date_raw"], "speed": 1,
                "paused": True, "map_ready": True, "history": [],
                "played_character": {"character_id": native["actor_character_id"], "alive": True},
                "active_event": None, "pending_character_interaction": None,
                "one_life_settlement": None, "active_wars": [], "player_armies": [],
            },
        }
        endpoint.publish(snapshot_packet)
        starting = driver.take_internal_semantic_snapshot()
        state_dir = tmp_path / role
        state_dir.mkdir()
        driver.state_dir = state_dir
        ledger_path = state_dir / LEDGER_FILE
        original_ledger = _original_ledger(native, role)
        ledger_path.write_text(json.dumps(original_ledger), encoding="utf-8")
        retained = [{"index": index, "command": f"retained-sway-{index}",
                     "ok": True, "result": {"values": _CountedPayload(range(32))}}
                    for index in range(1, 257)]
        original_history = deepcopy(retained)
        with driver._history_lock:
            driver._command_history = retained
            # Exercise the normal close barrier for existing pending state.
            driver._driver_state_dirty = True
        arguments = {"expected_revision": starting["revision"],
                     "target_character_id": native["target_character_id"]}
        if role == "completion":
            arguments["scheme_instance_id"] = native["scheme_instance_id"]
        tool = ("ck3_query_active_scheme_sway_completion_private_v1" if role == "completion"
                else "ck3_query_active_scheme_sway_outcome_opinion_private_v1")

        async def exercise():
            _CountedPayload.copies = 0
            with patch.object(driver, "_history_snapshot", wraps=driver._history_snapshot) as exports, \
                 patch.object(driver, "_read_driver_state",
                              side_effect=AssertionError("query reloaded Driver state")) as reads, \
                 patch.object(driver, "_encode_driver_state_locked",
                              wraps=driver._encode_driver_state_locked) as encodes, \
                 patch.object(driver, "_persist_driver_state", wraps=driver._persist_driver_state) as persists:
                async with Client(create_server(driver)) as client:
                    default = await client.call_tool("ck3_take_snapshot", {})
                    assert not default.is_error, default.content
                    assert default.structured_content["native_command_history"] == []
                    assert default.structured_content["native_command_history_export"]["total_count"] == 256
                    stale = await client.call_tool(tool, {
                        **arguments, "expected_revision": starting["revision"] + 1,
                    })
                    assert stale.is_error and endpoint.requests == []
                    assert read_sway_ledger(state_dir) == original_ledger

                    response = await client.call_tool(tool, arguments)
                    assert not response.is_error, response.content
                    actual = response.structured_content
                    assert {key: actual[key] for key in native} == native
                    assert actual["queried_revision"] == starting["revision"]
                    assert actual["queried_native_revision"] == native["snapshot_revision"]
                    assert len(endpoint.requests) == 1
                    assert endpoint.requests[0]["actor_character_id"] == native["actor_character_id"]
                    assert endpoint.requests[0]["expected_revision"] == native["snapshot_revision"]
                    assert driver.state.wait_for_command_result(endpoint.requests[0]["request_id"], 0) is None
                    assert driver._command_history == original_history
                    assert driver._driver_state_dirty is True
                    assert (exports.call_count, reads.call_count, encodes.call_count,
                            persists.call_count, _CountedPayload.copies) == (0, 0, 0, 0, 0)
                    resolved = read_sway_ledger(state_dir)["resolved"]
                    assert resolved["native_receipt"] == original_ledger["resolved"]["native_receipt"]
                    if role == "completion":
                        observed = resolved["latest_instance_observation"]
                        assert observed["native_observation"] == actual
                        assert observed["instance_terminal_outcome_observed"] == native["native_terminal_state_observed"]
                        assert observed["terminal_cause"] == native["terminal_cause"]
                    else:
                        material = resolved["material_intervention"]
                        assert material["scheme_sway_opinion"] == native["scheme_sway_opinion"]
                        assert material["sway_blocker_opinion"] == native["sway_blocker_opinion"]
                        assert material["target_opinion_of_actor"] == native["target_opinion_of_actor"]
                        assert not material["instance_terminal_outcome_observed"]

                    public = await client.call_tool("ck3_take_snapshot", {"include_native_command_history": True})
                    history = public.structured_content["native_command_history"]
                    assert not public.is_error and history == original_history
                    assert exports.call_count == 1 and _CountedPayload.copies == 256
                    history[0]["result"]["values"][0] = -1
                    assert driver._command_history[0]["result"]["values"][0] == 0

                    # Unmodified G2 callers still use the shared reader's default full export.
                    exports.reset_mock()
                    _CountedPayload.copies = 0
                    before, raw = read_private_g2_native_query_v1(
                        driver, permission=permission, step=packet["result"]["step"],
                        expected_revision=starting["revision"], timeout_seconds=0.1,
                    )
                    assert before["native_command_history"] == original_history
                    assert raw == packet["result"]
                    assert exports.call_count == 2 and _CountedPayload.copies == 512

                    exports.reset_mock()
                    _CountedPayload.copies = 0
                    saved_ledger = ledger_path.read_bytes()
                    changed = deepcopy(snapshot_packet)
                    changed["revision"] = native["snapshot_revision"] + 1
                    changed["snapshot_id"] = f"native:{changed['revision']}"
                    endpoint.after_send = changed
                    drift = await client.call_tool(tool, arguments)
                    assert drift.is_error
                    assert "crossed its paused frame" in " ".join(
                        getattr(block, "text", "") for block in drift.content)
                    assert ledger_path.read_bytes() == saved_ledger
                    assert len(endpoint.requests) == 3 and driver._command_history == original_history
                    assert (exports.call_count, reads.call_count, encodes.call_count,
                            persists.call_count, _CountedPayload.copies) == (0, 0, 0, 0, 0)
                # Closing the SDK retains the original full-history persistence barrier.
                driver.close()
                assert (persists.call_count, encodes.call_count) == (1, 1)
                assert driver._driver_state_dirty is False and driver._driver_state_error is None
                stored = json.loads(driver._native_driver_state_path().read_bytes())
                assert stored["command_history"] == original_history
                assert read_sway_ledger(state_dir)["resolved"] == resolved

        try:
            asyncio.run(exercise())
            assert packet == endpoint.packet == original_packet
        finally:
            driver.close()
