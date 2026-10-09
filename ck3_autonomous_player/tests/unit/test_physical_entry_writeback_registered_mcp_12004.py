"""AUTHORED_NOTRUN: one new physical Entry whole packet through registered MCP.

The native producer exercises the actual writer observer and whole serializer.
This compound consumes its untouched body through real Service/NativeDriver
and checks the Service-returned per-Ci/wrapper/postwrite numerical projection.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge.combat_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
    query_combat_simulation_inputs_step,
)
from xar_autoplayer.bridge.knight_stat_consumption_contract_12004 import (
    normalize_knight_stat_consumption_12004,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.simulation.knight_stat_consumption_12004 import (
    project_knight_stat_consumption_12004,
)


WIRE_ENV = "CK3_PHYSICAL_ENTRY_WRITEBACK_12004_MCP_WIRE_DIR"
WHOLE_BASENAME = "physical-entry-writeback-12004-whole.json"
TOOL = "ck3_query_combat_simulation_inputs"
PUBLIC_REVISION, NATIVE_REVISION, DATE_RAW = 97, 49, 53236632
ATTACKER, DEFENDER, WAR_ID = 16777217, 16777218, 16777217
TARGET, ENTRY_PROVINCE = 101, 100
PROPERTY_KEYS = list(range(0xC1, 0xCA))
OPERANDS = [100000, 0, 0, -200000, -300000, 0, 400000, -500000, 600000]
MODIFIERS = [-25000, 0, 0, -10000, 0, 0, 0, 0, 0]
CACHE_FIELDS = ("max_size", "siege_value_raw", "damage_raw", "toughness_raw", "pursuit_raw", "screen_raw")
OBSERVED_CACHE = dict(zip(CACHE_FIELDS, (17, -111, 28500000, 2850000, 222, -333)))
PROJECTED_CACHE = dict(zip(CACHE_FIELDS, (0, 0, 28500000, 2850000, 0, 0)))
PROJECTED_MATCHES = dict(zip(CACHE_FIELDS, (False, False, True, True, False, False)))
LINKED, SELECTED, REGIMENT = 0x03000001, 0x04000002, 0x06000004
WRITER_RETURN = 18446744073709551283


class _WholePacketEndpoint:
    pipe_name = "offline-physical-entry-writeback-whole-packet"

    def __init__(self, step, packet):
        self.step, self.packet = step, deepcopy(packet)
        self.on_frame = None
        self.requests, self.delivered = [], []

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def send(self, request):
        assert request["type"] == "execute_step" and request["protocol_version"] == 1
        assert request["step"] == self.step
        assert request["expected_revision"] == NATIVE_REVISION
        self.requests.append(deepcopy(request))
        response = deepcopy(self.packet)
        response["request_id"] = request["request_id"]
        assert {key: value for key, value in response.items() if key != "request_id"} == {
            key: value for key, value in self.packet.items() if key != "request_id"}
        self.delivered.append(deepcopy(response))
        self.on_frame(response)

    def transport_error(self):
        return None

    def close(self):
        pass


def _paused_snapshot(hello):
    def army(army_id, owner, province, controllable):
        return {"army_id": army_id, "owner_character_id": owner, "soldiers": 1000,
                "current_province_id": province, "move_target_province_id": None,
                "controllable": controllable}
    attacker = army(ATTACKER, 707, ENTRY_PROVINCE, True)
    defender = army(DEFENDER, 808, TARGET, False)
    war = {
        "war_id": WAR_ID, "player_side": "attacker",
        "primary_opponent_character_id": 808, "player_is_primary_war_leader": True,
        "enemy_primary_default_raise_province_id": None,
        "player_relative_war_score": 0,
        "allied_armies": [deepcopy(attacker)], "enemy_armies": [defender],
        "war_objective_province_ids": [], "objective_province_states": [],
        "targeted_title_ids": [],
    }
    return {
        "snapshot_id": "physical-entry-writeback-paused-revision49",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": 707, "alive": True},
        "player_armies": [attacker], "active_wars": [war],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-physical-entry-writeback-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }


def _json_value(value):
    return json.loads(json.dumps(value))


def _wire_numbers(value):
    if isinstance(value, list):
        return [_wire_numbers(item) for item in value]
    if isinstance(value, dict):
        return {key: _wire_numbers(item) for key, item in value.items()}
    if isinstance(value, str):
        if value.startswith(("0x", "0X")):
            return int(value, 16)
        digits = value[1:] if value.startswith("-") else value
        if digits and digits.isascii() and digits.isdecimal():
            return int(value, 10)
    return value


def _assert_physical_writeback(consumption, projection):
    assert consumption["configured"] is True
    assert consumption["observer_installed"] is False
    assert consumption["oldest_available_sequence"] == 1
    assert consumption["latest_sequence"] == 2
    assert consumption["overwritten_events"] == 0
    assert len(consumption["events"]) == len(projection["events"]) == 2
    assert projection["physical_entry_associated_event_count"] == 1
    assert projection["entry_association_proven"] is True
    for claim in ("historical_stage_equivalence_proven", "actual_model_write_performed",
                  "full_person_ready", "full_entry_ready"):
        assert projection[claim] is False
    for index, (event, result) in enumerate(zip(consumption["events"], projection["events"])):
        assert event["sequence"] == result["sequence"] == index + 1
        assert event["observed_date_raw"] == DATE_RAW
        assert event["wrapper_caller_return_rva"] == 0x2634509
        assert event["linked_character_id"] == LINKED
        assert event["linked_prowess_points"] == 3
        assert event["loaded_damage_multiplier"] == 100
        assert event["loaded_toughness_multiplier"] == 10
        assert event["regiment_id"] == REGIMENT
        assert event["target_province_id"] == TARGET
        assert result["selected_character_id"] == SELECTED != LINKED
        assert result["selected_character_ids"] == [SELECTED] * 9
        assert event["observed_output"]["ready"] is True
        assert event["observed_output"]["reason"] is None
        for field, value in OBSERVED_CACHE.items():
            assert event["observed_output"][field] == value
        contexts = event["contexts"]
        assert len(contexts) == 9
        assert [row["property_key"] for row in contexts] == PROPERTY_KEYS
        assert [row["operand_raw"] for row in contexts] == OPERANDS
        assert {row["selected_character_id"] for row in contexts} == {SELECTED}
        assert len({row["selected_character_identity"] for row in contexts}) == 1
        for ci, row in enumerate(contexts):
            pc = row["consumed_pc"]
            assert pc["ready"] is True
            assert pc["identity"] == row["context_identity"] + 0x68
            assert pc["weight_q100000"] == 0
            assert pc["count_i32"] == 9
            assert pc["properties"]["keys_u16"] == PROPERTY_KEYS
            assert pc["properties"]["values_q64"] == MODIFIERS
            for field in ("preparation_capture_sequence", "preparation_model_identity",
                          "preparation_context_identity", "preparation_owner_character_id",
                          "context_matches_preparation", "owner_matches_preparation",
                          "pc_matches_preparation_post"):
                assert row[field] is None
            detail = result["property_inputs"][ci]
            assert detail["consumed_pc_identity"] == pc["identity"]
            assert detail["context_identity"] == row["context_identity"]
            assert detail["operand_raw"] == OPERANDS[ci]
            assert detail["branch"] == ("zero_operand_skips_property" if OPERANDS[ci] == 0
                                         else "actual_consumed_pc_mode0")
        # The nine actual native calls include the zero-operand occurrences.
        assert result["consumed_contexts"] == contexts
        assert result["ready"] is True and result["missing_inputs"] == []
        assert result["modifier_raw"] == [-25000, None, None, -10000, 0, None, 0, 0, 0]
        assert result["operand_raw"] == OPERANDS
        assert result["projected_effectiveness_raw"] == 95000
        assert result["projected_output"] == PROJECTED_CACHE
        assert result["observed_output"] == event["observed_output"]
        assert result["comparison_ready"] is True
        # Nonzero ancillary cache fields are typed transfer/ABI diagnostics;
        # they are not claimed as native Knight-prefix arithmetic outputs.
        assert result["field_matches"] == PROJECTED_MATCHES
        assert result["matches_observed_output"] is False
        assert result["entry_association_proven"] is event["entry_association_proven"]
        assert result["physical_entry_writeback"] == event["physical_entry_writeback"]
        for claim in ("historical_stage_equivalence_proven", "shared_native_context_claimed",
                      "actual_model_write_performed", "full_person_ready", "full_entry_ready"):
            assert result[claim] is False
        if index == 0:
            assert event["origin"] == "native_physical_entry_writer"
            assert event["entry_association_proven"] is True
            writeback = event["physical_entry_writeback"]
            assert writeback["writer_sequence"] == 1
            assert type(writeback["entry_identity"]) is int and writeback["entry_identity"] > 0
            assert type(writeback["province_identity"]) is int and writeback["province_identity"] > 0
            assert writeback["regiment_id"] == REGIMENT
            assert writeback["province_id"] == TARGET
            assert writeback["regiment_member_at_query"] is True
            assert writeback["original_return_value"] == WRITER_RETURN > 2**63 - 1
            assert writeback["entry_cache"]["screen_raw"] == -333
            assert writeback["original_return_value"] != writeback["entry_cache"]["screen_raw"]
            assert writeback["output_cache_identity_matches_entry"] is False
            assert event["output_cache_identity"] not in (
                writeback["entry_identity"], writeback["entry_identity"] + 0x30)
            assert writeback["entry_cache"]["ready"] is True
            assert writeback["entry_cache"]["reason"] is None
            for field, value in OBSERVED_CACHE.items():
                assert writeback["entry_cache"][field] == value
            assert writeback["wrapper_output_comparison_ready"] is True
            assert writeback["wrapper_output_field_matches"] == [True] * 6
            assert writeback["wrapper_output_matches_entry_cache"] is True
            assert result["physical_entry_comparison_ready"] is True
            assert result["physical_entry_field_matches"] == PROJECTED_MATCHES
            assert result["projection_matches_physical_entry_cache"] is False
            assert result["wrapper_output_physical_comparison_ready"] is True
            assert result["wrapper_output_matches_physical_entry_cache"] is True
        else:
            assert event["origin"] == "bridge_query_scratch"
            assert event["entry_association_proven"] is False
            assert event["physical_entry_writeback"] is None
            assert result["physical_entry_comparison_ready"] is False
            assert result["physical_entry_field_matches"] == dict.fromkeys(CACHE_FIELDS)
            assert result["projection_matches_physical_entry_cache"] is None
            assert result["wrapper_output_physical_comparison_ready"] is False
            assert result["wrapper_output_matches_physical_entry_cache"] is None


def test_physical_entry_writeback_registered_mcp_12004_whole():
    from mcp import Client

    packet = json.loads((Path(os.environ[WIRE_ENV]) / WHOLE_BASENAME).read_bytes())
    original = deepcopy(packet)
    step = query_combat_simulation_inputs_step(TARGET, ENTRY_PROVINCE, [ATTACKER], [DEFENDER])
    assert packet["type"] == "command_result" and packet["ok"] is True
    assert packet["result"]["step"] == step
    assert packet["result"]["accepted"] is True
    assert packet["result"]["query_sequence"] == 1
    raw_consumption = packet["result"]["combat_simulation_inputs"]["knight_stat_consumption_v1"]
    endpoint = _WholePacketEndpoint(step, packet)
    driver = NativeHeadlessGameplayDriver(endpoint=endpoint, episode_projection="native_campaign")
    hello = {
        "type": "hello", "protocol_version": 1, "pid": 1,
        "capabilities": ["game.state.snapshot", QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY],
        "expected_ck3_version": CK3_12004.game_version,
        "expected_ck3_sha256": CK3_12004.executable_sha256,
    }
    assert driver.state.ingest(hello) == "hello"
    snapshot = _paused_snapshot(hello)

    async def exercise():
        with patch.object(driver, "take_snapshot", side_effect=lambda **kwargs: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                assert TOOL in {tool.name for tool in (await client.list_tools()).tools}
                response = await client.call_tool(TOOL, {
                    "target_province_id": TARGET, "attacker_entry_province_id": ENTRY_PROVINCE,
                    "attacker_army_ids": [ATTACKER], "defender_army_ids": [DEFENDER],
                    "expected_revision": PUBLIC_REVISION,
                })
                assert response.is_error is False, response.content
                actual = response.structured_content
                assert actual["status"] == packet["result"]["status"]
                assert actual["query_sequence"] == 1
                assert actual["queried_snapshot_id"] == snapshot["snapshot_id"]
                assert actual["queried_revision"] == PUBLIC_REVISION
                assert actual["queried_native_revision"] == NATIVE_REVISION
                consumption = actual["combat_simulation_inputs"]["knight_stat_consumption_v1"]
                assert consumption == normalize_knight_stat_consumption_12004(raw_consumption)
                expected_consumption = _wire_numbers(deepcopy(raw_consumption))
                for event in expected_consumption["events"]:
                    event.setdefault("physical_entry_writeback", None)
                assert consumption == expected_consumption
                assert driver._combat_simulation_inputs_query["combat_simulation_inputs"][
                    "knight_stat_consumption_v1"] == consumption
                projection = actual["knight_stat_consumption_projection_v1"]
                assert projection == _json_value(project_knight_stat_consumption_12004(consumption))
                _assert_physical_writeback(consumption, projection)
                assert actual["monte_carlo_ready"] is False
                assert "win_probability" not in actual
                return consumption, projection

    try:
        consumption, projection = asyncio.run(exercise())
        assert len(endpoint.requests) == len(endpoint.delivered) == 1
        assert packet == original and endpoint.packet == original
        assert driver.state._command_results == {}
        print(json.dumps({
            "status": "GREEN", "whole_packets": 1, "registered_mcp_calls": 1,
            "observed_wrapper_events": len(consumption["events"]),
            "projected_events": len(projection["events"]),
            "physical_entry_associated_events": 1, "query_scratch_unassociated_events": 1,
            "three_way_cache_field_comparisons": 6, "unsigned_writer_return_retained": True,
            "registered_tool": TOOL, "real_service": "GameplayBridgeService",
            "real_driver": "NativeHeadlessGameplayDriver", "service_projection_consumed": True,
            "native_payload_rewritten": False, "old_native_producer_replayed": False,
            "full_person_ready": False, "full_entry_ready": False,
            "monte_carlo_ready": False, "actual_model_write_performed": False,
            "new_g2_credit": 0,
        }))
    finally:
        driver.close()
