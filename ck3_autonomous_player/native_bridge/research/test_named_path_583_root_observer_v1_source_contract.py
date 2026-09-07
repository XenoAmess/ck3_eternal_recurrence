#!/usr/bin/env python3
"""Freeze the exact-build caller-local named-path 0x583 observer seam."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


EXPECTED_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_SIZE = 95_206_008


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sections(image: bytes) -> list[tuple[int, int, int, int]]:
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    if image[pe : pe + 4] != b"PE\0\0":
        raise AssertionError("PE signature drifted")
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


def _at(image: bytes, sections: list[tuple[int, int, int, int]], rva: int, size: int) -> bytes:
    for virtual_address, virtual_size, raw_offset, raw_size in sections:
        span = max(virtual_size, raw_size)
        if virtual_address <= rva and rva + size <= virtual_address + span:
            offset = raw_offset + rva - virtual_address
            return image[offset : offset + size]
    raise AssertionError(f"RVA 0x{rva:X} is not file-backed")


def _direct_target(rva: int, instruction: bytes) -> int:
    if len(instruction) != 5 or instruction[0] != 0xE8:
        raise AssertionError(f"RVA 0x{rva:X} is not a direct CALL")
    return rva + 5 + struct.unpack_from("<i", instruction, 1)[0]


def check(root: Path) -> None:
    native = root / "ck3_autonomous_player" / "native_bridge"
    header = (native / "include/xar_bridge/named_path_583_root_observer_v1.hpp").read_text(
        encoding="utf-8"
    )
    source = (native / "src/named_path_583_root_observer_v1.cpp").read_text(
        encoding="utf-8"
    )
    bridge = (native / "src/bridge.cpp").read_text(encoding="utf-8")
    cmake = (native / "CMakeLists.txt").read_text(encoding="utf-8")
    fixture_path = native / "research/fixtures/named_path_583_root_observer_v1_source_contract.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    abi = json.loads(
        (native / "research/named_path_583_root_observer_v1_abi.json").read_text(
            encoding="utf-8"
        )
    )

    _require(
        fixture["schema"]
        == "xar.named_path_583_root_observer_v1.source_contract.v1",
        "fixture schema drifted",
    )
    _require(
        abi["schema"] == "xar.named_path_583_root_observer_v1.abi.v1",
        "ABI schema drifted",
    )
    _require(fixture["exact_build"] == abi["exact_build"], "build binding drifted")
    for token in fixture["required_source_tokens"]:
        _require(token in header or token in source, f"missing source token: {token}")
    for token in fixture["required_bridge_tokens"]:
        _require(token in bridge or token in cmake, f"missing bridge token: {token}")
    option = "XAR_CK3_ENABLE_NAMED_PATH_583_ROOT_OBSERVER_V1"
    _require(option in cmake, "CMake option missing")
    _require("OFF" in cmake[cmake.index(option) :][:300], "option is not default OFF")
    _require("GetCurrentThreadId" not in source, "fast record calls GetCurrentThreadId")
    _require("QueryPerformanceCounter" not in source, "fast record calls QPC")
    _require("std::mutex" not in source, "fast record has a mutex")
    _require("new " not in source, "observer source contains dynamic new")
    _require("malloc" not in source, "observer source contains malloc")

    executable = root / "Crusader Kings III/binaries/ck3.exe"
    image = executable.read_bytes()
    _require(len(image) == EXPECTED_SIZE, "executable size drifted")
    _require(
        hashlib.sha256(image).hexdigest().upper() == EXPECTED_SHA256,
        "executable SHA-256 drifted",
    )
    sections = _sections(image)
    resolver_call = _at(image, sections, 0x3320A82, 5)
    move_anchor = _at(image, sections, 0x331F9E4, 11)
    _require(resolver_call == bytes.fromhex("E8 E9 61 87 00"), "resolver anchor drifted")
    _require(_direct_target(0x3320A82, resolver_call) == 0x3B96C70, "resolver target drifted")
    _require(
        move_anchor == bytes.fromhex("48 8B D0 48 8B CF E8 11 72 4C FD"),
        "move anchor drifted",
    )
    _require(_direct_target(0x331F9EA, move_anchor[6:]) == 0x7E6C00, "move target drifted")
    helper_call = _at(image, sections, 0x331F9DF, 5)
    _require(helper_call == bytes.fromhex("E8 7C 10 00 00"), "helper call drifted")
    _require(_direct_target(0x331F9DF, helper_call) == 0x3320A60, "helper target drifted")
    _require(
        _at(image, sections, 0x3320A7D, 5) == bytes.fromhex("B9 83 05 00 00"),
        "named-path id drifted",
    )
    _require(
        _at(image, sections, 0x331F9EF, 5) == bytes.fromhex("48 8D 4C 24 30"),
        "move continuation drifted",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    args = parser.parse_args()
    check(args.root.resolve())
    print("named-path-583-root-observer-source-contract: GREEN_STATIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
