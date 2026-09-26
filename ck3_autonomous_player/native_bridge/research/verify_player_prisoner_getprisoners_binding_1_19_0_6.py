#!/usr/bin/env python3
"""Verify the C57 exact-build prisoner collection entry without starting CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile


CONTRACT = Path(__file__).with_name(
    "player_prisoner_getprisoners_binding_1_19_0_6.json"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    expected = json.loads(CONTRACT.read_text(encoding="utf-8"))
    data = args.exe.read_bytes()
    image = pefile.PE(data=data, fast_load=True)
    build = expected["exact_build"]
    require(len(data) == build["executable_size"], "EXE size mismatch")
    require(hashlib.sha256(data).hexdigest().upper() == build["executable_sha256"],
            "EXE SHA mismatch")
    require(image.OPTIONAL_HEADER.ImageBase == int(build["image_base"], 16),
            "image base mismatch")

    def read(rva: int, size: int) -> bytes:
        offset = image.get_offset_from_rva(rva)
        return data[offset : offset + size]

    def check_function(entry: dict[str, str]) -> None:
        start = int(entry["start_rva"], 16)
        end = int(entry["end_rva_exclusive"], 16)
        require(start < end, "empty function range")
        require(hashlib.sha256(read(start, end - start)).hexdigest().upper() == entry["sha256"],
                f"function SHA mismatch at 0x{start:X}")

    def relative_target(instruction_rva: int, displacement_offset: int,
                        instruction_size: int) -> int:
        displacement = struct.unpack(
            "<i", read(instruction_rva + displacement_offset, 4)
        )[0]
        return instruction_rva + instruction_size + displacement

    character = expected["character_get_prisoners"]
    court = expected["court_window_get_prisoners"]
    require(read(int(character["name_rva"], 16), 13) == b"GetPrisoners\0",
            "name anchor mismatch")
    for entry in (character["registration_function"], character["wrapper_function"],
                  character["backing_getter"], court["registration_function"],
                  court["wrapper_function"]):
        check_function(entry)
    require(struct.unpack("<Q", read(int(character["registration_table_entry_rva"], 16), 8))[0] == (
        image.OPTIONAL_HEADER.ImageBase + int(character["registration_function"]["start_rva"], 16)
    ), "Character registration table mismatch")
    require(struct.unpack("<Q", read(int(court["registration_table_entry_rva"], 16), 8))[0] == (
        image.OPTIONAL_HEADER.ImageBase + int(court["registration_function"]["start_rva"], 16)
    ), "CourtWindow registration table mismatch")
    # Both name copies load the first eight bytes as movsd. A simple LEA-only
    # xref scan misses these two independent reflected registrations.
    require(read(int(character["name_copy_rva"], 16), 4) == bytes.fromhex("F2 0F 10 05"),
            "Character name copy opcode mismatch")
    require(read(int(court["same_name_copy_rva"], 16), 4) == bytes.fromhex("F2 0F 10 05"),
            "CourtWindow name copy opcode mismatch")
    edges = (
        (0x50E409, 4, 8, int(character["name_rva"], 16)),
        (0xFB2AB, 4, 8, int(character["name_rva"], 16)),
        (0x50E483, 3, 7, 0x26233E0),
        (0x50E48E, 1, 5, 0x97EA90),
        (0x26233EE, 1, 5, 0x2614F30),
        (0xFB2D0, 3, 7, 0xF4C090),
        (0xFB2E2, 1, 5, 0xF4C0D0),
        (0xF4C0A2, 1, 5, 0xF482D0),
    )
    for source, displacement_offset, instruction_size, target in edges:
        require(relative_target(source, displacement_offset, instruction_size) == target,
                f"registration edge mismatch at 0x{source:X}")
    require(read(0x2614F30, 0x18) == bytes.fromhex(
        "48 8B 81 B8 01 00 00 48 85 C0 74 07 48 05 D8 00 00 00 C3 E9 C8 DD F9 FE"
    ), "borrowed collection getter mismatch")
    # The adjacent native relationship search reads +0 and +0xC and scans
    # four-byte elements against CCharacter+0x18. This is layout evidence,
    # not a substitute for a paused full collection read.
    require(read(0x2614F99, 0x2D) == bytes.fromhex(
        "48 8B 0B 48 63 53 0C 48 8D 14 91 4C 8D 84 24 F0 01 00 00"
        " E8 0F 06 20 FE 48 63 53 0C 48 8B 0B 4C 8D 04 91 45 33 E4"
        " 49 3B C0 49 0F 44 C4"
    ), "four-byte identity array search mismatch")
    require(read(0x2614FDC, 7) == bytes.fromhex("8B 45 18 41 39 46 18"),
            "full character identity comparison mismatch")
    print("GREEN_STATIC prisoner GetPrisoners binding 1.19.0.6; no live reader")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
