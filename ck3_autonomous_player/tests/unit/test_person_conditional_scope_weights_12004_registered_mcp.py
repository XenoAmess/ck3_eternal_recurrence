"""AUTHORED_NOTRUN: original scope whole packets through the registered MCP.

Only request correlation and hello/paused framing are fixture seams. Consume
the five new native command_result bodies without manufacturing source inputs.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge.battle_person_conditional_scope_weights_12004 import (
    FIELD_NAME, SCHEMA,
    emit_scope_2921a90_requests_from_current_source_inputs_12004 as emit_scope,
    emit_scope_2921a90_row_requests_from_current_source_inputs_12004 as emit_row,
    emit_complete_scope_2921a90_requests_from_current_source_inputs_12004 as emit_complete,
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
PAYLOAD = 0xF2345678
OPINION = "following_2921a90_opinion"
CASES = (
    ("scope-dynamic-ready", True, 0),
    ("scope-dynamic-zero", True, 0),
    ("scope-literal-only", True, 0),
    ("scope-family-empty", True, None),
    ("scope-prior-row-unavailable", False, 0),
)


class ScopeWholeEndpoint:
    pipe_name = "offline-person-conditional-scope-original-whole"

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


def test_person_conditional_scope_weights_12004_registered_mcp_whole_packets():
    from mcp import Client

    directory = Path(os.environ["CK3_PERSON_CONDITIONAL_SCOPE_WEIGHTS_12004_MCP_WIRE_DIR"])
    packets = {name: json.loads((directory / (name + ".json")).read_bytes()) for name, *_ in CASES}
    originals = deepcopy(packets)
    step = query_battle_terminal_transition_v1_step(None, None, None, [ENEMY])
    endpoint = ScopeWholeEndpoint(step)
    driver = NativeHeadlessGameplayDriver(endpoint=endpoint, episode_projection="native_campaign")
    hello = {"type": "hello", "protocol_version": 1, "pid": 1,
             "capabilities": ["game.state.snapshot", QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY],
             "expected_ck3_version": CK3_12004.game_version,
             "expected_ck3_sha256": CK3_12004.executable_sha256}
    assert driver.state.ingest(hello) == "hello"
    snapshot = {"snapshot_id": "new-person-conditional-scope-offline-frame", "revision": PUBLIC,
                "native_revision": NATIVE, "date_raw": DATE, "paused": True, "map_ready": True,
                "backend_id": "native-headless", "played_character": {"character_id": PLAYER, "alive": True},
                "player_armies": [], "active_wars": [], "active_event": None,
                "pending_character_interaction": None, "episode_run_id": "offline-conditional-scope",
                "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)}}
    leaves, persons, emitted, combined, independent = {}, {}, {}, {}, {}

    def unavailable(function, reason, *arguments):
        try:
            function(*arguments)
        except ValueError as error:
            assert reason in str(error)
        else:
            raise AssertionError("An unread scope weight or PC released a complete value")

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
                    assert raw_person[OPINION]["source_inputs"] == raw_person["following_2921a90_conditional"]
                    assert [row["source_inputs"] for row in raw_leaf["rows"]] == raw_person[OPINION]["rows"]
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
                                     "following_2921a90": person["following_2921a90"],
                                     OPINION: person[OPINION], FIELD_NAME: leaf}
                    leaves[name], persons[name] = leaf, person
                    assert leaf["character_id"] == person[OPINION]["character_id"] == ENEMY
                    assert leaf["selected_object_identity"] == person[OPINION]["source_inputs"]["selected_object_identity"]
                    assert person[OPINION]["source_inputs"] == person["following_2921a90_conditional"]
                    assert [row["source_inputs"] for row in leaf["rows"]] == person[OPINION]["rows"]
                    assert leaf["ready"] is ready and leaf["classifier_result_i32"] == classifier
                    assert leaf["build_version"] == CK3_12004.game_version
                    assert leaf["executable_sha256"] == CK3_12004.executable_sha256
                    assert leaf["scope_initialized"] == raw_leaf["scope_initialized"]
                    assert leaf["scope_kind_u16"] == raw_leaf["scope_kind_u16"]
                    assert leaf["scope_payload_u32"] == raw_leaf["scope_payload_u32"]
                    for normalized, raw in zip(leaf["rows"], raw_leaf["rows"]):
                        for key in ("native_index", "evaluation_selection", "weight_call_ordinal", "scope_prefix_ready"):
                            assert normalized[key] == raw[key]
                        for key in ("object_identity", "expression_flag_280_i32", "expression_tree_278_identity",
                                    "expression_scoped_268_identity", "expression_count_1d4_i32"):
                            assert normalized["source_inputs"][key] == raw["source_inputs"][key]
                            if normalized["evaluated_inputs"] is not None:
                                assert normalized["evaluated_inputs"][key] == raw["evaluated_inputs"][key]
                    direct = emit_direct(source_inputs)
                    assert len(direct) == 4
                    if ready:
                        emitted[name] = emit_scope(source_inputs)
                        combined[name] = emit_complete(source_inputs)
                        assert combined[name][:len(direct)] == direct
                        assert len(emitted[name]) == leaf["occurrence_count"]
                        assert len(combined[name]) == len(direct) + len(emitted[name])
                        assert [request.source_ordinal for request in combined[name][len(direct):]] == [
                            len(person["following_2921a90"]["direct_rows"]) + request.source_ordinal
                            for request in emitted[name]]
                    else:
                        unavailable(emit_scope, leaf["reason"], source_inputs)
                        unavailable(emit_complete, leaf["reason"], source_inputs)
                    available_rows = {}
                    for wrapper in leaf["rows"]:
                        index, evaluated = wrapper["native_index"], wrapper["evaluated_inputs"]
                        if evaluated is not None and evaluated["ready"]:
                            requests = emit_row(source_inputs, index)
                            if evaluated["weight_q64"] == 0:
                                assert requests == ()
                                assert evaluated["properties"] is None and evaluated["metadata"] == []
                                assert evaluated["keys_count_i32"] is evaluated["values_count_i32"] is None
                            else:
                                assert len(requests) == 1 and requests[0].source_ordinal == index
                                assert requests[0].source_name == FIELD_NAME + "_12004"
                                assert requests[0].weight_q64 == 100000
                                assert requests[0].first_row_index == 0 and requests[0].row_count == 1
                                assert requests[0].definition_identity == evaluated["object_identity"]
                            available_rows[index] = requests
                        else:
                            reason = evaluated["reason"] if evaluated is not None else leaf["reason"]
                            unavailable(emit_row, reason, source_inputs, index)
                    independent[name] = available_rows
                    assert endpoint.packet == packet

    try:
        asyncio.run(consume())
    finally:
        driver.close()

    dynamic = leaves["scope-dynamic-ready"]
    zero = leaves["scope-dynamic-zero"]
    for leaf, weights in ((dynamic, [150000, -150000, 250000, 0, 100000]),
                          (zero, [0, -150000, 0, 0, 100000])):
        assert leaf["scope_initialized"] and leaf["scope_kind_u16"] == 4
        assert leaf["scope_payload_u32"] == PAYLOAD and PAYLOAD not in (ENEMY, PLAYER)
        assert [row["weight_call_ordinal"] for row in leaf["rows"]] == [0, 1, 2, 3, 4]
        assert all(row["scope_prefix_ready"] and row["evaluation_selection"] == "native_row_2872300"
                   for row in leaf["rows"])
        assert [row["evaluated_inputs"]["weight_q64"] for row in leaf["rows"]] == weights
        assert leaf["rows"][0]["source_inputs"]["object_identity"] == leaf["rows"][2]["source_inputs"]["object_identity"]
        for index in (0, 2):
            source, evaluated = leaf["rows"][index]["source_inputs"], leaf["rows"][index]["evaluated_inputs"]
            assert not source["ready"] and source["weight_q64"] is None
            assert source["reason"] == "weight_virtual_expression_9d7060_unobserved"
            assert source["expression_flag_280_i32"] == evaluated["expression_flag_280_i32"] == 1
            assert source["expression_tree_278_identity"] == evaluated["expression_tree_278_identity"]
            assert evaluated["ready"] and evaluated["reason"] is None
    for name in ("scope-dynamic-ready", "scope-dynamic-zero"):
        assert not persons[name][OPINION]["ready"]
        assert persons[name][OPINION]["reason"] == "weight_virtual_expression_9d7060_unobserved"
        assert persons[name][OPINION]["occurrence_count"] is None

    high = emitted["scope-dynamic-ready"]
    assert [request.source_ordinal for request in high] == [0, 1, 2, 4]
    assert [request.source_ordinal for request in combined["scope-dynamic-ready"]] == [0, 1, 2, 3, 4, 5, 6, 8]
    assert high[0].definition_identity == high[2].definition_identity
    assert high[0].base_property_block == {
        "keys_count": 4, "keys_u16": [1, 2, 65535, 1],
        "values_q64": [300000, -375001, 1498500, 100000]}
    assert high[2].base_property_block == {
        "keys_count": 4, "keys_u16": [1, 2, 65535, 1],
        "values_q64": [600000, -625002, 2497500, 300000]}
    assert high[1].base_property_block == {
        "keys_count": 2, "keys_u16": [1, 2], "values_q64": [-300000, 375001]}
    empty = {"keys_count": 0, "keys_u16": [], "values_q64": []}
    assert high[3].base_property_block == empty
    assert dynamic["occurrence_count"] == 4 and zero["occurrence_count"] == 2
    assert [request.source_ordinal for request in emitted["scope-dynamic-zero"]] == [1, 4]
    assert emitted["scope-dynamic-zero"][0].base_property_block == high[1].base_property_block
    assert emitted["scope-dynamic-zero"][1].base_property_block == empty

    literal = leaves["scope-literal-only"]
    assert not literal["scope_initialized"] and literal["scope_kind_u16"] is literal["scope_payload_u32"] is None
    assert literal["occurrence_count"] == 3 and len(literal["rows"]) == 3
    assert all(row["scope_prefix_ready"] and row["weight_call_ordinal"] is None
               and row["evaluation_selection"] == "same_sample_source"
               and row["evaluated_inputs"] == row["source_inputs"] for row in literal["rows"])
    assert [request.source_ordinal for request in emitted["scope-literal-only"]] == [0, 1, 2]
    literal_block = {"keys_count": 4, "keys_u16": [1, 2, 65535, 1],
                     "values_q64": [200000, -250001, 999000, 100000]}
    assert emitted["scope-literal-only"][0].base_property_block == emitted["scope-literal-only"][2].base_property_block == literal_block
    assert emitted["scope-literal-only"][1].base_property_block == empty

    family_empty = leaves["scope-family-empty"]
    assert family_empty["rows"] == [] and family_empty["occurrence_count"] == 0
    assert not family_empty["scope_initialized"]
    assert family_empty["scope_kind_u16"] is family_empty["scope_payload_u32"] is None
    assert emitted["scope-family-empty"] == ()
    assert len(combined["scope-family-empty"]) == 4

    missing = leaves["scope-prior-row-unavailable"]
    assert missing["scope_initialized"] and missing["scope_payload_u32"] == PAYLOAD
    assert missing["reason"] == "scope_weight_source_row_unavailable" and missing["occurrence_count"] is None
    assert all(row["weight_call_ordinal"] is None and not row["scope_prefix_ready"] for row in missing["rows"])
    assert [row["evaluation_selection"] for row in missing["rows"]] == [
        "unavailable", "unavailable", "same_sample_source", "same_sample_source", "same_sample_source"]
    assert missing["rows"][1]["evaluated_inputs"]["reason"] == "scope_weight_source_prefix_unavailable"
    assert set(independent["scope-prior-row-unavailable"]) == {2, 3, 4}
    assert independent["scope-prior-row-unavailable"][2][0].base_property_block == high[1].base_property_block
    assert independent["scope-prior-row-unavailable"][3] == ()
    assert independent["scope-prior-row-unavailable"][4][0].base_property_block == empty
    raw = packets["scope-dynamic-ready"]["result"]["battle_terminal_transition"]["character_observations"][0]["current_person_state"][FIELD_NAME]
    assert raw["rows"][0]["evaluated_inputs"]["weight_q64"] == "150000"
    assert raw["rows"][2]["evaluated_inputs"]["weight_q64"] == "250000"
    assert all(isinstance(value, str) for value in raw["rows"][0]["evaluated_inputs"]["properties"]["values_q64"])
    assert len(endpoint.requests) == len(endpoint.delivered) == 5
    assert driver.state._command_results == {}
    assert packets == originals
