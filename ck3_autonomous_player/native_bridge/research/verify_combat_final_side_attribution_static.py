#!/usr/bin/env python3
"""Verify the post-envelope side-attribution pass in exact CK3 1.19.0.6.

The verifier reads stock PE bytes only. It does not invoke CK3 functions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile
from capstone import CS_AC_WRITE, CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RBP, X86_REG_RSP


EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
DEFAULT_EXE = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe")
FUNCTION_START = 0x23C9770
FUNCTION_END = 0x23C98F5

SITES = {
    "pursuit_first_soft_write": (0x23CDA72, "48894120"),
    "pursuit_second_soft_write": (0x23CDC89, "49895f20"),
    "side_army_ids": (0x23C977A, "4c8b7110"),
    "army_regiment_ids": (0x23C97F1, "488b5838"),
    "regiment_current_int": (0x23C9839, "48634138"),
    "regiment_type_pointer": (0x23C9844, "4c8b4918"),
    "regiment_knight_id": (0x23C984F, "8b8148010000"),
    "current_q100000": (0x23C9848, "4869f8a0860100"),
    "row_type_compare": (0x23C9871, "4c3909"),
    "row_knight_compare": (0x23C9876, "394108"),
    "row_attribution_add": (0x23C98AB, "48017948"),
    "suppress_branch": (0x230A657, "0f8560030000"),
}

CALLS = {
    "pursuit_first_backing_before_soft_write": (0x23CDA59, 0x239C840),
    "pursuit_second_backing_before_soft_write": (0x23CDC77, 0x239C840),
    "result_side_0_before_pass": (0x230A984, 0x23DB050),
    "result_side_1_before_pass": (0x230A998, 0x23DB050),
    "normal_result_envelope_before_pass": (0x230A9A3, 0x230AF10),
    "side_0_pass": (0x230A9AC, FUNCTION_START),
    "side_1_pass": (0x230A9B8, FUNCTION_START),
    "create_attribution_row_if_missing": (0x23C989C, 0x23DE6F0),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    args = parser.parse_args()
    data = args.exe.read_bytes()
    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != EXE_SHA256:
        raise SystemExit(f"wrong CK3 EXE SHA-256: {actual_hash}")
    image = pefile.PE(data=data, fast_load=True)

    def read(rva: int, length: int) -> bytes:
        offset = image.get_offset_from_rva(rva)
        return data[offset : offset + length]

    for name, (rva, expected_hex) in SITES.items():
        expected = bytes.fromhex(expected_hex)
        if read(rva, len(expected)) != expected:
            raise SystemExit(f"{name} bytes differ at RVA 0x{rva:X}")
    for name, (rva, target) in CALLS.items():
        opcode = read(rva, 5)
        if opcode[0] != 0xE8 or rva + 5 + struct.unpack("<i", opcode[1:])[0] != target:
            raise SystemExit(f"{name} call edge differs at RVA 0x{rva:X}")

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    function = list(decoder.disasm(read(FUNCTION_START, FUNCTION_END - FUNCTION_START), FUNCTION_START))
    if not function or function[-1].address + function[-1].size != FUNCTION_END:
        raise SystemExit("bounded function decode is incomplete")
    calls = [insn.address for insn in function if insn.mnemonic == "call"]
    if calls != [0x23C989C]:
        raise SystemExit(f"unexpected direct or indirect call sites in side pass: {calls!r}")
    nonstack_writes = []
    for insn in function:
        for operand in insn.operands:
            if operand.type != X86_OP_MEM or not (operand.access & CS_AC_WRITE):
                continue
            if operand.mem.base not in (X86_REG_RSP, X86_REG_RBP):
                nonstack_writes.append(insn.address)
    if nonstack_writes != [0x23C98AB]:
        raise SystemExit(f"unexpected direct nonstack writes: {nonstack_writes!r}")
    print(json.dumps({"exe_sha256": actual_hash.upper(),
                      "function_range_rva": [f"0x{FUNCTION_START:X}", f"0x{FUNCTION_END:X}"],
                      "verified_site_count": len(SITES), "verified_call_count": len(CALLS),
                      "function_direct_nonstack_writes": [f"0x{x:X}" for x in nonstack_writes],
                      "function_calls": [f"0x{x:X}" for x in calls]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
