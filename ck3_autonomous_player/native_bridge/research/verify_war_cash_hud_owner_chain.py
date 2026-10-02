#!/usr/bin/env python3
"""Verify bounded static owner edges for the CK3 1.19.0.6 HUD top bar.

This never reads game memory. It proves executable instructions and RTTI,
not the existence, freshness or uniqueness of a live GUI object.
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
EXPECTED_TYPES = {
    "CIngameInterfaceIdlerGfx": (0x40B1D30, 0x45F5BC0, 0x501EF50,
                                  0xAA4070, 0xAA4350),
    "CIngameInterfaceHandler": (0x40AF630, 0x45F3F28, 0x5191068,
                                  0xA72A80, 0xA734B0),
}
INSTRUCTIONS = {
    0xA71E3E: ("lea", "rax, [rip + 0x363d7eb]"),
    0xA71E45: ("mov", "qword ptr [r14], rax"),
    0xA71E48: ("lea", "rax, [rip + 0x363d859]"),
    0xA71E4F: ("mov", "qword ptr [r14 + 0x58], rax"),
    0xAA435A: ("mov", "rbx, rcx"),
    0xAA435D: ("mov", "ecx, 0x16ce8"),
    0xAA437A: ("mov", "rdx, qword ptr [rbx + 0x20]"),
    0xAA4381: ("call", "0x140a71e00"),
    0xAA43A0: ("mov", "qword ptr [rbx + 0x88], rdi"),
    0xA734CF: ("mov", "r14, rcx"),
    0xA737E2: ("mov", "rbx, qword ptr [r14 + 0x40]"),
    0xA737E6: ("mov", "ecx, 0xfa0"),
    0xA737F7: ("mov", "r8, r14"),
    0xA737FA: ("mov", "rdx, rbx"),
    0xA73800: ("call", "0x140d465a0"),
    0xA7380D: ("mov", "qword ptr [r14 + 0x470], rax"),
    0xAA43C8: ("mov", "rcx, qword ptr [rip + 0x4c6b3e9]"),
    0xAA43D8: ("mov", "rcx, qword ptr [rcx + 0x10]"),
    0xAA43DC: ("lea", "r9, [rip + 0x457ab6d]"),
    0xAA43E3: ("lea", "r8, [rip + 0x457ab3e]"),
    0xAA43F4: ("call", "0x143e631f4"),
    0xAA43FE: ("mov", "rcx, qword ptr [rax + 0x88]"),
}


def inspect(exe: Path) -> dict[str, object]:
    binary = exe.read_bytes()
    digest = hashlib.sha256(binary).hexdigest().upper()
    if digest != EXE_SHA256:
        raise ValueError("CK3 executable SHA-256 mismatch")
    pe = pefile.PE(data=binary, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    if base != 0x140000000:
        raise ValueError("CK3 executable image base changed")

    def at(rva: int, fmt: str) -> tuple[int, ...]:
        return struct.unpack_from(fmt, binary, pe.get_offset_from_rva(rva))

    for name, (vtable, col_rva, descriptor, first, second) in EXPECTED_TYPES.items():
        col = at(col_rva, "<6I")
        hierarchy_rva = 0x45F56B8 if name == "CIngameInterfaceIdlerGfx" else 0x45F2D48
        if col != (1, 0, 0, descriptor, hierarchy_rva, col_rva):
            raise ValueError(f"{name} primary COL changed")
        label = f".?AV{name}@@".encode("ascii") + b"\0"
        offset = pe.get_offset_from_rva(descriptor + 0x10)
        if binary[offset:offset + len(label)] != label:
            raise ValueError(f"{name} RTTI name changed")
        if (at(vtable - 8, "<Q")[0] != base + col_rva
                or at(vtable, "<Q")[0] != base + first
                or at(vtable + 8, "<Q")[0] != base + second):
            raise ValueError(f"{name} vtable changed")
    if (at(0x45F3F00, "<6I")
            != (1, 0x58, 0, 0x5191068, 0x45F2D48, 0x45F3F00)
            or at(0x40AF6A0, "<Q")[0] != base + 0x45F3F00
            or at(0x40AF6A8, "<Q")[0] != base + 0xAA231C):
        raise ValueError("CIngameInterfaceHandler secondary vtable changed")

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    for rva, expected in INSTRUCTIONS.items():
        offset = pe.get_offset_from_rva(rva)
        actual = list(decoder.disasm(binary[offset:offset + 16], base + rva, count=1))
        if len(actual) != 1 or (actual[0].mnemonic, actual[0].op_str) != expected:
            raise ValueError(f"owner-chain instruction changed at {rva:#x}")

    # Validate the RIP and RTTI targets, not just the printed operand strings.
    if (0xAA43CF + 0x4C6B3E9 != 0x570F7B8
            or 0xAA43E3 + 0x457AB6D != 0x501EF50
            or 0xAA43EA + 0x457AB3E != 0x501EF28):
        raise ValueError("global/type-descriptor calculation changed")
    base_label = b".?AVCIdlerGfxBase@@\0"
    base_offset = pe.get_offset_from_rva(0x501EF28 + 0x10)
    if binary[base_offset:base_offset + len(base_label)] != base_label:
        raise ValueError("idler base RTTI name changed")

    return {
        "status": "static_owner_edges_only",
        "exe_sha256": digest,
        "candidate_global_slot_rva": "0x570f7b8",
        "candidate_chain": [
            "global pointer +0x10: CIdlerGfxBase* / candidate CIngameInterfaceIdlerGfx",
            "CIngameInterfaceIdlerGfx +0x88: CIngameInterfaceHandler*",
            "CIngameInterfaceHandler +0x470: CHudTopBar*",
        ],
        "handler_secondary_vtable_offset": "0x58",
        "static_constructor_and_holder_edges_proven": True,
        "unique_active_global_lifetime_proven": False,
        "live_pointer_chain_proven": False,
        "same_native_revision_cache_freshness_proven": False,
        "war_cash_formal_eligible": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path)
    args = parser.parse_args()
    if args.exe is None:
        import psutil

        paths = set()
        for process in psutil.process_iter(("name", "exe")):
            try:
                if (process.info["name"] or "").lower() == "ck3.exe":
                    paths.add(Path(process.info["exe"]))
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        if len(paths) != 1:
            raise ValueError("pass --exe when the exact CK3 process path is unavailable")
        args.exe = paths.pop()
    print(json.dumps(inspect(args.exe), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
