#!/usr/bin/env python3
"""Freeze BUILD2's exact construction producer/callsite observer seams."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


EXPECTED_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_SIZE = 95_206_008
PATCH_RVA = 0x2EBEE81
CALL_RVA = 0x2EBEE86
PRODUCER_RVA = 0x1921810
PATCH_ANCHOR = bytes.fromhex("488D542440E88529A6FE488B05160D9002")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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
    image: bytes,
    sections: list[tuple[int, int, int, int]],
    rva: int,
    size: int,
) -> bytes:
    for virtual_address, virtual_size, raw_offset, raw_size in sections:
        span = max(virtual_size, raw_size)
        if virtual_address <= rva and rva + size <= virtual_address + span:
            offset = raw_offset + rva - virtual_address
            return image[offset : offset + size]
    raise AssertionError(f"RVA 0x{rva:X} is not file-backed")


def _direct_target(rva: int, instruction: bytes) -> int:
    _require(
        len(instruction) == 5 and instruction[0] == 0xE8,
        f"RVA 0x{rva:X} is not a direct CALL",
    )
    return rva + 5 + struct.unpack_from("<i", instruction, 1)[0]


def _fnv1a64(value: bytes) -> int:
    result = 14_695_981_039_346_656_037
    for byte in value:
        result ^= byte
        result = (result * 1_099_511_628_211) & ((1 << 64) - 1)
    return result


def check(root: Path, *, ck3_executable: Path | None = None) -> None:
    native = root / "ck3_autonomous_player" / "native_bridge"
    header = (
        native
        / "include/xar_bridge/domain_construction_candidate_observer_v1.hpp"
    ).read_text(encoding="utf-8")
    source = (
        native / "src/domain_construction_candidate_observer_v1.cpp"
    ).read_text(encoding="utf-8")
    serializer = (
        native / "src/domain_construction_candidate_observer_v1_serializer.cpp"
    ).read_text(encoding="utf-8")
    contract = json.loads(
        (
            native
            / "research/fixtures/g2-domain-construction-candidate-observer-v1_source_contract.json"
        ).read_text(encoding="utf-8")
    )
    abi = json.loads(
        (
            native / "research/domain_construction_candidate_observer_v1_abi.json"
        ).read_text(encoding="utf-8")
    )
    capture = json.loads(
        (
            native
            / "research/fixtures/g2-domain-construction-candidate-observer-v1_capture_fixture.json"
        ).read_text(encoding="utf-8")
    )

    _require(contract["schema_version"] == 1, "source contract version drifted")
    _require(abi["schema_version"] == 1, "ABI version drifted")
    for token in contract["required_header_tokens"]:
        _require(token in header, f"missing header token: {token}")
    for token in contract["required_implementation_tokens"]:
        _require(token in source, f"missing implementation token: {token}")
    for token in contract["required_serializer_tokens"]:
        _require(
            token in serializer or token in header,
            f"missing serializer/header token: {token}",
        )

    _require(
        abi["scope"]["compile_option"]
        == "XAR_CK3_ENABLE_G2_DOMAIN_CONSTRUCTION_CANDIDATE_OBSERVER_V1",
        "private compile gate drifted",
    )
    _require(
        abi["unique_next_reverse_engineering_entry"]
        == "ai_attempt_to_build_building_effect_0x2EBEE81_post_candidate_row_identity_decoder",
        "unique next reverse-engineering entry drifted",
    )
    _require(
        capture["raw_pointer_fields_persisted"] is False
        and capture["row_bytes_reinterpreted_after_capture"] is False,
        "capture pointer boundary drifted",
    )
    for row in capture["capture"]["rows"]:
        raw = bytes.fromhex(row["row_bytes_hex"])
        _require(len(raw) == 0x28, "capture row stride drifted")
        _require(
            int.from_bytes(raw[:8], "little", signed=True) == row["score_raw"],
            "capture score/raw bytes drifted",
        )
        _require(
            f"{_fnv1a64(raw):016X}" == row["row_bytes_fnv1a64"],
            "capture row FNV drifted",
        )

    executable = ck3_executable or root / "Crusader Kings III/binaries/ck3.exe"
    image = executable.read_bytes()
    _require(len(image) == EXPECTED_SIZE, "executable size drifted")
    _require(
        hashlib.sha256(image).hexdigest().upper() == EXPECTED_SHA256,
        "executable SHA-256 drifted",
    )
    sections = _sections(image)
    _require(
        _at(image, sections, PATCH_RVA, len(PATCH_ANCHOR)) == PATCH_ANCHOR,
        "construction callsite anchor drifted",
    )
    _require(
        _direct_target(CALL_RVA, _at(image, sections, CALL_RVA, 5))
        == PRODUCER_RVA,
        "construction producer direct-call target drifted",
    )
    _require(
        _at(image, sections, PRODUCER_RVA, 5)
        == bytes.fromhex("48895C2408"),
        "construction producer prologue drifted",
    )
    rip_load = _at(image, sections, 0x2EBEE8B, 7)
    _require(rip_load[:3] == bytes.fromhex("488B05"), "post-call RIP load drifted")
    _require(
        0x2EBEE92 + struct.unpack_from("<i", rip_load, 3)[0] == 0x57BFBA8,
        "post-call RIP-load target drifted",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    parser.add_argument("--ck3-executable", type=Path)
    args = parser.parse_args()
    check(
        args.root.resolve(),
        ck3_executable=(
            args.ck3_executable.resolve() if args.ck3_executable else None
        ),
    )
    print("domain-construction-candidate-observer-source-contract: GREEN_STATIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
