"""AUTHORED_NOTRUN: ten fresh local-Title whole-query inputs via registered MCP.

The new native producer supplies original command_result packets. Only
transport scaffolding/constants are reused from the previous compound; its
producer and test are never invoked. Full Person/Entry and live credit remain
unavailable. No locally manufactured DTO substitutes for a production packet.
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
    compose_local_title_composer_blocks_from_current_source_inputs_12004 as compose,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004


WIRE_ENV = "CK3_PERSON_FOLLOWING_291E3A0_LOCAL_TITLES_12004_MCP_WIRE_DIR"
CASES = (
    ("context-empty", True, True, True, True),
    ("absent-context-static-empty", True, True, True, True),
    ("eligible-tier3-composer-duplicates", True, True, True, False),
    ("excluded-byte-and-dword", True, True, True, True),
    ("generation-fallback", True, True, True, False),
    ("null-title-registry-ids-retained", True, True, True, False),
    ("composer-values-unread-independent-sibling", False, True, False, False),
    ("negative-header-count", False, False, False, None),
    ("eligible-tier1-primary-positive", True, True, True, False),
    ("eligible-tier2-primary-supplemental-empty", True, True, True, False),
)
TITLE_A, TITLE_B, FALLBACK_TITLE = 0x03000001, 0x03000002, 0x05000003
P_VALUES, Q_VALUES, C_VALUES = [100000, -50000], [-200000, 300000], [125000]
COMPOSITE_A = {
    "keys_count": 3, "values_count": 3, "keys_u16": [554, 819, 1092],
    "values_q64": [0, -100000, 300000], "reason": None,
}
COMPOSITE_Q = {
    "keys_count": 2, "values_count": 2, "keys_u16": [554, 1092],
    "values_q64": Q_VALUES, "reason": None,
}
COMPOSITE_C = {
    "keys_count": 1, "values_count": 1, "keys_u16": [1365],
    "values_q64": C_VALUES, "reason": None,
}


def local_titles_snapshot(hello):
    return {
        "snapshot_id": "person-local-titles-paused-revision49",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": PLAYER_ID, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-local-titles-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }


def test_person_following_291e3a0_local_titles_12004_registered_mcp_whole_packets():
    from mcp import Client

    directory = Path(os.environ[WIRE_ENV])
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
    snapshot = local_titles_snapshot(hello)
    leaves, composites = {}, {}

    def expect_unavailable(section, index=None, reason=None):
        try:
            compose(section, index)
        except ValueError as error:
            if reason:
                assert reason in str(error)
        else:
            raise AssertionError("Unread local-Title operands produced a complete composite")

    async def exercise():
        with patch.object(driver, "take_snapshot", side_effect=lambda: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                assert TOOL in {tool.name for tool in (await client.list_tools()).tools}
                for sequence, (name, ready, input_ready, composer_ready, known_zero) in enumerate(CASES, 1):
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
                    assert leaf["schema"] == raw_leaf["schema"] == SCHEMA
                    assert leaf["build_version"] == CK3_12004.game_version
                    assert leaf["executable_sha256"] == CK3_12004.executable_sha256
                    assert leaf["character_id"] == SUBJECT_ID
                    assert leaf["ready"] is ready
                    assert leaf["family_input_ready"] is input_ready
                    assert leaf["composer_ready"] is composer_ready
                    assert leaf["primary_ready"] is input_ready and leaf["supplemental_ready"] is input_ready
                    assert leaf["family_known_zero"] is known_zero
                    assert leaf["full_helper_ready"] is False
                    assert leaf["full_helper_reason"] == "actual2b986b0_vector_unobserved"
                    assert leaf["reason"] == (None if ready else "local_title_count_negative"
                                              if name == "negative-header-count" else "composer_inputs_partial")
                    for key in ("character_identity", "selected_model_identity", "destination_pc_identity",
                                "character_context_1c0_identity", "header_selection", "header_identity",
                                "array_identity", "count_i32"):
                        assert leaf[key] == raw_leaf[key]
                    rows = leaf["rows"]
                    assert [row["native_index"] for row in rows] == list(range(len(rows)))
                    assert len(rows) == (0 if name in {"context-empty", "absent-context-static-empty",
                                                       "negative-header-count"} else 1 if name in {
                                                           "eligible-tier1-primary-positive",
                                                           "eligible-tier2-primary-supplemental-empty"} else 3)
                    for index, row in enumerate(rows):
                        raw_row = raw_leaf["rows"][index]
                        for key in ("native_index", "input_ready", "ready", "reason",
                                    "requested_title_full_id_u32", "selected_title_full_id_u32", "resolution",
                                    "exclusion_byte_130_u8", "exclusion_dword_12c_i32", "exclusion",
                                    "native_contribution_eligible", "template_identity", "template_tier_i32",
                                    "supplemental_array_identity", "supplemental_count_i32"):
                            assert row[key] == raw_row[key]
                        assert row["requested_title_full_id_u32"] == [TITLE_A, TITLE_B, TITLE_A][index]
                        assert row["resolution"]["requested_full_id_u32"] == row["requested_title_full_id_u32"]
                        composer = row["composer"]
                        raw_composer = raw_row["composer"]
                        for key in ("ready", "reason", "array_identity", "count_i32", "known_empty"):
                            assert composer[key] == raw_composer[key]
                        assert len(composer["source_pcs"]) == len(raw_composer["source_pcs"])
                        for pc_index, pc in enumerate(composer["source_pcs"]):
                            raw_pc = raw_composer["source_pcs"][pc_index]
                            for key in ("ready", "reason", "admitted", "identity", "count_i32", "weight_q100000"):
                                assert pc[key] == raw_pc[key]
                            assert pc["admitted"] is True and pc["weight_q100000"] == 100000
                            assert pc["properties"]["keys_u16"] == raw_pc["properties"]["keys_u16"]
                            values = pc["properties"]["values_q64"]
                            assert raw_pc["properties"]["values_q64"] == (
                                None if values is None else [str(value) for value in values])
                    section = {"character_id": SUBJECT_ID, FIELD_NAME: leaf}
                    if input_ready and composer_ready:
                        composites[name] = compose(section)
                    else:
                        expect_unavailable(section)
                    if name == "composer-values-unread-independent-sibling":
                        sibling = compose(section, 1)
                        assert sibling == ({"native_index": 1, "selected_title_full_id_u32": TITLE_B,
                                            "property_block": COMPOSITE_C, "outer_append_demanded": True},)
                        expect_unavailable(section, 0, "source_pcs_partial")
                        expect_unavailable(section, 2, "source_pcs_partial")
                    preceding = person["following_2922680"]
                    assert preceding["ready"] is True and preceding["primary_ready"] is True
                    assert preceding["append_occurrences"] == []
                    assert endpoint.packet == packet

    try:
        asyncio.run(exercise())
    finally:
        driver.close()

    for name in ("context-empty", "absent-context-static-empty", "excluded-byte-and-dword"):
        assert composites[name] == ()
    assert leaves["context-empty"]["header_selection"] == "context_1c0_1e0"
    absent = leaves["absent-context-static-empty"]
    assert absent["header_selection"] == "existing_default_5459c88"
    assert absent["header_identity"] == hex(0x140000000 + 0x5459C88)
    assert absent["count_i32"] == 0 and absent["array_identity"] == "0x0"
    assert leaves["context-empty"]["array_identity"] is not None
    negative = leaves["negative-header-count"]
    assert negative["count_i32"] == -2 and negative["array_identity"] is not None
    excluded = leaves["excluded-byte-and-dword"]["rows"]
    assert [row["exclusion"] for row in excluded] == [
        "byte_130_nonzero", "dword_12c_not_minus_one", "byte_130_nonzero"]
    assert [row["exclusion_dword_12c_i32"] for row in excluded] == [None, 17, None]
    assert all(row["native_contribution_eligible"] is False and row["template_identity"] is None
               and row["composer"]["source_pcs"] == [] for row in excluded)
    for name, ids, blocks in (
        ("eligible-tier3-composer-duplicates", [TITLE_A, TITLE_B, TITLE_A],
         [COMPOSITE_A, COMPOSITE_C, COMPOSITE_A]),
        ("generation-fallback", [FALLBACK_TITLE, TITLE_B, FALLBACK_TITLE],
         [COMPOSITE_Q, COMPOSITE_C, COMPOSITE_Q]),
        ("null-title-registry-ids-retained", [FALLBACK_TITLE] * 3,
         [COMPOSITE_Q] * 3),
        ("eligible-tier1-primary-positive", [TITLE_A], [COMPOSITE_A]),
        ("eligible-tier2-primary-supplemental-empty", [TITLE_A], [COMPOSITE_A]),
    ):
        expected = tuple({"native_index": index, "selected_title_full_id_u32": selected,
                          "property_block": block, "outer_append_demanded": True}
                         for index, (selected, block) in enumerate(zip(ids, blocks)))
        assert composites[name] == expected
    duplicate = leaves["eligible-tier3-composer-duplicates"]["rows"]
    assert duplicate[0]["resolution"]["selected_identity"] == duplicate[2]["resolution"]["selected_identity"]
    pcs = duplicate[0]["composer"]["source_pcs"]
    assert len(pcs) == 3 and pcs[0]["identity"] == pcs[2]["identity"] != pcs[1]["identity"]
    assert [pc["properties"]["values_q64"] for pc in pcs] == [P_VALUES, Q_VALUES, P_VALUES]
    assert COMPOSITE_A["values_q64"][0] == 0 and COMPOSITE_A["keys_count"] == 3
    generation = leaves["generation-fallback"]["rows"]
    assert [row["resolution"]["selection"] for row in generation] == ["fallback", "mapped", "fallback"]
    assert generation[0]["resolution"]["candidate_full_id_u32"] == 0x04000001
    null_registry = leaves["null-title-registry-ids-retained"]["rows"]
    assert [row["requested_title_full_id_u32"] for row in null_registry] == [TITLE_A, TITLE_B, TITLE_A]
    assert all(row["resolution"]["registry_identity"] == "0x0"
               and row["resolution"]["selection"] == "fallback" for row in null_registry)
    partial = leaves["composer-values-unread-independent-sibling"]["rows"]
    assert [row["ready"] for row in partial] == [False, True, False]
    for index in (0, 2):
        pcs = partial[index]["composer"]["source_pcs"]
        assert [pc["ready"] for pc in pcs] == [False, True, False]
        assert pcs[0]["properties"]["keys_u16"] == [554, 819]
        assert pcs[0]["properties"]["values_q64"] is None
        assert pcs[1]["properties"]["values_q64"] == Q_VALUES
    tier1, = leaves["eligible-tier1-primary-positive"]["rows"]
    assert tier1["template_tier_i32"] == 1 and tier1["primary"]["ready"] is True
    primary_pc, = tier1["primary"]["source_pcs"]
    assert primary_pc["ready"] is True and primary_pc["admitted"] is True
    assert primary_pc["count_i32"] == 1 and primary_pc["weight_q100000"] == 100000
    assert primary_pc["properties"] == {"keys_u16": [1638], "values_q64": [150000]}
    tier2, = leaves["eligible-tier2-primary-supplemental-empty"]["rows"]
    assert tier2["template_tier_i32"] == 2 and tier2["primary"]["ready"] is True
    assert tier2["primary"]["known_empty"] is True and tier2["primary"]["source_pcs"] == []
    assert tier2["primary"]["array_identity"] == "0x0" and tier2["primary"]["count_i32"] == 0
    assert tier1["supplemental_ready"] is True
    assert tier1["supplemental_array_identity"] is None and tier1["supplemental_count_i32"] is None
    assert tier2["supplemental_ready"] is True
    assert tier2["supplemental_array_identity"] == "0x0" and tier2["supplemental_count_i32"] == 0
    assert len(endpoint.requests) == len(endpoint.delivered) == len(CASES)
    assert driver.state._command_results == {}
    assert packets == originals
