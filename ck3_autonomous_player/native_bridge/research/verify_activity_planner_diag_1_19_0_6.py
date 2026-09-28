#!/usr/bin/env python3
"""Check the exact native anchors used by the private planner diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
IMAGE_BASE = 0x140000000
CODE = {
    0x10AC0F3: bytes.fromhex("49 89 B6 D0 00 00 00"),
    0x1F3097A: bytes.fromhex("48 8B 59 78"),
    0x10B0DC3: bytes.fromhex("48 63 81 B0 1A 00 00"),
}
VTABLE = {
    0x41205F0: 0x10AC480,
    0x41205F0 + 7 * 8: 0x1F30970,
    0x41205F0 + 11 * 8: 0xAA33F0,
    0x41205F0 + 12 * 8: 0x10AE180,
    0x41206C8: 0x10C8454,
}


def verify(executable: Path) -> dict[str, object]:
    raw = executable.read_bytes()
    actual_sha256 = hashlib.sha256(raw).hexdigest().upper()
    image = pefile.PE(data=raw, fast_load=True)
    mismatches: list[str] = []
    if actual_sha256 != EXE_SHA256:
        mismatches.append("executable_sha256")
    if image.OPTIONAL_HEADER.ImageBase != IMAGE_BASE:
        mismatches.append("image_base")
    for rva, expected in CODE.items():
        at = image.get_offset_from_rva(rva)
        if raw[at : at + len(expected)] != expected:
            mismatches.append(f"code:0x{rva:X}")
    for rva, expected_target in VTABLE.items():
        at = image.get_offset_from_rva(rva)
        actual_target = struct.unpack_from("<Q", raw, at)[0]
        if actual_target != IMAGE_BASE + expected_target:
            mismatches.append(f"vtable:0x{rva:X}")
    return {
        "schema": "xar.ck3.activity_planner_diag_exact_abi.v1",
        "executable_sha256": actual_sha256,
        "verified": not mismatches,
        "mismatches": mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.exe)
    print(json.dumps(result, indent=2))
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
