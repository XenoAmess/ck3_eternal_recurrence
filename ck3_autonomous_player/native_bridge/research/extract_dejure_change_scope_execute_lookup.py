#!/usr/bin/env python3
"""Freeze the exact-build execute-only lookup of setup_de_jure_cb change scope."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXE_SIZE = 95_206_008


def extract(exe: Path) -> dict[str, object]:
    data = exe.read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if len(data) != EXE_SIZE or digest != EXE_SHA256:
        raise ValueError("CK3 executable differs from frozen 1.19.0.6 build")
    image = pefile.PE(data=data, fast_load=True)
    md = Cs(CS_ARCH_X86, CS_MODE_64)

    def at(rva: int, size: int) -> bytes:
        offset = image.get_offset_from_rva(rva)
        value = data[offset : offset + size]
        if len(value) != size:
            raise ValueError(f"short read at RVA 0x{rva:X}")
        return value

    def ins(rva: int, mnemonic: str, operands: str) -> dict[str, str]:
        decoded = list(md.disasm(at(rva, 16), rva, count=1))
        if len(decoded) != 1 or (decoded[0].mnemonic, decoded[0].op_str) != (mnemonic, operands):
            raise ValueError(f"instruction at 0x{rva:X} changed")
        return {"rva": f"0x{rva:X}", "bytes": decoded[0].bytes.hex().upper(),
                "instruction": f"{mnemonic} {operands}"}

    def call(rva: int, target: int) -> dict[str, str]:
        raw = at(rva, 5)
        if raw[0] != 0xE8 or rva + 5 + struct.unpack_from("<i", raw, 1)[0] != target:
            raise ValueError(f"direct call at 0x{rva:X} changed")
        return {"call_rva": f"0x{rva:X}", "target_rva": f"0x{target:X}",
                "bytes": raw.hex().upper()}

    lookup_raw = at(0x2EA1D30, 0x2EA1DBA - 0x2EA1D30)
    decoded = list(md.disasm(lookup_raw, 0x2EA1D30))
    if not decoded or decoded[-1].address != 0x2EA1DB9 or decoded[-1].mnemonic != "ret":
        raise ValueError("change-scope lookup extent changed")
    if sum(i.mnemonic == "ret" for i in decoded) != 2:
        raise ValueError("change-scope lookup return paths changed")

    return {
        "schema": "xar.ck3.dejure-change-scope-execute-lookup.v1",
        "status": "STATIC_EXECUTE_LOOKUP_ONLY",
        "exact_build": {"version": "1.19.0.6-steam23530548", "exe_sha256": digest},
        "execute_path": {
            "effect_change_scope_offset": "0x1B0",
            "lea": ins(0x2E9F734, "lea", "rcx, [rsi + 0x1b0]"),
            "lookup_call": call(0x2E9F741, 0x2EA1D30),
            "returned_pointer_virtual_check": ins(0x2E9F74F, "call", "qword ptr [rdx + 8]"),
            "following_operation_helper": call(0x2E9F7F7, 0x24BD610),
        },
        "lookup": {
            "entry_rva": "0x2EA1D30", "last_ret_rva": "0x2EA1DB9",
            "byte_count": len(lookup_raw), "sha256": hashlib.sha256(lookup_raw).hexdigest().upper(),
            "scope_value_resolution": call(0x2EA1D4F, 0x336AB40),
            "tag_12_check": ins(0x2EA1D54, "cmp", "word ptr [rsp + 0x30], 0xc"),
            "global_table_base": ins(0x2EA1D6A, "mov", "rax, qword ptr [rcx + 0xd2b0]"),
            "global_table_count": ins(0x2EA1D71, "movsxd", "rcx, dword ptr [rcx + 0xd2bc]"),
            "candidate_id": ins(0x2EA1D81, "mov", "r8d, dword ptr [rsp + 0x38]"),
            "candidate_match": ins(0x2EA1D89, "cmp", "dword ptr [rcx + 8], r8d"),
            "candidate_pointer_return": ins(0x2EA1DA4, "mov", "rax, qword ptr [rax]"),
            "fallback_pointer_load": ins(0x2EA1DAD, "mov", "rax, qword ptr [rip + 0x29243e4]"),
        },
        "boundary": {
            "lookup_direction": "Execute resolves the inline +0x1B0 scope to a tag-12 ID and looks up a pointer in a global table; unmatched rows use a fallback pointer.",
            "not_proven": [
                "Actual War31 change-scope ID or resolved pointer",
                "Ownership and lifetime of the resolved title-and-vassal change object",
                "Transitive effects of virtual check or following operation helpers",
                "Final title/holder/liege/vassal operations and signed resources",
            ],
            "ck3_launched": False, "effect_invoked": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(extract(args.exe), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
