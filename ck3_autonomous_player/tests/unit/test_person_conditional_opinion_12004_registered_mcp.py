"""AUTHORED_NOTRUN: registered MCP consumer for five new opinion whole packets.

Consume genuine whole command_result bodies through NativeDriver, the main
normalizer, Service and the registered tool. Only request correlation and
hello/paused framing are fixture seams. No preceding fixture is executed.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge.battle_person_conditional_opinion_12004 import (
    FIELD_NAME, SCHEMA,
    emit_opinion_conditional_2921a90_requests_from_current_source_inputs_12004 as emit_conditional,
    emit_opinion_conditional_2921a90_row_requests_from_current_source_inputs_12004 as emit_row,
    emit_complete_opinion_2921a90_requests_from_current_source_inputs_12004 as emit_complete,
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
OWNERS = (0x06000004, 0x07000005, 0x08000006)
CASES = (
    ("opinion-high", True, 0),
    ("opinion-low", True, 2),
    ("opinion-mixed-tie", True, 1),
    ("opinion-provider-unavailable", False, None),
    ("opinion-dynamic-weight-later-ready", False, 0),
)


class OpinionWholeEndpoint:
    pipe_name = "offline-person-conditional-opinion-original-whole"

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
        assert {key: value for key, value in response.items() if key != "request_id"} == {
            key: value for key, value in self.packet.items() if key != "request_id"}
        self.delivered.append(deepcopy(response))
        self.on_frame(response)

    def close(self):
        pass


def test_person_conditional_opinion_12004_registered_mcp_whole_packets():
    from mcp import Client

    directory = Path(os.environ["CK3_PERSON_CONDITIONAL_OPINION_12004_MCP_WIRE_DIR"])
    packets = {name: json.loads((directory / (name + ".json")).read_bytes()) for name, *_ in CASES}
    originals = deepcopy(packets)
    step = query_battle_terminal_transition_v1_step(None, None, None, [ENEMY])
    endpoint = OpinionWholeEndpoint(step)
    driver = NativeHeadlessGameplayDriver(endpoint=endpoint, episode_projection="native_campaign")
    hello = {"type": "hello", "protocol_version": 1, "pid": 1,
             "capabilities": ["game.state.snapshot", QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY],
             "expected_ck3_version": CK3_12004.game_version,
             "expected_ck3_sha256": CK3_12004.executable_sha256}
    assert driver.state.ingest(hello) == "hello"
    snapshot = {"snapshot_id": "new-person-conditional-opinion-offline-frame", "revision": PUBLIC,
                "native_revision": NATIVE, "date_raw": DATE, "paused": True, "map_ready": True,
                "backend_id": "native-headless", "played_character": {"character_id": PLAYER, "alive": True},
                "player_armies": [], "active_wars": [], "active_event": None,
                "pending_character_interaction": None, "episode_run_id": "offline-conditional-opinion",
                "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)}}
    leaves, emitted, combined, independent = {}, {}, {}, {}

    def unavailable(function, reason, *arguments):
        try:
            function(*arguments)
        except ValueError as error:
            assert reason in str(error)
        else:
            raise AssertionError("An unread pair or selected PC operand released a complete value")

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
                    assert raw_leaf["source_inputs"] == raw_person["following_2921a90_conditional"]
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
                    outer_row = frame["character_observations"][0]
                    assert outer_row["character_id"] == ENEMY != PLAYER
                    person = outer_row["current_person_state"]
                    leaf = person[FIELD_NAME]
                    source_inputs = {"character_id": outer_row["character_id"],
                                     "following_2921a90": person["following_2921a90"], FIELD_NAME: leaf}
                    leaves[name] = leaf
                    assert leaf["character_id"] == person["following_2921a90"]["character_id"] == ENEMY
                    assert leaf["source_inputs"] == person["following_2921a90_conditional"]
                    assert leaf["ready"] is ready and leaf["classifier_result_i32"] == classifier
                    assert leaf["build_version"] == CK3_12004.game_version
                    assert leaf["executable_sha256"] == CK3_12004.executable_sha256
                    for key in ("character_identity", "selected_model_identity", "selected_object_identity"):
                        assert leaf["source_inputs"][key] == raw_leaf["source_inputs"][key]
                        assert leaf["source_inputs"][key] == person["following_2921a90"][key]
                    direct = emit_direct(source_inputs)
                    assert len(direct) == 4
                    if ready:
                        emitted[name] = emit_conditional(source_inputs)
                        combined[name] = emit_complete(source_inputs)
                        assert combined[name][:len(direct)] == direct
                        assert len(combined[name]) == len(direct) + len(emitted[name])
                        assert len(emitted[name]) == leaf["occurrence_count"]
                        assert [request.source_ordinal for request in combined[name][len(direct):]] == [
                            len(person["following_2921a90"]["direct_rows"]) + request.source_ordinal
                            for request in emitted[name]]
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
                                assert requests[0].source_name == FIELD_NAME + "_12004"
                                assert requests[0].weight_q64 == 100000
                                assert requests[0].first_row_index == 0 and requests[0].row_count == 1
                                assert requests[0].definition_identity == source["object_identity"]
                            available_rows[index] = requests
                        else:
                            unavailable(emit_row, source["reason"], source_inputs, index)
                    independent[name] = available_rows
                    for opinion in leaf["opinion_rows"]:
                        assert opinion["toward_full_character_id"] == ENEMY != PLAYER
                        assert opinion["toward_character_identity"] == leaf["source_inputs"]["character_identity"]
                        if opinion["source_selection"] == "native_pair_postclamp_28bc470":
                            assert opinion["selected_full_character_id"] != ENEMY
                            assert opinion["base_value"] is None and opinion["additional_value"] is None
                        if not opinion["ready"]:
                            assert opinion["vote"] == ""
                    assert endpoint.packet == packet

    try:
        asyncio.run(consume())
    finally:
        driver.close()

    assert leaves["opinion-high"]["selected_family"] == "bb0_bbc"
    assert leaves["opinion-low"]["selected_family"] == "b80_b8c"
    high = emitted["opinion-high"]
    assert [request.source_ordinal for request in high] == [0, 1, 2, 4]
    assert [request.source_ordinal for request in combined["opinion-high"]] == [0, 1, 2, 3, 4, 5, 6, 8]
    assert high[0].definition_identity == high[2].definition_identity
    assert high[0].base_property_block == high[2].base_property_block == {
        "keys_count": 4, "keys_u16": [1, 2, 65535, 1],
        "values_q64": [200000, -250001, 999000, 100000]}
    assert high[1].base_property_block == {
        "keys_count": 2, "keys_u16": [1, 2], "values_q64": [-300000, 375001]}
    assert high[3].base_property_block == {"keys_count": 0, "keys_u16": [], "values_q64": []}
    assert independent["opinion-high"][3] == ()
    low = emitted["opinion-low"]
    assert len(low) == 1 and low[0].source_ordinal == 0
    assert low[0].base_property_block == high[1].base_property_block
    for name, totals, votes in (
            ("opinion-high", [75, 60, 75], ["high", "high", "high"]),
            ("opinion-low", [-75, -60, -75], ["low", "low", "low"]),
            ("opinion-mixed-tie", [75, -75, 0], ["high", "low", "middle"])):
        opinions = leaves[name]["opinion_rows"]
        assert [row["total_opinion_i32"] for row in opinions] == totals
        assert [row["vote"] for row in opinions] == votes
        assert all(row["source_selection"] == "native_pair_postclamp_28bc470" for row in opinions)
        expected_owners = [OWNERS[0], OWNERS[1], OWNERS[2] if name == "opinion-mixed-tie" else OWNERS[0]]
        assert [row["selected_full_character_id"] for row in opinions] == expected_owners
    assert emitted["opinion-mixed-tie"] == ()
    assert leaves["opinion-mixed-tie"]["selected_family"] == "classifier_other_empty"
    assert leaves["opinion-mixed-tie"]["occurrence_count"] == 0
    assert any(not row["ready"] for row in leaves["opinion-provider-unavailable"]["opinion_rows"])
    assert not leaves["opinion-provider-unavailable"]["classifier_ready"]
    assert leaves["opinion-provider-unavailable"]["classifier_result_i32"] is None
    assert leaves["opinion-provider-unavailable"]["rows"] == []
    assert all(row["reason"] == "pair_opinion_provider_unavailable"
               and row["total_opinion_i32"] is None and row["vote"] == ""
               for row in leaves["opinion-provider-unavailable"]["opinion_rows"])
    dynamic = leaves["opinion-dynamic-weight-later-ready"]
    assert dynamic["classifier_ready"] and dynamic["reason"] == "weight_virtual_expression_9d7060_unobserved"
    assert dynamic["rows"] and not dynamic["rows"][0]["ready"]
    assert set(independent["opinion-dynamic-weight-later-ready"]) == {1, 3, 4}
    assert independent["opinion-dynamic-weight-later-ready"][1][0].base_property_block == high[1].base_property_block
    assert independent["opinion-dynamic-weight-later-ready"][3] == ()
    assert independent["opinion-dynamic-weight-later-ready"][4][0].base_property_block == high[3].base_property_block
    assert dynamic["rows"][0]["object_identity"] == dynamic["rows"][2]["object_identity"]
    assert dynamic["occurrence_count"] is None
    raw = packets["opinion-high"]["result"]["battle_terminal_transition"]["character_observations"][0]["current_person_state"][FIELD_NAME]
    assert raw["rows"][0]["weight_q64"] == "100000"
    assert raw["rows"][1]["raw_value_258_q64"] == "-150000"
    assert all(isinstance(value, str) for value in raw["rows"][0]["properties"]["values_q64"])
    assert len(endpoint.requests) == len(endpoint.delivered) == 5
    assert driver.state._command_results == {}
    assert packets == originals
