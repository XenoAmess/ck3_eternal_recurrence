#!/usr/bin/env python3
"""Read-only search for the stock MilitaryView military-expense getter registration.

This script does not open a game process or call a game function.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

EXPECTED_SHA = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
NAMES = ("GetAllRaisedGoldMilitaryExpenses", "GetGoldMilitaryExpenses",
         "GetAllRaisedTreasuryMilitaryExpenses")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    args = parser.parse_args()
    raw = args.exe.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA:
        raise ValueError("CK3 EXE SHA mismatch")
    image = pefile.PE(data=raw, fast_load=True)
    base = image.OPTIONAL_HEADER.ImageBase
    targets = {}
    for name in NAMES:
        position = raw.find(name.encode() + b"\0")
        if position < 0:
            print(f"{name}: absent")
            continue
        rva = image.get_rva_from_offset(position)
        targets[rva + base] = name
        print(f"{name}: offset={position:#x} rva={rva:#x}")
    code = next(section for section in image.sections if section.Name.rstrip(b"\0") == b".text")
    start = code.PointerToRawData
    body = raw[start:start + code.SizeOfRawData]
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    hits = []
    for instruction in decoder.disasm(body, base + code.VirtualAddress):
        for operand in instruction.operands:
            target = None
            if operand.type == X86_OP_IMM:
                target = operand.imm
            elif operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                target = instruction.address + instruction.size + operand.mem.disp
            if target in targets:
                hits.append((targets[target], instruction.address - base,
                             instruction.mnemonic, instruction.op_str))
    for row in hits:
        print(f"xref: {row[0]} rva={row[1]:#x} {row[2]} {row[3]}")


if __name__ == "__main__":
    main()
