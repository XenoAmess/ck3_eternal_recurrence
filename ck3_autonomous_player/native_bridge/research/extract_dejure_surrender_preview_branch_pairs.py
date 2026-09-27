#!/usr/bin/env python3
"""Freeze the two exact-build setup_de_jure_cb preview tuple producers.

This is an EXE-only static receipt. It never calls CK3 code and does not
establish that the complete preview or surrender effect is side-effect-free.
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
EXE_SIZE = 95_206_008
BRANCHES = ((0x28B21E0, 0x28B23BF), (0x28B1EB0, 0x28B21DA))


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

    def instruction(rva: int, mnemonic: str, operands: str) -> dict[str, str]:
        decoded = list(md.disasm(at(rva, 16), rva, count=1))
        if len(decoded) != 1 or (decoded[0].mnemonic, decoded[0].op_str) != (mnemonic, operands):
            raise ValueError(f"instruction at RVA 0x{rva:X} changed")
        return {"rva": f"0x{rva:X}", "bytes": decoded[0].bytes.hex().upper(),
                "instruction": f"{mnemonic} {operands}"}

    def direct_call(rva: int, target: int) -> dict[str, str]:
        raw = at(rva, 5)
        if raw[0] != 0xE8 or rva + 5 + struct.unpack_from("<i", raw, 1)[0] != target:
            raise ValueError(f"direct call at RVA 0x{rva:X} changed")
        return {"call_rva": f"0x{rva:X}", "target_rva": f"0x{target:X}",
                "bytes": raw.hex().upper()}

    functions = []
    for start, last_ret in BRANCHES:
        raw = at(start, last_ret + 1 - start)
        decoded = list(md.disasm(raw, start))
        if not decoded or decoded[-1].address != last_ret or decoded[-1].mnemonic != "ret":
            raise ValueError(f"branch extent at RVA 0x{start:X} changed")
        if any(ins.mnemonic == "ret" for ins in decoded[:-1]):
            raise ValueError(f"premature return in branch 0x{start:X}")
        functions.append({"entry_rva": f"0x{start:X}", "last_ret_rva": f"0x{last_ret:X}",
                          "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest().upper()})

    preview = list(md.disasm(at(0x2E9FA10, 0x2E9FC93 - 0x2E9FA10), 0x2E9FA10))
    if not preview or preview[-1].address != 0x2E9FC92 or preview[-1].mnemonic != "ret":
        raise ValueError("setup-de-jure preview extent changed")
    # This negative check only covers direct operands of the entry function;
    # its callees can still resolve or modify the change referent.
    direct_change_scope_reads = [
        f"0x{ins.address:X}" for ins in preview if "[rbx + 0x1b0]" in ins.op_str
    ]
    if direct_change_scope_reads:
        raise ValueError("preview entry gained a direct +0x1B0 scope operand")

    return {
        "schema": "xar.ck3.dejure-surrender-preview-branch-pairs.v1",
        "status": "STATIC_INTERMEDIATE_TUPLES_ONLY",
        "exact_build": {"version": "1.19.0.6-steam23530548", "exe_sha256": digest},
        "branch_functions": functions,
        "branch_calls": {
            "title_scope_present": direct_call(0x2EA0012, 0x28B21E0),
            "title_scope_absent": direct_call(0x2EA001C, 0x28B1EB0),
            "present_local_id_collection": direct_call(0x28B2289, 0x20B4E10),
            "absent_local_table_population": direct_call(0x28B1F87, 0x28B1C50),
            "absent_local_id_collection": direct_call(0x28B1FC1, 0x26287C0),
        },
        "present_branch_pair_writes": [
            instruction(0x28B2305, "mov", "dword ptr [rax + rcx*8], ebp"),
            instruction(0x28B2308, "mov", "dword ptr [rax + rcx*8 + 4], r12d"),
            instruction(0x28B235B, "mov", "dword ptr [rax + rcx*8], ebp"),
            instruction(0x28B235E, "mov", "dword ptr [rax + rcx*8 + 4], r12d"),
        ],
        "absent_branch_pair_writes": [
            instruction(0x28B2097, "mov", "dword ptr [rax + rdx*8], edi"),
            instruction(0x28B209A, "mov", "dword ptr [rax + rdx*8 + 4], ecx"),
            instruction(0x28B20F6, "mov", "dword ptr [rax + rcx*8], edi"),
            instruction(0x28B20F9, "mov", "dword ptr [rax + rcx*8 + 4], edx"),
        ],
        "absent_branch_local_table_write": instruction(0x28B1DB9, "mov", "dword ptr [r8], ecx"),
        "preview_entry": {
            "entry_rva": "0x2E9FA10", "last_ret_rva": "0x2E9FC92",
            "direct_effect_change_scope_0x1b0_operands": direct_change_scope_reads,
            "effect_title_scope_0x260_lea": instruction(0x2E9FB8A, "lea", "rcx, [rbx + 0x260]"),
            "read_boundary": "No direct +0x1B0 operand in this bounded entry; indirect callees and execute path remain unresolved.",
        },
        "interpretation": {
            "branch_output": "Both branches append 8-byte pairs of two 32-bit integers to the r8 output vector supplied by the preview helper.",
            "local_scratch": "The absent branch also fills a caller-stack dword table through 0x28B1C50; direct writes shown here do not identify final title/vassal operations.",
            "not_proven": [
                "Transitive write set of called helpers or complete preview side-effect safety",
                "Ownership and referent of the separate inline change scope at effect +0x1B0",
                "Resolved title/holder/liege/vassal operation rows or signed resources",
            ],
            "ck3_launched": False, "surrender_submitted": False,
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
