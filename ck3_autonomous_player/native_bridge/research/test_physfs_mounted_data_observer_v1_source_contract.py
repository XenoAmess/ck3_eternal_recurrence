#!/usr/bin/env python3
"""Freeze the exact-build caller-local PhysFS Mounted Data observer seam."""

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


def _rip_target(rva: int, instruction: bytes) -> int:
    _require(
        instruction[:3] == bytes.fromhex("48 8D 05"),
        f"RVA 0x{rva:X} is not the expected RIP-relative LEA",
    )
    return rva + len(instruction) + struct.unpack_from("<i", instruction, 3)[0]


def check(root: Path, *, ck3_executable: Path | None = None) -> None:
    native = root / "ck3_autonomous_player" / "native_bridge"
    header = (
        native / "include/xar_bridge/physfs_mounted_data_observer_v1.hpp"
    ).read_text(encoding="utf-8")
    source = (native / "src/physfs_mounted_data_observer_v1.cpp").read_text(
        encoding="utf-8"
    )
    cmake = (native / "CMakeLists.txt").read_text(encoding="utf-8")
    bridge = (native / "src/bridge.cpp").read_text(encoding="utf-8")
    fixture = json.loads(
        (
            native
            / "research/fixtures/physfs_mounted_data_observer_v1_source_contract.json"
        ).read_text(encoding="utf-8")
    )
    abi = json.loads(
        (native / "research/physfs_mounted_data_observer_v1_abi.json").read_text(
            encoding="utf-8"
        )
    )
    _require(
        fixture["schema"]
        == "xar.physfs_mounted_data_observer_v1.source_contract.v1",
        "fixture schema drifted",
    )
    _require(
        abi["schema"] == "xar.physfs_mounted_data_observer_v1.abi.v1",
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
        r"option\(\s*XAR_CK3_ENABLE_PHYSFS_MOUNTED_DATA_OBSERVER_V1"
        r".*?\s+(ON|OFF)\s*\)",
        cmake,
        flags=re.DOTALL,
    )
    _require(option is not None, "CMake observer option missing")
    _require(option.group(1) == "OFF", "observer must remain default-OFF")

    executable = ck3_executable or root / "Crusader Kings III/binaries/ck3.exe"
    image = executable.read_bytes()
    _require(len(image) == EXPECTED_SIZE, "executable size drifted")
    _require(
        hashlib.sha256(image).hexdigest().upper() == EXPECTED_SHA256,
        "executable SHA-256 drifted",
    )
    sections = _sections(image)
    call = _at(image, sections, 0x3B5CE1D, 5)
    _require(call == bytes.fromhex("E8 9E 4A 08 00"), "publisher call drifted")
    _require(
        _direct_target(0x3B5CE1D, call) == 0x3BE18C0,
        "publisher target drifted",
    )
    literal_lea = _at(image, sections, 0x3B5CEA7, 7)
    _require(
        literal_lea == bytes.fromhex("48 8D 05 A2 9F 9F 00"),
        "Mounted Data literal reference drifted",
    )
    _require(
        _rip_target(0x3B5CEA7, literal_lea) == 0x4556E50,
        "Mounted Data literal target drifted",
    )
    _require(
        _at(image, sections, 0x4556E50, len(b"Mounted Data")) == b"Mounted Data",
        "Mounted Data literal drifted",
    )
    _require(
        _at(image, sections, 0x3B5CF04, 6) == bytes.fromhex("41 B8 2D 03 00 00"),
        "virtualfilesystem_physfs.cpp source line 813 drifted",
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
    print("physfs-mounted-data-observer-source-contract: GREEN_STATIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
