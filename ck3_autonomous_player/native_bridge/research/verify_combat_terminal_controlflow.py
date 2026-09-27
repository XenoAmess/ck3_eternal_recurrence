#!/usr/bin/env python3
"""Verify exact-build combat phase/terminal control-flow anchors without running CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_64, Cs


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
ANCHORS = {
    "daily_day_increment": (0x27FB6C6, "inc", "edx"),
    "daily_main_call": (0x27FB6FD, "call", "0x142309e80"),
    "daily_pursuit_call": (0x27FB6DF, "call", "0x14230a2a0"),
    "daily_done_gate": (0x27FB730, "cmp", "dword ptr [rsi + 0x6b0], 3"),
    "daily_normal_finalizer": (0x27FB73E, "call", "0x14230a590"),
    "daily_storage_removal": (0x27FB74A, "call", "0x1427fdc50"),
    "main_forced_winner": (0x2309EA6, "mov", "edx, dword ptr [rdi + 0x700]"),
    "main_side0_total_gate": (0x2309EB1, "cmp", "qword ptr [rdi + 0xb8], 0"),
    "main_side1_total_gate": (0x2309ECF, "cmp", "qword ptr [rdi + 0x400], 0"),
    "main_winner_side1": (0x2309ECA, "jmp", "0x14230a010"),
    "main_winner_side0": (0x2309EE5, "jmp", "0x14230a010"),
    "winner_write": (0x230A080, "mov", "dword ptr [rdi + 0x6e0], ebx"),
    "loser_route_gate": (0x230A0DD, "call", "0x142308250"),
    "no_route_first_entry_clear": (0x230A10A, "call", "0x1423d2e30"),
    "no_route_second_entry_clear": (0x230A133, "call", "0x1423d2e30"),
    "no_route_done_write": (0x230A162, "mov", "qword ptr [rdi + 0x6b0], 3"),
    "route_initial_soft_levy": (0x230A22D, "mov", "qword ptr [rdi + 0x6e8], rax"),
    "route_initial_soft_maa": (0x230A25D, "mov", "qword ptr [rdi + 0x6f0], rax"),
    "route_pursuit_write": (0x230A264, "mov", "qword ptr [rdi + 0x6b0], 2"),
    "skip_pursuit_sync_call": (0x230A27B, "call", "0x14230a2a0"),
    "pursuit_skip_flag": (0x230A2DF, "cmp", "byte ptr [rax + rsi], 0"),
    "pursuit_day_gate": (0x230A2EF, "cmp", "dword ptr [rsi + 0x6b4], ebp"),
    "pursuit_damage_call": (0x230A3C7, "call", "0x1423cd2e0"),
    "pursuit_done_write": (0x230A3F9, "mov", "qword ptr [rsi + 0x6b0], 3"),
    "pursuit_finish_helper": (0x230A407, "call", "0x1423068e0"),
    "sweep_no_normal_finalizer": (0x27FBF85, "call", "0x14230a590"),
    "sweep_storage_removal": (0x27FBF91, "call", "0x1427fdc50"),
}


def inspect(exe: Path) -> dict:
    data = exe.read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if digest != EXE_SHA256:
        raise ValueError(f"CK3 EXE identity mismatch: {digest}")
    pe = pefile.PE(data=data, fast_load=True)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    rows = []
    for name, (rva, expected_mnemonic, expected_operand) in ANCHORS.items():
        offset = pe.get_offset_from_rva(rva)
        instructions = list(decoder.disasm(data[offset : offset + 16], pe.OPTIONAL_HEADER.ImageBase + rva, count=1))
        if len(instructions) != 1:
            raise ValueError(f"undecodable anchor: {name}")
        insn = instructions[0]
        if (insn.mnemonic, insn.op_str) != (expected_mnemonic, expected_operand):
            raise ValueError(f"anchor drift {name}: {insn.mnemonic} {insn.op_str}")
        rows.append({"name": name, "rva": f"0x{rva:X}", "bytes": insn.bytes.hex(), "instruction": f"{insn.mnemonic} {insn.op_str}"})
    return {"schema": "ck3-combat-terminal-controlflow-static-v1", "exe_sha256": digest, "anchors": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = inspect(args.exe)
    if args.expected is not None and report != json.loads(args.expected.read_text(encoding="utf-8")):
        raise ValueError("frozen control-flow report mismatch")
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
