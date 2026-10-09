"""Six new native historical captures through real registered same-MCP query.

Whole packets originate from the production observer/reader/serializer on a
declared synthetic graph. No capture DTO or historical stage is fabricated by
this consumer, and no old compound or native producer is invoked.
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
from xar_autoplayer.bridge.battle_person_title_tail_capture_12004 import (
    FIELD_NAME, SCHEMA, SOURCE_STAGE, SOURCE_RETURN_RVA,
    emit_captured_person_title_tail_request_12004 as emit,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004


WIRE_ENV = "CK3_PERSON_NATIVE_TITLE_TAIL_CAPTURE_12004_MCP_WIRE_DIR"
CASES = (
    "unobserved",
    "matching-final-tail-ordered-i64",
    "per-title-caller-ignored-original-once",
    "other-owner-generation-not-borrowed",
    "prepared-pc-values-unread",
    "immutable-capture-after-source-mutation",
)
OBSERVED = {CASES[1], CASES[4], CASES[5]}
WIDE_VALUE = 2**63 - 1 - 8
PREPARED_BLOCK = {"keys_count": 4, "keys_u16": [125, 97, 125, 111],
                  "values_q64": [WIDE_VALUE, 0, -WIDE_VALUE, 4294967296]}


def _native_numbers(value):
    """Project only the wire's existing signed64 decimal representation."""
    if isinstance(value, list):
        return [_native_numbers(item) for item in value]
    if isinstance(value, dict):
        return {key: ([int(item) for item in item_value] if item_value is not None
                      else None) if key == "values_q64" else _native_numbers(item_value)
                for key, item_value in value.items()}
    return value


def _unavailable(section):
    try:
        emit(section)
    except ValueError as error:
        assert "Required native input unavailable" in str(error)
    else:
        raise AssertionError("Unobserved or partial prepared PC produced a captured request")


def test_person_native_title_tail_capture_12004_registered_mcp_whole_packets():
    from mcp import Client

    directory = Path(os.environ[WIRE_ENV])
    packets = {name: json.loads((directory / (name + ".json")).read_bytes())
               for name in CASES}
    originals = deepcopy(packets)
    step = query_battle_terminal_transition_v1_step(None, None, None, [SUBJECT_ID])
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
        "snapshot_id": "person-native-title-tail-paused-revision49",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": PLAYER_ID, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-native-title-tail-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }
    leaves, emitted = {}, {}

    async def exercise():
        with patch.object(driver, "take_snapshot", side_effect=lambda: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                assert TOOL in {tool.name for tool in (await client.list_tools()).tools}
                for sequence, name in enumerate(CASES, 1):
                    packet = packets[name]
                    assert packet["type"] == "command_result" and packet["ok"] is True
                    result = packet["result"]
                    assert result["step"] == step and result["query_sequence"] == sequence
                    assert result["snapshot_revision"] == NATIVE_REVISION
                    raw_observation, = result["battle_terminal_transition"]["character_observations"]
                    raw_leaf = raw_observation["current_person_state"][FIELD_NAME]
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
                    assert actual["query_sequence"] == sequence
                    assert actual["queried_snapshot_id"] == snapshot["snapshot_id"]
                    assert actual["queried_revision"] == PUBLIC_REVISION
                    assert actual["queried_native_revision"] == NATIVE_REVISION
                    assert frame["observed_date_raw"] == DATE_RAW
                    assert frame["battle_terminal_transition_ready"] is False
                    assert actual["character_observations"] == frame["character_observations"]
                    observation, = frame["character_observations"]
                    assert observation["character_id"] == SUBJECT_ID != PLAYER_ID
                    assert observation["alive"] is True
                    person = observation["current_person_state"]
                    leaf = person[FIELD_NAME]
                    leaves[name] = leaf
                    assert leaf == _native_numbers(raw_leaf)
                    assert leaf["schema"] == SCHEMA
                    assert leaf["build_version"] == CK3_12004.game_version
                    assert leaf["executable_sha256"] == CK3_12004.executable_sha256
                    assert leaf["character_id"] == SUBJECT_ID
                    assert leaf["configured"] is True
                    assert leaf["source_stage"] == SOURCE_STAGE == "post_composer_pre_final_outer_append"
                    assert leaf["historical_capture"] is True
                    assert leaf["actual_model_write_performed"] is False
                    assert leaf["full_helper_ready"] is False
                    assert leaf["weight_q100000"] == 100000
                    observed = name in OBSERVED
                    partial = name == "prepared-pc-values-unread"
                    assert leaf["capture_observed"] is observed
                    assert leaf["capture_sequence"] == (1 if observed else 0)
                    assert leaf["ready"] is (observed and not partial)
                    assert leaf["reason"] == ("native_title_tail_unobserved" if not observed
                                              else "prepared_pc_partial" if partial else None)
                    section = {"character_id": SUBJECT_ID, FIELD_NAME: leaf}
                    if leaf["ready"]:
                        emitted[name] = emit(section)
                    else:
                        _unavailable(section)
                    if name == "immutable-capture-after-source-mutation":
                        assert leaf["model_identity"] != person["following_2922680"]["selected_model_identity"]
                    elif observed:
                        assert leaf["model_identity"] == person["following_2922680"]["selected_model_identity"]
                    assert endpoint.packet == packet

    try:
        asyncio.run(exercise())
    finally:
        driver.close()

    for name in CASES:
        leaf = leaves[name]
        pc, aggregate = leaf["prepared_pc"], leaf["model_aggregate_pc"]
        if name not in OBSERVED:
            assert all(leaf[key] is None for key in (
                "character_identity", "model_identity", "source_return_rva",
                "inline_destination_identity", "capture_date_raw"))
            for item in (pc, aggregate):
                assert item == {"ready": False, "reason": "pc_unobserved", "admitted": None,
                                "identity": None, "count_i32": None, "properties": None,
                                "weight_q100000": 100000}
            continue
        partial = name == "prepared-pc-values-unread"
        immutable = name == "immutable-capture-after-source-mutation"
        assert leaf["capture_date_raw"] == DATE_RAW
        assert int(leaf["source_return_rva"], 16) == SOURCE_RETURN_RVA == 0x291EBEF
        assert leaf["inline_destination_identity"] == hex(int(leaf["model_identity"], 16) + 0x10)
        assert pc["count_i32"] == 4 and pc["admitted"] is True
        assert pc["properties"]["keys_u16"] == PREPARED_BLOCK["keys_u16"]
        assert pc["properties"]["values_q64"] == (None if partial else PREPARED_BLOCK["values_q64"])
        assert pc["ready"] is (not partial)
        assert pc["reason"] == ("pc_values_unread" if partial else None)
        assert aggregate["identity"] == hex(int(leaf["model_identity"], 16) + 0x78)
        assert aggregate["count_i32"] == 2
        assert aggregate["properties"]["keys_u16"] == [125, 126]
        assert aggregate["ready"] is (not immutable)
        assert aggregate["reason"] == ("pc_values_unread" if immutable else None)
        assert aggregate["properties"]["values_q64"] == (None if immutable else [900000, -700000])
        if not partial:
            assert emitted[name] == {
                "source_family": "captured_final_title_tail",
                "source_stage": SOURCE_STAGE,
                "historical_capture": True,
                "capture_sequence": 1,
                "capture_date_raw": DATE_RAW,
                "character_id": SUBJECT_ID,
                "character_identity": leaf["character_identity"],
                "selected_model_identity": leaf["model_identity"],
                "inline_destination_identity": leaf["inline_destination_identity"],
                "source_return_rva": leaf["source_return_rva"],
                "property_block": PREPARED_BLOCK,
                "weight_q100000": 100000,
                "actual_model_write_performed": False,
                "full_helper_ready": False,
            }
    assert set(emitted) == {"matching-final-tail-ordered-i64", "immutable-capture-after-source-mutation"}
    assert len(endpoint.requests) == len(endpoint.delivered) == len(CASES)
    assert driver.state._command_results == {}
    assert packets == originals
