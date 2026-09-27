#!/usr/bin/env python3
"""Verify exact-build hard casualty component allocation and branch order.

Reads stock PE bytes only; never loads or calls game code. This proves the
bounded instructions and direct edges, not live reachability or setter guards.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_64, Cs


EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
DEFAULT_EXE = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe")
START = 0x239C840
END = 0x239CAD9

# RVA: instruction bytes. The branch targets below are checked independently.
SITES = {
    "regiment_current_gate": (0x239C871, "41837f3800"),
    "descriptor_count": (0x239C895, "458b672c"),
    "descriptor_stride": (0x239C8C3, "48c1e104"),
    "descriptor_base": (0x239C8C7, "49034f20"),
    "first_kind_three": (0x239C8DC, "83781803"),
    "first_current_zero": (0x239C8E2, "83780400"),
    "first_special_max": (0x239C8E8, "8b00"),
    "first_normal_current": (0x239C8EF, "8b4004"),
    "first_skip_zero_selected": (0x239C8F5, "85c0"),
    "first_capacity_q100000": (0x239C8FF, "4c69d0a0860100"),
    "first_signed_product": (0x239C909, "480faff3"),
    "first_candidate_cap": (0x239C9D5, "493bca"),
    "first_remaining_min": (0x239C9E6, "480f4cf1"),
    "first_whole_soldier_shift": (0x239C9F0, "48c1fa0e"),
    "first_setter_base_subtract": (0x239C9FE, "442bf2"),
    "first_remainder_subtract": (0x239CA09, "482bfe"),
    "first_post_setter_remainder_test": (0x239CA0C, "4885ff"),
    "second_entry_negative_test": (0x239CA26, "4885ff"),
    "second_kind_three": (0x239CA58, "4183781803"),
    "second_normal_current": (0x239CA5D, "8b4004"),
    "second_special_max": (0x239CA66, "418b00"),
    "second_capacity_q100000": (0x239CA77, "4869c1a0860100"),
    "second_remaining_min": (0x239CA84, "480f4cd8"),
    "second_whole_soldier_shift": (0x239CA8E, "48c1fa0e"),
    "second_setter_base_subtract": (0x239CA9C, "442bca"),
    "second_remainder_subtract": (0x239CAA7, "482bfb"),
    "second_post_setter_remainder_test": (0x239CAAA, "4885ff"),
}

CALLS = {
    "entry_auxiliary_guard": (0x239C864, 0x239CEB0),
    "first_descriptor_resolve": (0x239C8CB, 0x23821B0),
    "first_component_setter": (0x239CA04, 0x23D3090),
    "second_descriptor_resolve": (0x239CA4B, 0x23821B0),
    "second_component_setter": (0x239CAA2, 0x23D3090),
    "aggregate_rebuild": (0x239CACC, 0x239BAD0),
}

BRANCHES = {
    "first_empty_container_skips_first_pass": (0x239C8AB, 0x239CA21),
    "first_zero_selected_skips_to_next": (0x239C8F7, 0x239CA11),
    "first_stop_after_setter": (0x239CA0F, 0x239CA1C),
    "first_loop_to_descriptor": (0x239CA16, 0x239C8C0),
    "negative_remainder_skips_second_pass": (0x239CA29, 0x239CAB5),
    "second_empty_container_skips_second_pass": (0x239CA37, 0x239CAB5),
    "second_null_descriptor_skips_to_next": (0x239CA56, 0x239CAAF),
    "second_stop_after_setter": (0x239CAAD, 0x239CAB5),
    "second_loop_to_descriptor": (0x239CAB3, 0x239CA40),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    args = parser.parse_args()
    data = args.exe.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXE_SHA256:
        raise SystemExit(f"wrong CK3 EXE SHA-256: {digest}")
    image = pefile.PE(data=data, fast_load=True)

    def read(rva: int, length: int) -> bytes:
        offset = image.get_offset_from_rva(rva)
        return data[offset : offset + length]

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoded = list(decoder.disasm(read(START, END - START), START))
    if not decoded or decoded[-1].address + decoded[-1].size != END:
        raise SystemExit("bounded function decode is incomplete")
    instructions = {insn.address: insn for insn in decoded}
    for name, (rva, expected_hex) in SITES.items():
        expected = bytes.fromhex(expected_hex)
        insn = instructions.get(rva)
        if insn is None or insn.bytes != expected:
            raise SystemExit(f"{name} instruction bytes differ at RVA 0x{rva:X}")
    for name, (rva, expected_target) in CALLS.items():
        opcode = read(rva, 5)
        if opcode[0] != 0xE8:
            raise SystemExit(f"{name} is not a direct near call at RVA 0x{rva:X}")
        target = rva + 5 + struct.unpack("<i", opcode[1:])[0]
        if target != expected_target:
            raise SystemExit(f"{name} target 0x{target:X} != 0x{expected_target:X}")
    for name, (rva, expected_target) in BRANCHES.items():
        insn = instructions.get(rva)
        if insn is None or not insn.mnemonic.startswith("j"):
            raise SystemExit(f"{name} is not a decoded branch at RVA 0x{rva:X}")
        # This decoder reports the stock 0x140000000-based virtual target.
        # All anchors are below 4 GiB as RVAs; retain their low 32 bits.
        target = int(insn.op_str, 16) & 0xFFFFFFFF
        if target != expected_target:
            raise SystemExit(f"{name} target 0x{target:X} != 0x{expected_target:X}")
    all_calls = [insn.address for insn in decoded if insn.mnemonic == "call"]
    if all_calls != [0x239C856, *sorted(rva for rva, _ in CALLS.values())]:
        raise SystemExit(f"unexpected call sites in hard writer: {all_calls!r}")
    # Both passes perform setter -> remainder subtraction -> <=0 test. The
    # second pass has no selected-count-zero branch before its setter.
    if not (0x239CA04 < 0x239CA09 < 0x239CA0C < 0x239CA0F
            and 0x239CAA2 < 0x239CAA7 < 0x239CAAA < 0x239CAAD):
        raise SystemExit("setter/remainder/stop site order differs")
    for insn in decoded:
        if 0x239CA50 <= insn.address < 0x239CAA2 and insn.mnemonic.startswith("j"):
            target = int(insn.op_str, 16) & 0xFFFFFFFF
            if target == 0x239CAAF and insn.address != 0x239CA56:
                raise SystemExit("unexpected second-pass selected-count skip")
    print(json.dumps({
        "exe_sha256": digest.upper(),
        "function_range_rva": [f"0x{START:X}", f"0x{END:X}"],
        "verified_instruction_sites": len(SITES),
        "verified_direct_calls": len(CALLS),
        "verified_branch_targets": len(BRANCHES),
        "finding": "both passes call setter before remainder stop; second pass enters at zero",
        "live_reachability": "unverified",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
