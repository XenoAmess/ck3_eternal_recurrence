"""AUTHORED_NOTRUN: six new supplemental whole packets through real MCP.

Only the qualified transport scaffold and constants are reused. No historical
producer or test runs, and no DTO is manufactured or substituted for a native
body. The numerical projection is a local input, never a fresh Person/Entry.
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
from xar_autoplayer.bridge.battle_person_local_titles_12004 import (
    FIELD_NAME, SCHEMA,
    compose_local_title_supplemental_blocks_from_current_source_inputs_12004 as compose,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004


WIRE_ENV = "CK3_PERSON_LOCAL_TITLES_SUPPLEMENTAL_12004_MCP_WIRE_DIR"
CASES = (
    "supplemental-ordered-avx-tail-duplicates",
    "supplemental-no-match-and-empty",
    "supplemental-definition-byte-shortcircuits",
    "supplemental-generation-fallback",
    "supplemental-null-rite-registry-fallback",
    "supplemental-pc-partial-independent-sibling",
)
TITLE_A, TITLE_B = 0x03000001, 0x03000002
OBJECT_A, OBJECT_B, OBJECT_C, FALLBACK_OBJECT = (
    0x07000001, 0x07000002, 0x07000003, 0x09000004,
)
RITE_ID, MEMBERSHIP_KEY, LOW24_COLLISION = 0x06000001, 0x0100BEEF, 0x0200BEEF
BLOCK_A = {"keys_count": 3, "values_count": 3,
           "keys_u16": [554, 819, 1092], "values_q64": [0, -100000, 300000], "reason": None}
BLOCK_C = {"keys_count": 1, "values_count": 1,
           "keys_u16": [1365], "values_q64": [125000], "reason": None}
BLOCK_FALLBACK = {"keys_count": 3, "values_count": 3,
                  "keys_u16": [554, 1092, 1911], "values_q64": [-200000, 300000, 150000], "reason": None}
BLOCK_EMPTY = {"keys_count": 0, "values_count": 0,
               "keys_u16": [], "values_q64": [], "reason": None}


def _snapshot(hello):
    return {
        "snapshot_id": "person-local-title-supplemental-paused-revision49",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": PLAYER_ID, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-local-title-supplemental-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }


def _native_numbers(value):
    """Project only the production wire's signed64 decimal representation."""
    if isinstance(value, list):
        return [_native_numbers(item) for item in value]
    if isinstance(value, dict):
        return {key: ([int(item) for item in item_value] if item_value is not None
                      else None) if key == "values_q64" else _native_numbers(item_value)
                for key, item_value in value.items()}
    return value


def _unavailable(section, index=None):
    try:
        compose(section, index)
    except ValueError as error:
        assert "Required native input unavailable" in str(error)
    else:
        raise AssertionError("Unread supplemental input produced a complete projection")


def test_person_local_titles_supplemental_12004_registered_mcp_whole_packets():
    from mcp import Client

    directory = Path(os.environ[WIRE_ENV])
    packets = {name: json.loads((directory / (name + ".json")).read_bytes())
               for name in CASES}
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
    snapshot = _snapshot(hello)
    leaves, composites = {}, {}

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
                    raw_frame = result["battle_terminal_transition"]
                    assert raw_frame["observed_date_raw"] == DATE_RAW
                    raw_observation, = raw_frame["character_observations"]
                    assert raw_observation["character_id"] == SUBJECT_ID != PLAYER_ID
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
                    assert frame["battle_terminal_transition_ready"] is False
                    assert actual["character_observations"] == frame["character_observations"]
                    assert actual["queried_snapshot_id"] == snapshot["snapshot_id"]
                    assert actual["queried_revision"] == PUBLIC_REVISION
                    assert actual["queried_native_revision"] == NATIVE_REVISION
                    observation, = frame["character_observations"]
                    assert observation["character_id"] == SUBJECT_ID and observation["alive"] is True
                    person = observation["current_person_state"]
                    leaf = person[FIELD_NAME]
                    leaves[name] = leaf
                    assert leaf["schema"] == SCHEMA == raw_leaf["schema"]
                    assert leaf["build_version"] == CK3_12004.game_version
                    assert leaf["executable_sha256"] == CK3_12004.executable_sha256
                    assert leaf["character_id"] == SUBJECT_ID
                    assert leaf["full_helper_ready"] is False
                    assert leaf["full_helper_reason"] == "actual2b986b0_vector_unobserved"
                    partial = name == "supplemental-pc-partial-independent-sibling"
                    assert leaf["ready"] is (not partial)
                    assert leaf["family_input_ready"] is True
                    assert leaf["composer_ready"] is True and leaf["primary_ready"] is True
                    assert leaf["supplemental_ready"] is (not partial)
                    assert leaf["reason"] == ("supplemental_inputs_partial" if partial else None)
                    assert len(leaf["rows"]) == len(raw_leaf["rows"])
                    for index, row in enumerate(leaf["rows"]):
                        assert row["native_index"] == index
                        raw_row = raw_leaf["rows"][index]
                        assert row["requested_title_full_id_u32"] == raw_row["requested_title_full_id_u32"]
                        assert row["resolution"] == raw_row["resolution"]
                        assert row["supplemental"] == _native_numbers(raw_row["supplemental"])
                        supplemental = row["supplemental"]
                        assert row["supplemental_ready"] is supplemental["ready"]
                        assert row["supplemental_reason"] == supplemental["reason"]
                        assert row["supplemental_count_i32"] == supplemental["count_i32"]
                        assert row["supplemental_array_identity"] == supplemental["array_identity"]
                        for item_index, item in enumerate(supplemental["rows"]):
                            assert item["native_index"] == item_index
                            assert item["requested_full_id_u32"] == item["resolution"]["requested_full_id_u32"]
                            assert item["source_pc"]["weight_q100000"] == 100000
                            if item["admitted"] is True:
                                assert item["match_identity"] is not None and item["first_match_index"] is not None
                                assert item["source_pc"]["identity"] == hex(int(item["definition_identity"], 16) + 0x218)
                            elif item["admitted"] is False:
                                assert item["source_pc"]["ready"] is True
                                assert item["source_pc"]["admitted"] is False
                                assert item["source_pc"]["properties"] is None
                    section = {"character_id": SUBJECT_ID, FIELD_NAME: leaf}
                    if partial:
                        _unavailable(section)
                        _unavailable(section, 0)
                        composites[name] = compose(section, 1)
                    else:
                        composites[name] = compose(section)
                    assert person["following_2922680"]["ready"] is True
                    assert person["following_2922680"]["append_occurrences"] == []
                    assert endpoint.packet == packet

    try:
        asyncio.run(exercise())
    finally:
        driver.close()

    def projected(blocks):
        return tuple({"native_index": index, "selected_title_full_id_u32": title,
                      "property_block": block}
                     for index, (title, block) in enumerate(zip((TITLE_A, TITLE_B, TITLE_A), blocks)))

    for name in ("supplemental-ordered-avx-tail-duplicates",
                 "supplemental-null-rite-registry-fallback"):
        assert composites[name] == projected((BLOCK_A, BLOCK_C, BLOCK_A))
        assert leaves[name]["family_known_zero"] is False
    assert composites["supplemental-generation-fallback"] == projected((BLOCK_FALLBACK, BLOCK_C, BLOCK_FALLBACK))
    for name in ("supplemental-no-match-and-empty", "supplemental-definition-byte-shortcircuits"):
        assert composites[name] == projected((BLOCK_EMPTY, BLOCK_EMPTY, BLOCK_EMPTY))
        assert leaves[name]["family_known_zero"] is True
        for title in leaves[name]["rows"]:
            assert title["supplemental"]["ready"] is True
            assert title["supplemental"]["known_empty"] is True
            assert all(item["ready"] is True and item["admitted"] is False
                       for item in title["supplemental"]["rows"])
    positive = leaves["supplemental-ordered-avx-tail-duplicates"]["rows"]
    assert [title["requested_title_full_id_u32"] for title in positive] == [TITLE_A, TITLE_B, TITLE_A]
    assert positive[0]["resolution"]["selected_identity"] == positive[2]["resolution"]["selected_identity"]
    sources = positive[0]["supplemental"]["rows"]
    assert [item["requested_full_id_u32"] for item in sources] == [OBJECT_A, OBJECT_B, OBJECT_A]
    assert [item["first_match_index"] for item in sources] == [2, 9, 2]
    assert [item["membership_count_i32"] for item in sources] == [12, 12, 12]
    assert [len(item["membership_full_ids_u32"]) for item in sources] == [3, 10, 3]
    assert sources[0]["membership_full_ids_u32"] == [LOW24_COLLISION, 0x101, MEMBERSHIP_KEY]
    assert sources[1]["membership_full_ids_u32"] == [
        LOW24_COLLISION, 0x201, 0x202, 0x203, 0x204, 0x205, 0x206, 0x207, 0x208, MEMBERSHIP_KEY,
    ]
    assert sources[0]["match_identity"] == hex(int(sources[0]["membership_array_identity"], 16) + 8)
    assert sources[1]["match_identity"] == hex(int(sources[1]["membership_array_identity"], 16) + 36)
    assert sources[0]["source_pc"]["identity"] == sources[2]["source_pc"]["identity"]
    assert [item["source_pc"]["properties"]["values_q64"] for item in sources] == [
        [100000, -50000], [-200000, 300000], [100000, -50000],
    ]
    assert [item["definition_gate_224_i32"] for item in sources] == [2, 2, 2]
    assert all(item["character_rite_full_id_u32"] == RITE_ID
               and item["rite_id_demanded"] is True
               and item["rite_resolution"]["selection"] == "mapped" for item in sources)
    generation = leaves["supplemental-generation-fallback"]["rows"][0]["supplemental"]["rows"]
    assert [item["resolution"]["selection"] for item in generation] == ["fallback", "mapped", "fallback"]
    assert generation[0]["resolution"]["candidate_full_id_u32"] == 0x08000001
    assert generation[0]["requested_full_id_u32"] == OBJECT_A
    assert generation[0]["source_pc"]["properties"] == {"keys_u16": [1911], "values_q64": [75000]}
    assert generation[0]["resolution"]["selected_identity"] == generation[2]["resolution"]["selected_identity"]
    fallback_sources = leaves["supplemental-null-rite-registry-fallback"]["rows"][0]["supplemental"]["rows"]
    assert all(item["rite_id_demanded"] is False and item["character_rite_full_id_u32"] is None
               and item["rite_resolution"]["registry_identity"] == "0x0"
               and item["rite_resolution"]["selection"] == "fallback"
               and item["rite_membership_key_u32"] == MEMBERSHIP_KEY for item in fallback_sources)
    no_match = leaves["supplemental-no-match-and-empty"]["rows"][0]["supplemental"]["rows"]
    assert [len(item["membership_full_ids_u32"]) for item in no_match] == [12, 0, 12]
    assert no_match[1]["membership_count_i32"] == 0 and no_match[1]["membership_array_identity"] == "0x0"
    assert no_match[1]["rite_membership_key_u32"] == MEMBERSHIP_KEY
    assert all(item["first_match_index"] is None and item["match_identity"] is None for item in no_match)
    skipped = leaves["supplemental-definition-byte-shortcircuits"]["rows"][0]["supplemental"]["rows"]
    assert [item["definition_gate_224_i32"] for item in skipped] == [0, 2, 0]
    assert [item["object_gate_18_u8"] for item in skipped] == [None, 0, None]
    assert all(item["rite_id_demanded"] is None and item["membership_count_i32"] is None
               and item["membership_array_identity"] is None for item in skipped)
    partial = leaves["supplemental-pc-partial-independent-sibling"]
    assert partial["family_known_zero"] is False
    assert [title["supplemental"]["ready"] for title in partial["rows"]] == [False, True, False]
    partial_sources = partial["rows"][0]["supplemental"]["rows"]
    assert [item["ready"] for item in partial_sources] == [False, True, False]
    assert partial_sources[0]["source_pc"]["properties"]["keys_u16"] == [554, 819]
    assert partial_sources[0]["source_pc"]["properties"]["values_q64"] is None
    assert partial_sources[1]["source_pc"]["properties"]["values_q64"] == [-200000, 300000]
    assert composites["supplemental-pc-partial-independent-sibling"] == (
        {"native_index": 1, "selected_title_full_id_u32": TITLE_B, "property_block": BLOCK_C},
    )
    assert len(endpoint.requests) == len(endpoint.delivered) == len(CASES)
    assert driver.state._command_results == {}
    assert packets == originals
