#!/usr/bin/env python3
"""Verify the exact-build knight-event and regiment-casualty branch boundary.

Read-only byte/source-hash proof. Direct-call absence is local to the named
function bodies and says nothing about compiled script effects downstream.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
SOURCES = {
    "game/common/combat_phase_events/00_knight_phase_events.txt":
        "E8F8E4978BB1AF130D74AA6ED72EE41F014B09C9F324608EBFB0E87D56A5EDB1",
    "game/common/scripted_effects/20_health_effects.txt":
        "6D7DEF1245D899DE4DEBC42136815BC7F4D14F6A467A8320355507AD03528F12",
}
RANGES = {
    "main_tick": (0x2309E80, 0x230A007),
    "side_event_wrapper": (0x23CA2F0, 0x23CA353),
    "phase_event_fire": (0x23C9900, 0x23C9C8A),
    "regiment_casualty_writer": (0x23CDF70, 0x23CE080),
}
ANCHORS = {
    "side0_events_before_damage": ("main_tick", 0x2309EF2, "call", "0x23ca2f0"),
    "side1_events_before_damage": ("main_tick", 0x2309EFA, "call", "0x23ca2f0"),
    "side0_outgoing": ("main_tick", 0x2309F93, "call", "0x23cb1d0"),
    "side1_outgoing": ("main_tick", 0x2309FAF, "call", "0x23cb1d0"),
    "side0_casualty_apply": ("main_tick", 0x2309FE8, "call", "0x23ce080"),
    "side1_casualty_apply": ("main_tick", 0x230A002, "jmp", "0x23ce080"),
    "event_wrapper_refresh": ("side_event_wrapper", 0x23CA302, "call", "0x23cbc20"),
    "event_wrapper_tail_fire": ("side_event_wrapper", 0x23CA34E, "jmp", "0x23c9900"),
    "event_fire_reloads_knight_character": (
        "phase_event_fire", 0x23C9A6E, "mov", "eax, dword ptr [r8 + 0x148]"
    ),
    "event_fire_executes_compiled_effect": (
        "phase_event_fire", 0x23C9B11, "call", "0x3380310"
    ),
    "regiment_adds_soft": (
        "regiment_casualty_writer", 0x23CDFC3, "add", "qword ptr [r9 + 0x20], rdx"
    ),
    "regiment_subtracts_current": (
        "regiment_casualty_writer", 0x23CDFCB, "sub", "qword ptr [r9 + 0x18], rax"
    ),
    "regiment_writes_hard_component": (
        "regiment_casualty_writer", 0x23CDFD5, "call", "0x239c840"
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def verify(exe: Path) -> dict[str, object]:
    if sha256(exe) != EXE_SHA256:
        raise ValueError("exact CK3 executable SHA-256 differs")
    game_root = exe.parent.parent
    for relative, expected in SOURCES.items():
        if sha256(game_root / relative) != expected:
            raise ValueError(f"stock source SHA-256 differs: {relative}")

    image = pefile.PE(str(exe), fast_load=True)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoded = {}
    for name, (start, end) in RANGES.items():
        instructions = list(decoder.disasm(image.get_data(start, end - start), start))
        if not instructions or instructions[0].address != start:
            raise ValueError(f"cannot decode {name}")
        decoded[name] = {instruction.address: instruction for instruction in instructions}
    sites = {}
    for claim, (name, address, mnemonic, operands) in ANCHORS.items():
        instruction = decoded[name].get(address)
        actual = None if instruction is None else (instruction.mnemonic, instruction.op_str)
        if actual != (mnemonic, operands):
            raise ValueError(f"{claim} at 0x{address:X}: {actual}")
        sites[claim] = {"rva": f"0x{address:X}", "bytes_hex": instruction.bytes.hex().upper()}

    for name, forbidden in (
        ("phase_event_fire", {"0x239c840", "0x23cdf70", "0x23ce080"}),
        ("regiment_casualty_writer", {"0x3380310", "0x23c9900"}),
    ):
        direct = {
            instruction.op_str
            for instruction in decoded[name].values()
            if instruction.mnemonic in {"call", "jmp"}
            and instruction.op_str.startswith("0x")
        }
        if direct & forbidden:
            raise ValueError(f"{name} gained a direct cross-branch edge: {direct & forbidden}")

    knight_source = (game_root / next(iter(SOURCES))).read_text(encoding="utf-8-sig")
    health_source = (game_root / "game/common/scripted_effects/20_health_effects.txt").read_text(
        encoding="utf-8-sig"
    )
    for token in (
        "knight_wounded = {", "knight_maimed = {", "knight_killed = {",
        "increase_wounds_effect = { REASON = fight }", "maimed_in_battle_effect = yes",
        "death_reason = death_battle",
    ):
        if token not in knight_source:
            raise ValueError(f"knight phase-event source token missing: {token}")
    for token in (
        "increase_wounds_effect = {", "rank < 3", "rank = 3",
        "increase_wounds_no_death_effect = { REASON = $REASON$ }",
        "death_reason = death_$REASON$",
    ):
        if token not in health_source:
            raise ValueError(f"health effect source token missing: {token}")
    return {
        "schema": "ck3.knight_personal_vs_regiment_casualty_static.v1",
        "game_build": "1.19.0.6-steam23530548",
        "exe_sha256": EXE_SHA256,
        "stock_source_sha256": SOURCES,
        "sites": sites,
        "proof_boundary": (
            "main_tick_order_and_local_direct_edges_only; compiled script effects are indirect; "
            "not a live wound/death probability or casualty parity claim"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    body = (json.dumps(verify(args.exe), indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if args.expected is not None and args.expected.read_bytes() != body:
        raise ValueError("frozen static artifact differs")
    if args.output is None:
        print(body.decode("utf-8"), end="")
    else:
        with args.output.open("xb") as file:
            file.write(body)


if __name__ == "__main__":
    main()
