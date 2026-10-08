"""AUTHORED_NOTRUN: one registered MCP consumer of twelve NEW whole packets.

Root runs the new producer once, then this node once. NativeDriver, the main
normalizer, Service and the registered MCP route consume the original complete
command_result. Only request correlation and hello/paused framing are fixtures.
This does not execute the preceding ten-scene producer or its passed consumer.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge.battle_person_conditional_2921a90_12004 import (
    FIELD_NAME, SCHEMA,
    emit_conditional_2921a90_requests_from_current_source_inputs_12004 as emit_conditional,
    emit_conditional_2921a90_row_requests_from_current_source_inputs_12004 as emit_row,
    emit_complete_2921a90_requests_from_current_source_inputs_12004 as emit_complete,
)
from xar_autoplayer.bridge.battle_person_following_2921a90_12004 import (
    emit_following_2921a90_direct_requests_from_current_source_inputs_12004 as emit_direct,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004

TOOL = "ck3_query_battle_terminal_transition_v1"
ENEMY, PLAYER, PUBLIC, NATIVE, DATE = 0x04000003, 29829, 73, 41, 53236632
CASES = (
    ("self-high-default-and-raw", True, 0),
    ("self-low-b80", True, 2),
    ("self-middle-empty", True, 1),
    ("empty-classifier-list", True, 1),
    ("other-person-opinion", False, None),
    ("dynamic-weight", False, 0),
    ("pc-values-partial", False, 0),
    ("metadata-registry-null", False, 0),
    ("cold-default-classifier", False, None),
    ("negative-selected-count", False, 0),
    ("zero-demand-bypass", True, None),
    ("large-max-operand-weight", True, 0),
)


class ConditionalWholeEndpoint:
    pipe_name = "offline-person-conditional2921a90-original-whole"

    def __init__(self, step):
        self.step, self.packet, self.on_frame = step, None, None
        self.requests, self.delivered = [], []

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def select(self, packet):
        self.packet = deepcopy(packet)

    def send(self, request):
        assert request["type"] == "execute_step" and request["protocol_version"] == 1
        assert request["step"] == self.step and request["expected_revision"] == NATIVE
        self.requests.append(deepcopy(request))
        response = deepcopy(self.packet)
        response["request_id"] = request["request_id"]
        assert {k: v for k, v in response.items() if k != "request_id"} == {
            k: v for k, v in self.packet.items() if k != "request_id"}
        self.delivered.append(deepcopy(response))
        self.on_frame(response)

    def close(self):
        pass


def test_person_conditional_2921a90_12004_registered_mcp_whole_packets():
    from mcp import Client

    directory = Path(os.environ["CK3_PERSON_CONDITIONAL_2921A90_12004_MCP_WIRE_DIR"])
    packets = {name: json.loads((directory / (name + ".json")).read_bytes()) for name, *_ in CASES}
    originals = deepcopy(packets)
    step = query_battle_terminal_transition_v1_step(None, None, None, [ENEMY])
    endpoint = ConditionalWholeEndpoint(step)
    driver = NativeHeadlessGameplayDriver(endpoint=endpoint, episode_projection="native_campaign")
    hello = {"type": "hello", "protocol_version": 1, "pid": 1,
             "capabilities": ["game.state.snapshot", QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY],
             "expected_ck3_version": CK3_12004.game_version,
             "expected_ck3_sha256": CK3_12004.executable_sha256}
    assert driver.state.ingest(hello) == "hello"
    snapshot = {"snapshot_id": "new-person-conditional2921a90-offline-frame", "revision": PUBLIC,
                "native_revision": NATIVE, "date_raw": DATE, "paused": True, "map_ready": True,
                "backend_id": "native-headless", "played_character": {"character_id": PLAYER, "alive": True},
                "player_armies": [], "active_wars": [], "active_event": None,
                "pending_character_interaction": None, "episode_run_id": "offline-conditional2921a90",
                "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)}}
    leaves, emitted, independent, combined = {}, {}, {}, {}

    def unavailable(function, reason, *arguments):
        try:
            function(*arguments)
        except ValueError as error:
            assert reason in str(error)
        else:
            raise AssertionError("A missing actual operand produced a complete conditional value")

    async def consume():
        with patch.object(driver, "take_snapshot", side_effect=lambda: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                assert TOOL in {tool.name for tool in (await client.list_tools()).tools}
                for sequence, (name, ready, classifier) in enumerate(CASES, 1):
                    packet = packets[name]
                    assert packet["type"] == "command_result" and packet["ok"] is True
                    raw_frame = packet["result"]["battle_terminal_transition"]
                    assert packet["result"]["step"] == step
                    assert packet["result"]["query_sequence"] == sequence
                    assert packet["result"]["snapshot_revision"] == NATIVE
                    assert raw_frame["observed_date_raw"] == DATE
                    raw_person = raw_frame["character_observations"][0]["current_person_state"]
                    raw_leaf = raw_person[FIELD_NAME]
                    assert raw_leaf["schema"] == SCHEMA and raw_leaf["character_id"] == ENEMY
                    endpoint.select(packet)
                    response = await client.call_tool(TOOL, {
                        "prior_combat_id": None, "subject_public_cunit_id": None,
                        "expected_revision": PUBLIC, "character_ids": [ENEMY],
                    })
                    assert not response.is_error, response.content
                    result = response.structured_content
                    frame = result["battle_terminal_transition"]
                    assert result["status"] == frame["status"] == "available"
                    assert not frame["battle_terminal_transition_ready"]
                    assert result["queried_revision"] == PUBLIC and result["queried_native_revision"] == NATIVE
                    assert result["queried_snapshot_id"] == snapshot["snapshot_id"]
                    row = frame["character_observations"][0]
                    assert row["character_id"] == ENEMY != PLAYER
                    person = row["current_person_state"]
                    leaf = person[FIELD_NAME]
                    assert leaf["character_id"] == person["following_2921a90"]["character_id"] == row["character_id"]
                    source_inputs = {"character_id": row["character_id"],
                                     "following_2921a90": person["following_2921a90"], FIELD_NAME: leaf}
                    leaves[name] = leaf
                    assert leaf["ready"] is ready and leaf["classifier_result_i32"] == classifier
                    assert leaf["build_version"] == CK3_12004.game_version
                    assert leaf["executable_sha256"] == CK3_12004.executable_sha256
                    for key in ("character_identity", "selected_model_identity", "selected_object_identity"):
                        assert leaf[key] == raw_leaf[key] == person["following_2921a90"][key]
                    direct = emit_direct(source_inputs)
                    assert len(direct) == 4
                    if ready:
                        emitted[name] = emit_conditional(source_inputs)
                        combined[name] = emit_complete(source_inputs)
                        assert combined[name][:4] == direct
                        assert len(combined[name]) == 4 + len(emitted[name])
                        assert len(emitted[name]) == leaf["occurrence_count"]
                    else:
                        unavailable(emit_conditional, leaf["reason"], source_inputs)
                        unavailable(emit_complete, leaf["reason"], source_inputs)
                    available_rows = {}
                    for source in leaf["rows"]:
                        index = source["native_index"]
                        if source["ready"]:
                            requests = emit_row(source_inputs, index)
                            if source["weight_q64"] == 0:
                                assert requests == ()
                            else:
                                assert len(requests) == 1 and requests[0].source_ordinal == index
                                assert requests[0].weight_q64 == 100000
                                assert requests[0].row_count == 1 and requests[0].first_row_index == 0
                                assert requests[0].definition_identity == source["object_identity"]
                            available_rows[index] = requests
                        else:
                            unavailable(emit_row, source["reason"], source_inputs, index)
                    independent[name] = available_rows
                    assert endpoint.packet == packet

    try:
        asyncio.run(consume())
    finally:
        driver.close()

    full = emitted["self-high-default-and-raw"]
    assert [r.source_ordinal for r in full] == [0, 1, 2, 4]
    assert [r.source_ordinal for r in combined["self-high-default-and-raw"]] == [0, 1, 2, 3, 4, 5, 6, 8]
    assert full[0].definition_identity == full[2].definition_identity
    literal = {"keys_count": 4, "keys_u16": [1, 2, 65535, 1],
               "values_q64": [200000, -250001, (1 << 63) - 1, 200000]}
    assert full[0].base_property_block == full[2].base_property_block == literal
    assert full[1].base_property_block == {"keys_count": 2, "keys_u16": [1, 2], "values_q64": [-300000, 375001]}
    assert full[3].base_property_block == {"keys_count": 0, "keys_u16": [], "values_q64": []}
    assert independent["self-high-default-and-raw"][3] == ()
    votes = leaves["self-high-default-and-raw"]["classifier_rows"]
    assert len(votes) == 2 and all(v["selected_character_identity"] == leaves["self-high-default-and-raw"]["character_identity"] for v in votes)
    assert all(v["base_opinion_i32"] == 100 and v["additional_opinion_i32"] == 0 and v["vote"] == "high" for v in votes)
    assert all(v["low_threshold_bits_u32"] is None for v in votes)
    assert leaves["self-low-b80"]["selected_family"] == "b80_b8c"
    assert len(emitted["self-low-b80"]) == 1 and emitted["self-low-b80"][0].base_property_block["values_q64"] == [-300000, 375001]
    for name in ("self-middle-empty", "empty-classifier-list", "zero-demand-bypass"):
        assert emitted[name] == () and leaves[name]["occurrence_count"] == 0
    assert leaves["other-person-opinion"]["classifier_rows"][0]["ready"]
    assert not leaves["other-person-opinion"]["classifier_rows"][1]["ready"]
    assert leaves["other-person-opinion"]["reason"] == "classifier_25a1220_directional_opinion_unobserved"
    for name in ("dynamic-weight", "pc-values-partial"):
        assert set(independent[name]) == {1, 3, 4}
        assert leaves[name]["rows"][0]["object_identity"] == leaves[name]["rows"][2]["object_identity"]
        assert leaves[name]["occurrence_count"] is None
    assert leaves["dynamic-weight"]["reason"] == "weight_virtual_expression_9d7060_unobserved"
    assert leaves["pc-values-partial"]["rows"][0]["properties"]["keys_u16"] == [1, 2, 65535, 1]
    assert leaves["pc-values-partial"]["rows"][0]["properties"]["values_q64"] is None
    assert set(independent["metadata-registry-null"]) == {3, 4}
    assert leaves["metadata-registry-null"]["rows"][4]["metadata_registry_identity"] == "0x0"
    assert leaves["cold-default-classifier"]["classifier_default_guard_i32"] == 0
    assert leaves["cold-default-classifier"]["reason"] == "classifier_default_uninitialized"
    assert leaves["negative-selected-count"]["selected_count_i32"] == -1
    assert leaves["negative-selected-count"]["reason"] == "conditional_selected_count_negative"
    assert emitted["large-max-operand-weight"][0].base_property_block == {
        "keys_count": 1, "keys_u16": [2], "values_q64": [4611824369007940742]}
    raw = packets["self-high-default-and-raw"]["result"]["battle_terminal_transition"]["character_observations"][0]["current_person_state"][FIELD_NAME]
    assert raw["rows"][0]["weight_q64"] == "100000"
    assert raw["rows"][1]["raw_value_258_q64"] == "-150000"
    assert all(isinstance(value, str) for value in raw["rows"][0]["properties"]["values_q64"])
    assert len(endpoint.requests) == len(endpoint.delivered) == 12
    assert driver.state._command_results == {}
    assert packets == originals
