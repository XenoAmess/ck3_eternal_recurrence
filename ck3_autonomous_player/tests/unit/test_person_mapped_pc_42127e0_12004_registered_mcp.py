"""AUTHORED_NOTRUN: one registered compound, eleven new whole-query packets.

Set CK3_PERSON_MAPPED_PC_42127E0_12004_MCP_WIRE_DIR to the new native target's
output. Only transport scaffolding/constants are reused from the old compound;
its test and producer are never called. Real Driver/Service/MCP normalization
must preserve ordered primary/mapped occurrences, paired arrays and partials.
No-match/empty mapper branches have source closure, without simulated header
mutation or coherent-frame/live qualification from this fixture.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_person_following_2922680_12004_registered_mcp import (
    DATE_RAW, NATIVE_REVISION, PLAYER_ID, PUBLIC_REVISION, SUBJECT_ID, TOOL,
    WholePacketEndpoint,
)
from xar_autoplayer.bridge.battle_person_following_2922680_12004 import (
    FIELD_NAME, SCHEMA,
    emit_following_2922680_requests_from_current_source_inputs_12004 as emit_whole,
    emit_following_2922680_primary_requests_from_current_source_inputs_12004 as emit_primary,
    emit_following_2922680_primary_occurrence_requests_from_current_source_inputs_12004 as emit_occurrence,
    emit_following_2922680_mapped_occurrence_requests_from_current_source_inputs_12004 as emit_mapped_occurrence,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004


CASES = (
    ("first-full-id-whole-order", True, "mapped_first_full_id_match"),
    ("first-null-stays-null", False, "mapped_first_full_id_match_null"),
    ("wrong-magic-default-initialized", True, "mapped_default_wrong_magic"),
    ("wrong-magic-default-negative-epoch", True, "mapped_default_wrong_magic"),
    ("default-guard-unread", False, "mapped_default_guard_unread"),
    ("default-not-initialized", False, "mapped_default_not_initialized"),
    ("mapped-values-partial", False, "mapped_first_full_id_match:pc_values_unread"),
    ("nested-mapped-interleaved", True, "mapped_first_full_id_match"),
    ("first-match-unused-default-later", True, "mapped_first_full_id_match"),
    ("mapped-empty-pc", True, "mapped_first_full_id_match"),
    ("matched-pc-pointer-unread", False, "mapped_matched_pc_pointer_unread"),
)
PRIMARY_KINDS = {"item_primary", "nested_primary"}
FIRST_BLOCK = {
    "keys_count": 4, "keys_u16": [554, 65535, 554, 0],
    "values_q64": [-100000, -(1 << 63), 0, (1 << 63) - 1],
}
DEFAULT_BLOCK = {"keys_count": 1, "keys_u16": [1092], "values_q64": [-444444]}
EMPTY_BLOCK = {"keys_count": 0, "keys_u16": [], "values_q64": []}
ORDINARY_ORDER = [
    "item_primary", "item_mapped", "nested_primary", "item_primary",
    "nested_primary", "item_primary", "item_mapped", "nested_primary",
]
DUPLICATE_ORDER = [
    "item_primary", "item_mapped", "item_mapped", "nested_primary",
    "item_primary", "nested_primary", "item_primary", "item_mapped",
    "item_mapped", "nested_primary",
]
NESTED_ORDER = [
    "item_primary", "item_mapped", "nested_primary", "nested_mapped",
    "item_primary", "nested_primary", "item_primary", "item_mapped",
    "nested_primary", "nested_mapped",
]


def test_person_mapped_pc_42127e0_12004_registered_mcp_whole_packets():
    from mcp import Client

    directory = Path(os.environ["CK3_PERSON_MAPPED_PC_42127E0_12004_MCP_WIRE_DIR"])
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
        "snapshot_id": "person-mapped-42127e0-paused-revision49",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": PLAYER_ID, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-mapped-42127e0-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }
    leaves = {}

    async def exercise():
        with patch.object(driver, "take_snapshot", side_effect=lambda: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                assert TOOL in {tool.name for tool in (await client.list_tools()).tools}
                for sequence, (name, ready, reason) in enumerate(CASES, 1):
                    packet = packets[name]
                    assert packet["type"] == "command_result" and packet["ok"] is True
                    result = packet["result"]
                    assert result["step"] == step and result["query_sequence"] == sequence
                    assert result["snapshot_revision"] == NATIVE_REVISION
                    raw_frame = result["battle_terminal_transition"]
                    assert raw_frame["observed_date_raw"] == DATE_RAW
                    raw_observation, = raw_frame["character_observations"]
                    assert raw_observation["character_id"] == SUBJECT_ID != PLAYER_ID
                    assert raw_observation["alive"] is True
                    raw_leaf = raw_observation["current_person_state"][FIELD_NAME]
                    raw_opinion = raw_observation["current_person_state"]["following_2921a90_opinion"]
                    assert raw_opinion["ready"] is False
                    assert raw_opinion["reason"] == raw_opinion["source_inputs"]["reason"] == "registry_slot_unread"
                    assert raw_opinion["source_inputs"]["admitted"] is None
                    assert raw_opinion["classifier_ready"] is False
                    assert raw_opinion["classifier_reason"] is None
                    assert raw_opinion["classifier_result_i32"] is None
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
                    observation, = frame["character_observations"]
                    assert observation["character_id"] == SUBJECT_ID and observation["alive"] is True
                    opinion = observation["current_person_state"]["following_2921a90_opinion"]
                    assert opinion["ready"] is False and opinion["reason"] == "registry_slot_unread"
                    assert opinion["selected_family"] == "unavailable"
                    assert opinion["classifier_ready"] is False
                    assert opinion["classifier_reason"] is None and opinion["classifier_result_i32"] is None
                    assert opinion["opinion_rows"] == opinion["rows"] == []
                    leaf = observation["current_person_state"][FIELD_NAME]
                    leaves[name] = leaf
                    assert leaf["schema"] == raw_leaf["schema"] == SCHEMA
                    assert leaf["character_id"] == SUBJECT_ID
                    assert leaf["build_version"] == CK3_12004.game_version
                    assert leaf["executable_sha256"] == CK3_12004.executable_sha256
                    assert leaf["ready"] is ready and leaf["primary_ready"] is True
                    assert leaf["rows"][0]["primary_ready"] is True
                    for key in ("character_identity", "selected_model_identity", "destination_pc_identity",
                                "list_header_identity", "list_array_identity", "list_count_i32"):
                        assert leaf[key] == raw_leaf[key]
                    order = (DUPLICATE_ORDER if name == "first-full-id-whole-order" else
                             NESTED_ORDER if name == "nested-mapped-interleaved" else ORDINARY_ORDER)
                    appends = leaf["append_occurrences"]
                    assert [row["kind"] for row in appends] == order
                    assert len(appends) == len(raw_leaf["append_occurrences"])
                    mapped = [(index, row) for index, row in enumerate(appends)
                              if row["kind"] not in PRIMARY_KINDS]
                    assert len(mapped) == (4 if len(order) == 10 else 2)
                    for index, row in mapped:
                        raw = raw_leaf["append_occurrences"][index]
                        assert row["admitted"] is True and row["ready"] is ready
                        assert row["reason"] == raw["reason"] == reason
                        assert row["identity"] == raw["identity"]
                        assert row["weight_q100000"] == 100000
                        for key in ("outer_index", "source_index", "item_index", "nested_index", "descriptor_index"):
                            assert row[key] == raw[key]
                    source = {"character_id": SUBJECT_ID, FIELD_NAME: leaf}
                    primary = emit_primary(source)
                    primary_indices = [index for index, row in enumerate(appends)
                                       if row["kind"] in PRIMARY_KINDS]
                    assert [request.source_ordinal for request in primary] == primary_indices
                    assert len(primary) == 6
                    for index, request in zip(primary_indices, primary):
                        assert emit_occurrence(source, index) == (request,)
                        assert request.definition_identity == appends[index]["identity"]
                        assert request.source_name == "following_2922680_12004:" + appends[index]["kind"]
                        assert request.weight_q64 == 100000
                    if ready:
                        requests = emit_whole(source)
                        assert len(requests) == len(appends)
                        assert [request.source_ordinal for request in requests] == list(range(len(appends)))
                        assert tuple(requests[index] for index in primary_indices) == primary
                        for index, row in mapped:
                            request = requests[index]
                            block = (DEFAULT_BLOCK if name.startswith("wrong-magic-default") else
                                     EMPTY_BLOCK if name == "mapped-empty-pc" else FIRST_BLOCK)
                            assert request.base_property_block == block
                            assert request.definition_identity == row["identity"]
                            assert request.source_name == "following_2922680_12004:" + row["kind"]
                            assert request.first_row_index == 0 and request.row_count == 1
                            assert request.weight_q64 == 100000
                            assert emit_mapped_occurrence(source, index) == (request,)
                    else:
                        try:
                            emit_whole(source)
                        except ValueError:
                            pass
                        else:
                            raise AssertionError("Partial mapped source produced a complete helper")
                    assert endpoint.packet == packet

    try:
        asyncio.run(exercise())
    finally:
        driver.close()

    duplicate = leaves["first-full-id-whole-order"]
    membership = duplicate["rows"][0]["sources"][0]["items"][0]["membership"]
    assert [row["native_index"] for row in membership["rows"]] == [0, 1, 2, 3]
    assert [row["admitted"] for row in membership["rows"]] == [False, False, True, True]
    assert membership["rows"][2]["key_identity"] != membership["rows"][3]["key_identity"]
    mapped = [row for row in duplicate["append_occurrences"] if row["kind"] == "item_mapped"]
    assert [row["descriptor_index"] for row in mapped] == [2, 3, 2, 3]
    assert len({row["identity"] for row in mapped}) == 1
    assert all(row["properties"]["values_q64"] == FIRST_BLOCK["values_q64"] for row in mapped)
    raw_mapped = packets["first-full-id-whole-order"]["result"]["battle_terminal_transition"][
        "character_observations"][0]["current_person_state"][FIELD_NAME]["append_occurrences"][1]
    assert raw_mapped["properties"]["values_q64"] == [str(value) for value in FIRST_BLOCK["values_q64"]]
    for name in ("wrong-magic-default-initialized", "wrong-magic-default-negative-epoch",
                 "default-guard-unread", "default-not-initialized"):
        for row in leaves[name]["append_occurrences"]:
            if row["kind"] == "item_mapped":
                assert row["identity"] == hex(0x140000000 + 0x5DC21B0)
    for row in leaves["first-null-stays-null"]["append_occurrences"]:
        if row["kind"] == "item_mapped":
            assert row["identity"] == "0x0" and row["count_i32"] is None and row["properties"] is None
    for row in leaves["matched-pc-pointer-unread"]["append_occurrences"]:
        if row["kind"] == "item_mapped":
            assert row["identity"] is None and row["properties"] is None
    for row in leaves["mapped-values-partial"]["append_occurrences"]:
        if row["kind"] == "item_mapped":
            assert row["count_i32"] == 4
            assert row["properties"]["keys_u16"] == FIRST_BLOCK["keys_u16"]
            assert row["properties"]["values_q64"] is None
    nested = [row for row in leaves["nested-mapped-interleaved"]["append_occurrences"]
              if row["kind"] == "nested_mapped"]
    assert [row["item_index"] for row in nested] == [0, 2]
    assert all(row["nested_index"] == 0 and row["descriptor_index"] == 0 for row in nested)
    assert len(endpoint.requests) == len(endpoint.delivered) == len(CASES)
    assert driver.state._command_results == {}
    assert packets == originals
