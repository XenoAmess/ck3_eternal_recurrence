"""AUTHORED_NOTRUN: six new baseline/completion worlds, one registered compound.

Root runs the native producer and this node once. Each unchanged whole packet
and its production sidecar pass through real MCP, Service and NativeDriver.
No Native62 producer, seven-world consumer or original native callback is replayed.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge.battle_person_six_stage_capture_12004 import (
    FIELD_NAME,
    emit_captured_person_pre_six_aggregate_12004,
    emit_captured_person_six_stage_requests_12004,
    normalize_person_six_stage_query_12004,
    select_person_six_stage_capture_12004,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.simulation.battle_person_six_stage_postimage_12004 import (
    compose_captured_six_stage_postimage_12004,
)


WIRE_ENV = "CK3_PERSON_PRE_SIX_BASELINE_12004_MCP_WIRE_DIR"
SUBJECT, PUBLIC_REVISION, NATIVE_REVISION, DATE_RAW = 0x04000003, 97, 49, 53236632
TOOL = "ck3_query_battle_terminal_transition_v1"
CASES = (
    "baseline-before-original-mutation",
    "baseline-observed-empty",
    "baseline-values-unread-six-ready",
    "observe-bypass-lacks-baseline",
    "wrong-caller-original-once",
    "same-owner-new-capture-fresh-baseline",
)
BASELINE_A = {"keys_count": 4, "keys_u16": [129, 97, 129, 111],
              "values_q64": [2**63 - 9, 0, -(2**63 - 9), 4294967296]}
BASELINE_B = {"keys_count": 3, "keys_u16": [222, 129, 222], "values_q64": [75, 0, -75]}
RAW_COUNTS = [7, -3, 0, 2**31 - 1, -1, -(2**31)]
ORDINALS = [0, 1, 2, 3, 5, 6, 7, 8, 10, 11]
WEIGHTS = [700000, 800000, -300000, -200000, 100000,
           214748364700000, -214748364800000, -100000,
           -214748364800000, -214748364700000]


def _wire_numbers(value):
    if isinstance(value, list):
        return [_wire_numbers(item) for item in value]
    if isinstance(value, dict):
        return {key: ([int(item) for item in item_value] if item_value is not None else None)
                if key == "values_q64" else
                (int(item_value) if item_value is not None else None)
                if key == "weight_q100000" else _wire_numbers(item_value)
                for key, item_value in value.items()}
    return value


def _unavailable(callback):
    try:
        callback()
    except ValueError:
        return
    raise AssertionError("missing or partial baseline became a total postimage input")


class _WholePacketEndpoint:
    pipe_name = "offline-person-pre-six-baseline-whole-packets"

    def __init__(self, step):
        self.step, self.packet, self.on_frame = step, None, None
        self.requests, self.delivered = [], []

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def select(self, packet):
        self.packet = deepcopy(packet)

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

    def close(self):
        pass


def test_person_pre_six_baseline_12004_registered_mcp_whole_packets():
    from mcp import Client

    directory = Path(os.environ[WIRE_ENV])
    packets = {name: json.loads((directory / (name + ".json")).read_bytes()) for name in CASES}
    originals = deepcopy(packets)
    step = query_battle_terminal_transition_v1_step(None, None, None, [SUBJECT])
    endpoint = _WholePacketEndpoint(step)
    driver = NativeHeadlessGameplayDriver(endpoint=endpoint, episode_projection="native_campaign")
    hello = {
        "type": "hello", "protocol_version": 1, "pid": 1,
        "capabilities": ["game.state.snapshot", QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY],
        "expected_ck3_version": CK3_12004.game_version,
        "expected_ck3_sha256": CK3_12004.executable_sha256,
    }
    assert driver.state.ingest(hello) == "hello"
    snapshot = {
        "snapshot_id": "person-pre-six-baseline-paused-revision49",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": 29829, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-pre-six-baseline-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }
    leaves, projections = {}, {}

    async def exercise():
        # Match the qualified Native62 ingress recipe while accepting the scoped
        # readonly snapshot flag. No query, observer or normalizer is replaced.
        with patch.object(driver, "take_snapshot", side_effect=lambda **kwargs: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                assert TOOL in {tool.name for tool in (await client.list_tools()).tools}
                for sequence, name in enumerate(CASES, 1):
                    packet = packets[name]
                    assert packet["type"] == "command_result" and packet["ok"] is True
                    wire = packet["result"]
                    assert wire["step"] == step and wire["query_sequence"] == sequence
                    assert wire["snapshot_revision"] == NATIVE_REVISION
                    raw_leaf, = wire["person_six_stage_captures"]["character_captures"]
                    endpoint.select(packet)
                    response = await client.call_tool(TOOL, {
                        "prior_combat_id": None, "subject_public_cunit_id": None,
                        "after_terminal_sequence": None, "expected_revision": PUBLIC_REVISION,
                        "character_ids": [SUBJECT],
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
                    sidecar = actual["person_six_stage_captures"]
                    assert sidecar == normalize_person_six_stage_query_12004(
                        wire["person_six_stage_captures"],
                        expected_snapshot_revision=NATIVE_REVISION,
                        expected_observed_date_raw=DATE_RAW,
                        expected_character_ids=[SUBJECT],
                    )
                    leaf, = sidecar["character_captures"]
                    section = select_person_six_stage_capture_12004(sidecar, SUBJECT)
                    assert section[FIELD_NAME] == leaf
                    assert leaf["character_id"] == frame["character_observations"][0]["character_id"] == SUBJECT
                    assert leaf["actual_model_write_performed"] is False
                    assert leaf["full_helper_ready"] is False
                    for field in ("pre_six_aggregate", "post_six_aggregate"):
                        assert leaf[field] == _wire_numbers(raw_leaf[field])
                        assert leaf[field]["context_pc_offset"] == 104
                        assert leaf[field]["pc"]["weight_q100000"] is None
                    pre, post = leaf["pre_six_aggregate"], leaf["post_six_aggregate"]
                    assert pre["source_stage"] == "before_first_count_callback"
                    assert post["source_stage"] == "same_thread_capture_completion"
                    wrong = name == CASES[4]
                    missing = name == CASES[3] or wrong
                    partial = name == CASES[2]
                    total = not missing and not partial
                    assert leaf["capture_observed"] is (not wrong)
                    assert leaf["capture_complete"] is (not wrong)
                    assert leaf["raw_counts_ready"] is (not wrong)
                    assert leaf["ready"] is (not wrong)
                    assert leaf["capture_sequence"] == (0 if wrong else 2 if name == CASES[5] else 1)
                    assert pre["observed"] is (not missing)
                    assert pre["pc"]["ready"] is total
                    assert post["observed"] is (not wrong)
                    assert post["pc"]["ready"] is (not wrong)
                    assert leaf["aggregate_postimage_inputs_ready"] is total
                    assert leaf["aggregate_postimage_comparison_ready"] is total
                    if wrong:
                        assert leaf["character_identity"] is None and leaf["context_identity"] is None
                        _unavailable(lambda: emit_captured_person_six_stage_requests_12004(section))
                    else:
                        assert leaf["capture_thread_id"] == leaf["query_thread_id"]
                        assert [stage["raw_count_i32"] for stage in leaf["stages"]] == RAW_COUNTS
                        requests = emit_captured_person_six_stage_requests_12004(section)
                        assert [row["source_ordinal"] for row in requests] == ORDINALS
                        assert [row["weight_q100000"] for row in requests] == WEIGHTS
                        assert pre["pc"]["identity"] in (None, post["pc"]["identity"])
                        assert post["pc"]["identity"] == hex(int(leaf["context_identity"], 16) + 0x68)
                        if name in CASES[:2]:
                            assert all(row["property_block"]["keys_count"] == 0 for row in requests)
                        expected_post = [] if name == CASES[1] else [-50, 25] if name == CASES[5] else [44, 0, -44]
                        assert post["pc"]["properties"]["values_q64"] == expected_post
                    if not total:
                        _unavailable(lambda: emit_captured_person_pre_six_aggregate_12004(section))
                        _unavailable(lambda: compose_captured_six_stage_postimage_12004(section))
                        if partial:
                            assert pre["pc"]["count_i32"] == 4
                            assert pre["pc"]["properties"]["keys_u16"] == BASELINE_A["keys_u16"]
                            assert pre["pc"]["properties"]["values_q64"] is None
                            assert pre["pc"]["reason"] == "pc_values_unread"
                        elif missing:
                            assert pre["pc"]["identity"] is None and pre["pc"]["count_i32"] is None
                    else:
                        baseline = emit_captured_person_pre_six_aggregate_12004(section)
                        expected_baseline = BASELINE_A if name == CASES[0] else BASELINE_B if name == CASES[5] else {
                            "keys_count": 0, "keys_u16": [], "values_q64": []}
                        for key, value in expected_baseline.items():
                            assert baseline["property_block"][key] == value
                        projection = compose_captured_six_stage_postimage_12004(section)
                        projections[name] = projection
                        assert projection["composition_kind"] == "captured_pre_six_aggregate_and_natural_appends"
                        assert projection["source_ordinals"] == ORDINALS
                        assert projection["pre_six_baseline_observed"] is True
                        assert projection["historical_postimage_ready"] is True
                        assert projection["capture_sequence"] == leaf["capture_sequence"]
                        assert projection["baseline_pc_identity"] == pre["pc"]["identity"]
                        assert projection["completion_observation_ready"] is True
                        assert projection["completion_observation_source_stage"] == post["source_stage"]
                        assert projection["completion_pc_identity"] == post["pc"]["identity"]
                        assert projection["completion_matches_composition"] is (name == CASES[1])
                        if name in CASES[:2]:
                            # Actual admitted empty PCs leave the captured initial
                            # state intact; baseline absence is never seeded as zero.
                            assert projection["keys_u16"] == expected_baseline["keys_u16"]
                            assert projection["values_q64"] == expected_baseline["values_q64"]
                    leaves[name] = leaf
                    assert endpoint.packet == packet

    try:
        asyncio.run(exercise())
        assert len(endpoint.requests) == len(endpoint.delivered) == len(CASES) == 6
        assert driver.state._command_results == {}
        assert packets == originals
        assert projections[CASES[0]]["keys_u16"] == BASELINE_A["keys_u16"]
        assert projections[CASES[1]]["keys_u16"] == []
        assert leaves[CASES[2]]["ready"] is True and leaves[CASES[3]]["ready"] is True
        print(json.dumps({
            "status": "GREEN", "fresh_native_worlds": 6, "whole_packets": 6,
            "registered_person_mcp_cases": 6, "registered_tool": TOOL,
            "real_service": "GameplayBridgeService",
            "real_driver": "NativeHeadlessGameplayDriver",
            "native_payload_rewritten": False, "baseline_composition_cases": 3,
            "exact_baseline_only_cases": 2, "old_native_producer_replayed": False,
            "full_person_ready": False, "entry_ready": False,
            "full_helper_ready": False, "actual_model_write_performed": False,
            "new_g2_credit": 0,
        }))
    finally:
        driver.close()
