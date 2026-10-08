"""AUTHORED_NOTRUN: one registered same-query consumer of eight NEW whole wires.

Root first runs the new native production-reader/formatter fixture, then selects
only test_person_carrier_direct12004_registered_mcp_eight_whole_packets with
PYTHONPATH=<source tree>/ck3_autonomous_player/src and
CK3_PERSON_CARRIER_DIRECT_12004_MCP_WIRE_DIR=<new native output directory>.
Original command_result/result/DTO packets are never reconstructed; transport
adapts only top-level request_id. Hello and paused player snapshot are fixtures.
Offline source qualification grants no live, stage-start, or full Entry credit.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge.battle_person_carrier_direct_12004 import (
    FIELD_NAME,
    emit_carrier_1c8_b70_direct_requests_from_current_source_inputs_12004,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004


TOOL = "ck3_query_battle_terminal_transition_v1"
ENEMY_FULL_ID = 0x04000003
PLAYER_FULL_ID = 29829
PUBLIC_REVISION = 73
NATIVE_REVISION = 41
DATE_RAW = 53236632
EXPECTATIONS = (
    ("absent-carrier", True, "none", 0),
    ("wrong-magic", True, "none", 0),
    ("mapped-empty", True, "mapped_row", 0),
    ("mapped-nonempty-signed-prowess", True, "mapped_row", 1),
    ("fallback-initialized", True, "static_default_5d71200", 1),
    ("fallback-guard-zero", False, "static_default_5d71200", None),
    ("raw-partial-values", False, "mapped_row", None),
    ("negative-rank-undemanded-count", True, "static_default_5d71200", 0),
)


class OriginalWholePacketEndpoint:
    """Inject original native packets into the real Driver protocol callback."""

    pipe_name = "offline-person-carrier-direct12004-whole-packets"

    def __init__(self, step):
        self.step = step
        self.requests = []
        self.delivered = []
        self.packet = None
        self.on_frame = None

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def select(self, packet):
        self.packet = deepcopy(packet)

    def send(self, request):
        assert request["type"] == "execute_step"
        assert request["protocol_version"] == 1
        assert request["step"] == self.step
        assert request["expected_revision"] == NATIVE_REVISION
        self.requests.append(deepcopy(request))
        response = deepcopy(self.packet)
        # Preserve the production formatter's complete result and raw leaf.
        response["request_id"] = request["request_id"]
        assert {key: response[key] for key in self.packet if key != "request_id"} == {
            key: value for key, value in self.packet.items() if key != "request_id"
        }
        self.delivered.append(deepcopy(response))
        self.on_frame(response)

    def close(self):
        pass


def test_person_carrier_direct12004_registered_mcp_eight_whole_packets():
    # This is the project's held mcp==2.0.0 Client API, not a guessed SDK shim.
    from mcp import Client

    directory = Path(os.environ["CK3_PERSON_CARRIER_DIRECT_12004_MCP_WIRE_DIR"])
    packets = {
        basename: json.loads((directory / (basename + ".json")).read_bytes())
        for basename, *_ in EXPECTATIONS
    }
    originals = deepcopy(packets)
    step = query_battle_terminal_transition_v1_step(None, None, None, [ENEMY_FULL_ID])
    assert step == "query-battle-terminal-transition-v1-none:characters:67108867"
    endpoint = OriginalWholePacketEndpoint(step)
    driver = NativeHeadlessGameplayDriver(endpoint=endpoint, episode_projection="native_campaign")
    hello = {
        "type": "hello", "protocol_version": 1, "pid": 1,
        "capabilities": ["game.state.snapshot", QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY],
        "expected_ck3_version": CK3_12004.game_version,
        "expected_ck3_sha256": CK3_12004.executable_sha256,
    }
    assert driver.state.ingest(hello) == "hello"
    snapshot = {
        "snapshot_id": "person-carrier-direct12004-paused-native41",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": PLAYER_FULL_ID, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-carrier-direct12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }
    leaves = {}
    contributions = {}

    async def exercise():
        # Snapshot scaffolding is the sole Driver method seam. Capabilities,
        # execute_step, primitive, main normalizer, Service and MCP remain real.
        with patch.object(driver, "take_snapshot", side_effect=lambda: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                registered = {tool.name for tool in (await client.list_tools()).tools}
                assert TOOL in registered
                for sequence, (basename, ready, selection, occurrence) in enumerate(EXPECTATIONS, 1):
                    packet = packets[basename]
                    assert packet["type"] == "command_result"
                    assert packet["protocol_version"] == 1 and packet["ok"] is True
                    native_result = packet["result"]
                    assert native_result["step"] == step
                    assert native_result["query_sequence"] == sequence
                    assert native_result["snapshot_revision"] == NATIVE_REVISION
                    raw_frame = native_result["battle_terminal_transition"]
                    assert raw_frame["observed_date_raw"] == DATE_RAW
                    assert [row["character_id"] for row in raw_frame["character_observations"]] == [ENEMY_FULL_ID]
                    raw_state = raw_frame["character_observations"][0]["current_person_state"]
                    raw_leaf = raw_state[FIELD_NAME]
                    assert raw_leaf["character_id"] == ENEMY_FULL_ID
                    assert raw_leaf["build_version"] == CK3_12004.game_version
                    assert raw_leaf["executable_sha256"].upper() == CK3_12004.executable_sha256

                    endpoint.select(packet)
                    response = await client.call_tool(TOOL, {
                        "prior_combat_id": None, "subject_public_cunit_id": None,
                        "expected_revision": PUBLIC_REVISION,
                        "character_ids": [ENEMY_FULL_ID],
                    })
                    assert response.is_error is False, response.content
                    actual = response.structured_content
                    frame = actual["battle_terminal_transition"]
                    assert actual["status"] == frame["status"] == "available"
                    assert frame["battle_terminal_transition_ready"] is False
                    assert frame["prior_combat_id"] == frame["subject_public_cunit_id"] == -1
                    assert all(frame[key] is None for key in ("prior", "removal", "subject", "successor"))
                    assert actual["character_observations"] == frame["character_observations"]
                    assert actual["queried_snapshot_id"] == snapshot["snapshot_id"]
                    assert actual["queried_revision"] == PUBLIC_REVISION
                    assert actual["queried_native_revision"] == NATIVE_REVISION
                    row = frame["character_observations"][0]
                    assert row["character_id"] == ENEMY_FULL_ID != PLAYER_FULL_ID
                    state = row["current_person_state"]
                    assert {key: value for key, value in state.items() if key != FIELD_NAME} == {
                        key: value for key, value in raw_state.items() if key != FIELD_NAME
                    }
                    leaf = state[FIELD_NAME]
                    leaves[basename] = leaf
                    assert leaf["character_id"] == row["character_id"] == ENEMY_FULL_ID
                    assert leaf["ready"] is ready
                    assert leaf["selection"] == selection
                    assert leaf["source_occurrence_count"] == occurrence
                    for key in ("selected_model_identity", "destination_pc_identity",
                                "character_identity", "selected_pc_identity"):
                        assert leaf[key] == raw_leaf[key]

                    # Feed the actual joined production result to the existing
                    # pure ordered contribution helper; never rebuild a frame.
                    source = {"character_id": row["character_id"], FIELD_NAME: leaf}
                    if ready:
                        emitted = emit_carrier_1c8_b70_direct_requests_from_current_source_inputs_12004(source)
                        assert len(emitted) == occurrence
                        contributions[basename] = emitted
                        for request in emitted:
                            assert request.source_ordinal == 0
                            assert request.first_row_index == 0 and request.row_count == 1
                            assert request.weight_q64 == 100000
                            assert request.definition_identity == leaf["selected_pc_identity"]
                    else:
                        try:
                            emit_carrier_1c8_b70_direct_requests_from_current_source_inputs_12004(source)
                        except ValueError as error:
                            assert leaf["reason"] in str(error)
                        else:
                            raise AssertionError("An available partial frame produced a complete contribution")
                    assert snapshot["played_character"]["character_id"] == PLAYER_FULL_ID
                    assert endpoint.packet == packet

    try:
        asyncio.run(exercise())
    finally:
        driver.close()

    signed_values = [-100000, -(1 << 63), 0, (1 << 63) - 1]
    signed = contributions["mapped-nonempty-signed-prowess"][0].base_property_block
    assert signed["keys_count"] == 4
    assert signed["keys_u16"] == [0x22A, 0xFFFF, 0x22A, 0]
    assert signed["values_q64"] == signed_values
    raw_signed = packets["mapped-nonempty-signed-prowess"]["result"]["battle_terminal_transition"]["character_observations"][0]["current_person_state"][FIELD_NAME]["properties"]
    assert raw_signed["keys_u16"] == signed["keys_u16"]
    assert raw_signed["values_q64"] == [str(value) for value in signed_values]
    default = contributions["fallback-initialized"][0].base_property_block
    assert default["keys_u16"] == [0x22A]
    assert default["values_q64"] == [-250000]
    pending = leaves["fallback-guard-zero"]
    assert pending["default_guard_raw"] == 0
    assert pending["selected_pc_count_i32"] == 1
    assert pending["properties"]["values_q64"] == [-250000]
    partial = leaves["raw-partial-values"]
    assert partial["properties"]["keys_u16"] == [0x22A, 0xFFFF, 0x22A, 0]
    assert partial["properties"]["values_q64"] is None
    negative = leaves["negative-rank-undemanded-count"]
    assert negative["rank_i32"] == -1 and negative["row_count_i32"] is None
    assert negative["selected_pc_count_i32"] == 0
    assert len(endpoint.requests) == len(endpoint.delivered) == 8
    assert {request["expected_revision"] for request in endpoint.requests} == {NATIVE_REVISION}
    assert driver.state._command_results == {}
    assert packets == originals
