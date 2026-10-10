"""AUTHORED_NOTRUN: four new historical base/piety-input packets, one compound.

Root may run the new producer and this sole consumer once. Every original
packet passes through registered MCP, GameplayBridgeService and NativeDriver;
only transport request correlation is rebound. These synthetic production-path
checks grant no live, FullPerson, Entry or forecast credit.
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
    FIELD_NAME,
    emit_captured_person_base_point_12004,
    emit_captured_person_base_points_12004,
    emit_captured_person_piety_category_12004,
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

SUBJECT, PUBLIC_REVISION, NATIVE_REVISION, DATE_RAW = 0x04000003, 97, 49, 53_236_632
TOOL = "ck3_query_battle_terminal_transition_v1"
SOURCE_STAGE = "before_each_original_count"
CASES = (
    "base-before-each-original-mutation",
    "base-index2-unread-six-ready",
    "base-observe-bypass-unobserved",
    "base-same-owner-new-capture-retained",
)
BASE_A = [0, -7, 2**31 - 1, -(2**31), 19, -1]
BASE_B = [-(2**31), 2**31 - 1, -11, 0, 23, -29]
RAW_COUNTS = [7, -3, 0, 2**31 - 1, -1, -(2**31)]
ORDINALS = [0, 1, 2, 3, 5, 6, 7, 8, 10, 11]
WEIGHTS = [700000, 800000, -300000, -200000, 100000,
           214748364700000, -214748364800000, -100000,
           -214748364800000, -214748364700000]
PIETY_SCORES = [-1, 0, 99, 100, 200, 2**63 - 1]
PIETY_CAPS = [-1, -1, 1, 1, 2, -1]
PIETY_CATEGORIES = [0, 1, 1, 1, 0, 3]
PIETY_THRESHOLDS = [[0], [0, 100], [0, 100], [0, 100, 200], [], [0, 100, 200]]


class _Checks:
    def __init__(self):
        self.count = 0

    def require(self, condition, detail):
        self.count += 1
        if not condition:
            raise AssertionError(detail)

    def unavailable(self, callback, detail):
        self.count += 1
        try:
            callback()
        except ValueError:
            return
        raise AssertionError(detail)


class _WholePacketEndpoint:
    """Qualified transport pattern; native result bodies remain untouched."""

    pipe_name = "offline-person-six-stage-base-points-whole-packets"

    def __init__(self, step, checks):
        self.step, self.checks = step, checks
        self.packet, self.on_frame = None, None
        self.requests, self.delivered = [], []

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def select(self, packet):
        self.packet = deepcopy(packet)

    def send(self, request):
        self.checks.require(
            request["type"] == "execute_step" and request["protocol_version"] == 1,
            "registered MCP must use the production execute-step transport",
        )
        self.checks.require(request["step"] == self.step, "requested query/full ID changed")
        self.checks.require(
            request["expected_revision"] == NATIVE_REVISION,
            "public revision must bind the exact native frame",
        )
        self.requests.append(deepcopy(request))
        response = deepcopy(self.packet)
        response["request_id"] = request["request_id"]
        self.checks.require(
            {key: value for key, value in response.items() if key != "request_id"}
            == {key: value for key, value in self.packet.items() if key != "request_id"},
            "native packet body changed at ingress",
        )
        self.delivered.append(deepcopy(response))
        self.on_frame(response)

    def close(self):
        pass


def _identity(leaf):
    return {
        "character_id": SUBJECT,
        "character_identity": leaf["character_identity"],
        "context_identity": leaf["context_identity"],
        "capture_sequence": leaf["capture_sequence"],
        "capture_date_raw": leaf["capture_date_raw"],
        "capture_thread_id": leaf["capture_thread_id"],
        "source_stage": SOURCE_STAGE,
        "historical_capture": True,
        "actual_model_write_performed": False,
        "full_helper_ready": False,
    }


async def _consume_registered(packets, checks, *, resume_after_first=False):
    from mcp import Client

    originals = deepcopy(packets)
    run_names = CASES[1:] if resume_after_first else CASES
    step = query_battle_terminal_transition_v1_step(None, None, None, [SUBJECT])
    endpoint = _WholePacketEndpoint(step, checks)
    driver = NativeHeadlessGameplayDriver(endpoint=endpoint, episode_projection="native_campaign")
    hello = {
        "type": "hello", "protocol_version": 1, "pid": 1,
        "capabilities": ["game.state.snapshot", QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY],
        "expected_ck3_version": CK3_12004.game_version,
        "expected_ck3_sha256": CK3_12004.executable_sha256,
    }
    checks.require(driver.state.ingest(hello) == "hello", "exact-build hello rejected")
    snapshot = {
        "snapshot_id": "person-six-stage-base-points-paused-revision49",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": 29829, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-six-stage-base-points-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }
    leaves, total_inputs, stage_inputs = {}, {}, {}
    try:
        # Endpoint and paused snapshot are fixture scaffolding. create_server
        # constructs the real service; the real driver and service each normalize
        # this same sibling, including its historical base operands.
        with patch.object(driver, "take_snapshot", side_effect=lambda **kwargs: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                checks.require(
                    TOOL in {tool.name for tool in (await client.list_tools()).tools},
                    "production Person query MCP tool is not registered",
                )
                for query_sequence, name in enumerate(CASES, 1):
                    if name not in run_names:
                        continue
                    packet = packets[name]
                    checks.require(
                        packet["type"] == "command_result" and packet["ok"] is True,
                        name + ": expected original native whole command result",
                    )
                    wire = packet["result"]
                    checks.require(
                        wire["step"] == step and wire["query_sequence"] == query_sequence,
                        name + ": native query identity/sequence changed",
                    )
                    checks.require(
                        wire["snapshot_revision"] == NATIVE_REVISION,
                        name + ": native envelope frame changed",
                    )
                    raw_leaf, = wire["person_six_stage_captures"]["character_captures"]
                    endpoint.select(packet)
                    response = await client.call_tool(TOOL, {
                        "prior_combat_id": None, "subject_public_cunit_id": None,
                        "after_terminal_sequence": None, "expected_revision": PUBLIC_REVISION,
                        "character_ids": [SUBJECT],
                    })
                    checks.require(response.is_error is False, str(response.content))
                    actual = response.structured_content
                    frame = actual["battle_terminal_transition"]
                    checks.require(
                        actual["status"] == frame["status"] == "available",
                        name + ": independent query frame unavailable",
                    )
                    checks.require(actual["query_sequence"] == query_sequence, name + ": query sequence lost")
                    checks.require(
                        actual["queried_snapshot_id"] == snapshot["snapshot_id"]
                        and actual["queried_revision"] == PUBLIC_REVISION
                        and actual["queried_native_revision"] == NATIVE_REVISION
                        and actual["snapshot_revision"] == frame["snapshot_revision"] == NATIVE_REVISION
                        and frame["observed_date_raw"] == DATE_RAW,
                        name + ": requested public/native/date frame join failed",
                    )
                    checks.require(
                        actual["character_observations"] == frame["character_observations"]
                        and frame["character_observations"][0]["character_id"] == SUBJECT,
                        name + ": main frame full CharacterID join failed",
                    )
                    sidecar = actual["person_six_stage_captures"]
                    expected_sidecar = normalize_person_six_stage_query_12004(
                        wire["person_six_stage_captures"],
                        expected_snapshot_revision=NATIVE_REVISION,
                        expected_observed_date_raw=DATE_RAW,
                        expected_character_ids=[SUBJECT],
                    )
                    checks.require(sidecar == expected_sidecar, name + ": production double normalization changed inputs")
                    checks.require(
                        normalize_person_six_stage_query_12004(
                            sidecar, expected_snapshot_revision=NATIVE_REVISION,
                            expected_observed_date_raw=DATE_RAW, expected_character_ids=[SUBJECT],
                        ) == sidecar,
                        name + ": normalized production sibling is not idempotent",
                    )
                    leaf, = sidecar["character_captures"]
                    section = select_person_six_stage_capture_12004(sidecar, SUBJECT)
                    checks.require(section[FIELD_NAME] == leaf, name + ": selected leaf changed")
                    checks.require(leaf["character_id"] == SUBJECT, name + ": capture borrowed another full ID")
                    checks.require(
                        leaf["capture_observed"] is True and leaf["capture_complete"] is True
                        and leaf["raw_counts_ready"] is True and leaf["ready"] is True,
                        name + ": historical base readiness changed existing capture readiness",
                    )
                    checks.require(
                        leaf["actual_model_write_performed"] is False and leaf["full_helper_ready"] is False,
                        name + ": base publication changed scope",
                    )
                    checks.require(
                        leaf["capture_sequence"] == (2 if name == CASES[3] else 1)
                        and leaf["capture_date_raw"] == DATE_RAW
                        and leaf["capture_thread_id"] == leaf["query_thread_id"],
                        name + ": historical capture identity changed",
                    )
                    checks.require(
                        [stage["raw_count_i32"] for stage in leaf["stages"]] == RAW_COUNTS,
                        name + ": original raw signed callback returns changed",
                    )
                    requests = emit_captured_person_six_stage_requests_12004(section)
                    checks.require(
                        [row["source_ordinal"] for row in requests] == ORDINALS
                        and [row["weight_q100000"] for row in requests] == WEIGHTS,
                        name + ": original append decisions/weights changed",
                    )
                    checks.require(
                        all(row["property_block"] == {
                            "keys_count": 0, "keys_u16": [], "values_q64": []}
                            for row in requests),
                        name + ": independent empty append operands changed",
                    )
                    bypass, partial = name == CASES[2], name == CASES[1]
                    values = ([None] * 6 if bypass else
                              BASE_A[:2] + [None] + BASE_A[3:] if partial else
                              BASE_B if name == CASES[3] else BASE_A)
                    expected_base = {
                        "source_stage": SOURCE_STAGE, "character_offset": 192, "stride_bytes": 4,
                        "observed": [not bypass] * 6, "values_i32": values,
                        "ready": not bypass and not partial,
                        "reason": "base_point_unobserved" if bypass else "base_point_unread" if partial else None,
                    }
                    checks.require(
                        raw_leaf["base_point_inputs"] == leaf["base_point_inputs"] == expected_base,
                        name + ": owned pre-call signed DWORD inputs changed",
                    )
                    categories = leaf["piety_category_inputs"]["stages"]
                    for index, category in enumerate(categories):
                        category_unread = partial and index == 2
                        checks.require(
                            category["observed"] is (not bypass)
                            and category["ready"] is (not bypass and not category_unread)
                            and category["property_key_u16"] == (None if bypass else 101 + index)
                            and category["category_i32"] == (
                                None if bypass or category_unread else PIETY_CATEGORIES[index]),
                            name + ": piety category lost its physical key, cap/boundary or availability",
                        )
                        if bypass or category_unread:
                            checks.unavailable(
                                lambda index=index: emit_captured_person_piety_category_12004(section, index),
                                name + ": unavailable piety source became a numerical multiplier",
                            )
                            continue
                        piety = emit_captured_person_piety_category_12004(section, index)
                        checks.require(
                            piety["character_id"] == SUBJECT
                            and piety["capture_sequence"] == leaf["capture_sequence"]
                            and piety["capture_thread_id"] == leaf["capture_thread_id"]
                            and piety["context_identity"] == leaf["context_identity"]
                            and piety["stage_index"] == index
                            and piety["property_key_u16"] == 101 + index
                            and piety["category_multiplier_i32"] == PIETY_CATEGORIES[index]
                            and piety["score_q64"] == (None if index == 4 else PIETY_SCORES[index])
                            and piety["cap_i32"] == (None if index == 4 else PIETY_CAPS[index])
                            and piety["threshold_count_i32"] == (None if index == 4 else 3)
                            and piety["thresholds_used_q64"] == PIETY_THRESHOLDS[index],
                            name + ": historical category source/emitter changed its signed operands",
                        )
                    identity = _identity(leaf)
                    if expected_base["ready"]:
                        total_inputs[name] = emit_captured_person_base_points_12004(section)
                        checks.require(
                            total_inputs[name] == {
                                **identity, "character_offset": 192, "stride_bytes": 4,
                                "values_i32": values,
                            },
                            name + ": whole operand emitter lost identity or exact values",
                        )
                    else:
                        checks.unavailable(
                            lambda: emit_captured_person_base_points_12004(section),
                            name + ": incomplete base inputs became whole ready inputs",
                        )
                    stage_inputs[name] = {}
                    for index, value in enumerate(values):
                        if value is None:
                            checks.unavailable(
                                lambda index=index: emit_captured_person_base_point_12004(section, index),
                                name + ": unavailable physical slot became an observed base value",
                            )
                        else:
                            point = emit_captured_person_base_point_12004(section, index)
                            checks.require(
                                point == {**identity, "stage_index": index, "value_i32": value,
                                          "source_offset_bytes": 192 + 4 * index},
                                name + ": independent physical base slot lost its signed value/identity",
                            )
                            stage_inputs[name][index] = point
                    # Change only expected request bindings for these rejection
                    # checks; the original native sibling/leaf remains untouched.
                    if name == CASES[0]:
                        for revision, date, full_id in (
                            (NATIVE_REVISION + 1, DATE_RAW, SUBJECT),
                            (NATIVE_REVISION, DATE_RAW + 1, SUBJECT),
                            (NATIVE_REVISION, DATE_RAW, SUBJECT ^ 0x01000000),
                        ):
                            checks.unavailable(
                                lambda revision=revision, date=date, full_id=full_id:
                                normalize_person_six_stage_query_12004(
                                    wire["person_six_stage_captures"],
                                    expected_snapshot_revision=revision,
                                    expected_observed_date_raw=date,
                                    expected_character_ids=[full_id],
                                ),
                                "native sibling borrowed an unrequested frame or full CharacterID",
                            )
                        checks.unavailable(
                            lambda: select_person_six_stage_capture_12004(sidecar, SUBJECT ^ 0x01000000),
                            "full-ID capture selection borrowed another character generation",
                        )
                    leaves[name] = leaf
                    checks.require(endpoint.packet == packet, name + ": native body was edited")
        checks.require(
            len(endpoint.requests) == len(endpoint.delivered) == len(run_names),
            "each remaining original whole packet must traverse registered MCP once",
        )
        checks.require(driver.state._command_results == {}, "native command results were not consumed")
        checks.require(packets == originals, "original native packet data changed")
        checks.require(
            total_inputs[CASES[3]]["values_i32"] == BASE_B
            and leaves[CASES[3]]["capture_sequence"] == 2,
            "new capture publication lost its own historical values or sequence",
        )
        if not resume_after_first:
            checks.require(
                total_inputs[CASES[0]]["values_i32"] == BASE_A
                and leaves[CASES[0]]["capture_sequence"] == 1,
                "new capture publication overwrote retained earlier historical values",
            )
        checks.require(
            set(stage_inputs[CASES[1]]) == {0, 1, 3, 4, 5}
            and not stage_inputs[CASES[2]],
            "one failed base copy blocked later slots or legacy observation invented values",
        )
        return {
            "status": "GREEN", "evidence_kind": "synthetic-production-path-qualification",
            "fresh_native_worlds": 4, "whole_packets": len(run_names),
            "registered_person_mcp_cases": len(run_names),
            "passed_case_names": list(run_names),
            "retained_prior_completed_cases": list(CASES[:1]) if resume_after_first else [],
            "retained_prior_completion_evidence": (
                "Inferred from prior FIRST failing in case2 native normalization after the sequential case1 assertions; no independent case1 GREEN receipt"
                if resume_after_first else None),
            "registered_tool": TOOL, "real_service": "GameplayBridgeService",
            "real_driver": "NativeHeadlessGameplayDriver", "native_payload_rewritten": False,
            "whole_base_input_cases": len(total_inputs),
            "piety_category_input_cases": len(run_names),
            "piety_category_source": "actual28BE0B0 per-stage piety integer and actual2BA94A8 U16 key",
            "independent_readable_base_slots": sum(map(len, stage_inputs.values())),
            "unavailable_whole_base_checks": 2, "unavailable_base_slot_checks": 7,
            "frame_or_full_id_rejection_checks": 0 if resume_after_first else 4,
            "check_count": checks.count,
            "sole_python_consumer": True, "old_native_producer_replayed": False,
            "live_ready": False, "full_person_ready": False, "entry_ready": False,
            "forecast_ready": False, "full_helper_ready": False,
            "actual_model_write_performed": False, "new_g2_credit": 0,
        }
    finally:
        driver.close()


def consume(directory: Path, *, resume_after_first=False) -> dict:
    packets = {
        name: json.loads((directory / (name + ".json")).read_bytes())
        for name in CASES
    }
    report = asyncio.run(_consume_registered(
        packets, _Checks(), resume_after_first=resume_after_first))
    return {**report, "packets": str(directory.resolve())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", type=Path, required=True)
    parser.add_argument("--producer-exe", type=Path)
    parser.add_argument("--resume-after-first", action="store_true",
                        help="Retain the prior completed first case; consume original cases2-4 only")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.producer_exe is not None:
        subprocess.run([str(args.producer_exe), str(args.packets)], check=True)
    report = consume(args.packets, resume_after_first=args.resume_after_first)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
