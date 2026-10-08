"""AUTHORED_NOTRUN: sole registered consumer of NEW actual4 2921A90 whole wires.

Root native FIRST publishes the ten original production command_result packets.
Set CK3_PERSON_FOLLOWING_2921A90_12004_MCP_WIRE_DIR to that output directory and
PYTHONPATH to this tree's ck3_autonomous_player/src; select only the node below.
Only request correlation and hello/paused-snapshot scaffolding are fixtures.
No historical carrier case, complete Entry, conditional evaluation, merger or
paused-live qualification is run or claimed by this source package.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge.battle_person_following_2921a90_12004 import (
    CONDITIONAL_GAP, FIELD_NAME, SCHEMA,
    emit_following_2921a90_requests_from_current_source_inputs_12004 as emit_whole,
    emit_following_2921a90_direct_requests_from_current_source_inputs_12004 as emit_direct,
    emit_following_2921a90_row_requests_from_current_source_inputs_12004 as emit_row,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004


TOOL = "ck3_query_battle_terminal_transition_v1"
ENEMY_FULL_ID, PLAYER_FULL_ID = 0x04000003, 29829
PUBLIC_REVISION, NATIVE_REVISION, DATE_RAW = 73, 41, 53236632
CASES = (
    ("mapped-ordered-pcs", True, True, True, (True, True, True, True)),
    ("empty-direct-list", True, True, True, ()),
    ("absent-carrier-fallback", True, True, True, (True,)),
    ("generation-mismatch-fallback", True, True, True, (True,)),
    ("wrong-selected-magic", True, True, True, ()),
    ("fallback-id-sentinel", True, True, True, ()),
    ("row-values-partial", False, False, True, (False, True, False, True)),
    ("conditional-b8c-demanded", False, True, False, (True, True, True, True)),
    ("conditional-bbc-demanded", False, True, False, (True, True, True, True)),
    ("negative-direct-count", False, False, True, ()),
)


class FollowingWholePacketEndpoint:
    """Reuse the qualified callback transport shape, with original new packets."""

    pipe_name = "offline-person-following-2921a90-12004-whole-packets"

    def __init__(self, step):
        self.step = step
        self.requests = []
        self.delivered = []
        self.packet = None
        self.on_frame = None

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def select(self, packet):
        self.packet = deepcopy(packet)

    def send(self, request):
        assert request["type"] == "execute_step" and request["protocol_version"] == 1
        assert request["step"] == self.step and request["expected_revision"] == NATIVE_REVISION
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


def test_person_following_2921a90_12004_registered_mcp_whole_packets():
    from mcp import Client

    directory = Path(os.environ["CK3_PERSON_FOLLOWING_2921A90_12004_MCP_WIRE_DIR"])
    packets = {name: json.loads((directory / (name + ".json")).read_bytes())
               for name, *_ in CASES}
    originals = deepcopy(packets)
    step = query_battle_terminal_transition_v1_step(None, None, None, [ENEMY_FULL_ID])
    assert step == "query-battle-terminal-transition-v1-none:characters:67108867"
    endpoint = FollowingWholePacketEndpoint(step)
    driver = NativeHeadlessGameplayDriver(endpoint=endpoint, episode_projection="native_campaign")
    hello = {
        "type": "hello", "protocol_version": 1, "pid": 1,
        "capabilities": ["game.state.snapshot", QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY],
        "expected_ck3_version": CK3_12004.game_version,
        "expected_ck3_sha256": CK3_12004.executable_sha256,
    }
    assert driver.state.ingest(hello) == "hello"
    snapshot = {
        "snapshot_id": "person-following-2921a90-paused-native41",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": PLAYER_FULL_ID, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-following-2921a90-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }
    leaves, direct_requests, row_requests = {}, {}, {}

    def expect_unavailable(emitter, reason, *arguments):
        try:
            emitter(*arguments)
        except ValueError as error:
            assert reason in str(error)
        else:
            raise AssertionError("An unobserved family or row produced a complete request")

    async def exercise():
        # Reuse the qualified framework's sole snapshot seam. Everything from
        # primitive/state wait through main normalizer, Service and MCP is real.
        with patch.object(driver, "take_snapshot", side_effect=lambda: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                assert TOOL in {tool.name for tool in (await client.list_tools()).tools}
                for sequence, (name, whole_ready, direct_ready, conditional_ready, ready_rows) in enumerate(CASES, 1):
                    packet = packets[name]
                    assert packet["type"] == "command_result"
                    assert packet["protocol_version"] == 1 and packet["ok"] is True
                    result = packet["result"]
                    assert result["step"] == step and result["query_sequence"] == sequence
                    assert result["snapshot_revision"] == NATIVE_REVISION
                    raw_frame = result["battle_terminal_transition"]
                    assert raw_frame["observed_date_raw"] == DATE_RAW
                    assert [row["character_id"] for row in raw_frame["character_observations"]] == [ENEMY_FULL_ID]
                    raw_leaf = raw_frame["character_observations"][0]["current_person_state"][FIELD_NAME]
                    assert raw_leaf["schema"] == SCHEMA
                    assert raw_leaf["character_id"] == ENEMY_FULL_ID
                    endpoint.select(packet)
                    response = await client.call_tool(TOOL, {
                        "prior_combat_id": None, "subject_public_cunit_id": None,
                        "expected_revision": PUBLIC_REVISION, "character_ids": [ENEMY_FULL_ID],
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
                    observed = frame["character_observations"][0]
                    assert observed["character_id"] == ENEMY_FULL_ID != PLAYER_FULL_ID
                    leaf = observed["current_person_state"][FIELD_NAME]
                    leaves[name] = leaf
                    assert leaf["character_id"] == observed["character_id"]
                    assert leaf["build_version"] == CK3_12004.game_version
                    assert leaf["executable_sha256"] == CK3_12004.executable_sha256
                    assert (leaf["ready"], leaf["direct_ready"], leaf["conditional_ready"]) == (
                        whole_ready, direct_ready, conditional_ready)
                    assert tuple(row["ready"] for row in leaf["direct_rows"]) == ready_rows
                    for key in ("requested_full_id_u32", "selected_full_id_u32",
                                "selected_model_identity", "character_identity", "destination_pc_identity"):
                        assert leaf[key] == raw_leaf[key]
                    source = {"character_id": observed["character_id"], FIELD_NAME: leaf}
                    if direct_ready:
                        emitted = emit_direct(source)
                        direct_requests[name] = emitted
                        assert len(emitted) == len(leaf["direct_rows"])
                        assert [item.source_ordinal for item in emitted] == list(range(len(emitted)))
                    else:
                        expect_unavailable(emit_direct, leaf["direct_reason"], source)
                    if whole_ready:
                        assert emit_whole(source) == direct_requests[name]
                    else:
                        expect_unavailable(emit_whole, leaf["reason"], source)
                    independent = {}
                    for row in leaf["direct_rows"]:
                        index = row["native_index"]
                        if row["ready"]:
                            items = emit_row(source, index)
                            assert len(items) == 1 and items[0].source_ordinal == index
                            assert items[0].first_row_index == 0 and items[0].row_count == 1
                            assert items[0].weight_q64 == 100000
                            assert items[0].definition_identity == row["source_pc_identity"]
                            independent[index] = items[0]
                        else:
                            expect_unavailable(emit_row, row["reason"], source, index)
                    row_requests[name] = independent
                    assert endpoint.packet == packet
                    assert snapshot["played_character"]["character_id"] == PLAYER_FULL_ID

    try:
        asyncio.run(exercise())
    finally:
        driver.close()

    mapped = direct_requests["mapped-ordered-pcs"]
    assert len(mapped) == 4
    assert all(item.weight_q64 == 100000 and item.row_count == 1 for item in mapped)
    assert mapped[0].definition_identity == mapped[2].definition_identity
    assert mapped[0].source_ordinal == 0 and mapped[2].source_ordinal == 2
    signed = mapped[0].base_property_block
    values = [-100000, -(1 << 63), 0, (1 << 63) - 1]
    assert signed == {"keys_count": 4, "keys_u16": [554, 65535, 554, 0], "values_q64": values}
    assert mapped[2].base_property_block == signed
    assert mapped[1].base_property_block == {"keys_count": 0, "keys_u16": [], "values_q64": []}
    assert mapped[3].base_property_block["values_q64"] == [-250000]
    raw_mapped = packets["mapped-ordered-pcs"]["result"]["battle_terminal_transition"]["character_observations"][0]["current_person_state"][FIELD_NAME]
    assert raw_mapped["direct_rows"][0]["properties"]["values_q64"] == [str(value) for value in values]
    assert raw_mapped["direct_rows"][0]["properties"]["keys_u16"] == [554, 65535, 554, 0]
    assert direct_requests["empty-direct-list"] == ()
    assert leaves["absent-carrier-fallback"]["requested_full_id_u32"] == 0xFFFFFFFF
    assert leaves["absent-carrier-fallback"]["carrier_present"] is False
    assert leaves["generation-mismatch-fallback"]["resolution_selection"] == "fallback"
    assert leaves["generation-mismatch-fallback"]["requested_full_id_u32"] == 0x03000001
    assert leaves["generation-mismatch-fallback"]["selected_full_id_u32"] == 0x05000002
    wrong_magic = leaves["wrong-selected-magic"]
    assert wrong_magic["admitted"] is False and wrong_magic["selected_magic_u32"] == 0
    assert wrong_magic["selected_full_id_u32"] is None
    assert leaves["fallback-id-sentinel"]["selected_full_id_u32"] == 0xFFFFFFFF
    assert direct_requests["wrong-selected-magic"] == direct_requests["fallback-id-sentinel"] == ()
    partial = leaves["row-values-partial"]
    assert partial["direct_rows"][0]["properties"]["keys_u16"] == [554, 65535, 554, 0]
    assert partial["direct_rows"][0]["properties"]["values_q64"] is None
    assert sorted(row_requests["row-values-partial"]) == [1, 3]
    assert row_requests["row-values-partial"][1].base_property_block["keys_count"] == 0
    assert row_requests["row-values-partial"][3].base_property_block["values_q64"] == [-250000]
    for name in ("conditional-b8c-demanded", "conditional-bbc-demanded"):
        assert leaves[name]["conditional_reason"] == CONDITIONAL_GAP
        assert leaves[name]["conditional_occurrence_count"] is None
        assert len(direct_requests[name]) == 4
    assert leaves["conditional-b8c-demanded"]["conditional_b8c_count_i32"] == 1
    assert leaves["conditional-b8c-demanded"]["conditional_bbc_count_i32"] is None
    assert leaves["conditional-bbc-demanded"]["conditional_b8c_count_i32"] == 0
    assert leaves["conditional-bbc-demanded"]["conditional_bbc_count_i32"] == -1
    assert leaves["negative-direct-count"]["direct_count_i32"] == -1
    assert leaves["negative-direct-count"]["direct_rows"] == []
    assert len(endpoint.requests) == len(endpoint.delivered) == 10
    assert driver.state._command_results == {}
    assert packets == originals
