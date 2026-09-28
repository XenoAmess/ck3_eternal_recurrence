#!/usr/bin/env python3
"""Verify CK3 1.19.0.6 embark quote static anchors without launching CK3.

The result identifies a GUI cached amount and its calculation path. It does
not prove that the calculation is safe to call or that any live cache is fresh.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP
import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
NAME_RVAS = {
    "GetEmbarkCost": 0x4101938,
    "IsCostOverOwned": 0x4101308,
}
# Exact instruction anchors, not a claim about all paths through the callees.
ANCHORS = {
    0xE1659: ("movsd", "xmm0, qword ptr [rip + 0x40202d7]"),
    0xE16DD: ("lea", "rdx, [rip + 0xda7dac]"),
    0xE16E8: ("call", "0x140ec33a0"),
    0xE17C9: ("movsd", "xmm0, qword ptr [rip + 0x401fb37]"),
    0xE1858: ("lea", "rdx, [rip + 0xda7c71]"),
    0xE1863: ("call", "0x140ec3870"),
    0xE894A1: ("mov", "rax, qword ptr [rcx + 0x68]"),
    0xE894AA: ("mov", "rcx, qword ptr [rax + 0x78]"),
    0xE894B6: ("call", "0x14096d5d0"),
    0xE894E2: ("call", "0x140e823a0"),
    0xE81728: ("xor", "ebp, ebp"),
    0xE81778: ("mov", "qword ptr [rax + 0x78], rbp"),
    0xE81F62: ("xor", "r12d, r12d"),
    0xE81F99: ("mov", "rbx, r12"),
    0xE81FBF: ("mov", "r8d, dword ptr [rdi]"),
    0xE81FEF: ("mov", "r8, qword ptr [r15 + 0x68]"),
    0xE81FFA: ("call", "0x1422775f0"),
    0xE81FFF: ("add", "rbx, qword ptr [rax]"),
    0xE820E2: ("mov", "qword ptr [rax + 0x78], rbx"),
    0xE8248F: ("mov", "rax, qword ptr [rax + 0x100]"),
    0xE82496: ("mov", "rcx, qword ptr [rdi + 0x68]"),
    0xE8249F: ("cmp", "rax, qword ptr [rcx + 0x78]"),
    0x22775F0: ("mov", "qword ptr [rsp + 0x18], r8"),
    0x22779C4: ("test", "r12, r12"),
    0x2277B52: ("test", "rbx, rbx"),
    0x2277B57: ("add", "rbx, -0xc350"),
    0x2277B60: ("add", "rbx, 0xc350"),
    0x2277B67: ("imul", "rbx"),
    0x2277B6A: ("sar", "rdx, 0xe"),
    0x2277B7B: ("imul", "rcx, rax, 0x186a0"),
    0x2277B82: ("mov", "rax, qword ptr [rbp + 0x188]"),
    0x2277B89: ("mov", "qword ptr [rax], rcx"),
}


def inspect(exe: Path) -> dict[str, object]:
    binary = exe.read_bytes()
    digest = hashlib.sha256(binary).hexdigest().upper()
    if digest != EXE_SHA256:
        raise ValueError("CK3 executable SHA-256 mismatch")
    pe = pefile.PE(data=binary, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True

    for name, expected_rva in NAME_RVAS.items():
        needle = name.encode("ascii") + b"\0"
        offset = binary.find(needle)
        if offset < 0 or binary.find(needle, offset + 1) >= 0:
            raise ValueError(f"{name} is absent or ambiguous")
        if pe.get_rva_from_offset(offset) != expected_rva:
            raise ValueError(f"{name} RVA changed")

    checked: list[str] = []
    for rva, expected in ANCHORS.items():
        offset = pe.get_offset_from_rva(rva)
        instructions = list(decoder.disasm(binary[offset:offset + 16], base + rva, count=1))
        if len(instructions) != 1:
            raise ValueError(f"missing instruction at {rva:#x}")
        row = instructions[0]
        if (row.mnemonic, row.op_str) != expected:
            raise ValueError(f"instruction changed at {rva:#x}: {row.mnemonic} {row.op_str}")
        checked.append(hex(rva))

    # Verify name references and registration pointers really target their
    # expected data and callback code, rather than merely matching mnemonics.
    for rva, name in ((0xE1659, "GetEmbarkCost"), (0xE17C9, "IsCostOverOwned")):
        offset = pe.get_offset_from_rva(rva)
        row = next(decoder.disasm(binary[offset:offset + 16], base + rva, count=1))
        operand = row.operands[1]
        if (operand.type != X86_OP_MEM or operand.mem.base != X86_REG_RIP
                or row.address + row.size + operand.mem.disp - base != NAME_RVAS[name]):
            raise ValueError(f"name reference changed at {rva:#x}")

    callbacks = {}
    for rva, name in ((0xE16DD, "GetEmbarkCost"), (0xE1858, "IsCostOverOwned")):
        offset = pe.get_offset_from_rva(rva)
        row = next(decoder.disasm(binary[offset:offset + 16], base + rva, count=1))
        operand = row.operands[1]
        if operand.type != X86_OP_MEM or operand.mem.base != X86_REG_RIP:
            raise ValueError(f"callback pointer changed at {rva:#x}")
        callbacks[name] = row.address + row.size + operand.mem.disp - base
    if callbacks != {"GetEmbarkCost": 0xE89490, "IsCostOverOwned": 0xE894D0}:
        raise ValueError(f"callback targets changed: {callbacks}")

    return {
        "status": "static_cached_embark_quote_candidate_only",
        "exe_sha256": digest,
        "name_rvas": {k: hex(v) for k, v in NAME_RVAS.items()},
        "callback_rvas": {k: hex(v) for k, v in callbacks.items()},
        "cache_object_offset": "0x78",
        "quote_calculator_rva": "0x22775f0",
        "fixed_point_scale_candidate": 100000,
        "checked_instruction_rvas": checked,
        "safe_to_call_from_live_bridge": False,
        "same_frame_amount_observed": False,
        "priced_action_identity_proven": False,
        "complete_cash_inputs_proven": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.exe), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
