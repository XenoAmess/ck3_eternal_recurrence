#!/usr/bin/env python3
"""Verify DEV15's exact-build construction candidate identity decoder."""

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
EXPECTED_STATUS = "static-ready-private-candidate-identity-decoder"
EXPECTED_NEXT = "native_runtime_candidate_cost_affordability_and_final_legality_decoder"


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


def check(root: Path, executable: Path) -> None:
    research = root / "ck3_autonomous_player/native_bridge/research"
    fixtures = research / "fixtures"
    abi = _load(research / "domain_construction_candidate_identity_decoder_v1_abi.json")
    contract = _load(
        fixtures
        / "g2-domain-construction-candidate-identity-decoder-v1_source_contract.json"
    )
    fixture = _load(
        fixtures / "g2-domain-construction-candidate-identity-decoder-v1_fixture.json"
    )
    upstream = _load(research / "domain_construction_runtime_callsite_observer_v1_abi.json")

    _require(abi["schema_version"] == 1, "decoder ABI schema drifted")
    _require(contract["schema_version"] == 1, "source contract schema drifted")
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
        upstream["unique_next_reverse_engineering_entry"]
        == "native_runtime_0x18D2954_candidate_row_identity_decoder",
        "upstream observer no longer points to this decoder",
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
    _require("DEV15-CANDIDATE-IDENTITY-DECODER" in docs,
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
            "existing_holding_row_constructor",
            "new_holding_selector_gate",
            "new_holding_row_constructor",
            "selected_row_copy",
            "building_command_scalar_reads",
            "new_holding_candidate_forward",
            "new_holding_validation_forward",
        },
        "exact span set drifted",
    )

    _require(fixture["offline_fixture"] is True,
             "identity fixture must remain offline")
    _require(fixture["raw_pointer_fields_persisted"] is False,
             "identity fixture persisted raw pointers")
    cases = {case["case"]: case for case in fixture["cases"]}
    _require(cases["building_in_holding"]["expected"] == {
        "ready": True,
        "kind": "building_in_holding",
        "candidate_id": "building:17:4:16777258",
    }, "building identity fixture drifted")
    _require(cases["new_holding"]["expected"] == {
        "ready": True,
        "kind": "new_holding",
        "candidate_id": "holding:867:3",
    }, "holding identity fixture drifted")
    _require(cases["ambiguous_identity_shape"]["expected"] == {
        "ready": False,
        "failure": "identity_shape",
        "candidate_id": "",
    }, "typed ambiguous identity fixture drifted")
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
    print("domain-construction-candidate-identity-decoder-source-contract: GREEN_EXACT_SPANS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
