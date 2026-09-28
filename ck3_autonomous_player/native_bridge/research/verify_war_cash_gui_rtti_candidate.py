#!/usr/bin/env python3
"""Verify exact CK3 GUI type fingerprints for passive war-cash research.

This checks static RTTI and vtable bytes only. A type fingerprint does not
locate a unique live object or prove that a GUI cache is current.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
TYPES = {
    "CHudTopBar": {
        "name_rva": 0x51E1900,
        "col_rva": 0x464A948,
        "vtable_rva": 0x40E6F68,
        "first_method_rva": 0xD46F60,
        "secondary_col_rva": 0x464A970,
        "secondary_vtable_rva": 0x40E7038,
        "secondary_offset": 0x10,
    },
    "CMilitaryView": {
        "name_rva": 0x5260220,
        "col_rva": 0x46CA510,
        "vtable_rva": 0x4135EE0,
        "first_method_rva": 0x11F3170,
        "secondary_col_rva": 0x46CA538,
        "secondary_vtable_rva": 0x4135FB0,
        "secondary_offset": 0x10,
    },
    "CFleetEmbarkMapIcon": {
        "name_rva": 0x51FEE98,
        "col_rva": 0x4668A58,
        "vtable_rva": 0x41003F0,
        "first_method_rva": 0xE81850,
    },
}


def inspect(exe: Path) -> dict[str, object]:
    binary = exe.read_bytes()
    digest = hashlib.sha256(binary).hexdigest().upper()
    if digest != EXE_SHA256:
        raise ValueError("CK3 executable SHA-256 mismatch")
    pe = pefile.PE(data=binary, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase

    def at(rva: int, fmt: str) -> tuple[int, ...]:
        return struct.unpack_from(fmt, binary, pe.get_offset_from_rva(rva))

    results: dict[str, object] = {}
    for name, expected in TYPES.items():
        name_offset = pe.get_offset_from_rva(expected["name_rva"])
        type_name = f".?AV{name}@@".encode("ascii") + b"\0"
        if binary[name_offset:name_offset + len(type_name)] != type_name:
            raise ValueError(f"{name} RTTI type name changed")
        type_descriptor_rva = expected["name_rva"] - 0x10
        for key_prefix, object_offset in (("", 0), ("secondary_", 0x10)):
            col_key = key_prefix + "col_rva"
            if col_key not in expected:
                continue
            col_rva = expected[col_key]
            vtable_rva = expected[key_prefix + "vtable_rva"]
            col = at(col_rva, "<6I")
            if col[0] != 1 or col[1] != object_offset or col[3] != type_descriptor_rva or col[5] != col_rva:
                raise ValueError(f"{name} {key_prefix}complete object locator changed")
            if at(vtable_rva - 8, "<Q")[0] != base + col_rva:
                raise ValueError(f"{name} {key_prefix}vtable locator changed")
        if at(expected["vtable_rva"], "<Q")[0] != base + expected["first_method_rva"]:
            raise ValueError(f"{name} first virtual method changed")
        results[name] = {
            "primary_vtable_rva": hex(expected["vtable_rva"]),
            "secondary_vtable_rva": (hex(expected["secondary_vtable_rva"])
            if "secondary_vtable_rva" in expected else None),
        }

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    constructor_anchors = {
        0xD4661D: ("mov", "qword ptr [r13 + 0xc8], rbx"),
        0xD46624: ("mov", "qword ptr [r13 + 0xd0], rdi"),
        0xD46649: ("lea", "rcx, [rip + 0x33a0918]"),
        0xD46650: ("mov", "qword ptr [r13], rcx"),
        0xD46654: ("lea", "rcx, [rip + 0x33a09dd]"),
        0xD4665B: ("mov", "qword ptr [r13 + 0x10], rcx"),
    }
    for rva, expected_instruction in constructor_anchors.items():
        offset = pe.get_offset_from_rva(rva)
        rows = list(decoder.disasm(binary[offset:offset + 16], base + rva, count=1))
        if len(rows) != 1 or (rows[0].mnemonic, rows[0].op_str) != expected_instruction:
            raise ValueError(f"CHudTopBar constructor changed at {rva:#x}")

    # The primary CHudTopBar deleting destructor frees a 0xFA0-byte object.
    # This bounds a passive fingerprint read, not a live instance search.
    destructor_bytes = binary[pe.get_offset_from_rva(0xD46F79):
                              pe.get_offset_from_rva(0xD46F79) + 9]
    if destructor_bytes != bytes.fromhex("BAA00F0000488BCFE8"):
        raise ValueError("CHudTopBar object-size anchor changed")

    return {
        "status": "static_gui_type_fingerprints_only",
        "exe_sha256": digest,
        "hud_object_size_candidate": 0xFA0,
        "types": results,
        "hud_constructor_rva": "0xd465a0",
        "hud_constructor_owner_slot_candidate": "0xc8",
        "unique_live_instance_proven": False,
        "cache_same_native_revision_proven": False,
        "war_cash_formal_eligible": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.exe), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
