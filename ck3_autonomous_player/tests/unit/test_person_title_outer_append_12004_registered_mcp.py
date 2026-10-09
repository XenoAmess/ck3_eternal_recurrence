"""New outer requests from three retained Root59 production whole packets.

No native producer or historical compound is invoked. Original packet bodies,
including query sequences 1/5/6, remain unchanged; only transport correlation
is assigned by the existing whole-packet endpoint.
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
from xar_autoplayer.bridge.battle_person_first_title_vector_12004 import FIELD_NAME
from xar_autoplayer.bridge.battle_person_title_outer_append_12004 import (
    project_person_first_title_composer_outer_requests_12004 as project,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004


WIRE_ENV = "CK3_PERSON_TITLE_OUTER_APPEND_12004_RETAINED_WIRE_DIR"
CASES = (
    ("phase-a-distinct-receiver-nonzero-filter", 1),
    ("composer-partial-independent-element", 5),
    ("phase-b-negative-count-preserves-phase-a", 6),
)
BLOCK_A = {"keys_count": 3, "values_count": 3,
           "keys_u16": [554, 819, 1092], "values_q64": [0, -100000, 300000], "reason": None}
BLOCK_B = {"keys_count": 1, "values_count": 1,
           "keys_u16": [1365], "values_q64": [125000], "reason": None}


def _expected(leaf, phase, index, block):
    return {
        "source_family": "first_title_vector",
        "phase": phase,
        "native_index": index,
        "title_identity": leaf[phase]["rows"][index]["element"]["identity"],
        "selected_model_identity": leaf["selected_model_identity"],
        "inline_destination_identity": hex(int(leaf["selected_model_identity"], 16) + 0x10),
        "property_block": block,
        "weight_q100000": 100000,
        "actual_model_write_performed": False,
        "full_helper_ready": False,
    }


def _unavailable(section, phase=None, native_index=None):
    try:
        project(section, phase=phase, native_index=native_index)
    except ValueError as error:
        assert "Required native input unavailable" in str(error)
    else:
        raise AssertionError("Unread composer inputs produced a complete outer request family")


def test_person_title_outer_append_12004_registered_mcp_retained_whole_packets():
    from mcp import Client

    directory = Path(os.environ[WIRE_ENV])
    packets = {name: json.loads((directory / (name + ".json")).read_bytes())
               for name, _ in CASES}
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
        "snapshot_id": "retained-root59-title-outer-request-inputs",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": PLAYER_ID, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-title-outer-append-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }
    leaves, requests = {}, {}

    async def exercise():
        with patch.object(driver, "take_snapshot", side_effect=lambda: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                assert TOOL in {tool.name for tool in (await client.list_tools()).tools}
                for name, native_sequence in CASES:
                    packet = packets[name]
                    assert packet["type"] == "command_result" and packet["ok"] is True
                    assert packet["result"]["step"] == step
                    assert packet["result"]["query_sequence"] == native_sequence
                    assert packet["result"]["snapshot_revision"] == NATIVE_REVISION
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
                    assert actual["query_sequence"] == native_sequence
                    assert actual["queried_revision"] == PUBLIC_REVISION
                    assert actual["queried_native_revision"] == NATIVE_REVISION
                    assert frame["observed_date_raw"] == DATE_RAW
                    assert frame["battle_terminal_transition_ready"] is False
                    observation, = frame["character_observations"]
                    assert observation["character_id"] == SUBJECT_ID != PLAYER_ID
                    assert observation["alive"] is True
                    leaf = observation["current_person_state"][FIELD_NAME]
                    leaves[name] = leaf
                    assert leaf["character_id"] == SUBJECT_ID
                    assert leaf["build_version"] == CK3_12004.game_version
                    assert leaf["executable_sha256"] == CK3_12004.executable_sha256
                    assert leaf["full_helper_ready"] is False
                    section = {"character_id": SUBJECT_ID, FIELD_NAME: leaf}
                    if native_sequence == 1:
                        requests[name] = project(section)
                        assert project(section, phase="phase_a", native_index=1) == ()
                    else:
                        _unavailable(section)
                        phase = "phase_b" if native_sequence == 5 else "phase_a"
                        requests[name] = project(section, phase=phase, native_index=0)
                        if native_sequence == 5:
                            _unavailable(section, "phase_a", 0)
                    assert endpoint.packet == packet

    try:
        asyncio.run(exercise())
    finally:
        driver.close()

    baseline = leaves[CASES[0][0]]
    baseline_requests = requests[CASES[0][0]]
    assert baseline_requests == (
        _expected(baseline, "phase_a", 0, BLOCK_A),
        _expected(baseline, "phase_a", 2, BLOCK_A),
        _expected(baseline, "phase_b", 0, BLOCK_B),
        _expected(baseline, "phase_b", 1, BLOCK_A),
        _expected(baseline, "phase_b", 2, BLOCK_B),
    )
    assert [request["title_identity"] for request in baseline_requests] == baseline["emitted_element_identities"]
    assert baseline_requests[0]["title_identity"] == baseline_requests[1]["title_identity"] == baseline_requests[3]["title_identity"]
    assert baseline_requests[2]["title_identity"] == baseline_requests[4]["title_identity"]
    for name, native_sequence in CASES:
        leaf = leaves[name]
        inline_destination = hex(int(leaf["selected_model_identity"], 16) + 0x10)
        assert inline_destination != leaf["destination_pc_identity"]
        assert all(request["inline_destination_identity"] == inline_destination
                   and request["weight_q100000"] == 100000
                   and request["actual_model_write_performed"] is False
                   and request["full_helper_ready"] is False for request in requests[name])
        if native_sequence == 5:
            assert leaf["ready"] is False and leaf["producer_ready"] is True
            assert leaf["composer_ready"] is False
            assert requests[name] == (_expected(leaf, "phase_b", 0, BLOCK_B),)
        elif native_sequence == 6:
            assert leaf["ready"] is False and leaf["producer_ready"] is False
            assert leaf["phase_b"]["count_i32"] == -2
            assert requests[name] == (_expected(leaf, "phase_a", 0, BLOCK_A),)
    assert len(endpoint.requests) == len(endpoint.delivered) == 3
    assert [packet["result"]["query_sequence"] for packet in endpoint.delivered] == [1, 5, 6]
    assert driver.state._command_results == {}
    assert packets == originals
