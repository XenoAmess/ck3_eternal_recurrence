#!/usr/bin/env python3
"""Read-only exact-build anchors for physician trait-XP effect; no live hook grant."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
INSTRUCTIONS = {
    "add_trait_xp_registration_name": (0x5D1841, "488d0530d1e803"),
    "add_trait_xp_factory_vtable": (0x2ED205C, "488d053dd25801488907"),
    "xp_context_kind": (0x2ED12BC, "488b02"),
    "xp_context_character_id": (0x2ED12C5, "66833804"),
    "xp_trait_id": (0x2ED14B6, "8b4610"),
    "xp_character_trait_vector": (0x2ED14C1, "488b8ff0000000"),
    "xp_flat_track_offset": (0x2ED1523, "e848d573ff"),
    "xp_vector": (0x2ED152D, "488b8738010000"),
    "xp_old_value": (0x2ED1534, "488b14c8"),
    "xp_new_value_write": (0x2ED158B, "498917"),
    "add_trait_registration_name": (0x5D1001, "488d05285cb203"),
    "add_trait_factory_vtable": (0x2ED1BC3, "488d05a6db5801"),
    "add_trait_composite_child_call": (0x3380EE3, "488b0b488bd6e812fbffff"),
    "remove_trait_vector_decrement": (0x260F22B, "ff8ffc000000"),
}
POINTERS = {
    "add_trait_xp_execute_vtable_slot": (0x445F350, 0x2ED12B0),
    "add_trait_execute_vtable_slot": (0x445F820, 0x3380EC0),
}


def verify(exe: Path) -> dict[str, object]:
    binary = exe.read_bytes()
    digest = hashlib.sha256(binary).hexdigest().upper()
    if digest != EXE_SHA256:
        raise ValueError(f"EXE SHA-256 mismatch: {digest}")
    image = pefile.PE(data=binary, fast_load=True)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    rows = []
    for name, (rva, expected_hex) in INSTRUCTIONS.items():
        expected = bytes.fromhex(expected_hex)
        actual = binary[image.get_offset_from_rva(rva):][:len(expected)]
        if actual != expected:
            raise ValueError(f"{name} RVA {rva:#x}: bytes mismatch")
        decoded = list(decoder.disasm(actual, image.OPTIONAL_HEADER.ImageBase + rva))
        if sum(len(row.bytes) for row in decoded) != len(expected):
            raise ValueError(f"{name} RVA {rva:#x}: incomplete instruction")
        rows.append({"name": name, "rva": f"0x{rva:X}", "bytes": expected_hex.upper()})
    for name, (rva, target_rva) in POINTERS.items():
        actual = struct.unpack_from("<Q", binary, image.get_offset_from_rva(rva))[0]
        expected = image.OPTIONAL_HEADER.ImageBase + target_rva
        if actual != expected:
            raise ValueError(f"{name} RVA {rva:#x}: pointer mismatch")
        rows.append({"name": name, "rva": f"0x{rva:X}", "target_rva": f"0x{target_rva:X}"})
    return {
        "status": "rankup_xp_branch_static_only",
        "exe_sha256": digest,
        "anchors": rows,
        "physician_random_node_identified": False,
        "physician_named_scope_identity_observed": False,
        "physician_effective_learning_observed": False,
        "physician_add_trait_write_proven": False,
        "physician_rankup_before_after_observed": False,
        "safe_to_enable_physician_field_hook": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(verify(arguments.exe), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
