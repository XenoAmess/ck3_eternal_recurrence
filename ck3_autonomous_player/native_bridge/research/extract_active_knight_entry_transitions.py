#!/usr/bin/env python3
"""Read-only exact-build disassembly for active knight and entry transitions.

This is an address aid, not proof of runtime ordering across combat managers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
import pefile


EXPECTED_EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
FUNCTIONS = {
    "schedule": (0x23C8750, 0x23C8A60),
    "commander_select": (0x23C8A60, 0x23C9100),
    "fire": (0x23C9900, 0x23C9B70),
    "side_modifier_refresh": (0x23CBCE0, 0x23CC2B0),
    "manager_stat_refresh": (0x2308D50, 0x2308DA0),
    "side_entry_refresh": (0x23CC2B0, 0x23CC330),
    "entry_stat_refresh": (0x23D2CE0, 0x23D2D70),
    "join": (0x23C9100, 0x23C9310),
    "owner_subset_leave": (0x23CA360, 0x23CA550),
    "daily_schedule_dispatch": (0x27FB53B, 0x27FB5BA),
    "daily_phase_dispatch": (0x27FB5D0, 0x27FB780),
}

# Exact instruction sites, reviewed against the pinned 1.19.0.6 executable.
# The source hash and instruction check must both pass before emitting a claim.
ANCHORS = {
    "schedule_clears_event_count": ("schedule", 0x23C87AD, "mov", "dword ptr [rbx + 0xe4], 0"),
    "schedule_reads_maa_entries": ("schedule", 0x23C87B7, "mov", "rbp, qword ptr [rbx + 0x40]"),
    "schedule_reads_regiment_knight": ("schedule", 0x23C8843, "mov", "edx, dword ptr [rdi + 0x148]"),
    "schedule_adds_character_and_day": ("schedule", 0x23C88A6, "lea", "eax, [r9 + r13]"),
    "schedule_uses_character_day_modulo": ("schedule", 0x23C88AA, "div", "dword ptr [rip + 0x33466ec]"),
    "schedule_stores_regiment_id": ("schedule", 0x23C893D, "mov", "ecx, dword ptr [rdi + 0x10]"),
    "schedule_writes_regiment_id_to_row": ("schedule", 0x23C8940, "mov", "dword ptr [rax + rdx*8 + 8], ecx"),
    "fire_reads_scheduled_rows": ("fire", 0x23C99A5, "mov", "rbx, qword ptr [r14 + 0xd8]"),
    "fire_reloads_regiment_id": ("fire", 0x23C99F6, "mov", "edx, dword ptr [rbx + 8]"),
    "fire_checks_army_combat_backlink": ("fire", 0x23C9A62, "cmp", "dword ptr [rcx + 0x128], eax"),
    "fire_reloads_knight_id": ("fire", 0x23C9A6E, "mov", "eax, dword ptr [r8 + 0x148]"),
    "manager_refreshes_stats": ("daily_schedule_dispatch", 0x27FB57A, "call", "0x2308d50"),
    "manager_schedules_side0": ("daily_schedule_dispatch", 0x27FB58F, "call", "0x23c8750"),
    "refreshes_side0_modifiers": ("manager_stat_refresh", 0x2308D66, "call", "0x23cbce0"),
    "refreshes_side1_modifiers": ("manager_stat_refresh", 0x2308D72, "call", "0x23cbce0"),
    "refreshes_side0_entries": ("manager_stat_refresh", 0x2308D82, "call", "0x23cc2b0"),
    "refreshes_side1_entries": ("manager_stat_refresh", 0x2308D95, "call", "0x23cc2b0"),
    "refreshes_levy_entry": ("side_entry_refresh", 0x23CC2E8, "call", "0x23d2ce0"),
    "refreshes_maa_entry": ("side_entry_refresh", 0x23CC316, "call", "0x23d2ce0"),
    "recomputes_entry_stats": ("entry_stat_refresh", 0x23D2D2F, "call", "0x239cae0"),
    "manager_selects_side0_commander": ("daily_phase_dispatch", 0x27FB683, "call", "0x23c8a60"),
    "manager_selects_side1_commander": ("daily_phase_dispatch", 0x27FB6A2, "call", "0x23c8a60"),
    "manager_enters_main_tick": ("daily_phase_dispatch", 0x27FB6FD, "call", "0x2309e80"),
    "entry_writes_effective_damage": ("entry_stat_refresh", 0x23D2D46, "mov", "qword ptr [rbx + 0x40], rcx"),
    "entry_writes_effective_toughness": ("entry_stat_refresh", 0x23D2D4E, "mov", "qword ptr [rbx + 0x48], rcx"),
}


def load_image(exe: Path) -> pefile.PE:
    data = exe.read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if digest != EXPECTED_EXE_SHA256:
        raise ValueError(f"unexpected executable SHA-256: {digest}")
    return pefile.PE(data=data, fast_load=True)


def instructions(image: pefile.PE, name: str) -> list:
    start, end = FUNCTIONS[name]
    code = image.get_data(start, end - start)
    if len(code) != end - start:
        raise ValueError("short executable read")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    return list(decoder.disasm(code, start))


def verify(image: pefile.PE) -> dict:
    decoded = {name: {instruction.address: instruction for instruction in instructions(image, name)}
               for name in {row[0] for row in ANCHORS.values()}}
    result = {}
    for claim, (name, address, mnemonic, operands) in ANCHORS.items():
        instruction = decoded[name].get(address)
        if instruction is None or (instruction.mnemonic, instruction.op_str) != (mnemonic, operands):
            actual = None if instruction is None else f"{instruction.mnemonic} {instruction.op_str}"
            raise ValueError(f"{claim} at 0x{address:X}: expected {mnemonic} {operands}, got {actual}")
        result[claim] = {"rva": f"0x{address:X}", "bytes_hex": instruction.bytes.hex().upper(),
                         "instruction": f"{mnemonic} {operands}"}
    return {"schema": "ck3.native_active_knight_entry_static_anchors.v1",
            "game_build": "1.19.0.6", "exe_sha256": EXPECTED_EXE_SHA256,
            "proof_layer": "exact-build-instruction-sites", "anchors": result,
            "static_order": [
                "manager_refreshes_stats < manager_schedules_side0",
                "refreshes_side0_modifiers < refreshes_side1_modifiers < refreshes_side0_entries < refreshes_side1_entries",
                "manager_selects_side0_commander < manager_selects_side1_commander < manager_enters_main_tick",
                "schedule_writes_regiment_id_to_row; fire_reloads_regiment_id_and_knight_id",
            ],
            "not_proven": ["cross-manager global tick order", "future join/leave schedule",
                           "all wounded/death effects", "next-day effective stat values"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--function", choices=sorted(FUNCTIONS), help="print a reviewed function disassembly")
    parser.add_argument("--verify", action="store_true", help="verify exact instruction sites and emit JSON")
    parser.add_argument("--output", type=Path, help="exclusively create a new verification artifact")
    parser.add_argument("--expected", type=Path, help="compare verification bytes with an existing frozen artifact")
    args = parser.parse_args()
    if args.verify == bool(args.function):
        parser.error("provide exactly one of --verify or --function")
    image = load_image(args.exe)
    if args.verify:
        body = json.dumps(verify(image), indent=2) + "\n"
        if args.expected is not None and args.expected.read_bytes() != body.encode("utf-8"):
            raise ValueError(f"frozen verification artifact differs: {args.expected}")
        if args.output is None:
            print(body, end="")
        else:
            with args.output.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(body)
    else:
        if args.output is not None or args.expected is not None:
            parser.error("--output/--expected are only valid with --verify")
        print("\n".join(f"{instruction.address:08X}  {instruction.mnemonic:<8} {instruction.op_str}"
                        for instruction in instructions(image, args.function)))


if __name__ == "__main__":
    main()
