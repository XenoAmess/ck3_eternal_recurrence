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
DEFAULT_SERIALIZER = HERE.parent / "src" / "event_window_context_v1_serializer.cpp"
DEFAULT_BINDINGS = HERE.parent / "src" / "ck3_11906.cpp"
DEFAULT_BRIDGE = HERE.parent / "src" / "bridge.cpp"


def integer(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(f"expected integer or integer string, found {value!r}")


def signed_int32(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and -(2**31) <= value < 2**31
    )


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
    parser.add_argument("--serializer", type=Path, default=DEFAULT_SERIALIZER)
    parser.add_argument("--bindings", type=Path, default=DEFAULT_BINDINGS)
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
                "kEventDataAuthoredOptionDataOffset",
                "kEventDataAuthoredOptionCapacityOffset",
                "kEventDataAuthoredOptionCountOffset",
                "kEventOptionDefinitionIsCancelOffset",
                "kIdlerFromOwnerOffset",
                "bindings.ingame_interface_idler_vtable",
                "kManagerFromIdlerOffset",
                "bindings.event_window_primary_vtable",
                "expected_event_instance_id",
                "before.active_event_instance_id",
                "after != before",
                "kOptionOwnerOffset",
                "kOptionEffectDataOffset",
                "kOptionEffectCapacityOffset",
                "kOptionEffectCountOffset",
                "kEffectIndicatorStride",
                "bindings.trait_database_slot",
                "kTraitNativeIdOffset",
                "kTraitStableKeyOffset",
                "bindings.scheme_type_database_slot",
                "bindings.scheme_type_fallback_slot",
                "bindings.scheme_type_primary_vtable",
                "bindings.hash_stable_key",
                "bindings.hash_stable_key(\n      database",
                "bindings.lookup_scheme_type",
                "kSchemeTypeStableKeyOffset",
                "option.native_option_index >= authored_count",
                "is_cancel > 1",
                "option.cancel = is_cancel != 0",
                "ReadMatchingWindow(bindings, identity_before.event_data",
                "ReadNativeString",
                "identity_after != identity_before",
                "candidate.event_definition_identity_ready = true",
                "candidate.effect_indicators_ready = true",
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
                "effect_indicators_ready",
            ),
        ),
        "serializer": (
            arguments.serializer,
            (
                "played-character-event-icon-indicators-1.19.0.6-v1",
                "indicator_subset_has_no_completeness_signal",
                "resource_deltas",
                "relationship_deltas",
                "effect_indicators_ready",
                "semantic_decision_ready",
            ),
        ),
        "bindings": (
            arguments.bindings,
            (
                "kSchemeTypePrimaryVtableRva = 0x44081E8",
                "kTraitDatabaseSlotRva = 0x570C0F8",
                "kSchemeTypeDatabaseSlotRva = 0x570BD98",
                "kSchemeTypeFallbackSlotRva = 0x570CB58",
                "kHashStableKeyRva = 0x3B8B000",
                "kLookupSchemeTypeRva = 0x0A48C70",
                "result.scheme_type_primary_vtable",
                "result.trait_database_slot",
                "result.scheme_type_database_slot",
                "result.scheme_type_fallback_slot",
                "result.hash_stable_key",
                "result.lookup_scheme_type",
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
        "construct_effect_preview_collector",
        "traverse_loaded_effect",
        "kDataCancelOptionIndexOffset",
        "option.native_option_index == cancel_index",
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
    readiness = contract["readiness"]
    if not readiness["stable_event_definition_key_published"]:
        failures.append("contract: stable event definition key is not published")
    if not readiness["event_definition_identity_wire_ready"]:
        failures.append("contract: event definition identity wire is not ready")
    if not readiness["effect_indicator_wire_ready"]:
        failures.append("contract: effect indicator wire is not ready")
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
    published_options = set(query_contract["published_option_fields"])
    required_indicator_fields = {
        "effect_indicators",
        "effect_preview_unavailable",
        "resource_deltas_unavailable",
        "relationship_deltas_unavailable",
    }
    if not required_indicator_fields <= published_options:
        failures.append("contract: effect indicator wire fields are incomplete")
    live = contract.get("live_validation", {})
    if not (
        contract.get("live_validated") is True
        and contract.get("game_process_started") is True
        and readiness.get("bridge_query_ready") is True
        and readiness.get("current_event_window_context_fixture_live_ready")
        is True
        and readiness.get("empty_effect_indicator_surface_live_ready") is True
        and readiness.get("nonempty_effect_indicator_kinds_live_ready") is False
        and readiness.get("event_window_lifecycle_live_ready") is False
        and readiness.get("semantic_decision_ready") is False
        and readiness.get("live_validated") is True
    ):
        failures.append("contract: scoped live readiness drifted")
    if not (
        live.get("evidence_classification") == "fixture-scoped-live-confirmed"
        and live.get("artifact_size") == 130779
        and live.get("artifact_sha256")
        == "690EB5EA188B0903281E5F5DFDA343DA795117EE0FB1C83C3FCDC7F572170B7B"
        and live.get("frozen_source_commit")
        == "cea30a067b1e112596d70532b98fa068b2102ebf"
        and live.get("full_event_instance_id") == 17
        and live.get("canonical_event_definition_key")
        == "xar_event_window_live_fixture.1"
        and signed_int32(live.get("seed_calculated_event_id"))
        and signed_int32(live.get("cold_calculated_event_id"))
        and signed_int32(live.get("seed_runtime_stats_ordinal"))
        and signed_int32(live.get("cold_runtime_stats_ordinal"))
        and live.get("materialized_native_option_indices") == [0, 1, 3]
        and live.get("cancel_native_option_indices") == [3]
        and live.get("effect_indicator_rows_per_option") == [0, 0, 0]
        and live.get("adjacent_cold_frames_equal") is True
        and live.get("fixture_bytes_equal_across_stages") is True
        and live.get("no_event_option_selected") is True
        and live.get("managed_process_cleanup") is True
        and live.get("nonce_root_removed") is True
        and live.get("no_ck3_processes_after") is True
    ):
        failures.append("contract: Attempt4 fixture-live evidence drifted")
    live_acceptance = query_contract.get("live_acceptance", {})
    if not (
        isinstance(live_acceptance, dict)
        and "Attempt4" in live_acceptance.get("completed", "")
        and "nonempty indicator" in live_acceptance.get("remaining", "")
    ):
        failures.append("contract: live acceptance boundary drifted")
    typed_context = contract.get("typed_context_proposal", {})
    if not (
        typed_context.get("status")
        == (
            "definition_identity_presentation_and_empty_effect_indicator_"
            "surface_fixture_live"
        )
        and "Attempt4" in typed_context.get("live_scope", "")
        and "nonempty indicator" in typed_context.get(
            "remaining_live_scope", ""
        )
        and "semantic choice" in typed_context.get(
            "remaining_live_scope", ""
        )
    ):
        failures.append("contract: typed context live scope drifted")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print(
        f"PASS spans={len(function_spans) + len(additional_spans)} "
        "pdata=1 exact_build=1 read_only=1 "
        "source_contract=1 fixture_live=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
