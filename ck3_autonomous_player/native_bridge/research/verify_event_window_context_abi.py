#!/usr/bin/env python3
"""Verify pinned CK3 event-window-context byte spans without starting CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from scan_anchors import PeImage


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "event_window_context_1_19_0_6_abi.json"
DEFAULT_EXE = HERE.parents[2] / "Crusader Kings III" / "binaries" / "ck3.exe"
DEFAULT_READER = HERE.parent / "src" / "event_window_context_v1.cpp"
DEFAULT_MAILBOX = HERE.parent / "src" / "event_window_context_v1_mailbox.cpp"
DEFAULT_BRIDGE = HERE.parent / "src" / "bridge.cpp"


def integer(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(f"expected integer or integer string, found {value!r}")


def runtime_function_ranges(data: bytes, image: PeImage) -> set[tuple[int, int]]:
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    optional = pe_offset + 24
    if struct.unpack_from("<H", data, optional)[0] != 0x20B:
        raise ValueError("expected PE32+ optional header")
    exception_rva, exception_size = struct.unpack_from(
        "<II", data, optional + 112 + 3 * 8
    )
    if exception_size % 12:
        raise ValueError("malformed AMD64 exception directory")
    offset = image.rva_to_offset(exception_rva)
    return {
        struct.unpack_from("<II", data, offset + delta)
        for delta in range(0, exception_size, 12)
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--reader", type=Path, default=DEFAULT_READER)
    parser.add_argument("--mailbox", type=Path, default=DEFAULT_MAILBOX)
    parser.add_argument("--bridge", type=Path, default=DEFAULT_BRIDGE)
    arguments = parser.parse_args()

    executable = arguments.exe.resolve()
    contract_path = arguments.contract.resolve()
    data = executable.read_bytes()
    image = PeImage(data)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    executable_sha = hashlib.sha256(data).hexdigest().upper()
    expected_executable_sha = contract["executable_sha256"].upper()
    if executable_sha != expected_executable_sha:
        failures.append(
            "executable SHA mismatch: "
            f"expected {expected_executable_sha}, found {executable_sha}"
        )

    pdata_ranges = runtime_function_ranges(data, image)
    source_contract = contract["source_contract"]
    function_spans = source_contract["exact_function_spans"]
    for span in function_spans:
        declared_regions = span.get("runtime_function_regions")
        if declared_regions:
            regions = []
            for region in declared_regions:
                start_text, end_text = region.split("..", maxsplit=1)
                regions.append((integer(start_text), integer(end_text)))
        else:
            regions = [(integer(span["start_rva"]), integer(span["end_rva"]))]
        for begin, end in regions:
            if (begin, end) not in pdata_ranges:
                failures.append(
                    f"{span['name']}: 0x{begin:X}..0x{end:X} "
                    "is not an exact .pdata runtime-function extent"
                )

        start = integer(span["start_rva"])
        end = integer(span["end_rva"])
        expected_length = integer(span["byte_length"])
        actual_length = end - start
        if actual_length != expected_length:
            failures.append(
                f"{span['name']}: declared length 0x{expected_length:X}, "
                f"RVA range length 0x{actual_length:X}"
            )
            continue
        offset = image.rva_to_offset(start)
        blob = data[offset : offset + actual_length]
        if len(blob) != actual_length:
            failures.append(f"{span['name']}: range is not fully file-backed")
            continue
        actual_sha = hashlib.sha256(blob).hexdigest().upper()
        expected_sha = span["sha256"].upper()
        if actual_sha != expected_sha:
            failures.append(
                f"{span['name']}: expected {expected_sha}, found {actual_sha}"
            )
            continue
        print(
            f"OK {span['name']} RVA=0x{start:X}..0x{end:X} "
            f"bytes=0x{actual_length:X} SHA256={actual_sha}"
        )

    additional_spans = [
        *source_contract.get("exact_semantic_spans", []),
        *source_contract.get("exact_data_spans", []),
    ]
    for span in additional_spans:
        start = integer(span["start_rva"])
        end = integer(span["end_rva"])
        expected_length = integer(span["byte_length"])
        actual_length = end - start
        if actual_length != expected_length:
            failures.append(
                f"{span['name']}: declared length 0x{expected_length:X}, "
                f"RVA range length 0x{actual_length:X}"
            )
            continue
        offset = image.rva_to_offset(start)
        blob = data[offset : offset + actual_length]
        if len(blob) != actual_length:
            failures.append(f"{span['name']}: range is not fully file-backed")
            continue
        actual_sha = hashlib.sha256(blob).hexdigest().upper()
        expected_sha = span["sha256"].upper()
        if actual_sha != expected_sha:
            failures.append(
                f"{span['name']}: expected {expected_sha}, found {actual_sha}"
            )
            continue
        print(
            f"OK {span['name']} RVA=0x{start:X}..0x{end:X} "
            f"bytes=0x{actual_length:X} SHA256={actual_sha}"
        )

    source_contracts = {
        "reader": (
            arguments.reader,
            (
                "bindings.jomini_state_slot",
                "bindings.game_state_slot",
                "bindings.event_manager_offset == 0",
                "bindings.get_current_event",
                "kActiveEventDataOffset",
                "kEventDataCalculatedIdOffset",
                "kEventDataRuntimeStatsOrdinalOffset",
                "kEventDataDefinitionKeyOffset",
                "kIdlerFromOwnerOffset",
                "bindings.ingame_interface_idler_vtable",
                "kManagerFromIdlerOffset",
                "bindings.event_window_primary_vtable",
                "expected_event_instance_id",
                "before.active_event_instance_id",
                "after != before",
                "kOptionOwnerOffset",
                "option.native_option_index == cancel_index",
                "ReadNativeString",
                "identity_after != identity_before",
                "candidate.event_definition_identity_ready = true",
            ),
        ),
        "mailbox": (
            arguments.mailbox,
            (
                "GetCurrentThreadId() != stamp.thread_id",
                "ExecuteEventWindowContextMailboxQueryV1",
                "snapshot != query->expected_snapshot",
                "snapshot.active_event_instance_id",
                "ReadEventWindowContextV1(",
                "event_definition_identity_ready",
            ),
        ),
        "bridge": (
            arguments.bridge,
            (
                "permitted_executor_duodenary",
                "kEventWindowContextV1Step",
                "ParseEventWindowContextRequestV1",
                "current_snapshot.active_event_instance_id",
                "ExecuteEventWindowContextMailboxQueryV1",
                "EventWindowContextResultFrame",
            ),
        ),
    }
    for name, (path, required_tokens) in source_contracts.items():
        try:
            source = path.resolve().read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"{name}: cannot read source contract: {error}")
            continue
        for token in required_tokens:
            if token not in source:
                failures.append(f"{name}: missing source-contract token {token!r}")
    reader_source = arguments.reader.resolve().read_text(encoding="utf-8")
    for forbidden in (
        "SubmitSelectEventOption",
        "select_event_option",
        "loaded_effect_executor",
        "0x3380410",
    ):
        if forbidden in reader_source:
            failures.append(f"reader: forbidden executor token {forbidden!r}")

    locator = contract["locator_chain"]
    query_contract = contract["production_query"]
    if not locator["root_to_idler_static_ready"]:
        failures.append("contract: stable root-to-idler is not closed")
    if query_contract["capability"] != (
        "game.command.query-current-event-window-context-v1"
    ):
        failures.append("contract: production capability drifted")
    if not contract["readiness"]["stable_event_definition_key_published"]:
        failures.append("contract: stable event definition key is not published")
    if not contract["readiness"]["event_definition_identity_wire_ready"]:
        failures.append("contract: event definition identity wire is not ready")
    published_identity = set(
        query_contract.get("published_event_definition_fields", [])
    )
    if published_identity != {
        "event_definition_key",
        "calculated_event_id",
        "runtime_stats_ordinal",
    }:
        failures.append("contract: published event definition fields drifted")
    if published_identity & set(query_contract["explicitly_unavailable"]):
        failures.append("contract: published event identity remains unavailable")
    if contract["readiness"]["live_validated"]:
        failures.append("contract: offline verifier cannot admit live validation")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print(
        f"PASS spans={len(function_spans) + len(additional_spans)} "
        "pdata=1 exact_build=1 read_only=1 "
        "source_contract=1 live_pending=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
