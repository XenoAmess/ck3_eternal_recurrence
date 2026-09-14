#!/usr/bin/env python3
"""Verify DEV16's exact-build construction cost and legality decoder."""

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
EXPECTED_STATUS = "static-ready-private-candidate-cost-legality-decoder"
EXPECTED_CURRENT = "native_runtime_candidate_cost_affordability_and_final_legality_decoder"
EXPECTED_NEXT = "native_runtime_candidate_cost_legality_live_capture_observer"


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


def _tokens(text: str, expected: list[str], owner: str) -> None:
    for token in expected:
        _require(token in text, f"{owner} token missing: {token}")


def _direct_call_target(image: bytes, sections: list[tuple[int, int, int, int]], call_rva: int) -> int:
    encoded = _at(image, sections, call_rva, 5)
    _require(encoded[0] == 0xE8, f"RVA 0x{call_rva:X} is no longer a direct call")
    displacement = struct.unpack_from("<i", encoded, 1)[0]
    return call_rva + 5 + displacement


def _fixture_outcome(case: dict[str, Any]) -> dict[str, Any]:
    expected_binding = case["expected_binding"]
    observed_binding = case["observed_binding"]
    generations = (
        expected_binding["generation"],
        observed_binding["generation"],
    )
    if any(value == 0 or value % 2 for value in generations):
        return {"ready": False, "actionable": False, "unavailable": "generation"}
    if expected_binding["proof_epoch"] == 0 or observed_binding["proof_epoch"] == 0:
        return {"ready": False, "actionable": False, "unavailable": "proof_epoch"}
    if expected_binding != observed_binding:
        return {"ready": False, "actionable": False, "unavailable": "binding_drift"}

    affordable = [
        cost <= 0 or cost < balance
        for cost, balance in zip(
            case["cost_raw"], case["resource_balance_raw"], strict=True
        )
    ]
    blocking_mask = sum(1 << slot for slot, value in enumerate(affordable) if not value)
    if blocking_mask:
        return {
            "ready": True,
            "native_affordable": False,
            "native_final_legal": False,
            "actionable": False,
            "first_blocking_resource_slot": next(
                slot for slot, value in enumerate(affordable) if not value
            ),
            "blocking_resource_mask": blocking_mask,
            "rejection_reason": "insufficient_resource",
            "unavailable": "none",
        }

    final = case["final_legality"]
    if not final["observed"]:
        return {
            "ready": False,
            "actionable": False,
            "unavailable": "final_legality_unobserved",
        }
    expected_branch = (
        "building"
        if case["candidate"]["kind"] == "building_in_holding"
        else "new_holding"
    )
    if final["branch"] != expected_branch:
        return {
            "ready": False,
            "actionable": False,
            "unavailable": "candidate_kind_branch_mismatch",
        }
    allowed = final["allowed"]
    reason = "none"
    if not allowed:
        reason = (
            "building_native_final_legality_rejected"
            if expected_branch == "building"
            else "holding_native_final_legality_rejected"
        )
    return {
        "ready": True,
        "native_affordable": True,
        "native_final_legal": allowed,
        "actionable": allowed,
        "blocking_resource_mask": 0,
        "rejection_reason": reason,
        "unavailable": "none",
    }


def check(root: Path, executable: Path) -> None:
    research = root / "ck3_autonomous_player/native_bridge/research"
    fixtures = research / "fixtures"
    abi = _load(research / "domain_construction_candidate_cost_legality_decoder_v1_abi.json")
    contract = _load(
        fixtures
        / "g2-domain-construction-candidate-cost-legality-decoder-v1_source_contract.json"
    )
    fixture = _load(
        fixtures / "g2-domain-construction-candidate-cost-legality-decoder-v1_fixture.json"
    )
    upstream = _load(research / "domain_construction_candidate_identity_decoder_v1_abi.json")

    _require(abi["schema_version"] == 1, "decoder ABI schema drifted")
    _require(contract["schema_version"] == 1, "source contract schema drifted")
    _require(abi["reverse_engineering_entry"] == EXPECTED_CURRENT,
             "decoder reverse-engineering entry drifted")
    _require(abi["status"] == contract["status"] == EXPECTED_STATUS,
             "private decoder status drifted")
    for item in (abi, contract):
        _require(item["exact_build"]["product_version"] == EXPECTED_BUILD,
                 "exact product version drifted")
        _require(item["exact_build"]["executable_sha256"] == EXPECTED_SHA256,
                 "exact executable identity drifted")
        _require(item["unique_next_reverse_engineering_entry"] == EXPECTED_NEXT,
                 "unique next reverse-engineering entry drifted")
    _require(
        upstream["unique_next_reverse_engineering_entry"] == EXPECTED_CURRENT,
        "upstream identity decoder no longer points to this decoder",
    )

    implementation = contract["implementation"]
    header = (research.parent / implementation["header"]).read_text(encoding="utf-8")
    source = (research.parent / implementation["source"]).read_text(encoding="utf-8")
    test = (research.parent / implementation["test"]).read_text(encoding="utf-8")
    runner = (research.parent / implementation["runner"]).read_text(encoding="utf-8")
    docs = (root / "docs/ck3-native-ai/domain-construction-ai.md").read_text(
        encoding="utf-8"
    )
    _tokens(header, contract["required_header_tokens"], "decoder header")
    _tokens(source, contract["required_source_tokens"], "decoder source")
    _tokens(test, contract["required_test_tokens"], "standalone test")
    _tokens(runner, contract["required_runner_tokens"], "standalone runner")
    _require("DEV16-COST-LEGALITY-DECODER" in docs,
             "construction topic increment is missing")
    _require(EXPECTED_STATUS in docs and EXPECTED_NEXT in docs,
             "construction topic status/next seam drifted")

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
        _require(len(expected) == span["size"], f"{name} size/hex drifted")
        _require(hashlib.sha256(expected).hexdigest().upper() == span["sha256"],
                 f"{name} fixture digest drifted")
        observed = _at(image, sections, int(span["rva"], 0), span["size"])
        _require(observed == expected, f"{name} exact bytes drifted")
    _require(
        names
        == {
            "cost_variant_and_eight_slot_projection",
            "eight_slot_strict_affordability",
            "building_final_legality",
            "holding_final_legality",
        },
        "exact span set drifted",
    )
    for call in contract["direct_call_targets"]:
        call_rva = int(call["call_rva"], 0)
        target_rva = int(call["target_rva"], 0)
        _require(
            _direct_call_target(image, sections, call_rva) == target_rva,
            f"{call['span']} direct target drifted at 0x{call_rva:X}",
        )

    _require(fixture["offline_fixture"] is True,
             "cost/legality fixture must remain offline")
    _require(fixture["raw_pointer_fields_persisted"] is False,
             "cost/legality fixture persisted raw pointers")
    cases = {case["case"]: case for case in fixture["cases"]}
    _require(
        set(cases)
        == {
            "building_actionable",
            "holding_insufficient_resource",
            "building_final_legality_rejected",
            "binding_date_drift",
            "affordable_without_final_observation",
        },
        "fixture case set drifted",
    )
    for name, case in cases.items():
        _require(len(case["cost_raw"]) == len(case["resource_balance_raw"]) == 8,
                 f"{name} resource vector size drifted")
        observed = _fixture_outcome(case)
        _require(observed == case["expected"], f"{name} semantic result drifted")

    _require(
        abi["decode"]["affordability_predicate_per_slot"]
        == "cost <= 0 || cost < resource_balance",
        "strict native affordability predicate drifted",
    )
    _require(
        abi["readiness"]["private_decoder_core_ready"] is True
        and abi["readiness"]["exact_spans_ready"] is True
        and abi["readiness"]["paired_native_runtime_capture_ready"] is False
        and abi["readiness"]["public_candidate_reader_ready"] is False,
        "private/live readiness boundary drifted",
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
    print("domain-construction-candidate-cost-legality-source-contract: GREEN_EXACT_SPANS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
