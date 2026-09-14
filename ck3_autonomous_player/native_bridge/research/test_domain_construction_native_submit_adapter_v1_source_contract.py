#!/usr/bin/env python3
"""Verify DEV19's exact-build private construction native-submit contract."""

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
EXPECTED_STATUS = "static-ready-private-construction-native-submit-adapter-unwired"


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
    image: bytes,
    sections: list[tuple[int, int, int, int]],
    call_rva: int,
) -> int:
    encoded = _at(image, sections, call_rva, 5)
    _require(encoded[0] == 0xE8, f"RVA 0x{call_rva:X} is no longer a direct call")
    displacement = struct.unpack_from("<i", encoded, 1)[0]
    return call_rva + 5 + displacement


def _tokens(text: str, expected: list[str], owner: str) -> None:
    for token in expected:
        _require(token in text, f"{owner} token missing: {token}")


def check(root: Path, executable: Path) -> None:
    research = root / "ck3_autonomous_player/native_bridge/research"
    contract = _load(
        research / "fixtures/g2-domain-construction-native-submit-adapter-v1_source_contract.json"
    )
    abi = _load(research / "domain_construction_native_submit_adapter_v1_abi.json")
    upstream = _load(research / "domain_construction_semantic_action_core_v1_abi.json")

    _require(contract["schema_version"] == abi["schema_version"] == 1,
             "schema version drifted")
    _require(contract["status"] == abi["status"] == EXPECTED_STATUS,
             "private status drifted")
    _require(abi["upstream_private_contract"] == upstream["contract"],
             "DEV18 upstream contract drifted")
    for item in (contract, abi):
        exact = item["exact_build"]
        _require(exact["product_version"] == EXPECTED_BUILD,
                 "exact product version drifted")
        _require(exact["executable_sha256"] == EXPECTED_SHA256,
                 "exact executable identity drifted")
        _require(exact["executable_size"] == EXPECTED_SIZE,
                 "exact executable size drifted")

    implementation = contract["implementation"]
    header = (research.parent / implementation["header"]).read_text(encoding="utf-8")
    source = (research.parent / implementation["source"]).read_text(encoding="utf-8")
    test = (research.parent / implementation["test"]).read_text(encoding="utf-8")
    runner = (research.parent / implementation["runner"]).read_text(encoding="utf-8")
    docs = (root / "docs/ck3-native-ai/domain-construction-ai.md").read_text(
        encoding="utf-8"
    )
    _tokens(header, contract["required_header_tokens"], "adapter header")
    _tokens(source, contract["required_source_tokens"], "adapter source")
    _tokens(test, contract["required_test_tokens"], "standalone test")
    _tokens(runner, contract["required_runner_tokens"], "standalone runner")
    _require("DEV19-CONSTRUCTION-NATIVE-SUBMIT" in docs,
             "construction topic DEV19 increment is missing")
    _require(EXPECTED_STATUS in docs and "0x341D990" in docs,
             "construction topic status or receiver anchor drifted")

    image = executable.read_bytes()
    _require(len(image) == EXPECTED_SIZE, "executable size drifted")
    _require(hashlib.sha256(image).hexdigest().upper() == EXPECTED_SHA256,
             "executable SHA-256 drifted")
    sections = _sections(image)
    expected_names = {
        "building_command_context_and_validator",
        "building_materialize_and_receiver",
        "new_holding_command_context_and_validator",
        "new_holding_materialize_and_receiver",
        "common_leftover_wrapper_lifecycle",
        "receiver_queue_and_ownership_lifecycle",
        "building_native_final_validator",
        "new_holding_native_final_validator_entry",
    }
    observed_names: set[str] = set()
    for span in contract["exact_spans"]:
        name = span["name"]
        _require(name not in observed_names, f"duplicate exact span: {name}")
        observed_names.add(name)
        expected = bytes.fromhex(span["hex"])
        _require(len(expected) == span["size"], f"{name} size/hex drifted")
        _require(hashlib.sha256(expected).hexdigest().upper() == span["sha256"],
                 f"{name} fixture digest drifted")
        actual = _at(image, sections, int(span["rva"], 0), span["size"])
        _require(actual == expected, f"{name} exact bytes drifted")
    _require(observed_names == expected_names, "exact span set drifted")

    for call in contract["direct_call_targets"]:
        call_rva = int(call["call_rva"], 0)
        target_rva = int(call["target_rva"], 0)
        _require(_direct_call_target(image, sections, call_rva) == target_rva,
                 f"{call['span']} direct target drifted at 0x{call_rva:X}")

    assertions = contract["semantic_assertions"]
    _require(assertions["receiver_true_is_pending_ack_only"] is True,
             "receiver ACK boundary drifted")
    _require(assertions["ack_is_application_success"] is False,
             "ACK was promoted to application success")
    _require(assertions["raw_pointer_fields_persisted"] is False,
             "raw pointer persistence boundary drifted")
    _require(assertions["offline_callback_can_claim_production"] is False,
             "offline callback can claim production")
    _require(assertions["adapter_can_set_production_native_path"] is False,
             "private adapter can claim production")
    _require(abi["executor_boundary"]["adapter_can_set_production_native_path"] is False,
             "unwired adapter production boundary drifted")
    _require(abi["executor_boundary"]["production_executor_wired"] is False,
             "unwired private executor was promoted to production")
    _require(abi["readiness"]["production_live_acceptance_ready"] is False,
             "static candidate was promoted to live")
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
    print("domain-construction-native-submit-source-contract: GREEN_EXACT_SPANS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
