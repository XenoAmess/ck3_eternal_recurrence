"""Freeze the two private observer entry and caller anchors to CK3 1.19.0.6."""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

EXPECTED_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
ANCHORS = {
    0x186B190: bytes.fromhex("48 89 5c 24 08 48 89 74 24 10 48 89 7c 24 18"),
    0x187235D: bytes.fromhex("e8 2e 8e ff ff"),
    0x973E00: bytes.fromhex("48 89 5c 24 08 4c 89 4c 24 20 57 48 83 ec 20"),
    0x186B2C5: bytes.fromhex("e8 36 8b 10 ff"),
}


def file_offset_for_rva(image: bytes, rva: int) -> int:
    if image[:2] != b"MZ":
        raise AssertionError("not a PE executable")
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    if image[pe : pe + 4] != b"PE\0\0":
        raise AssertionError("invalid PE signature")
    section_count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    section_table = pe + 24 + optional_size
    for index in range(section_count):
        header = section_table + 40 * index
        virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from(
            "<IIII", image, header + 8
        )
        if virtual_address <= rva < virtual_address + max(virtual_size, raw_size):
            offset = raw_pointer + (rva - virtual_address)
            if offset >= len(image):
                raise AssertionError(f"RVA 0x{rva:x} maps outside file")
            return offset
    raise AssertionError(f"RVA 0x{rva:x} has no PE section")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ck3-executable", type=Path, required=True)
    args = parser.parse_args()
    image = args.ck3_executable.read_bytes()
    actual_hash = hashlib.sha256(image).hexdigest()
    assert actual_hash == EXPECTED_SHA256, actual_hash
    for rva, expected in ANCHORS.items():
        offset = file_offset_for_rva(image, rva)
        actual = image[offset : offset + len(expected)]
        assert actual == expected, (hex(rva), actual.hex(), expected.hex())
    print("AI terminal reentry exact-build anchors: PASS")


if __name__ == "__main__":
    main()
