"""Locate exact-build RTTI/vtable owners of contact and combat daily ticks.

This is an offline identity check.  Adjacent vtable entries do not establish
the order in which separate manager objects are called by the game loop.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile


EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
SLOTS = {"unit_contact_daily": 0x43404B8, "combat_daily": 0x43407C0}


def inspect(exe: Path) -> dict:
    raw = exe.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXE_SHA256:
        raise ValueError("CK3 EXE bytes do not match 1.19.0.6 contract")
    image = pefile.PE(data=raw, fast_load=True)
    base = image.OPTIONAL_HEADER.ImageBase
    rows = {}
    for label, slot in SLOTS.items():
        target = struct.unpack("<Q", image.get_data(slot, 8))[0] - base
        candidates = []
        for start in range(slot & ~7, slot - 0x2000, -8):
            pointer = struct.unpack("<Q", image.get_data(start - 8, 8))[0]
            col_rva = pointer - base
            if not 0 < col_rva < image.OPTIONAL_HEADER.SizeOfImage:
                continue
            col = image.get_data(col_rva, 24)
            if len(col) != 24:
                continue
            signature, offset, displacement, type_rva, hierarchy_rva, self_rva = struct.unpack("<6I", col)
            if signature != 1 or self_rva != col_rva or offset > 0x1000:
                continue
            name = image.get_data(type_rva + 16, 256).split(b"\0", 1)[0]
            if not name.startswith(b".?AV"):
                continue
            candidates.append({
                "vtable_start_rva": f"0x{start:X}",
                "slot_index": (slot - start) // 8,
                "type_name": name.decode("ascii", errors="replace"),
                "col_rva": f"0x{col_rva:X}",
                "hierarchy_rva": f"0x{hierarchy_rva:X}",
                "subobject_offset": offset,
                "constructor_displacement": displacement,
            })
        if not candidates:
            raise ValueError(f"no RTTI owner found for 0x{slot:X}")
        rows[label] = {"slot_rva": f"0x{slot:X}", "target_rva": f"0x{target:X}",
                       "nearest_rtti_owner": candidates[0]}
    return {"schema": "ck3.battle_daily_vtables.v1", "game_build": "1.19.0.6",
            "exe_sha256": EXE_SHA256.upper(), "rows": rows,
            "proves_cross_manager_call_order": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = inspect(arguments.exe)
    with arguments.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
