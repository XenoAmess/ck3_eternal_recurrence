#!/usr/bin/env python3
"""Read-only exact-build discovery of the stock embark-cost GUI binding.

This locates registration/code candidates only. It does not call CK3 code,
open a game process, or prove that a value is safe for a cash receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP
import pefile


EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
NAME = b"GetEmbarkCost\0"
NAME_RVA = 0x4101938
NAME_XREF_RVA = 0xE1659
NAME_BUILDER_BEGIN_RVA = 0xE1610
NAME_BUILDER_END_RVA = 0xE1770


def inspect(exe: Path) -> dict[str, object]:
    binary = exe.read_bytes()
    digest = hashlib.sha256(binary).hexdigest().upper()
    if digest != EXPECTED_EXE_SHA256:
        raise ValueError("CK3 executable SHA-256 mismatch")
    pe = pefile.PE(data=binary, fast_load=True)
    name_offset = binary.find(NAME)
    if name_offset < 0 or binary.find(NAME, name_offset + 1) >= 0:
        raise ValueError("GetEmbarkCost name is absent or ambiguous")
    if pe.get_rva_from_offset(name_offset) != NAME_RVA:
        raise ValueError("GetEmbarkCost name RVA changed")
    base = pe.OPTIONAL_HEADER.ImageBase
    start = pe.get_offset_from_rva(NAME_BUILDER_BEGIN_RVA)
    end = pe.get_offset_from_rva(NAME_BUILDER_END_RVA)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    instructions = list(decoder.disasm(
        binary[start:end], base + NAME_BUILDER_BEGIN_RVA,
    ))
    name_xrefs = [
        row for row in instructions
        if row.address - base == NAME_XREF_RVA
        and any(
            operand.type == X86_OP_MEM
            and operand.mem.base == X86_REG_RIP
            and row.address + row.size + operand.mem.disp == base + NAME_RVA
            for operand in row.operands
        )
    ]
    if len(name_xrefs) != 1:
        raise ValueError("GetEmbarkCost name xref changed")
    rows = [
        {"rva": hex(row.address - base), "mnemonic": row.mnemonic,
         "operands": row.op_str}
        for row in instructions
    ]
    return {
        "status": "static_gui_name_builder_candidate_only",
        "exe_sha256": digest,
        "name_rva": hex(NAME_RVA),
        "xref_rva": hex(NAME_XREF_RVA),
        "safe_to_call_from_live_bridge": False,
        "same_frame_amount_observed": False,
        "name_builder_disassembly": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.exe), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
