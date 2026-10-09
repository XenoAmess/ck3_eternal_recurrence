"""AUTHORED_NOTRUN: seven fresh whole-query Government gate observations.

Set CK3_PERSON_FOLLOWING_291CE01_GOVERNMENT_GATE_12004_MCP_WIRE_DIR to the new
native target's output. Only transport scaffolding/constants are reused from
the earlier compound; its producer and test are never invoked. The real
Driver/Service/registered MCP must retain the optional gate and ordered getter
steps, including unread flags. A set gate observes admission to an unclosed
conditional branch; it supplies no PC operand or complete Person/Entry result.
The separate native direct-reader death case produces no whole packet.
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
from xar_autoplayer.bridge.battle_person_government_gate_12004 import FIELD_NAME, SCHEMA
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004


CLEAR_FLAGS, SET_FLAGS = 0x80000001, 0x80080001
CASES = (
    ("living-context-bit-clear", True, False, "living_context", 1),
    ("living-context-bit-set", True, True, "living_context", 1),
    ("selected-null-default-bit-clear", True, False, "selected_null_fallback", 1),
    ("invalid-input-default-bit-set", True, True, "invalid_character_fallback", 1),
    ("related-character-generation-hit", True, False, "living_context", 2),
    ("related-character-generation-fallback", True, True, "living_context", 2),
    ("government-flags-unread", False, None, "living_context", 1),
)


def test_person_following_291ce01_government_gate_12004_registered_mcp_whole_packets():
    from mcp import Client

    directory = Path(os.environ["CK3_PERSON_FOLLOWING_291CE01_GOVERNMENT_GATE_12004_MCP_WIRE_DIR"])
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
        "snapshot_id": "person-government-gate-paused-revision49",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": PLAYER_ID, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-government-gate-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }
    leaves = {}

    async def exercise():
        with patch.object(driver, "take_snapshot", side_effect=lambda: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                assert TOOL in {tool.name for tool in (await client.list_tools()).tools}
                for sequence, (name, ready, bit_set, selection, step_count) in enumerate(CASES, 1):
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
                    assert leaf == raw_leaf
                    assert leaf["schema"] == SCHEMA
                    assert leaf["build_version"] == CK3_12004.game_version
                    assert leaf["executable_sha256"] == CK3_12004.executable_sha256
                    assert leaf["character_id"] == SUBJECT_ID
                    assert leaf["selected_model_identity"] is not None
                    assert leaf["model_owner_matches"] is True
                    assert leaf["ready"] is ready and leaf["selection"] == selection
                    assert leaf["government_identity"] is not None
                    assert leaf["bit19_set"] is bit_set and leaf["branch_admitted"] is bit_set
                    assert leaf["known_no_contribution"] is (None if bit_set is None else not bit_set)
                    if ready:
                        assert leaf["reason"] is None
                        assert leaf["flags_40_u32"] == (SET_FLAGS if bit_set else CLEAR_FLAGS)
                    else:
                        assert leaf["reason"] == "government_flags_unread"
                        assert leaf["flags_40_u32"] is None
                    steps = leaf["steps"]
                    assert len(steps) == step_count
                    assert [row["native_index"] for row in steps] == list(range(step_count))
                    assert steps[0]["character_identity"] == leaf["character_identity"]
                    assert steps[0]["magic_u32"] == (0 if name == "invalid-input-default-bit-set"
                                                       else 0x43686172)
                    preceding = person["following_2922680"]
                    assert preceding["ready"] is True and preceding["primary_ready"] is True
                    assert preceding["append_occurrences"] == []
                    assert endpoint.packet == packet

    try:
        asyncio.run(exercise())
    finally:
        driver.close()

    for name, candidate_id, selected_id in (
        ("related-character-generation-hit", 0x03000001, 0x03000001),
        ("related-character-generation-fallback", 0x04000001, 0x05000002),
    ):
        root, resolved = leaves[name]["steps"]
        assert root["related_context_identity"] is not None
        assert root["related_full_id_u32"] == 0x03000001
        assert root["registry_count_u32"] == 2 and root["registry_slots_identity"] is not None
        assert root["candidate_full_id_u32"] == candidate_id
        assert root["selected_character_identity"] == resolved["character_identity"]
        assert resolved["magic_u32"] == 0x43686172 and resolved["full_id_u32"] == selected_id
        assert resolved["living_context_identity"] is not None
        if candidate_id == selected_id:
            assert root["resolution_selection"] == "mapped"
            assert root["candidate_identity"] == root["selected_character_identity"]
        else:
            assert root["resolution_selection"] == "fallback"
            assert root["candidate_identity"] != root["selected_character_identity"]
            assert root["selected_character_identity"] == leaves[name]["character_fallback_identity"]
    assert len(endpoint.requests) == len(endpoint.delivered) == len(CASES)
    assert driver.state._command_results == {}
    assert packets == originals
