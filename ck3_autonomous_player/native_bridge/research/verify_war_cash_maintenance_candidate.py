#!/usr/bin/env python3
"""Verify the exact-build maintenance-vector helper without executing CK3.

The function's transitive calls and runtime behavior are not proved read-only.
This verifier grants no permission to invoke it in a game process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
import pefile

EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
START_RVA = 0x290BA70
END_RVA = 0x290BDAC
FUNCTION_SHA256 = "A6D40023A1B422DF749610533E403A8BE054A46D952D36D3785973A5485F6B2F"
ANCHORS = {
    0x290BA95: ("mov", "r14, rdx"),
    0x290BA98: ("mov", "rsi, rcx"),
    0x290BA9E: ("movups", "xmmword ptr [rcx], xmm0"),
    0x290BAAD: ("movups", "xmmword ptr [rcx + 0x40], xmm0"),
    0x290BAB1: ("mov", "rax, qword ptr [rdx + 0x1b8]"),
    0x290BAD0: ("call", "0x14290b8a0"),
    0x290BB26: ("mov", "rax, qword ptr [r14 + 0x1b8]"),
    0x290BB32: ("add", "rax, 0x108"),
    0x290BBA5: ("call", "0x142395370"),
    0x290BD88: ("mov", "rax, rsi"),
    0x290BDAB: ("ret", ""),
}


def verify(exe: Path) -> dict[str, object]:
    binary = exe.read_bytes()
    exe_sha256 = hashlib.sha256(binary).hexdigest().upper()
    if exe_sha256 != EXE_SHA256:
        raise ValueError("CK3 executable SHA-256 mismatch")
    image = pefile.PE(data=binary, fast_load=True)
    start_offset = image.get_offset_from_rva(START_RVA)
    function = binary[start_offset:start_offset + END_RVA - START_RVA]
    function_sha256 = hashlib.sha256(function).hexdigest().upper()
    if function_sha256 != FUNCTION_SHA256:
        raise ValueError("maintenance-vector function bytes changed")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    instructions = list(decoder.disasm(
        function, image.OPTIONAL_HEADER.ImageBase + START_RVA,
    ))
    if sum(row.size for row in instructions) != len(function):
        raise ValueError("maintenance-vector function has undecoded bytes")
    by_rva = {
        row.address - image.OPTIONAL_HEADER.ImageBase: row
        for row in instructions
    }
    for rva, (mnemonic, operand) in ANCHORS.items():
        row = by_rva.get(rva)
        if row is None or (row.mnemonic, row.op_str) != (mnemonic, operand):
            raise ValueError(f"maintenance-vector anchor {rva:#x} changed")
    return {
        "schema": "xar.ck3.war-cash-maintenance-candidate-static.v1",
        "status": "exact_build_direct_instructions_only",
        "exe_sha256": exe_sha256,
        "function_start_rva": hex(START_RVA),
        "function_end_rva_exclusive": hex(END_RVA),
        "function_sha256": function_sha256,
        "anchor_count": len(ANCHORS),
        "direct_observation": (
            "0x290BA70 takes an output pointer in RCX and a character pointer "
            "in RDX, zeroes 0x50 output bytes, reads the character +0x1B8 "
            "extension, accumulates ten qword slots including a per-regiment "
            "helper call, and returns the output pointer"
        ),
        "transitive_helper_effects_proven_read_only": False,
        "safe_to_call_from_live_bridge": False,
        "same_frame_player_maintenance_observed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.exe), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
