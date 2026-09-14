#!/usr/bin/env python3
"""Verify DEV17's exact-build construction cost/legality live observer core."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
from pathlib import Path
from typing import Any


EXPECTED_BUILD = "1.19.0.6"
EXPECTED_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_SIZE = 95_206_008
EXPECTED_STATUS = "static-ready-private-cost-legality-live-observer-core-unwired"
EXPECTED_CURRENT = "native_runtime_candidate_cost_legality_live_capture_observer"
EXPECTED_NEXT = (
    "wire_private_cost_legality_live_observer_into_default_off_exact_"
    "application_main_collector"
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"JSON root must be an object: {path}")
    return value


def _sections(image: bytes) -> list[tuple[int, int, int, int]]:
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    _require(image[pe : pe + 4] == b"PE\0\0", "PE signature drifted")
    count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    cursor = pe + 24 + optional_size
    result: list[tuple[int, int, int, int]] = []
    for _ in range(count):
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
            "<IIII", image, cursor + 8
        )
        result.append((virtual_address, virtual_size, raw_offset, raw_size))
        cursor += 40
    return result


def _at(
    image: bytes, sections: list[tuple[int, int, int, int]], rva: int, size: int
) -> bytes:
    for virtual_address, virtual_size, raw_offset, raw_size in sections:
        span = max(virtual_size, raw_size)
        if virtual_address <= rva and rva + size <= virtual_address + span:
            offset = raw_offset + rva - virtual_address
            return image[offset : offset + size]
    raise AssertionError(f"RVA 0x{rva:X} is not file-backed")


def _direct_call_target(
    image: bytes, sections: list[tuple[int, int, int, int]], call_rva: int
) -> int:
    encoded = _at(image, sections, call_rva, 5)
    _require(encoded[0] == 0xE8, f"RVA 0x{call_rva:X} is not a direct call")
    displacement = struct.unpack_from("<i", encoded, 1)[0]
    return call_rva + 5 + displacement


def _tokens(text: str, expected: list[str], owner: str) -> None:
    for token in expected:
        _require(token in text, f"{owner} token missing: {token}")


def check(root: Path, executable: Path) -> None:
    research = root / "ck3_autonomous_player/native_bridge/research"
    fixtures = research / "fixtures"
    abi = _load(research / "domain_construction_cost_legality_live_observer_v1_abi.json")
    contract = _load(
        fixtures
        / "g2-domain-construction-cost-legality-live-observer-v1_source_contract.json"
    )
    fixture = _load(
        fixtures / "g2-domain-construction-cost-legality-live-observer-v1_fixture.json"
    )
    upstream = _load(
        research / "domain_construction_candidate_cost_legality_decoder_v1_abi.json"
    )

    _require(abi["schema_version"] == contract["schema_version"] == 1,
             "observer schema version drifted")
    _require(abi["status"] == contract["status"] == EXPECTED_STATUS,
             "observer status drifted")
    _require(abi["reverse_engineering_entry"] == EXPECTED_CURRENT,
             "observer reverse-engineering entry drifted")
    _require(
        upstream["unique_next_reverse_engineering_entry"] == EXPECTED_CURRENT,
        "DEV16 no longer points to the DEV17 observer",
    )
    for item in (abi, contract):
        _require(item["exact_build"]["product_version"] == EXPECTED_BUILD,
                 "exact product version drifted")
        _require(item["exact_build"]["executable_sha256"] == EXPECTED_SHA256,
                 "exact executable identity drifted")
        _require(item["unique_next_integration_entry"] == EXPECTED_NEXT,
                 "unique next integration entry drifted")

    implementation = contract["implementation"]
    adapter_header = (research.parent / implementation["adapter_header"]).read_text(
        encoding="utf-8"
    )
    adapter_source = (research.parent / implementation["adapter_source"]).read_text(
        encoding="utf-8"
    )
    observer_header = (research.parent / implementation["observer_header"]).read_text(
        encoding="utf-8"
    )
    observer_source = (research.parent / implementation["observer_source"]).read_text(
        encoding="utf-8"
    )
    test = (research.parent / implementation["test"]).read_text(encoding="utf-8")
    runner = (research.parent / implementation["runner"]).read_text(encoding="utf-8")
    docs = (root / "docs/ck3-native-ai/domain-construction-ai.md").read_text(
        encoding="utf-8"
    )
    _tokens(adapter_header, contract["required_adapter_header_tokens"],
            "collector adapter header")
    _tokens(adapter_source, contract["required_adapter_source_tokens"],
            "collector adapter source")
    _tokens(observer_header, contract["required_observer_header_tokens"],
            "live observer header")
    _tokens(observer_source, contract["required_observer_source_tokens"],
            "live observer source")
    _tokens(test, contract["required_test_tokens"], "standalone test")
    _tokens(runner, contract["required_runner_tokens"], "standalone runner")
    _require("DEV17-COST-LEGALITY-LIVE-OBSERVER" in docs,
             "construction topic DEV17 increment is missing")
    _require(EXPECTED_STATUS in docs and EXPECTED_NEXT in docs,
             "construction topic DEV17 boundary drifted")

    image = executable.read_bytes()
    _require(len(image) == EXPECTED_SIZE, "executable size drifted")
    _require(hashlib.sha256(image).hexdigest().upper() == EXPECTED_SHA256,
             "executable SHA-256 drifted")
    sections = _sections(image)
    names: set[str] = set()
    for span in contract["exact_spans"]:
        name = span["name"]
        _require(name not in names, f"duplicate exact span: {name}")
        names.add(name)
        expected = bytes.fromhex(span["hex"])
        _require(len(expected) == span["size"], f"{name} size drifted")
        _require(hashlib.sha256(expected).hexdigest().upper() == span["sha256"],
                 f"{name} digest fixture drifted")
        _require(
            _at(image, sections, int(span["rva"], 0), span["size"]) == expected,
            f"{name} exact bytes drifted",
        )
    _require(
        names
        == {
            "application_main_candidate_producer_collector",
            "selected_candidate_row_copy",
            "cost_variant_and_eight_slot_projection",
            "eight_slot_strict_affordability",
            "building_final_legality",
            "holding_final_legality",
        },
        "exact span set drifted",
    )
    for call in contract["direct_call_targets"]:
        call_rva = int(call["call_rva"], 0)
        _require(
            _direct_call_target(image, sections, call_rva)
            == int(call["target_rva"], 0),
            f"direct call target drifted at 0x{call_rva:X}",
        )

    _require(fixture["offline_fixture"] is True,
             "fixture must remain explicitly offline")
    _require(fixture["production_live_capture"] is False,
             "offline fixture was mislabeled production live")
    _require(fixture["raw_pointer_fields_persisted"] is False,
             "fixture persisted raw pointers")
    _require(fixture["raw_row_bytes_persisted"] is False,
             "fixture persisted raw rows")
    cases = {case["case"]: case for case in fixture["cases"]}
    _require(set(cases) == {
        "actionable_available_double_sample",
        "known_insufficient_candidate_available",
        "identity_binding_branch_drift_red",
    }, "fixture case set drifted")
    actionable = cases["actionable_available_double_sample"]
    _require(actionable["sample_count"] == 2,
             "available fixture is not double sampled")
    _require(actionable["expected"] == {
        "available": True,
        "publication_generation": 2,
        "candidate_ready": True,
        "actionable": True,
        "typed_red_flags": 0,
    }, "actionable available publication fixture drifted")
    rejected = cases["known_insufficient_candidate_available"]["expected"]
    _require(rejected["available"] is True and rejected["candidate_ready"] is True,
             "known rejection was collapsed into unavailable")
    _require(rejected["rejection_reason"] == "insufficient_resource"
             and rejected["blocking_resource_mask"] == 5,
             "known affordability rejection fixture drifted")
    drift = cases["identity_binding_branch_drift_red"]["expected"]
    _require(set(drift["typed_red"]) == {
        "identity", "generation", "proof_epoch", "date", "branch"
    }, "required typed drift RED set drifted")
    _require(drift["previous_complete_generation_retained"] is True,
             "typed RED no longer retains previous publication")

    readiness = abi["readiness"]
    _require(
        readiness["source_adapter_core_ready"] is True
        and readiness["same_admission_double_sample_ready"] is True
        and readiness["pointer_free_available_publication_ready"] is True
        and readiness["production_live_capture_ready"] is False
        and readiness["shared_collector_wiring_ready"] is False,
        "private core/live boundary drifted",
    )
    for key in (
        "shared_cmake_modified",
        "shared_bridge_modified",
        "public_schema_modified",
        "mcp_modified",
        "ck3_started",
    ):
        _require(abi["scope"][key] is False, f"scope boundary drifted: {key}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    parser.add_argument("--ck3-executable", type=Path)
    arguments = parser.parse_args()
    executable = arguments.ck3_executable
    if executable is None:
        configured = os.environ.get("CK3_EXACT_EXECUTABLE")
        executable = Path(configured) if configured else None
    if executable is None:
        parser.error("--ck3-executable or CK3_EXACT_EXECUTABLE is required")
    check(arguments.root.resolve(), executable.resolve())
    print("domain-construction-cost-legality-live-observer: GREEN_EXACT_SPANS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
