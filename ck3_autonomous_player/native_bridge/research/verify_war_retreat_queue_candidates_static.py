"""Bounded exact-build RTTI check for war-AI-adjacent queue producers.

The listed instructions are candidate locations, not a complete queue census.
No game process is started or attached.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP
import pefile


EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
MOVE_UNIT_PRIMARY_VTABLE = 0x432BF18
SITES = {
    0x183E484: (0x183E423, 0x183E42F),
    0x183E674: (0x183E642, 0x183E64E),
    0x183E7BA: (0x183E77A, 0x183E786),
    0x183E918: (0x183E8E5, 0x183E8F1),
    0x187BBDB: (0x187BB77, 0x187BB7E),
    0x187C7F1: (0x187C7B8, 0x187C7C4),
}


def instruction(pe: pefile.PE, decoder: Cs, rva: int):
    code = pe.get_data(rva, 15)
    insn = next(decoder.disasm(code, pe.OPTIONAL_HEADER.ImageBase + rva), None)
    if insn is None or insn.address != pe.OPTIONAL_HEADER.ImageBase + rva:
        raise ValueError(f"cannot decode at 0x{rva:x}")
    return insn


def vtable_identity(pe: pefile.PE, address_point_rva: int) -> dict[str, object]:
    base = pe.OPTIONAL_HEADER.ImageBase
    col_va = struct.unpack("<Q", pe.get_data(address_point_rva - 8, 8))[0]
    col_rva = col_va - base
    signature, subobject_offset, _cd, type_rva, _hier, _self = struct.unpack(
        "<6I", pe.get_data(col_rva, 24)
    )
    if signature != 1:
        raise ValueError(f"bad COL at 0x{col_rva:x}")
    name = pe.get_data(type_rva + 16, 128).split(b"\0", 1)[0].decode("ascii")
    return {
        "address_point_rva": f"0x{address_point_rva:x}",
        "col_rva": f"0x{col_rva:x}",
        "subobject_offset": subobject_offset,
        "type_name": name,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    raw = args.exe.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXE_SHA256:
        raise ValueError("exact-build EXE SHA mismatch")
    pe = pefile.PE(data=raw, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    rows = []
    for submit_rva, vtable_rvas in SITES.items():
        submit = instruction(pe, decoder, submit_rva)
        if submit.mnemonic != "call" or int(submit.op_str, 16) - base != 0x973E00:
            raise ValueError(f"queue submit changed at 0x{submit_rva:x}")
        identities = []
        for source_rva in vtable_rvas:
            insn = instruction(pe, decoder, source_rva)
            operands = [
                operand for operand in insn.operands
                if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP
            ]
            if insn.mnemonic != "lea" or len(operands) != 1:
                raise ValueError(f"vtable load changed at 0x{source_rva:x}")
            address_point_rva = source_rva + insn.size + operands[0].mem.disp
            identities.append({
                "source_rva": f"0x{source_rva:x}",
                "instruction_bytes": insn.bytes.hex(),
                **vtable_identity(pe, address_point_rva),
            })
        if identities[0]["type_name"] != identities[1]["type_name"]:
            raise ValueError(f"two subobjects disagree at 0x{submit_rva:x}")
        rows.append({
            "submit_rva": f"0x{submit_rva:x}",
            "submit_bytes": submit.bytes.hex(),
            "is_move_unit_command": any(
                int(row["address_point_rva"], 16) == MOVE_UNIT_PRIMARY_VTABLE
                for row in identities
            ),
            "vtables": identities,
        })
    print(json.dumps({
        "schema": "xar.war-retreat-queue-candidates-static.v1",
        "exe_sha256": sha,
        "scope": "six fixed queue sites in war-AI-adjacent code; not a complete census",
        "live_execution_performed": False,
        "sites": rows,
    }, indent=2))


if __name__ == "__main__":
    main()
