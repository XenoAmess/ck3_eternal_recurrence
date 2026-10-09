"""Six new production whole packets through registered MCP; source preparation.

Reuse only the synthetic transport scaffold. No historical fixture or compound
runs. Numerical blocks describe helper inputs; FullPerson/Entry remain partial.
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
from xar_autoplayer.bridge.battle_person_first_title_vector_12004 import (
    FIELD_NAME, SCHEMA,
    compose_first_title_vector_inputs_from_current_source_inputs_12004 as compose,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004


WIRE_ENV = "CK3_PERSON_FIRST_TITLE_VECTOR_12004_MCP_WIRE_DIR"
CASES = (
    "phase-a-distinct-receiver-nonzero-filter",
    "phase-b-direct-ignores-local-exclusions",
    "null-title-registry-skips-list-ids",
    "title-generation-fallback-preserves-order",
    "composer-partial-independent-element",
    "phase-b-negative-count-preserves-phase-a",
)
TITLE_A, TITLE_B, INITIAL_TITLE, FALLBACK_TITLE = (
    0x03000001, 0x03000002, 0x03000003, 0x05000004,
)
SECOND_ID, RECEIVER_ID = 0x09000001, 0x08000009
BLOCK_A = {"keys_count": 3, "values_count": 3,
           "keys_u16": [554, 819, 1092], "values_q64": [0, -100000, 300000], "reason": None}
BLOCK_B = {"keys_count": 1, "values_count": 1,
           "keys_u16": [1365], "values_q64": [125000], "reason": None}
BLOCK_F = {"keys_count": 1, "values_count": 1,
           "keys_u16": [1911], "values_q64": [75000], "reason": None}
BLOCK_EMPTY = {"keys_count": 0, "values_count": 0,
               "keys_u16": [], "values_q64": [], "reason": None}


def _snapshot(hello):
    return {
        "snapshot_id": "person-first-title-vector-paused-revision49",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": PLAYER_ID, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-first-title-vector-12004",
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


def _unavailable(section, phase=None, native_index=None):
    try:
        compose(section, phase=phase, native_index=native_index)
    except ValueError as error:
        assert "Required native input unavailable" in str(error)
    else:
        raise AssertionError("Incomplete vector inputs produced a complete numerical projection")


def _composer(phase, index, row, block):
    return {"phase": phase, "native_index": index,
            "element_identity": row["element"]["identity"],
            "property_block": block, "outer_append_demanded": True}


def test_person_first_title_vector_12004_registered_mcp_whole_packets():
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
    leaves, projections = {}, {}

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
                    assert leaf == _native_numbers(raw_leaf)
                    assert leaf["schema"] == SCHEMA == "xar.ck3.person-first-title-vector-12004-v1"
                    assert leaf["build_version"] == CK3_12004.game_version
                    assert leaf["executable_sha256"] == CK3_12004.executable_sha256
                    assert leaf["character_id"] == SUBJECT_ID
                    assert leaf["character_identity"] == person["following_2922680"]["character_identity"]
                    assert leaf["selected_model_identity"] == person["following_2922680"]["selected_model_identity"]
                    assert leaf["destination_pc_identity"] is not None
                    assert leaf["full_helper_ready"] is False
                    assert leaf["full_helper_reason"] == "historical_post_callback_model_and_final_append_unobserved"
                    negative = name == "phase-b-negative-count-preserves-phase-a"
                    partial = name == "composer-partial-independent-element"
                    assert leaf["ready"] is (not (negative or partial))
                    assert leaf["source_inputs_ready"] is (not negative)
                    assert leaf["producer_ready"] is (not negative)
                    assert leaf["family_input_ready"] is (not negative)
                    assert leaf["primary_ready"] is (not negative)
                    assert leaf["composer_ready"] is (not (negative or partial))
                    assert leaf["supplemental_ready"] is (not negative)
                    assert leaf["family_known_zero"] is False
                    assert leaf["reason"] == ("first_vector_source_inputs_partial" if negative
                                              else "composer_inputs_partial" if partial else None)
                    receiver = leaf["receiver"]
                    assert receiver["ready"] is True and receiver["selection"] == "context_candidate"
                    assert receiver["candidate_magic_1c_u32"] == 0x43686172
                    assert receiver["candidate_full_id_18_u32"] == RECEIVER_ID
                    assert receiver["selected_identity"] == receiver["context_candidate_28_identity"]
                    assert receiver["selected_identity"] != leaf["character_identity"]
                    assert receiver["input_link_1b8_identity"] == "0x0"
                    inputs = leaf["phase_b_inputs"]
                    assert inputs["ready"] is True and inputs["selection"] == "context_first"
                    assert inputs["context_count_1ec_i32"] == 1
                    assert inputs["initial_title_full_id_u32"] == INITIAL_TITLE
                    assert inputs["second_requested_full_id_330_u32"] == SECOND_ID
                    assert inputs["second_resolution"]["selection"] == "mapped"
                    assert leaf["phase_a"]["ready"] is True
                    assert leaf["phase_b"]["ready"] is (not negative)
                    assert leaf["phase_b"]["count_i32"] == (-2 if negative else 3)
                    assert leaf["phase_b"]["reason"] == ("phase_count_negative" if negative else None)
                    for phase in ("phase_a", "phase_b"):
                        for index, row in enumerate(leaf[phase]["rows"]):
                            assert row["native_index"] == index and row["ready"] is True
                            if row["emitted"] is False:
                                assert row["element"] is None
                                continue
                            element = row["element"]
                            assert element["identity"] == row["resolution"]["selected_identity"]
                            assert element["template_tier_i32"] == 3 and element["input_ready"] is True
                            assert element["primary"]["ready"] is True
                            assert element["primary"]["known_empty"] is True
                            assert element["primary"]["source_pcs"] == []
                            assert element["supplemental"]["ready"] is True
                            assert element["supplemental"]["known_empty"] is True
                            assert element["supplemental"]["rows"] == []
                            assert element["composer"]["known_empty"] is False
                            assert all(pc["weight_q100000"] == 100000
                                       for pc in element["composer"]["source_pcs"])
                    section = {"character_id": SUBJECT_ID, FIELD_NAME: leaf}
                    if negative or partial:
                        _unavailable(section)
                        if negative:
                            projections[name] = compose(section, phase="phase_a", native_index=0)
                        else:
                            _unavailable(section, "phase_a", 0)
                            projections[name] = compose(section, phase="phase_b", native_index=0)
                    else:
                        projections[name] = compose(section)
                    assert person["following_2922680"]["ready"] is True
                    assert person["following_2922680"]["append_occurrences"] == []
                    assert endpoint.packet == packet

    try:
        asyncio.run(exercise())
    finally:
        driver.close()

    for name in CASES:
        leaf, projected = leaves[name], projections[name]
        assert projected["main_property_block"] == BLOCK_EMPTY
        assert projected["full_helper_ready"] is False
        assert projected["complete_vector_input"] is (name not in CASES[-2:])
        phase_a, phase_b = leaf["phase_a"]["rows"], leaf["phase_b"]["rows"]
        if name == "phase-b-negative-count-preserves-phase-a":
            assert leaf["emitted_element_identities"] is None and phase_b == []
            assert projected["composer_blocks"] == (_composer("phase_a", 0, phase_a[0], BLOCK_A),)
            continue
        emitted = [row["element"]["identity"] for phase in (phase_a, phase_b)
                   for row in phase if row["emitted"] is True]
        assert leaf["emitted_element_identities"] == emitted
        if name == "phase-b-direct-ignores-local-exclusions":
            assert leaf["phase_a"]["admitted"] is False and phase_a == []
            assert all(leaf["phase_a"][key] is None for key in (
                "header_identity", "array_identity", "count_i32",
                "title_registry_identity", "title_fallback_identity"))
            assert projected["composer_blocks"] == tuple(
                _composer("phase_b", index, row, block)
                for index, (row, block) in enumerate(zip(phase_b, (BLOCK_B, BLOCK_A, BLOCK_B))))
        elif name == "null-title-registry-skips-list-ids":
            assert len(emitted) == 6 and len(set(emitted)) == 1
            assert leaf["phase_b_inputs"]["initial_title_resolution"]["selection"] == "fallback"
            assert leaf["phase_b_inputs"]["initial_title_resolution"]["requested_full_id_u32"] == INITIAL_TITLE
            assert all(row["id_demanded"] is False and row["requested_full_id_u32"] is None
                       and row["resolution"]["requested_full_id_u32"] is None
                       and row["resolution"]["selection"] == "fallback"
                       for phase in (phase_a, phase_b) for row in phase)
            assert projected["composer_blocks"] == tuple(
                _composer(phase, index, row, BLOCK_F)
                for phase, rows in (("phase_a", phase_a), ("phase_b", phase_b))
                for index, row in enumerate(rows))
        elif name == "composer-partial-independent-element":
            assert all(row["ready"] is True for row in phase_a + phase_b)
            element = phase_a[0]["element"]
            assert element["ready"] is False and element["reason"] == "composer_inputs_partial"
            pcs = element["composer"]["source_pcs"]
            assert [pc["ready"] for pc in pcs] == [False, True, False]
            assert pcs[0]["properties"] == {"keys_u16": [554, 819], "values_q64": None}
            assert pcs[1]["properties"]["values_q64"] == [-200000, 300000]
            assert pcs[0]["identity"] == pcs[2]["identity"]
            assert projected["composer_blocks"] == (_composer("phase_b", 0, phase_b[0], BLOCK_B),)
        else:
            fallback = name == "title-generation-fallback-preserves-order"
            assert [row["requested_full_id_u32"] for row in phase_a] == [TITLE_A, TITLE_B, TITLE_A]
            assert [row["requested_full_id_u32"] for row in phase_b] == [TITLE_B, TITLE_A, TITLE_B]
            assert [row["emitted"] for row in phase_a] == [True, False, True]
            assert [row["filter_byte_130_u8"] for row in phase_a] == [1, 0, 1]
            block_a = BLOCK_F if fallback else BLOCK_A
            assert projected["composer_blocks"] == (
                _composer("phase_a", 0, phase_a[0], block_a),
                _composer("phase_a", 2, phase_a[2], block_a),
                _composer("phase_b", 0, phase_b[0], BLOCK_B),
                _composer("phase_b", 1, phase_b[1], block_a),
                _composer("phase_b", 2, phase_b[2], BLOCK_B),
            )
            assert emitted == [emitted[0], emitted[0], emitted[2], emitted[0], emitted[2]]
            if fallback:
                for row in (phase_a[0], phase_a[2], phase_b[1]):
                    assert row["resolution"]["selection"] == "fallback"
                    assert row["resolution"]["candidate_full_id_u32"] == 0x04000001
            else:
                pcs = phase_a[0]["element"]["composer"]["source_pcs"]
                assert pcs[0]["identity"] == pcs[2]["identity"]
        assert all(row["filter_byte_130_u8"] is None and row["emitted"] is True for row in phase_b)
    assert len(endpoint.requests) == len(endpoint.delivered) == len(CASES)
    assert driver.state._command_results == {}
    assert packets == originals
