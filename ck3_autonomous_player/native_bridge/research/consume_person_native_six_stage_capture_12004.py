"""One Root-run compound: fresh native seven-world producer, sole Python consumer.

Source workers author this recipe without executing the producer or imports.
The packets are synthetic qualification evidence, never live Person evidence.
"""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.battle_person_six_stage_capture_12004 import (
    emit_captured_person_six_stage_occurrence_requests_12004,
    emit_captured_person_six_stage_requests_12004,
    normalize_person_six_stage_query_12004,
    select_person_six_stage_capture_12004,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    normalize_battle_terminal_transition_v1,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004

SUBJECT = 0x04000003
REVISION = 49
DATE_RAW = 53_236_632
PUBLIC_REVISION = 97
TOOL = "ck3_query_battle_terminal_transition_v1"
CASES = (
    "unobserved",
    "six-ordered-negative-zero-wrap-weight",
    "three-stages-incomplete",
    "one-admitted-pc-values-unread",
    "full-generation-not-borrowed",
    "owned-pcs-after-source-and-model-mutation",
    "other-caller-originals-once-rax-and-args",
)
RAW_COUNTS = [7, -3, 0, 2**31 - 1, -1, -(2**31)]
ORDINALS = [0, 1, 2, 3, 5, 6, 7, 8, 10, 11]
WEIGHTS = [700000, 800000, -300000, -200000, 100000,
           214748364700000, -214748364800000, -100000,
           -214748364800000, -214748364700000]


def unavailable(callback) -> None:
    try:
        callback()
    except ValueError:
        return
    raise AssertionError("partial native inputs were published as ready requests")


class WholePacketEndpoint:
    """Qualified Person-history transport pattern; only correlation is changed.

    Reuses tests/unit/test_person_native_title_tail_capture_12004_registered_mcp.py
    and its following2922680 endpoint pattern without importing or replaying any
    historical producer or test. Driver, Service and MCP remain real.
    """
    pipe_name = "offline-person-six-stage-whole-command"

    def __init__(self, step: str, packet: dict):
        self.step = step
        self.packet = deepcopy(packet)
        self.on_frame = None
        self.requests = []
        self.delivered = []

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def send(self, request):
        assert request["type"] == "execute_step" and request["protocol_version"] == 1
        assert request["step"] == self.step
        assert request["expected_revision"] == REVISION
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


async def consume_registered_person_mcp(packet: dict) -> dict:
    """Carry one fresh native whole packet through the modified real stack."""
    from mcp import Client

    original = deepcopy(packet)
    step = query_battle_terminal_transition_v1_step(None, None, None, [SUBJECT])
    assert packet["result"]["step"] == step
    endpoint = WholePacketEndpoint(step, packet)
    driver = NativeHeadlessGameplayDriver(endpoint=endpoint, episode_projection="native_campaign")
    hello = {
        "type": "hello", "protocol_version": 1, "pid": 1,
        "capabilities": ["game.state.snapshot", QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY],
        "expected_ck3_version": CK3_12004.game_version,
        "expected_ck3_sha256": CK3_12004.executable_sha256,
    }
    assert driver.state.ingest(hello) == "hello"
    snapshot = {
        "snapshot_id": "person-six-stage-paused-revision49",
        "revision": PUBLIC_REVISION, "native_revision": REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": 29829, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-six-stage-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }
    try:
        # Only the transport and paused snapshot are fixture scaffolding.
        # create_server constructs the real GameplayBridgeService, which calls
        # the real NativeDriver query and both new side-sibling normalizers.
        with patch.object(driver, "take_snapshot", side_effect=lambda: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                assert TOOL in {tool.name for tool in (await client.list_tools()).tools}
                response = await client.call_tool(TOOL, {
                    "prior_combat_id": None, "subject_public_cunit_id": None,
                    "after_terminal_sequence": None,
                    "expected_revision": PUBLIC_REVISION,
                    "character_ids": [SUBJECT],
                })
                assert response.is_error is False, response.content
                actual = response.structured_content
                frame = actual["battle_terminal_transition"]
                assert actual["status"] == frame["status"] == "available"
                assert actual["query_sequence"] == packet["result"]["query_sequence"]
                assert actual["queried_snapshot_id"] == snapshot["snapshot_id"]
                assert actual["queried_revision"] == PUBLIC_REVISION
                assert actual["queried_native_revision"] == REVISION
                assert actual["snapshot_revision"] == frame["snapshot_revision"] == REVISION
                assert frame["observed_date_raw"] == DATE_RAW
                assert actual["character_observations"] == frame["character_observations"]
                sidecar = actual["person_six_stage_captures"]
                assert sidecar == normalize_person_six_stage_query_12004(
                    packet["result"]["person_six_stage_captures"],
                    expected_snapshot_revision=REVISION,
                    expected_observed_date_raw=DATE_RAW,
                    expected_character_ids=[SUBJECT],
                )
                leaf, = sidecar["character_captures"]
                assert leaf["character_id"] == frame["character_observations"][0]["character_id"] == SUBJECT
                section = select_person_six_stage_capture_12004(sidecar, SUBJECT)
                requests = emit_captured_person_six_stage_requests_12004(section)
                assert [row["source_ordinal"] for row in requests] == ORDINALS
                assert [row["weight_q100000"] for row in requests] == WEIGHTS
                assert requests[0]["property_block"]["values_q64"] == [
                    2**63 - 9, 0, -(2**63 - 9), 4294967296,
                ]
        assert len(endpoint.requests) == len(endpoint.delivered) == 1
        assert driver.state._command_results == {}
        assert endpoint.packet == packet == original
        return {"registered_person_mcp_cases": 1,
                "registered_tool": TOOL,
                "real_service": "GameplayBridgeService",
                "real_driver": "NativeHeadlessGameplayDriver",
                "native_payload_rewritten": False,
                "fixture_transport_correlations": 1}
    finally:
        driver.close()


def consume(directory: Path) -> dict:
    ordered_packet = None
    for sequence, name in enumerate(CASES, 1):
        packet = json.loads((directory / (name + ".json")).read_text(encoding="utf-8"))
        if name == CASES[1]:
            ordered_packet = packet
        assert packet["type"] == "command_result" and packet["ok"] is True
        result = packet["result"]
        assert result["query_sequence"] == sequence
        assert result["snapshot_revision"] == REVISION
        frame = normalize_battle_terminal_transition_v1(
            result["battle_terminal_transition"],
            expected_prior_combat_id=-1,
            expected_subject_public_cunit_id=-1,
            expected_after_terminal_sequence=None,
            expected_observed_date_raw=DATE_RAW,
            expected_snapshot_revision=REVISION,
            expected_character_ids=[SUBJECT],
        )
        assert frame["character_observations"][0]["character_id"] == SUBJECT
        sidecar = normalize_person_six_stage_query_12004(
            result["person_six_stage_captures"],
            expected_snapshot_revision=REVISION,
            expected_observed_date_raw=DATE_RAW,
            expected_character_ids=[SUBJECT],
        )
        section = select_person_six_stage_capture_12004(sidecar, SUBJECT)
        leaf = sidecar["character_captures"][0]
        assert leaf["full_helper_ready"] is False
        assert leaf["actual_model_write_performed"] is False
        observed = name in CASES[1:4] or name == CASES[5]
        assert leaf["capture_observed"] is observed
        if not observed:
            assert leaf["capture_sequence"] == 0
            assert leaf["character_identity"] is None
            unavailable(lambda: emit_captured_person_six_stage_requests_12004(section))
            continue
        incomplete = name == CASES[2]
        partial = name == CASES[3]
        assert leaf["capture_complete"] is (not incomplete)
        assert leaf["raw_counts_ready"] is (not incomplete)
        assert leaf["ready"] is (not incomplete and not partial)
        assert [stage["raw_count_i32"] for stage in leaf["stages"]] == (
            RAW_COUNTS[:3] + [None] * 3 if incomplete else RAW_COUNTS)
        if incomplete:
            assert leaf["query_thread_id"] is None
            assert leaf["stages"][2]["first_pc"]["admitted"] is None
            unavailable(lambda: emit_captured_person_six_stage_requests_12004(section))
            continue
        assert leaf["capture_thread_id"] == leaf["query_thread_id"]
        assert leaf["stages"][2]["first_pc"]["admitted"] is False
        assert leaf["stages"][2]["first_pc"]["weight_q100000"] is None
        assert leaf["stages"][4]["second_pc"]["admitted"] is False
        if partial:
            assert leaf["stages"][3]["second_pc"]["properties"]["values_q64"] is None
            unavailable(lambda: emit_captured_person_six_stage_requests_12004(section))
            requests = emit_captured_person_six_stage_occurrence_requests_12004(section, 0)
            assert [row["source_ordinal"] for row in requests] == [0, 1]
            continue
        requests = emit_captured_person_six_stage_requests_12004(section)
        assert [row["source_ordinal"] for row in requests] == ORDINALS
        assert [row["weight_q100000"] for row in requests] == WEIGHTS
        assert requests[0]["property_block"] == {
            "keys_count": 4, "keys_u16": [129, 97, 129, 111],
            "values_q64": [2**63 - 9, 0, -(2**63 - 9), 4294967296],
        }
        assert all(row["character_id"] == SUBJECT for row in requests)
        assert all(row["context_identity"] == leaf["context_identity"] for row in requests)
    assert ordered_packet is not None
    registered = asyncio.run(consume_registered_person_mcp(ordered_packet))
    return {"status": "GREEN", "fresh_native_worlds": 7, **registered,
            "sole_python_consumer": True, "liveprimitive_only": True,
            "noFullPerson": True, "noG2credit": True,
            "new_g2_credit": 0, "packets": str(directory.resolve())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", type=Path, required=True)
    parser.add_argument("--producer-exe", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.producer_exe is not None:
        subprocess.run([str(args.producer_exe), str(args.packets)], check=True)
    report = consume(args.packets)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
