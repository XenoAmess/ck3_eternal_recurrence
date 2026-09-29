#!/usr/bin/env python3
"""Verify exact-build anchors for the read-only feast guest route proof."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
CODE = {
    # Planner's selected 16-byte rows and parallel cached join vector.
    0x10B19D0: bytes.fromhex("4D 8B B5 78 16 00 00 41 83 7C 3E 08 FF"),
    0x10B19E3: bytes.fromhex("49 8B 85 30 1A 00 00 80 3C 06 00"),
    # Zero copied selected rows take the ordinary Commit branch.
    0x10B1AD2: bytes.fromhex("85 DB 75 0D 49 8B CD E8 12 F9 FF FF"),
    # Commit refreshes the planner; it is not invoked by this verifier.
    0x10B13F0: bytes.fromhex("48 89 5C 24 10 57 48 81 EC 10 0A 00 00"),
    # Existing candidate reader's active-rule/group and GUI list anchors.
    0x10B0796: bytes.fromhex("4C 8D B9 90 15 00 00"),
    0x10B07A3: bytes.fromhex("48 81 C1 18 1A 00 00"),
    0x151CD75: bytes.fromhex("48 8B 90 90 15 00 00"),
}


def verify(executable: Path) -> dict[str, object]:
    raw = executable.read_bytes()
    actual_sha256 = hashlib.sha256(raw).hexdigest().upper()
    image = pefile.PE(data=raw, fast_load=True)
    mismatches = []
    if actual_sha256 != EXE_SHA256:
        mismatches.append("executable_sha256")
    for rva, expected in CODE.items():
        offset = image.get_offset_from_rva(rva)
        if raw[offset : offset + len(expected)] != expected:
            mismatches.append(f"code:0x{rva:X}")
    return {
        "schema": "xar.ck3.activity_feast_guest_route_proof_abi/1.19.0.6-v1",
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
