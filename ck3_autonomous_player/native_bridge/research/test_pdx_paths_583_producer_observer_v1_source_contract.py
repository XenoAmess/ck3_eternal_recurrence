#!/usr/bin/env python3
"""Freeze the exact-build private pdx_paths 0x583 producer observer seam."""

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


def check(root: Path) -> None:
    native = root / "ck3_autonomous_player" / "native_bridge"
    header = (
        native / "include/xar_bridge/pdx_paths_583_producer_observer_v1.hpp"
    ).read_text(encoding="utf-8")
    source = (native / "src/pdx_paths_583_producer_observer_v1.cpp").read_text(
        encoding="utf-8"
    )
    bridge = (native / "src/bridge.cpp").read_text(encoding="utf-8")
    cmake = (native / "CMakeLists.txt").read_text(encoding="utf-8")
    protocol = (native / "include/xar_bridge/protocol.hpp").read_text(
        encoding="utf-8"
    )
    fixture = json.loads(
        (
            native
            / "research/fixtures/pdx_paths_583_producer_observer_v1_source_contract.json"
        ).read_text(encoding="utf-8")
    )
    abi = json.loads(
        (native / "research/pdx_paths_583_producer_observer_v1_abi.json").read_text(
            encoding="utf-8"
        )
    )
    _require(
        fixture["schema"]
        == "xar.pdx_paths_583_producer_observer_v1.source_contract.v1",
        "fixture schema drifted",
    )
    _require(
        abi["schema"] == "xar.pdx_paths_583_producer_observer_v1.abi.v1",
        "ABI schema drifted",
    )
    _require(fixture["exact_build"] == abi["exact_build"], "build binding drifted")
    for token in fixture["required_source_tokens"]:
        _require(token in header or token in source, f"missing source token: {token}")
    for token in fixture["required_bridge_tokens"]:
        _require(token in bridge or token in cmake, f"missing bridge token: {token}")
    for token in fixture["forbidden_public_tokens"]:
        _require(token not in protocol, f"private observer leaked publicly: {token}")
    option = "XAR_CK3_ENABLE_PDX_PATHS_583_PRODUCER_OBSERVER_V1"
    _require(option in cmake, "CMake option missing")
    _require("OFF" in cmake[cmake.index(option) :][:300], "option is not default OFF")
    _require("GetCurrentThreadId" not in source, "record path calls GetCurrentThreadId")
    _require("QueryPerformanceCounter" not in source, "record path calls QPC")
    _require("std::mutex" not in source, "record path contains a mutex")
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
    anchors = {
        0x3B96A2E: "48 89 7C 24 30",
        0x3B96A4E: "E8 ED B8 04 00",
        0x3B96B62: "E8 D9 B7 04 00",
        0x3B96531: "48 89 4C 24 60",
        0x3B96897: "E8 54 41 9A FE",
    }
    for rva, expected in anchors.items():
        _require(_at(image, sections, rva, 5) == bytes.fromhex(expected),
                 f"anchor drifted at RVA 0x{rva:X}")
    _require(
        _direct_target(0x3B96A4E, _at(image, sections, 0x3B96A4E, 5))
        == 0x3BE2340,
        "paths lookup target drifted",
    )
    _require(
        _direct_target(0x3B96B62, _at(image, sections, 0x3B96B62, 5))
        == 0x3BE2340,
        "checksummed lookup target drifted",
    )
    _require(
        _direct_target(0x3B96897, _at(image, sections, 0x3B96897, 5))
        == 0x253A9F0,
        "insert target drifted",
    )
    _require(
        _at(image, sections, 0x3B96878, 31)
        == bytes.fromhex(
            "48 8D 44 24 40 48 89 44 24 28 4C 8D 8D E8 04 00 00 "
            "48 8D 95 A8 00 00 00 48 8D 0D 01 DE BC 01"
        ),
        "insert caller argument setup drifted",
    )
    _require(
        _at(image, sections, 0x253AA8E, 4) == bytes.fromhex("48 8B 45 58"),
        "insert sixth-argument read drifted",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    args = parser.parse_args()
    check(args.root.resolve())
    print("pdx-paths-583-producer-observer-source-contract: GREEN_STATIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
