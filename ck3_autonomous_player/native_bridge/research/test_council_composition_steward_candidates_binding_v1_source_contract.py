#!/usr/bin/env python3
"""Validate the Council7 private binding and optional exact CK3 image."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_rva(image: bytes, rva: int, size: int) -> bytes:
    pe_offset = struct.unpack_from("<I", image, 0x3C)[0]
    require(image[pe_offset : pe_offset + 4] == b"PE\0\0", "invalid PE image")
    section_count = struct.unpack_from("<H", image, pe_offset + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe_offset + 20)[0]
    sections = pe_offset + 24 + optional_size
    for index in range(section_count):
        offset = sections + index * 40
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
            "<IIII", image, offset + 8
        )
        span = max(virtual_size, raw_size)
        if virtual_address <= rva and rva + size <= virtual_address + span:
            file_offset = raw_offset + (rva - virtual_address)
            return image[file_offset : file_offset + size]
    raise AssertionError(f"RVA 0x{rva:X}+{size} is outside PE sections")


def validate_executable(path: Path, contract: dict) -> None:
    image = path.read_bytes()
    require(
        hashlib.sha256(image).hexdigest().upper() == EXPECTED_EXE_SHA256,
        "exact CK3 executable identity drifted",
    )
    for frozen in contract["exact_executable_slices"]:
        rva = int(frozen["rva"], 16)
        payload = read_rva(image, rva, frozen["size"])
        require(
            hashlib.sha256(payload).hexdigest().upper() == frozen["sha256"],
            f"exact slice drifted at {frozen['rva']}",
        )

    image_base = 0x140000000
    vtable = read_rva(image, 0x4098A20, 0x40)
    entries = [struct.unpack_from("<Q", vtable, offset)[0] for offset in range(0, 0x40, 8)]
    require(
        entries
        == [
            image_base + 0x82D790,
            image_base + 0x7E8FF0,
            image_base + 0x7E8FB0,
            image_base + 0x7E8F90,
            image_base + 0x91E320,
            image_base + 0x91E320,
            image_base + 0x82A9A0,
            image_base + 0x82A9A0,
        ],
        "inline allocator vtable entries drifted",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ck3-executable", type=Path)
    args = parser.parse_args()

    research = Path(__file__).resolve().parent
    native = research.parent
    contract = load_json(
        research
        / "fixtures/council_composition_steward_candidates_binding_v1_source_contract.json"
    )
    abi = load_json(
        research / "council_composition_steward_candidates_binding_v1_abi.json"
    )
    fixture = load_json(
        research
        / "fixtures/council_composition_steward_candidates_binding_v1_fixture.json"
    )

    require(contract["schema_version"] == 1, "source contract version drifted")
    require(abi["schema_version"] == 1, "ABI version drifted")
    require(fixture["schema_version"] == 1, "fixture version drifted")
    require(
        contract["private_key"] == abi["private_key"] == fixture["private_key"],
        "private key drifted",
    )
    for relative in contract["required_sources"]:
        require((native / relative).is_file(), f"missing required source: {relative}")

    header = (
        native
        / "include/xar_bridge/council_composition_steward_candidates_binding_v1.hpp"
    ).read_text(encoding="utf-8")
    implementation = (
        native / "src/council_composition_steward_candidates_binding_v1.cpp"
    ).read_text(encoding="utf-8")
    for token in contract["required_header_tokens"]:
        require(token in header, f"missing header token: {token}")
    for token in contract["required_implementation_tokens"]:
        require(token in implementation, f"missing implementation token: {token}")

    require(
        implementation.index("ResolveActiveStewardTask")
        < implementation.index("state.operations.initialize_vector(")
        < implementation.index("state.operations.invoke_producer(")
        < implementation.index("state.operations.release_allocation("),
        "resolve/initialize/produce/release order drifted",
    )
    require(
        abi["producer"]["native_vector_layout"]["size_bytes"] == 24
        and abi["temporary_vector_allocator"]["object_size_bytes"] == 528
        and abi["temporary_vector_allocator"]["inline_candidate_capacity"] == 64,
        "native vector or allocator layout drifted",
    )
    readiness = abi["readiness"]
    require(
        readiness["production_private_binding_implemented"]
        and readiness["exact_producer_bound"]
        and readiness["exact_release_bound"]
        and readiness["active_steward_task_resolution_bound"]
        and not readiness["shared_cmake_registered"]
        and not readiness["bridge_mailbox_glue_registered"]
        and not readiness["public_capability_registered"]
        and not readiness["production_query_live"],
        "readiness boundary drifted",
    )
    success = fixture["success_case"]
    require(
        success["active_task_id"] == 7159
        and success["position_key"] == "councillor_steward"
        and success["producer_count"] == success["release_count"] == 1,
        "success fixture pairing drifted",
    )
    failures = {case["case"]: case for case in fixture["failure_cases"]}
    require(
        failures["producer_failure_after_initialization"]["release_count"] == 1
        and failures["release_failure"]["expected_failure"]
        == "temporary_vector_release_failed"
        and failures["task_generation_mismatch"]["producer_count"] == 0,
        "failure fixture drifted",
    )

    if args.ck3_executable is not None:
        validate_executable(args.ck3_executable.resolve(), contract)
    print("council-composition-steward-candidates-binding-v1: GREEN_STATIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
