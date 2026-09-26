#!/usr/bin/env python3
"""Classify two generic queue producers by exact-build command RTTI.

This is an intentionally bounded negative check, not a global AI census.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
IMAGE_BASE = 0x140000000
MOVE_MAIN = 0x432BF18
MOVE_SECONDARY = 0x432BFB0
PRODUCERS = (
    {
        "submit_rva": 0x187B5DE,
        "main_lea_rva": 0x187B54F,
        "secondary_lea_rva": 0x187B55A,
        "main_vtable_rva": 0x40829F8,
        "secondary_vtable_rva": 0x40829C8,
        "rtti": ".?AVCSendCharacterInteractionCommand@@",
    },
    {
        "submit_rva": 0x187BA0C,
        "main_lea_rva": 0x187B9D8,
        "secondary_lea_rva": 0x187B9E3,
        "main_vtable_rva": 0x43304F0,
        "secondary_vtable_rva": 0x4330588,
        "rtti": ".?AVCExtendMercenaryCompanyCommand@@",
    },
)


def checked_lea_target(exe: bytes, image: pefile.PE, rva: int) -> int:
    offset = image.get_offset_from_rva(rva)
    instruction = exe[offset : offset + 7]
    if instruction[:3] not in (b"\x48\x8d\x05", b"\x48\x8d\x15"):
        raise ValueError(f"RVA 0x{rva:X}: expected lea RIP-relative vtable")
    return rva + 7 + struct.unpack("<i", instruction[3:])[0]


def checked_rtti(exe: bytes, image: pefile.PE, vtable_rva: int) -> tuple[str, int]:
    pointer = image.get_offset_from_rva(vtable_rva - 8)
    col_rva = struct.unpack_from("<Q", exe, pointer)[0] - IMAGE_BASE
    col_offset = image.get_offset_from_rva(col_rva)
    signature, displacement, _, type_rva, _, self_rva = struct.unpack_from("<6I", exe, col_offset)
    if signature != 1 or self_rva != col_rva or displacement not in (0, 24):
        raise ValueError(f"RVA 0x{vtable_rva:X}: unexpected MSVC COL")
    name_offset = image.get_offset_from_rva(type_rva + 16)
    name = exe[name_offset : name_offset + 160].split(b"\0", 1)[0].decode("ascii")
    return name, displacement


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    args = parser.parse_args()
    exe = args.exe.read_bytes()
    digest = hashlib.sha256(exe).hexdigest().upper()
    if digest != EXE_SHA256:
        raise ValueError(f"unexpected EXE SHA-256: {digest}")
    image = pefile.PE(data=exe, fast_load=True)
    if image.OPTIONAL_HEADER.ImageBase != IMAGE_BASE:
        raise ValueError("unexpected PE image base")
    rows = []
    for row in PRODUCERS:
        submit_rva = row["submit_rva"]
        submit_offset = image.get_offset_from_rva(submit_rva)
        instruction = exe[submit_offset : submit_offset + 5]
        if instruction[0] != 0xE8 or submit_rva + 5 + struct.unpack("<i", instruction[1:])[0] != 0x973E00:
            raise ValueError(f"RVA 0x{submit_rva:X}: not generic queue submit")
        if checked_lea_target(exe, image, row["main_lea_rva"]) != row["main_vtable_rva"]:
            raise ValueError(f"RVA 0x{submit_rva:X}: main vtable mismatch")
        if checked_lea_target(exe, image, row["secondary_lea_rva"]) != row["secondary_vtable_rva"]:
            raise ValueError(f"RVA 0x{submit_rva:X}: secondary vtable mismatch")
        main_name, main_offset = checked_rtti(exe, image, row["main_vtable_rva"])
        secondary_name, secondary_offset = checked_rtti(exe, image, row["secondary_vtable_rva"])
        if (main_name, secondary_name, main_offset, secondary_offset) != (row["rtti"], row["rtti"], 0, 24):
            raise ValueError(f"RVA 0x{submit_rva:X}: unexpected command RTTI")
        if row["main_vtable_rva"] == MOVE_MAIN or row["secondary_vtable_rva"] == MOVE_SECONDARY:
            raise ValueError("candidate unexpectedly is CMoveUnitCommand")
        rows.append({"submit_rva": f"0x{submit_rva:X}", "command_rtti": main_name,
                     "main_vtable_rva": f"0x{row['main_vtable_rva']:X}",
                     "secondary_vtable_rva": f"0x{row['secondary_vtable_rva']:X}"})
    print(json.dumps({"status": "static_source_verified", "exe_sha256": EXE_SHA256,
                      "producers": rows, "global_active_retreat_policy_excluded": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
