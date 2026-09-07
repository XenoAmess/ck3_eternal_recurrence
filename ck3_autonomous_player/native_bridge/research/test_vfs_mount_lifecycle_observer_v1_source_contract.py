#!/usr/bin/env python3
"""Freeze the exact-build private VFS mount lifecycle observer seams."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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


def _rip_target(rva: int, instruction: bytes, displacement_offset: int) -> int:
    displacement = struct.unpack_from("<i", instruction, displacement_offset)[0]
    return rva + len(instruction) + displacement


def check(root: Path) -> None:
    native = root / "ck3_autonomous_player" / "native_bridge"
    header = (
        native / "include/xar_bridge/vfs_mount_lifecycle_observer_v1.hpp"
    ).read_text(encoding="utf-8")
    source = (native / "src/vfs_mount_lifecycle_observer_v1.cpp").read_text(
        encoding="utf-8"
    )
    cmake = (native / "CMakeLists.txt").read_text(encoding="utf-8")
    bridge = (native / "src/bridge.cpp").read_text(encoding="utf-8")
    fixture = json.loads(
        (
            native
            / "research/fixtures/vfs_mount_lifecycle_observer_v1_source_contract.json"
        ).read_text(encoding="utf-8")
    )
    abi = json.loads(
        (
            native / "research/vfs_mount_lifecycle_observer_v1_abi.json"
        ).read_text(encoding="utf-8")
    )
    _require(
        fixture["schema"]
        == "xar.vfs_mount_lifecycle_observer_v1.source_contract.v1",
        "fixture schema drifted",
    )
    _require(
        abi["schema"] == "xar.vfs_mount_lifecycle_observer_v1.abi.v1",
        "ABI schema drifted",
    )
    _require(fixture["exact_build"] == abi["exact_build"], "build binding drifted")
    for token in fixture["required_source_tokens"]:
        _require(token in header or token in source, f"missing source token: {token}")
    for token in fixture["forbidden_hook_path_tokens"]:
        _require(token not in source, f"forbidden hook-path token: {token}")
    integration = cmake + "\n" + bridge
    for token in fixture["required_integration_tokens"]:
        _require(token in integration, f"missing integration token: {token}")
    option = re.search(
        r"option\(\s*XAR_CK3_ENABLE_VFS_MOUNT_LIFECYCLE_OBSERVER_V1"
        r".*?\s+(ON|OFF)\s*\)",
        cmake,
        flags=re.DOTALL,
    )
    _require(option is not None, "CMake observer option missing")
    _require(option.group(1) == "OFF", "observer must remain default-OFF")

    executable = root / "Crusader Kings III/binaries/ck3.exe"
    image = executable.read_bytes()
    _require(len(image) == EXPECTED_SIZE, "executable size drifted")
    _require(
        hashlib.sha256(image).hexdigest().upper() == EXPECTED_SHA256,
        "executable SHA-256 drifted",
    )
    sections = _sections(image)
    anchors = {
        0x07E7136: "E8 D5 52 37 03",
        0x3BE18C0: "48 89 5C 24 08",
        0x3BE1A07: "4C 8D 5C 24 50",
        0x3BE239C: "48 63 4E 08 48 8B 53 38",
    }
    for rva, expected in anchors.items():
        encoded = bytes.fromhex(expected)
        _require(
            _at(image, sections, rva, len(encoded)) == encoded,
            f"anchor drifted at RVA 0x{rva:X}",
        )
    _require(
        _direct_target(0x07E7136, _at(image, sections, 0x07E7136, 5))
        == 0x3B5C410,
        "core init call target drifted",
    )
    _require(
        _direct_target(0x3BE2365, _at(image, sections, 0x3BE2365, 5))
        == 0x3BDED80,
        "lookup singleton getter call drifted",
    )
    _require(
        _at(image, sections, 0x3BE2373, 4) == bytes.fromhex("48 8D 58 08"),
        "lookup manager+8 derivation drifted",
    )
    manager_lea = _at(image, sections, 0x3BDEDA0, 7)
    _require(
        manager_lea == bytes.fromhex("48 8D 05 89 0C C8 01"),
        "singleton static-manager LEA drifted",
    )
    _require(
        _rip_target(0x3BDEDA0, manager_lea, 3) == 0x585FA30,
        "singleton static-manager target drifted",
    )
    _require(
        _at(image, sections, 0x3BE194D, 4) == bytes.fromhex("4C 8D 77 08"),
        "publisher manager+8 derivation drifted",
    )
    _require(
        _at(image, sections, 0x3BE19F2, 3) == bytes.fromhex("49 89 16"),
        "publisher head write drifted",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    args = parser.parse_args()
    check(args.root.resolve())
    print("vfs-mount-lifecycle-observer-source-contract: GREEN_STATIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
