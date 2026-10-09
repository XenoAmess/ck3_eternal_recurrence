"""AUTHORED_NOTRUN: three new preparation-Model worlds, one registered compound.

Root produces only these three whole packets. Their production sidecars pass
unchanged through registered MCP, Service and NativeDriver. No older producer
or registered compound is invoked.
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
    emit_captured_person_preparation_model_12004,
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


WIRE_ENV = "CK3_PERSON_PREPARATION_MODEL_12004_MCP_WIRE_DIR"
SUBJECT, PUBLIC_REVISION, NATIVE_REVISION, DATE_RAW = 0x04000003, 97, 49, 53236632
TOOL = "ck3_query_battle_terminal_transition_v1"
CASES = (
    "historical-preparation-model-before-original-mutation",
    "preparation-model-owner-unread-numerical-ready",
    "new-context-fresh-preparation-model",
)
BASELINE_A = {"keys_count": 3, "keys_u16": [129, 97, 111],
              "values_q64": [100000, 0, -25000]}
BASELINE_B = {"keys_count": 2, "keys_u16": [222, 129], "values_q64": [75, -25]}
RAW_COUNTS = [7, -3, 0, 2**31 - 1, -1, -(2**31)]
ORDINALS = [0, 1, 2, 3, 5, 6, 7, 8, 10, 11]
WEIGHTS = [700000, 800000, -300000, -200000, 100000,
           214748364700000, -214748364800000, -100000,
           -214748364800000, -214748364700000]


def _unavailable(callback):
    try:
        callback()
    except ValueError as error:
        assert "preparation_model_owner_unread" in str(error)
        return
    raise AssertionError("unread preparation owner became a complete association")


class _WholePacketEndpoint:
    pipe_name = "offline-person-preparation-model-whole-packets"

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


def test_person_preparation_model_12004_registered_mcp_whole_packets():
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
        "snapshot_id": "person-preparation-model-paused-revision49",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": 29829, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-preparation-model-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }
    leaves, associations, projections = {}, {}, {}

    async def exercise():
        # Only the paused semantic frame is supplied. Query execution, native
        # result ingress, sidecar binding and domain normalization remain real.
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
                    observed, = frame["character_observations"]
                    assert leaf["character_id"] == observed["character_id"] == SUBJECT
                    assert leaf["capture_observed"] is True
                    assert leaf["capture_complete"] is True
                    assert leaf["ready"] is True and leaf["raw_counts_ready"] is True
                    assert leaf["capture_sequence"] == (2 if name == CASES[2] else 1)
                    assert leaf["capture_date_raw"] == DATE_RAW
                    assert leaf["capture_thread_id"] == leaf["query_thread_id"]
                    assert leaf["aggregate_postimage_inputs_ready"] is True
                    assert leaf["aggregate_postimage_comparison_ready"] is True
                    assert leaf["actual_model_write_performed"] is False
                    assert leaf["full_helper_ready"] is False
                    assert [stage["raw_count_i32"] for stage in leaf["stages"]] == RAW_COUNTS
                    preparation = leaf["preparation_model"]
                    assert preparation == raw_leaf["preparation_model"]
                    assert preparation["observed"] is True
                    assert preparation["context_offset"] == 16
                    assert preparation["owner_offset"] == 8
                    assert preparation["source_stage"] == "before_first_count_callback"
                    assert preparation["model_identity"] == hex(int(leaf["context_identity"], 16) - 0x10)
                    current = observed["current_person_state"]["following_2922680"]
                    assert current["character_id"] == SUBJECT
                    assert current["character_identity"] == leaf["character_identity"]
                    assert current["selected_model_identity"] != preparation["model_identity"]
                    assert current["destination_pc_identity"] == hex(int(current["selected_model_identity"], 16) + 0x10)
                    partial = name == CASES[1]
                    assert preparation["ready"] is (not partial)
                    if partial:
                        assert preparation["reason"] == "preparation_model_owner_unread"
                        assert preparation["owner_character_identity"] is None
                        assert preparation["owner_character_id"] is None
                        assert preparation["owner_matches_capture"] is None
                        _unavailable(lambda: emit_captured_person_preparation_model_12004(section))
                    else:
                        assert preparation["reason"] is None
                        assert preparation["owner_character_identity"] == leaf["character_identity"]
                        assert preparation["owner_character_id"] == SUBJECT
                        assert preparation["owner_matches_capture"] is True
                        association = emit_captured_person_preparation_model_12004(section)
                        for key in ("model_identity", "owner_character_identity", "owner_character_id",
                                    "owner_matches_capture", "context_offset", "owner_offset", "source_stage"):
                            assert association[key] == preparation[key]
                        for key in ("capture_sequence", "capture_date_raw", "capture_thread_id", "context_identity"):
                            assert association[key] == leaf[key]
                        assert association["character_id"] == SUBJECT
                        assert association["historical_capture"] is True
                        assert association["actual_model_write_performed"] is False
                        assert association["full_helper_ready"] is False
                        associations[name] = association
                    # The partial association deliberately leaves the old
                    # captured numerical inputs and composition usable.
                    requests = emit_captured_person_six_stage_requests_12004(section)
                    assert [row["source_ordinal"] for row in requests] == ORDINALS
                    assert [row["weight_q100000"] for row in requests] == WEIGHTS
                    assert all(row["property_block"]["keys_count"] == 0 for row in requests)
                    baseline = emit_captured_person_pre_six_aggregate_12004(section)
                    expected_baseline = BASELINE_B if name == CASES[2] else BASELINE_A
                    for key, value in expected_baseline.items():
                        assert baseline["property_block"][key] == value
                    projection = compose_captured_six_stage_postimage_12004(section)
                    assert projection["composition_kind"] == "captured_pre_six_aggregate_and_natural_appends"
                    assert projection["source_ordinals"] == ORDINALS
                    assert projection["keys_u16"] == expected_baseline["keys_u16"]
                    assert projection["values_q64"] == expected_baseline["values_q64"]
                    assert projection["completion_observation_ready"] is True
                    assert projection["completion_matches_composition"] is True
                    assert projection["capture_sequence"] == leaf["capture_sequence"]
                    assert leaf["pre_six_aggregate"]["pc"]["identity"] == hex(int(leaf["context_identity"], 16) + 0x68)
                    assert leaf["post_six_aggregate"]["pc"]["identity"] == leaf["pre_six_aggregate"]["pc"]["identity"]
                    projections[name], leaves[name] = projection, leaf
                    assert endpoint.packet == packet

    try:
        asyncio.run(exercise())
        assert len(endpoint.requests) == len(endpoint.delivered) == len(CASES) == 3
        assert driver.state._command_results == {}
        assert packets == originals
        assert projections[CASES[1]]["historical_postimage_ready"] is True
        assert len(associations) == 2 and leaves[CASES[2]]["capture_sequence"] == 2
        print(json.dumps({
            "status": "GREEN", "fresh_native_worlds": 3, "whole_packets": 3,
            "registered_person_mcp_cases": 3, "registered_tool": TOOL,
            "real_service": "GameplayBridgeService",
            "real_driver": "NativeHeadlessGameplayDriver",
            "native_payload_rewritten": False, "historical_model_associations": 2,
            "partial_owner_numerical_ready_cases": 1,
            "fresh_model_recapture_cases": 1, "baseline_composition_cases": 3,
            "old_native_producer_replayed": False, "full_person_ready": False,
            "entry_ready": False, "full_helper_ready": False,
            "actual_model_write_performed": False, "new_g2_credit": 0,
        }))
    finally:
        driver.close()
