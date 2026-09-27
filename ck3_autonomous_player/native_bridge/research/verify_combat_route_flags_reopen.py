#!/usr/bin/env python3
"""Freeze CK3 1.19.0.6 combat route-flag writers and pursuit reopen edges."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
import pefile

from verify_combat_terminal_controlflow import EXE_SHA256


ANCHORS = {
    "effect_disallow_bool": (0x2EB471F, "call", "0x141977600"),
    "effect_disallow_write": (0x2EB472E, "mov", "byte ptr [rdi + 0xc0], al"),
    "effect_allow_early_bool": (0x2EB476F, "call", "0x141977600"),
    "effect_allow_early_write": (0x2EB477E, "mov", "byte ptr [rdi + 0xc1], al"),
    "effect_skip_bool": (0x2EB47BF, "call", "0x141977600"),
    "effect_skip_write": (0x2EB47CE, "mov", "byte ptr [rdi + 0xc2], al"),
    "validator_disallow_read": (0x23082CE, "cmp", "byte ptr [rax + rsi], r13b"),
    "validator_allow_early_read": (0x2308434, "cmp", "byte ptr [rax + rsi], 0"),
    "winner_loser_first_army": (0x230A097, "mov", "rax, qword ptr [rsi + 0x30]"),
    "winner_route_validator": (0x230A0DD, "call", "0x142308250"),
    "winner_skip_flag": (0x230A26F, "cmp", "byte ptr [rsi + 0xe2], r14b"),
    "pursuit_skip_flag": (0x230A2DF, "cmp", "byte ptr [rax + rsi], 0"),
    "join_backlink": (0x230422D, "mov", "dword ptr [rsi + 0x128], eax"),
    "join_pursuit_gate": (0x2304233, "cmp", "dword ptr [rbx + 0x6b0], 2"),
    "join_main_reopen": (0x230423C, "mov", "qword ptr [rbx + 0x6b0], 1"),
    "join_winner_reset": (0x2304247, "mov", "dword ptr [rbx + 0x6e0], 0xffffffff"),
    "join_side0_total_refresh": (0x2304255, "call", "0x1423cb840"),
    "join_side1_total_refresh": (0x2304261, "call", "0x1423cb840"),
    "join_width_refresh": (0x2304272, "call", "0x142305580"),
}


def inspect(path: Path) -> dict:
    image = path.read_bytes()
    digest = hashlib.sha256(image).hexdigest().upper()
    if digest != EXE_SHA256:
        raise ValueError(f"CK3 EXE identity mismatch: {digest}")
    pe = pefile.PE(data=image, fast_load=True)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    anchors = []
    for name, (rva, mnemonic, operand) in ANCHORS.items():
        offset = pe.get_offset_from_rva(rva)
        decoded = list(decoder.disasm(image[offset : offset + 16], pe.OPTIONAL_HEADER.ImageBase + rva, count=1))
        if len(decoded) != 1 or (decoded[0].mnemonic, decoded[0].op_str) != (mnemonic, operand):
            raise ValueError(f"route/reopen anchor drift: {name}")
        instruction = decoded[0]
        anchors.append({"name": name, "rva": f"0x{rva:X}", "bytes": instruction.bytes.hex(), "instruction": f"{mnemonic} {operand}"})
    return {"schema": "ck3-combat-route-flags-reopen-static-v1", "exe_sha256": digest, "anchors": anchors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = inspect(args.exe)
    if args.expected is not None and report != json.loads(args.expected.read_text(encoding="utf-8")):
        raise ValueError("frozen route/reopen report mismatch")
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
