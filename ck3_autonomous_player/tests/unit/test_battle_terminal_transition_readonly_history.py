"""One registered production-path regression using one retained Native60 packet.

Root supplies CK3_PERSON_READONLY_HISTORY_PACKET; no native producer is run.
Only native transport and paused semantic frames are synthetic. Service,
NativeDriver dispatch, snapshots, frame validation and normalizers are real.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge.battle_person_title_tail_capture_12004 import (
    FIELD_NAME,
    emit_captured_person_title_tail_request_12004,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    normalize_battle_terminal_transition_v1,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004


class _CountedPayload(list):
    copies = 0

    def __deepcopy__(self, memo):
        type(self).copies += 1
        detached = list(self)
        memo[id(self)] = detached
        return detached


class _PacketEndpoint:
    pipe_name = "offline-person-readonly-history"

    def __init__(self, packet):
        self.packet = deepcopy(packet)
        self.requests = []
        self.after_send = None
        self.on_frame = None

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, frame):
        self.on_frame(frame)

    def send(self, request):
        if request["type"] == "ping":
            return
        assert request["type"] == "execute_step"
        assert request["step"] == self.packet["result"]["step"]
        assert request["expected_revision"] == self.packet["result"]["snapshot_revision"]
        self.requests.append(deepcopy(request))
        response = deepcopy(self.packet)
        response["request_id"] = request["request_id"]
        self.publish(response)
        if self.after_send is not None:
            self.publish(self.after_send)

    def close(self):
        pass


def test_registered_terminal_query_omits_history_and_preserves_command_evidence():
    from mcp import Client

    packet_path = Path(os.environ["CK3_PERSON_READONLY_HISTORY_PACKET"])
    packet = json.loads(packet_path.read_bytes())
    original_packet = deepcopy(packet)
    assert packet_path.name == "matching-final-tail-ordered-i64.json"
    assert packet["type"] == "command_result" and packet["ok"] is True
    wire = packet["result"]
    raw_frame = wire["battle_terminal_transition"]
    observation, = raw_frame["character_observations"]
    subject = observation["character_id"]
    native_revision = wire["snapshot_revision"]
    date_raw = raw_frame["observed_date_raw"]
    step = query_battle_terminal_transition_v1_step(None, None, None, [subject])
    assert wire["step"] == step
    expected_frame = normalize_battle_terminal_transition_v1(
        raw_frame,
        expected_prior_combat_id=None,
        expected_subject_public_cunit_id=None,
        expected_after_terminal_sequence=None,
        expected_observed_date_raw=date_raw,
        expected_snapshot_revision=native_revision,
        expected_character_ids=[subject],
    )
    endpoint = _PacketEndpoint(packet)
    driver = NativeHeadlessGameplayDriver(
        endpoint=endpoint, episode_projection="native_campaign",
        command_timeout_seconds=0.1,
    )
    endpoint.publish({
        "type": "hello", "protocol_version": 1, "pid": 80808,
        "capabilities": ["game.state.snapshot", QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY],
        "expected_ck3_version": CK3_12004.game_version,
        "expected_ck3_sha256": CK3_12004.executable_sha256,
    })
    snapshot_packet = {
        "type": "state_snapshot", "protocol_version": 1,
        "snapshot_id": f"native:{native_revision}", "revision": native_revision,
        "state": {
            "phase": "map_hud", "date": "synthetic:person-readonly-history",
            "date_raw": date_raw, "speed": 1, "paused": True, "map_ready": True,
            "history": [], "active_event": None, "pending_character_interaction": None,
            "played_character": {"character_id": 29829, "alive": True},
            "one_life_settlement": None, "active_wars": [], "player_armies": [],
        },
    }
    endpoint.publish(snapshot_packet)
    starting = driver.take_internal_semantic_snapshot()
    retained = [{"index": index, "command": f"query-retained-person-{index}",
                 "ok": True, "result": {"values": _CountedPayload(range(32))}}
                for index in range(1, 257)]
    original_history = deepcopy(retained)
    with driver._history_lock:
        driver._command_history = retained
        driver._driver_state_dirty = False
    arguments = {
        "prior_combat_id": None, "subject_public_cunit_id": None,
        "after_terminal_sequence": None, "expected_revision": starting["revision"],
        "character_ids": [subject],
    }

    async def exercise():
        _CountedPayload.copies = 0
        with patch.object(driver, "_history_snapshot", wraps=driver._history_snapshot) as exports, \
             patch.object(driver, "_read_driver_state",
                          side_effect=AssertionError("query reloaded Driver state")) as reads, \
             patch.object(driver, "_encode_driver_state_locked",
                          side_effect=AssertionError("query encoded complete Driver state")) as encodes, \
             patch.object(driver, "_persist_driver_state", wraps=driver._persist_driver_state) as persists:
            async with Client(create_server(driver)) as client:
                default = await client.call_tool("ck3_take_snapshot", {})
                assert default.is_error is False, default.content
                assert default.structured_content["native_command_history"] == []
                assert default.structured_content["native_command_history_export"]["total_count"] == 256

                stale = await client.call_tool("ck3_query_battle_terminal_transition_v1", {
                    **arguments, "expected_revision": starting["revision"] + 1,
                })
                assert stale.is_error is True
                assert endpoint.requests == [] and len(driver._command_history) == 256

                response = await client.call_tool("ck3_query_battle_terminal_transition_v1", arguments)
                assert response.is_error is False, response.content
                actual = response.structured_content
                assert actual["battle_terminal_transition"] == expected_frame
                assert actual["character_observations"] == expected_frame["character_observations"]
                assert actual["query_sequence"] == wire["query_sequence"]
                assert actual["snapshot_revision"] == actual["queried_native_revision"] == native_revision
                assert actual["queried_revision"] == starting["revision"]
                assert actual["queried_snapshot_id"] == starting["snapshot_id"]
                section, = actual["character_observations"]
                request = emit_captured_person_title_tail_request_12004({
                    "character_id": subject,
                    FIELD_NAME: section["current_person_state"][FIELD_NAME],
                })
                assert request["property_block"]["keys_u16"] == [125, 97, 125, 111]
                assert request["property_block"]["values_q64"] == [
                    2**63 - 9, 0, -(2**63 - 9), 4294967296,
                ]
                assert len(endpoint.requests) == 1
                assert driver._command_history[:-1] == original_history
                recorded = driver._command_history[-1]
                assert recorded["index"] == 257 and recorded["command"] == step
                assert recorded["ok"] is True
                assert recorded["result"] == {key: actual[key] for key in recorded["result"]}
                assert driver._driver_state_dirty is True
                assert (exports.call_count, reads.call_count, encodes.call_count,
                        persists.call_count, _CountedPayload.copies) == (0, 0, 0, 0, 0)
                actual["battle_terminal_transition"]["status"] = "changed-by-consumer"
                assert recorded["result"]["battle_terminal_transition"]["status"] == "available"

                public = await client.call_tool("ck3_take_snapshot", {
                    "include_native_command_history": True,
                })
                assert public.is_error is False, public.content
                history = public.structured_content["native_command_history"]
                assert len(history) == 257 and history == driver._command_history
                assert exports.call_count == 1 and _CountedPayload.copies == 256
                history[0]["result"]["values"][0] = -1
                assert driver._command_history[0]["result"]["values"][0] == 0

                exports.reset_mock()
                _CountedPayload.copies = 0
                changed = deepcopy(snapshot_packet)
                changed["revision"] = native_revision + 1
                changed["snapshot_id"] = f"native:{native_revision + 1}"
                endpoint.after_send = changed
                drift = await client.call_tool("ck3_query_battle_terminal_transition_v1", arguments)
                assert drift.is_error is True
                assert "crossed a snapshot revision" in " ".join(
                    getattr(block, "text", "") for block in drift.content)
                assert len(endpoint.requests) == 2 and len(driver._command_history) == 258
                assert driver._command_history[:-2] == original_history
                assert driver._command_history[-1]["ok"] is False
                assert "crossed a snapshot revision" in driver._command_history[-1]["error"]
                assert (exports.call_count, reads.call_count, encodes.call_count,
                        persists.call_count, _CountedPayload.copies) == (0, 0, 0, 1, 0)

    try:
        asyncio.run(exercise())
        assert packet == endpoint.packet == original_packet
    finally:
        driver.close()
