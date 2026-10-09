"""AUTHORED_NOTRUN: one compound consuming only the new actual4 whole packets.

Root's sole new native producer supplies fourteen original command_result files.
Set CK3_PERSON_FOLLOWING_2922680_12004_MCP_WIRE_DIR to that output directory.
The real Driver, normalizer, Service and registered MCP carry each complete
packet; only correlation and hello/paused-snapshot scaffolding are fixtures.
No historical producer, complete Person/Entry or paused-live case is replayed.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge.battle_person_following_2922680_12004 import (
    FIELD_NAME,
    MAPPED_GAP,
    SCHEMA,
    emit_following_2922680_requests_from_current_source_inputs_12004 as emit_whole,
    emit_following_2922680_primary_requests_from_current_source_inputs_12004 as emit_primary,
    emit_following_2922680_primary_occurrence_requests_from_current_source_inputs_12004 as emit_occurrence,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004


TOOL = "ck3_query_battle_terminal_transition_v1"
SUBJECT_ID, PLAYER_ID = 0x04000003, 29829
PUBLIC_REVISION, NATIVE_REVISION, DATE_RAW = 97, 49, 53236632
CASES = (
    ("context-header-zero", True, True),
    ("absent-context-static-zero", True, True),
    ("gated-context-static-zero", True, True),
    ("negative-list-count", False, False),
    ("expired-ordered-duplicates", True, True),
    ("zero-source-count", True, True),
    ("generation-fallback", True, True),
    ("null-row-registry-skips-ids", True, True),
    ("repeated-row-date-partial", False, False),
    ("negative-source-count", False, False),
    ("primary-ordered-duplicates-matched-nested", True, True),
    ("membership-nonmatch-known-zero", True, True),
    ("membership-admitted-primary-usable", False, True),
    ("partial-primary-independent-siblings", False, False),
)
NUMERIC_CASES = {name for name, *_ in CASES[-4:]}


class WholePacketEndpoint:
    pipe_name = "offline-person-following-2922680-whole-packets"

    def __init__(self, step):
        self.step = step
        self.packet = None
        self.on_frame = None
        self.requests = []
        self.delivered = []

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def select(self, packet):
        self.packet = deepcopy(packet)

    def send(self, request):
        assert request["type"] == "execute_step" and request["protocol_version"] == 1
        assert request["step"] == self.step
        assert request["expected_revision"] == NATIVE_REVISION
        self.requests.append(deepcopy(request))
        response = deepcopy(self.packet)
        response["request_id"] = request["request_id"]
        assert {key: value for key, value in response.items() if key != "request_id"} == {
            key: value for key, value in self.packet.items() if key != "request_id"
        }
        self.delivered.append(deepcopy(response))
        self.on_frame(response)

    def close(self):
        pass


def test_person_following_2922680_12004_registered_mcp_whole_packets():
    from mcp import Client

    directory = Path(os.environ["CK3_PERSON_FOLLOWING_2922680_12004_MCP_WIRE_DIR"])
    packets = {name: json.loads((directory / (name + ".json")).read_bytes())
               for name, *_ in CASES}
    originals = deepcopy(packets)
    step = query_battle_terminal_transition_v1_step(None, None, None, [SUBJECT_ID])
    assert step == "query-battle-terminal-transition-v1-none:characters:67108867"
    endpoint = WholePacketEndpoint(step)
    driver = NativeHeadlessGameplayDriver(endpoint=endpoint, episode_projection="native_campaign")
    hello = {
        "type": "hello", "protocol_version": 1, "pid": 1,
        "capabilities": ["game.state.snapshot", QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY],
        "expected_ck3_version": CK3_12004.game_version,
        "expected_ck3_sha256": CK3_12004.executable_sha256,
    }
    assert driver.state.ingest(hello) == "hello"
    snapshot = {
        "snapshot_id": "person-following-2922680-paused-revision49",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": PLAYER_ID, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-following-2922680-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }
    leaves, emitted, independent = {}, {}, {}

    def expect_rejected(emitter, *arguments, reason=None):
        try:
            emitter(*arguments)
        except ValueError as error:
            if reason:
                assert reason in str(error)
        else:
            raise AssertionError("Partial native inputs produced a complete contribution")

    async def exercise():
        with patch.object(driver, "take_snapshot", side_effect=lambda: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                assert TOOL in {tool.name for tool in (await client.list_tools()).tools}
                for sequence, (name, whole_ready, primary_ready) in enumerate(CASES, 1):
                    packet = packets[name]
                    assert packet["type"] == "command_result" and packet["ok"] is True
                    result = packet["result"]
                    assert result["step"] == step and result["query_sequence"] == sequence
                    assert result["snapshot_revision"] == NATIVE_REVISION
                    raw_frame = result["battle_terminal_transition"]
                    assert raw_frame["observed_date_raw"] == DATE_RAW
                    raw_observations = raw_frame["character_observations"]
                    assert [row["character_id"] for row in raw_observations] == [SUBJECT_ID]
                    raw_leaf = raw_observations[0]["current_person_state"][FIELD_NAME]
                    assert raw_leaf["schema"] == SCHEMA
                    endpoint.select(packet)
                    response = await client.call_tool(TOOL, {
                        "prior_combat_id": None,
                        "subject_public_cunit_id": None,
                        "after_terminal_sequence": None,
                        "expected_revision": PUBLIC_REVISION,
                        "character_ids": [SUBJECT_ID],
                    })
                    assert response.is_error is False, response.content
                    actual = response.structured_content
                    frame = actual["battle_terminal_transition"]
                    assert actual["status"] == frame["status"] == "available"
                    assert frame["battle_terminal_transition_ready"] is False
                    assert actual["character_observations"] == frame["character_observations"]
                    assert actual["queried_snapshot_id"] == snapshot["snapshot_id"]
                    assert actual["queried_revision"] == PUBLIC_REVISION
                    assert actual["queried_native_revision"] == NATIVE_REVISION
                    observation = frame["character_observations"][0]
                    assert observation["character_id"] == SUBJECT_ID != PLAYER_ID
                    leaf = observation["current_person_state"][FIELD_NAME]
                    leaves[name] = leaf
                    assert leaf["character_id"] == observation["character_id"]
                    assert leaf["build_version"] == CK3_12004.game_version
                    assert leaf["executable_sha256"] == CK3_12004.executable_sha256
                    assert (leaf["ready"], leaf["primary_ready"]) == (whole_ready, primary_ready)
                    for key in ("selected_model_identity", "character_identity",
                                "destination_pc_identity", "list_header_identity",
                                "list_array_identity", "list_count_i32"):
                        assert leaf[key] == raw_leaf[key]
                    source = {"character_id": observation["character_id"], FIELD_NAME: leaf}
                    if primary_ready:
                        emitted[name] = emit_primary(source)
                    else:
                        expect_rejected(emit_primary, source)
                    if whole_ready:
                        assert emit_whole(source) == emitted[name]
                    else:
                        expect_rejected(emit_whole, source)
                    independent[name] = {}
                    for index, append in enumerate(leaf["append_occurrences"]):
                        if append["kind"] in ("item_mapped", "nested_mapped"):
                            assert append["ready"] is False and append["reason"] == MAPPED_GAP
                            continue
                        if not append["ready"]:
                            expect_rejected(emit_occurrence, source, index, reason=append["reason"])
                            continue
                        requests = emit_occurrence(source, index)
                        assert len(requests) == 1
                        request = requests[0]
                        assert request.source_ordinal == index
                        assert request.source_name == "following_2922680_12004:" + append["kind"]
                        assert request.definition_identity == append["identity"]
                        assert request.first_row_index == 0 and request.row_count == 1
                        assert request.weight_q64 == 100000
                        independent[name][index] = request
                    if primary_ready:
                        assert emitted[name] == tuple(independent[name].values())
                    assert endpoint.packet == packet
                    assert snapshot["played_character"]["character_id"] == PLAYER_ID

    try:
        asyncio.run(exercise())
    finally:
        driver.close()

    for name, *_ in CASES[:4]:
        assert leaves[name]["rows"] == []
        assert leaves[name]["list_array_identity"] is None
        assert leaves[name]["append_occurrences"] == []
    static_header = hex(0x140000000 + 0x5D67DE0)
    assert leaves["absent-context-static-zero"]["list_header_identity"] == static_header
    assert leaves["gated-context-static-zero"]["list_header_identity"] == static_header
    assert leaves["negative-list-count"]["list_count_i32"] == -2
    assert leaves["negative-list-count"]["reason"] == "list_count_negative"
    for name, *_ in CASES[4:10]:
        rows = leaves[name]["rows"]
        assert [row["native_index"] for row in rows] == [0, 1, 2, 3]
        assert leaves[name]["append_occurrences"] == []
        if name != "null-row-registry-skips-ids":
            assert [row["list_full_id_u32"] for row in rows] == [
                0x03000001, 0x03000002, 0x03000001, 0x03000003]
        if name in ("repeated-row-date-partial", "negative-source-count"):
            assert [row["ready"] for row in rows] == [False, True, False, True]
            assert rows[1]["known_no_contribution"] and rows[3]["known_no_contribution"]
        else:
            assert all(row["ready"] and row["known_no_contribution"] for row in rows)
    fallback = leaves["generation-fallback"]["rows"]
    assert fallback[0]["resolution"]["selection"] == "fallback"
    assert fallback[0]["resolution"]["candidate_full_id_u32"] == 0x04000001
    assert fallback[0]["resolution"]["selected_identity"] == fallback[2]["resolution"]["selected_identity"]
    for row in leaves["null-row-registry-skips-ids"]["rows"]:
        assert row["list_id_demanded"] is False and row["list_full_id_u32"] is None
    for row in leaves["zero-source-count"]["rows"]:
        assert row["derived_year_i32"] == 1 and row["raw_date_c7c8_i32"] is None
        assert row["current_date_i32"] is None and row["source_list_count_i32"] == 0
        assert row["source_list_array_identity"] is None and row["sources"] == []

    a_values = [-100000, -(1 << 63), 0, (1 << 63) - 1]
    expected_blocks = [
        {"keys_count": 4, "keys_u16": [554, 65535, 554, 0], "values_q64": a_values},
        {"keys_count": 1, "keys_u16": [273], "values_q64": [-250000]},
        {"keys_count": 0, "keys_u16": [], "values_q64": []},
        {"keys_count": 1, "keys_u16": [819], "values_q64": [300000]},
        {"keys_count": 4, "keys_u16": [554, 65535, 554, 0], "values_q64": a_values},
        {"keys_count": 1, "keys_u16": [273], "values_q64": [-250000]},
    ]
    for name in NUMERIC_CASES:
        leaf = leaves[name]
        source = leaf["rows"][0]["sources"][0]
        assert source["getter"]["admitted"] is True
        assert source["getter"]["selected_value_u32"] == 0x07000001
        items = source["items"]
        assert [item["native_index"] for item in items] == [0, 1, 2]
        assert items[0]["object_identity"] == items[2]["object_identity"]
        assert [row["matched"] for row in items[0]["nested"]] == [True, False]
        primary = [row for row in leaf["append_occurrences"]
                   if row["kind"] in ("item_primary", "nested_primary")]
        assert len(primary) == 6
        assert [row["kind"] for row in primary] == ["item_primary", "nested_primary"] * 3
        if name != "partial-primary-independent-siblings":
            assert [request.base_property_block for request in emitted[name]] == expected_blocks
            assert emitted[name][0].definition_identity == emitted[name][4].definition_identity
        else:
            assert [row["ready"] for row in primary] == [False, True, True, True, False, True]
            assert primary[0]["properties"]["keys_u16"] == [554, 65535, 554, 0]
            assert primary[0]["properties"]["values_q64"] is None
            assert sorted(independent[name]) == [1, 2, 3, 5]
            assert independent[name][2].base_property_block == expected_blocks[2]
            assert independent[name][3].base_property_block == expected_blocks[3]
    raw_primary = packets["primary-ordered-duplicates-matched-nested"]["result"][
        "battle_terminal_transition"]["character_observations"][0][
        "current_person_state"][FIELD_NAME]["append_occurrences"]
    assert raw_primary[0]["properties"]["values_q64"] == [str(value) for value in a_values]
    nonmatch = leaves["membership-nonmatch-known-zero"]["rows"][0]["sources"][0]
    assert nonmatch["items"][0]["membership"]["rows"][0]["admitted"] is False
    admitted = leaves["membership-admitted-primary-usable"]
    mapped = [row for row in admitted["append_occurrences"] if row["kind"] == "item_mapped"]
    assert len(mapped) == 2 and all(row["reason"] == MAPPED_GAP for row in mapped)
    assert admitted["primary_ready"] is True and admitted["ready"] is False
    assert len(endpoint.requests) == len(endpoint.delivered) == len(CASES)
    assert driver.state._command_results == {}
    assert packets == originals
