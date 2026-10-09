"""AUTHORED_NOTRUN: one new whole combat packet through registered MCP.

The producer exercises the real consumption observers and whole serializer.
This compound keeps that body unchanged and uses real Service/NativeDriver
query ingestion before projecting the observed per-call numerical inputs.
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
    project_consumed_knight_stat_event_12004,
    project_knight_stat_consumption_12004,
)


WIRE_ENV = "CK3_KNIGHT_STAT_CONSUMPTION_12004_MCP_WIRE_DIR"
WHOLE_BASENAME = "knight-stat-consumption-12004-whole.json"
TOOL = "ck3_query_combat_simulation_inputs"
PUBLIC_REVISION, NATIVE_REVISION, DATE_RAW = 97, 49, 53236632
ATTACKER, DEFENDER, WAR_ID = 16777217, 16777218, 16777217
TARGET, ENTRY_PROVINCE = 101, 100
PROPERTY_KEYS = list(range(0xC1, 0xCA))
OPERANDS = [100000, 0, 0, -200000, -300000, 0, 400000, -500000, 600000]
MODIFIERS = [-25000, 0, 0, -10000, 0, 0, 0, 0, 0]
LINKED, SELECTED_A, SELECTED_B = 0x03000001, 0x04000002, 0x05000003


class _WholePacketEndpoint:
    pipe_name = "offline-knight-stat-consumption-whole-packet"

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


def _army(army_id, owner, province, controllable):
    return {
        "army_id": army_id, "owner_character_id": owner, "soldiers": 1000,
        "current_province_id": province, "move_target_province_id": None,
        "controllable": controllable,
    }


def _paused_snapshot(hello):
    attacker = _army(ATTACKER, 707, ENTRY_PROVINCE, True)
    defender = _army(DEFENDER, 808, TARGET, False)
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
        "snapshot_id": "knight-stat-consumption-paused-revision49",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": 707, "alive": True},
        "player_armies": [attacker], "active_wars": [war],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-knight-stat-consumption-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }


def _wire_numbers(value):
    """Compare every retained field after the wire's integer representation."""
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


def _cache(damage, toughness):
    return {"max_size": 0, "siege_value_raw": 0, "damage_raw": damage,
            "toughness_raw": toughness, "pursuit_raw": 0, "screen_raw": 0}


def _json_value(value):
    """Represent a direct helper result as the MCP JSON transport does."""
    return json.loads(json.dumps(value))


def _assert_literal_events(consumption, projection):
    """Check the two new native worlds' literal inputs and independent results."""
    assert consumption["configured"] is True
    assert consumption["observer_installed"] is False
    assert consumption["oldest_available_sequence"] == 1
    assert consumption["latest_sequence"] == 2
    assert consumption["overwritten_events"] == 0
    assert len(consumption["events"]) == len(projection["events"]) == 2
    for claim in ("entry_association_proven", "historical_stage_equivalence_proven",
                  "actual_model_write_performed", "full_person_ready", "full_entry_ready"):
        assert projection[claim] is False
    for index, (event, result) in enumerate(zip(consumption["events"], projection["events"])):
        assert event["sequence"] == result["sequence"] == index + 1
        assert event["observed_date_raw"] == DATE_RAW
        assert event["wrapper_caller_return_rva"] == 0x2634509
        assert event["linked_character_id"] == result["linked_character_id"] == LINKED
        assert event["linked_prowess_points"] == 3
        assert event["loaded_damage_multiplier"] == 100
        assert event["loaded_toughness_multiplier"] == 10
        assert type(event["output_cache_identity"]) is int and event["output_cache_identity"] > 0
        assert type(event["native_return_identity"]) is int
        assert event["entry_association_proven"] is False
        selected = SELECTED_A if index == 0 else SELECTED_B
        assert selected != LINKED
        assert result["selected_character_id"] == selected
        assert result["selected_character_ids"] == [selected] * 9
        contexts = event["contexts"]
        assert len(contexts) == 9
        assert [row["property_key"] for row in contexts] == PROPERTY_KEYS
        assert [row["operand_raw"] for row in contexts] == OPERANDS
        assert {row["selected_character_id"] for row in contexts} == {selected}
        assert len({row["selected_character_identity"] for row in contexts}) == 1
        assert result["operand_raw"] == OPERANDS
        assert result["consumed_contexts"] == contexts
        assert result["source_stage"] == "native_wrapper_consumed_per_ci_contexts"
        assert result["observed_output"] == event["observed_output"]
        for claim in ("entry_association_proven", "historical_stage_equivalence_proven",
                      "shared_native_context_claimed", "actual_model_write_performed",
                      "full_person_ready", "full_entry_ready"):
            assert result[claim] is False
        for ci, (row, detail) in enumerate(zip(contexts, result["property_inputs"])):
            assert type(row["context_identity"]) is int
            assert row["consumed_pc"]["identity"] == row["context_identity"] + 0x68
            assert row["consumed_pc"]["weight_q100000"] == 0
            assert row["consumed_pc"]["count_i32"] == 9
            assert row["consumed_pc"]["properties"]["keys_u16"] == PROPERTY_KEYS
            assert detail["property_key"] == PROPERTY_KEYS[ci]
            assert detail["operand_raw"] == OPERANDS[ci]
            assert detail["context_identity"] == row["context_identity"]
            assert detail["consumed_pc_identity"] == row["consumed_pc"]["identity"]
            if OPERANDS[ci] == 0:
                # All nine native getter calls remain observed above. This
                # branch skips only the projector's zero-operand PC lookup.
                assert detail["branch"] == "zero_operand_skips_property"
                assert detail["lookups"] == []
            elif index == 1 and ci == 3:
                assert detail["branch"] == "consumed_pc_unavailable"
            else:
                assert detail["branch"] == "actual_consumed_pc_mode0"
                assert len(detail["lookups"]) == 1
                assert detail["lookups"][0]["key"] == PROPERTY_KEYS[ci]
            if index == 0:
                assert row["preparation_capture_sequence"] == 1
                assert row["preparation_owner_character_id"] == SELECTED_A
                assert row["preparation_model_identity"] == row["preparation_context_identity"] - 0x10
                assert row["owner_matches_preparation"] is True
                assert row["context_matches_preparation"] is (ci != 4)
                assert row["pc_matches_preparation_post"] is (ci != 4)
                assert row["consumed_pc"]["ready"] is True
                expected = MODIFIERS.copy()
                if ci == 4:
                    expected[4] = 15000
                assert row["consumed_pc"]["properties"]["values_q64"] == expected
            else:
                for field in ("preparation_capture_sequence", "preparation_model_identity",
                              "preparation_context_identity", "preparation_owner_character_id",
                              "context_matches_preparation", "owner_matches_preparation",
                              "pc_matches_preparation_post"):
                    assert row[field] is None
                assert row["consumed_pc"]["ready"] is (ci != 3)
                if ci == 3:
                    assert row["consumed_pc"]["properties"]["values_q64"] is None
                    assert row["consumed_pc"]["reason"] == "pc_values_unread"
                else:
                    assert row["consumed_pc"]["properties"]["values_q64"] == MODIFIERS
        assert event["observed_output"]["ready"] is True
        assert event["observed_output"]["reason"] is None
        if index == 0:
            assert event["origin"] == result["origin"] == "bridge_query_scratch"
            assert event["regiment_id"] == 0x06000004
            assert event["target_province_id"] == TARGET
            assert len({row["context_identity"] for row in contexts}) == 2
            assert result["ready"] is True and result["missing_inputs"] == []
            assert result["modifier_raw"] == [-25000, None, None, -10000, 15000, None, 0, 0, 0]
            assert result["projected_effectiveness_raw"] == 50000
            assert result["projected_output"] == _cache(15000000, 1500000)
            for key, value in _cache(15000000, 1500000).items():
                assert event["observed_output"][key] == value
            assert result["comparison_ready"] is True
            assert all(value is True for value in result["field_matches"].values())
            assert result["matches_observed_output"] is True
            # Substituting the first context for C5 would yield 95000 rather
            # than 50000. Its actual independent positive modifier is needed.
            assert contexts[0]["consumed_pc"]["properties"]["values_q64"][4] == 0
            assert contexts[4]["consumed_pc"]["properties"]["values_q64"][4] == 15000
        else:
            assert event["origin"] == result["origin"] == "native_wrapper_output_unclassified"
            assert event["regiment_id"] is None and event["target_province_id"] is None
            assert result["ready"] is False and result["missing_inputs"]
            assert result["modifier_raw"] == [-25000, None, None, None, 0, None, 0, 0, 0]
            assert result["projected_effectiveness_raw"] is None
            assert result["projected_output"] is None
            for key, value in _cache(28500000, 2850000).items():
                assert event["observed_output"][key] == value
            assert result["comparison_ready"] is False
            assert all(value is None for value in result["field_matches"].values())
            assert result["matches_observed_output"] is None


def test_knight_stat_consumption_registered_mcp_12004_whole_packets():
    from mcp import Client

    path = Path(os.environ[WIRE_ENV]) / WHOLE_BASENAME
    packet = json.loads(path.read_bytes())
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
        # Supply only the synthetic paused semantic frame. The registered tool,
        # Service, Driver command path and native result normalizer stay real.
        with patch.object(driver, "take_snapshot", side_effect=lambda **kwargs: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                assert TOOL in {tool.name for tool in (await client.list_tools()).tools}
                response = await client.call_tool(TOOL, {
                    "target_province_id": TARGET,
                    "attacker_entry_province_id": ENTRY_PROVINCE,
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
                inputs = actual["combat_simulation_inputs"]
                consumption = inputs["knight_stat_consumption_v1"]
                assert consumption == normalize_knight_stat_consumption_12004(raw_consumption)
                assert consumption == _wire_numbers(raw_consumption)
                assert driver._combat_simulation_inputs_query["combat_simulation_inputs"][
                    "knight_stat_consumption_v1"] == consumption
                projection = actual["knight_stat_consumption_projection_v1"]
                assert projection == _json_value(project_knight_stat_consumption_12004(consumption))
                assert projection["events"] == [
                    _json_value(project_consumed_knight_stat_event_12004(event))
                    for event in consumption["events"]]
                _assert_literal_events(consumption, projection)
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
            "ready_numerical_events": 1, "partial_pc_observed_output_retained_events": 1,
            "distinct_per_ci_context_numerical_cases": 1,
            "registered_tool": TOOL, "real_service": "GameplayBridgeService",
            "real_driver": "NativeHeadlessGameplayDriver",
            "service_projection_consumed": True,
            "native_payload_rewritten": False, "old_native_producer_replayed": False,
            "entry_association_proven": False, "full_person_ready": False,
            "full_entry_ready": False, "monte_carlo_ready": False,
            "actual_model_write_performed": False, "new_g2_credit": 0,
        }))
    finally:
        driver.close()
