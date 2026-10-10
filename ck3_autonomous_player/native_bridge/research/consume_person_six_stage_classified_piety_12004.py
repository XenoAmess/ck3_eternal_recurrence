"""AUTHORED_NOTRUN: sole consumer of five new native classified-piety packets.

The registered MCP tool, real GameplayBridgeService and NativeDriver consume
each original whole packet once. Only request_id correlation is rebound.
Numerical outputs are source-evaluated historical inputs, not observed native
mode calls, live qualification, FullPerson, Entry or forecast completion.
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
    _classified_q64,
    emit_captured_person_classified_piety_row_12004,
    emit_captured_person_classified_piety_value_12004,
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
CASES = (
    "classified-piety-signed-scaled-duplicates",
    "classified-piety-zero-selections",
    "classified-piety-selected-value-unread-later-ready",
    "classified-piety-new-sequence-retained",
    "classified-piety-observe-bypass-unobserved",
)
SOURCE = {
    "source_stage": "before_each_original_count",
    "context_rows_offset": 0, "context_count_offset": 12,
    "row_stride_bytes": 16, "row_pc_offset": 0, "row_scale_offset": 8,
    "classified_reader_rva": 0x2438980, "key_lookup_rva": 0x23036E0,
}
RAW_COUNTS = [7, -3, 0, 2**31 - 1, -1, -(2**31)]
ORDINALS = [0, 1, 2, 3, 5, 6, 7, 8, 10, 11]
WEIGHTS = [700000, 800000, -300000, -200000, 100000,
           214748364700000, -214748364800000, -100000,
           -214748364800000, -214748364700000]
MAX64, MIN64 = 2**63 - 1, -(2**63)


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
    pipe_name = "offline-person-six-stage-classified-piety-whole-packets"

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
            request["type"] == "execute_step" and request["protocol_version"] == 1
            and request["step"] == self.step and request["expected_revision"] == NATIVE_REVISION,
            "registered request must bind the original full ID and native frame",
        )
        self.requests.append(deepcopy(request))
        response = deepcopy(self.packet)
        response["request_id"] = request["request_id"]
        self.checks.require(
            {key: value for key, value in response.items() if key != "request_id"}
            == {key: value for key, value in self.packet.items() if key != "request_id"},
            "native whole result body changed",
        )
        self.delivered.append(deepcopy(response))
        self.on_frame(response)

    def close(self):
        pass


def _decoded_rows(value):
    """Expected wire conversion only; preserve every physical null and identity."""
    if isinstance(value, list):
        return [_decoded_rows(item) for item in value]
    if isinstance(value, dict):
        return {key: (int(item) if item is not None else None)
                if key in ("raw_value_q64", "scale_q64") else _decoded_rows(item)
                for key, item in value.items()}
    return value


def _reference_rows(name, index):
    """Independent fixture references; never call the production math kernel."""
    if name == CASES[4] or name == CASES[1] and index == 5:
        return []
    if name == CASES[1] and index < 4:
        return [("sentinel" if index in (0, 3) else "empty" if index == 1 else "absent",
                 None if index in (0, 3) else 0 if index == 1 else 4,
                 None, 0, -100000 if index in (0, 3) else 200000 if index == 1 else 100000, 0)]
    if name == CASES[3]:
        a, b, c = 1300000 + 100000 * index, -700000 - 10000 * index, -900000 + 10000 * index
        if index == 4:
            a, b, c = 214748364850000, 0, 0
        if index == 5:
            a, b, c = MAX64, MIN64, 1
    else:
        a, b, c = 300000 + 100000 * index, -200000 - 10000 * index, -500000 + 10000 * index
    scaled_b = MIN64 if name == CASES[3] and index == 5 else (-b * 3) // 2
    rows = [
        ("mapped", 4, 1, a, 100000, a),
        ("mapped", 4, 1, a, -100000, -a),
        ("mapped", 1, 0, b, -150000, scaled_b),
        ("mapped", 1, 0, c, 100000, c),
    ]
    if name == CASES[2] and index == 2:
        rows[0] = ("mapped", 4, 1, None, 100000, None)
    return rows


def _reference_value(name, index, mode):
    if name == CASES[1] and index != 4:
        return 0, None if index == 5 else 0
    if name == CASES[3]:
        if index == 4:
            return (214748364850000, 1) if mode == 1 else (-214748364850000, -1)
        if index == 5:
            # Actual max split makes MIN64 * -150000 scale to MIN64.
            # Positive rows MAX64 and 1 wrap to MIN64; the two included
            # negative rows -MAX64 and MIN64 wrap to 1.
            return (MIN64, 0) if mode == 1 else (1, 0)
        return ((2350000 + 115000 * index, [47, 49, 51, 53][index])
                if mode == 1 else (-2200000 - 90000 * index, [-44, -45, -47, -49][index]))
    value = 600000 + 115000 * index if mode == 1 else -800000 - 90000 * index
    term = ([12, 14, 16, 18, 21, 23] if mode == 1 else [-16, -17, -19, -21, -23, -25])[index]
    return value, None if name == CASES[1] and index == 4 else term


def _provenance(leaf, stage, mode):
    return {
        "character_id": SUBJECT, "character_identity": leaf["character_identity"],
        "context_identity": leaf["context_identity"],
        "capture_sequence": leaf["capture_sequence"],
        "capture_date_raw": leaf["capture_date_raw"],
        "capture_thread_id": leaf["capture_thread_id"],
        "source_stage": "before_each_original_count", "historical_capture": True,
        "actual_model_write_performed": False, "full_helper_ready": False,
        "stage_index": stage["index"], "mode": mode,
        "property_key_u16": stage["property_key_u16"],
        "row_array_identity": stage["row_array_identity"],
        "classified_reader_rva": 0x2438980, "key_lookup_rva": 0x23036E0,
        "source_evaluated": True, "native_mode_call_observed": False,
    }


async def _consume_registered(packets, checks):
    from mcp import Client

    originals = deepcopy(packets)
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
        "snapshot_id": "person-classified-piety-paused-revision49",
        "revision": PUBLIC_REVISION, "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW, "paused": True, "map_ready": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": 29829, "alive": True},
        "player_armies": [], "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "episode_run_id": "offline-person-classified-piety-12004",
        "diagnostics": {"connection_generation": 1, "hello": deepcopy(hello)},
    }
    values, rows_emitted = {}, 0
    try:
        with patch.object(driver, "take_snapshot", side_effect=lambda **kwargs: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                checks.require(TOOL in {tool.name for tool in (await client.list_tools()).tools},
                               "production MCP query tool is not registered")
                for sequence, name in enumerate(CASES, 1):
                    packet, wire = packets[name], packets[name]["result"]
                    checks.require(
                        packet["type"] == "command_result" and packet["ok"] is True
                        and wire["step"] == step and wire["query_sequence"] == sequence
                        and wire["snapshot_revision"] == NATIVE_REVISION,
                        name + ": original native query identity changed",
                    )
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
                        actual["status"] == frame["status"] == "available"
                        and actual["query_sequence"] == sequence
                        and actual["queried_snapshot_id"] == snapshot["snapshot_id"]
                        and actual["queried_revision"] == PUBLIC_REVISION
                        and actual["queried_native_revision"] == NATIVE_REVISION
                        and actual["snapshot_revision"] == frame["snapshot_revision"] == NATIVE_REVISION
                        and frame["observed_date_raw"] == DATE_RAW,
                        name + ": exact requested frame binding failed",
                    )
                    sidecar = actual["person_six_stage_captures"]
                    checks.require(sidecar == normalize_person_six_stage_query_12004(
                        wire["person_six_stage_captures"], expected_snapshot_revision=NATIVE_REVISION,
                        expected_observed_date_raw=DATE_RAW, expected_character_ids=[SUBJECT],
                    ), name + ": real driver/service double normalization changed the new leaf")
                    checks.require(sidecar == normalize_person_six_stage_query_12004(
                        sidecar, expected_snapshot_revision=NATIVE_REVISION,
                        expected_observed_date_raw=DATE_RAW, expected_character_ids=[SUBJECT],
                    ), name + ": normalized integer Q64 operands failed a subsequent pass")
                    leaf, = sidecar["character_captures"]
                    raw_leaf, = wire["person_six_stage_captures"]["character_captures"]
                    section = select_person_six_stage_capture_12004(sidecar, SUBJECT)
                    checks.require(
                        leaf["character_id"] == frame["character_observations"][0]["character_id"] == SUBJECT
                        and actual["character_observations"] == frame["character_observations"]
                        and leaf["capture_sequence"] == (2 if name == CASES[3] else 1)
                        and leaf["capture_date_raw"] == DATE_RAW
                        and leaf["capture_thread_id"] == leaf["query_thread_id"],
                        name + ": historical full-ID/sequence/date/thread join failed",
                    )
                    checks.require(
                        leaf["ready"] is True and leaf["raw_counts_ready"] is True
                        and leaf["capture_complete"] is True
                        and leaf["actual_model_write_performed"] is False and leaf["full_helper_ready"] is False
                        and [stage["raw_count_i32"] for stage in leaf["stages"]] == RAW_COUNTS,
                        name + ": classified source changed old count/capture readiness",
                    )
                    appends = emit_captured_person_six_stage_requests_12004(section)
                    checks.require(
                        [row["source_ordinal"] for row in appends] == ORDINALS
                        and [row["weight_q100000"] for row in appends] == WEIGHTS,
                        name + ": original append observations changed",
                    )
                    inputs = leaf["classified_piety_inputs"]
                    checks.require(
                        {key: inputs[key] for key in SOURCE} == SOURCE
                        and inputs == _decoded_rows(raw_leaf["classified_piety_inputs"]),
                        name + ": historical raw operands/nulls/identities were not preserved",
                    )
                    for index, stage in enumerate(inputs["stages"]):
                        bypass = name == CASES[4]
                        partial = name == CASES[2] and index == 2
                        expected_rows = _reference_rows(name, index)
                        key = (None if bypass or name == CASES[1] and index == 5 else
                               [0xFFFF, 129, 130, 0xFFFF, 129, None][index] if name == CASES[1] else 129)
                        checks.require(
                            stage["index"] == index and stage["observed"] is (not bypass)
                            and stage["ready"] is (not bypass and not partial)
                            and stage["property_key_u16"] == key
                            and stage["row_count_i32"] == (None if bypass else len(expected_rows))
                            and len(stage["rows"]) == len(expected_rows),
                            name + ": independent stage readiness/source operands changed",
                        )
                        if bypass or name == CASES[1] and index == 5:
                            checks.require(stage["row_array_identity"] is None,
                                           name + ": undemanded row pointer was substituted")
                        if len(expected_rows) == 4:
                            checks.require(stage["rows"][0]["pc_identity"] == stage["rows"][1]["pc_identity"],
                                           name + ": duplicate physical PC rows were deduplicated")
                        for row_index, (row, expected) in enumerate(zip(stage["rows"], expected_rows)):
                            selection, count, selected, raw_value, scale, scaled = expected
                            checks.require(
                                row["native_index"] == row_index and row["lookup_selection"] == selection
                                and row["pc_count_i32"] == count and row["selected_index_u32"] == selected
                                and row["raw_value_q64"] == raw_value and row["scale_q64"] == scale
                                and row["ready"] is (scaled is not None),
                                name + ": physical selected row/duplicate index/signed scale changed",
                            )
                            raw_row = raw_leaf["classified_piety_inputs"]["stages"][index]["rows"][row_index]
                            checks.require(
                                all(raw_row[field] is None or type(raw_row[field]) is str
                                    for field in ("raw_value_q64", "scale_q64")),
                                name + ": original native Q64 operands must be decimal strings or null",
                            )
                            for mode in (1, 2):
                                if scaled is None:
                                    checks.unavailable(
                                        lambda mode=mode, row_index=row_index:
                                        emit_captured_person_classified_piety_row_12004(section, index, row_index, mode),
                                        name + ": unread selected QWORD became a ready row",
                                    )
                                else:
                                    included = scaled > 0 if mode == 1 else scaled < 0
                                    point = emit_captured_person_classified_piety_row_12004(section, index, row_index, mode)
                                    checks.require(point == {
                                        **_provenance(leaf, stage, mode), **row,
                                        "scaled_value_q64": scaled, "included": included,
                                        "value_q64": scaled if included else 0,
                                    }, name + ": source-evaluated row math/identity/filter changed")
                                    rows_emitted += 1
                        for mode in (1, 2):
                            if not stage["ready"]:
                                checks.unavailable(
                                    lambda mode=mode: emit_captured_person_classified_piety_value_12004(section, index, mode),
                                    name + ": incomplete classified stage became a whole value",
                                )
                                continue
                            value, direct_term = _reference_value(name, index, mode)
                            category_ready = not (name == CASES[1] and index in (4, 5))
                            piety = leaf["piety_category_inputs"]["stages"][index]
                            checks.require(piety["ready"] is category_ready,
                                           name + ": fixture category availability changed")
                            evaluated = emit_captured_person_classified_piety_value_12004(section, index, mode)
                            included = [row_index for row_index, row in enumerate(expected_rows)
                                        if (row[5] > 0 if mode == 1 else row[5] < 0)]
                            checks.require(evaluated == {
                                **_provenance(leaf, stage, mode), "row_count_i32": stage["row_count_i32"],
                                "value_q64": value, "included_native_indexes": included,
                                "category_multiplier_i32": 2 if category_ready else None,
                                "direct_term_ready": category_ready, "direct_term_i32": direct_term,
                                "direct_term_reason": None if category_ready else piety["reason"],
                            }, name + ": max-split/filter/wrap64/category/low32 reference differs")
                            values[name, index, mode] = evaluated
                    if name == CASES[0]:
                        for revision, date, full_id in (
                            (NATIVE_REVISION + 1, DATE_RAW, SUBJECT),
                            (NATIVE_REVISION, DATE_RAW + 1, SUBJECT),
                            (NATIVE_REVISION, DATE_RAW, SUBJECT ^ 0x01000000),
                        ):
                            checks.unavailable(
                                lambda revision=revision, date=date, full_id=full_id:
                                normalize_person_six_stage_query_12004(
                                    wire["person_six_stage_captures"], expected_snapshot_revision=revision,
                                    expected_observed_date_raw=date, expected_character_ids=[full_id]),
                                "new leaf borrowed an unrequested frame or full CharacterID",
                            )
                        checks.unavailable(
                            lambda: select_person_six_stage_capture_12004(sidecar, SUBJECT ^ 0x01000000),
                            "capture selector borrowed another character generation",
                        )
                        for mode in (0, 3, True, 1.0):
                            checks.unavailable(
                                lambda mode=mode: emit_captured_person_classified_piety_value_12004(section, 0, mode),
                                "classified evaluation accepted a non-native/non-classified mode",
                            )
                    checks.require(endpoint.packet == packet, name + ": original native body changed")
        for invalid in (True, 1.0, MIN64 - 1, MAX64 + 1, str(MAX64 + 1)):
            checks.unavailable(lambda invalid=invalid: _classified_q64(invalid, "classified_q64"),
                               "classified Q64 decoder accepted bool/float/out-of-range input")
        checks.require(
            _classified_q64(str(MIN64), "classified_q64") == MIN64
            and _classified_q64(str(MAX64), "classified_q64") == MAX64,
            "classified Q64 decoder lost signed64 boundaries",
        )
        checks.require(
            len(endpoint.requests) == len(endpoint.delivered) == len(CASES) == 5
            and driver.state._command_results == {} and packets == originals,
            "five original whole packets must remain owned and unchanged",
        )
        checks.require(
            values[CASES[0], 0, 1]["value_q64"] == 600000
            and values[CASES[3], 0, 1]["value_q64"] == 2350000
            and values[CASES[0], 0, 1]["capture_sequence"] == 1
            and values[CASES[3], 0, 1]["capture_sequence"] == 2,
            "new capture/source mutation overwrote retained historical values",
        )
        return {
            "status": "GREEN", "evidence_kind": "synthetic-production-path-qualification",
            "fresh_native_worlds": 5, "whole_packets": 5, "registered_person_mcp_cases": 5,
            "registered_tool": TOOL, "real_service": "GameplayBridgeService",
            "real_driver": "NativeHeadlessGameplayDriver", "native_payload_rewritten": False,
            "source_evaluated_mode_values": len(values), "independent_ready_mode_rows": rows_emitted,
            "check_count": checks.count, "sole_python_consumer": True,
            "old_native_producer_replayed": False, "native_mode_call_observed": False,
            "live_ready": False, "full_person_ready": False, "entry_ready": False,
            "forecast_ready": False, "actual_model_write_performed": False, "new_g2_credit": 0,
        }
    finally:
        driver.close()


def consume(directory: Path) -> dict:
    packets = {name: json.loads((directory / (name + ".json")).read_bytes()) for name in CASES}
    return {**asyncio.run(_consume_registered(packets, _Checks())), "packets": str(directory.resolve())}


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
