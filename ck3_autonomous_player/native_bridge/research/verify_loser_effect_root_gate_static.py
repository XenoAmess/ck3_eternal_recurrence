#!/usr/bin/env python3
"""Verify exact-build generic effect gates reachable from the loser root.

This establishes dispatch structure, not the identity or value of a loaded
``warscore_value >= 15`` trigger, nor any executed legitimacy writeback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
ON_ACTION_SHA256 = "B35D696F472E801BB332D7204AA46008349E8AFBFDB38985C781EB099BBFB233"
COMBAT_EVENTS_SHA256 = "CF4E7F43786477DF43319638138232086CFD477FEE0F2951B34DD41BE265CADD"

ANCHORS = {
    0x230B0AD: "488b9860020000",  # loaded loser root: table element 76
    0x230B0E8: "488bd3",          # RDX = that root
    0x230B0EE: "e85dd20e01",      # generic effect dispatcher
    0x33F8389: "488bfa",          # RDI = current effect node
    0x33F8397: "84c0",            # inspect node-level gate result
    0x33F8399: "0f845a030000",    # false skips child dispatch
    0x33F6ABA: "488b8b38030000",  # node +0x338 gate pointer
    0x33F6AC1: "4885c9",         # absent gate is accepted
    0x33F6AC4: "7410",           # jump to true case
    0x33F6AC6: "488bd6",         # evaluation context to RDX
    0x33F6ACE: "84c0",           # test evaluator result
    0x33F6AD0: "7504",           # true case
    0x33F6AD2: "32db",           # false result
    0x33F6AD6: "b301",           # true result
    0x33F8DA7: "498b9fb0020000",  # first vector base +0x2B0
    0x33F8DAE: "496387bc020000",  # first vector count +0x2BC
    0x33F8DB5: "4c8d2440",      # count * 3
    0x33F8DB9: "49c1e404",      # *16 = 0x30 stride
    0x33F8DD0: "488b3b",        # element's first pointer
    0x33F8DD9: "ff5030",        # first virtual predicate
    0x33F8DE9: "ff5040",        # second virtual predicate
    0x33F8E16: "4883c330",      # first vector increment
    0x33F87C7: "488b9ef8020000",  # second vector base +0x2F8
    0x33F87CE: "48638604030000",  # second vector count +0x304
    0x33F87D5: "488d0cc0",      # count * 9
    0x33F87D9: "4c8d24cb",      # *8 = 0x48 stride
    0x33F87F0: "488b7b20",      # per-entry +0x20 pointer
    0x33F87F4: "4885ff",        # absent entry skipped
    0x33F8831: "4883c348",      # second vector increment
    0x33F8633: "488b9748030000",  # nested child pointer +0x348
    0x33F863A: "4885d2",        # absent child skipped
    0x33F8653: "e8f8fcffff",    # recurse into generic dispatcher
}

CALLS = {
    0x230B0EE: 0x33F8350,
    0x33F8392: 0x33F6A20,
    0x33F6AC9: 0x334C510,
    0x33F8561: 0x33F8D00,
    0x33F8589: 0x33F8720,
    0x33F87FF: 0x33F6A20,
    0x33F8653: 0x33F8350,
}


def checked(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest().upper()
    if actual != expected:
        raise ValueError(f"{path}: unexpected SHA-256 {actual}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--on-action", required=True, type=Path)
    parser.add_argument("--combat-events", required=True, type=Path)
    args = parser.parse_args()
    exe = checked(args.exe, EXE_SHA256)
    on_action = checked(args.on_action, ON_ACTION_SHA256).decode("utf-8-sig").splitlines()
    combat_events = checked(args.combat_events, COMBAT_EVENTS_SHA256).decode("utf-8-sig").splitlines()
    required_lines = {
        519: "on_combat_end_loser = {",
        531: "effect = {",
        561: "if = {",
        562: "limit = {",
        563: "combat = { warscore_value >= 15 }",
        566: "side_primary_participant = {",
        568: "limit = { is_valid_for_legitimacy_change = yes }",
        569: "send_interface_toast = {",
        575: "add_legitimacy = minor_legitimacy_loss",
    }
    for line_number, expected in required_lines.items():
        if on_action[line_number - 1].strip() != expected:
            raise ValueError(f"on-action line {line_number} differs")
    if combat_events[2237].strip() != "combat = { warscore_value >= 15 }":
        raise ValueError("combat event's same-text comparator differs")
    image = pefile.PE(data=exe, fast_load=True)
    if image.OPTIONAL_HEADER.ImageBase != 0x140000000:
        raise ValueError("unexpected PE image base")
    for rva, expected_hex in ANCHORS.items():
        expected = bytes.fromhex(expected_hex)
        offset = image.get_offset_from_rva(rva)
        actual = exe[offset : offset + len(expected)]
        if actual != expected:
            raise ValueError(f"RVA 0x{rva:X}: expected {expected.hex()}, got {actual.hex()}")
    for rva, target in CALLS.items():
        offset = image.get_offset_from_rva(rva)
        if exe[offset] != 0xE8:
            raise ValueError(f"RVA 0x{rva:X}: expected relative call")
        displacement = struct.unpack_from("<i", exe, offset + 1)[0]
        if rva + 5 + displacement != target:
            raise ValueError(f"RVA 0x{rva:X}: call target differs")
    for rva, target in ((0x33F8399, 0x33F86F9), (0x33F6AC4, 0x33F6AD6)):
        offset = image.get_offset_from_rva(rva)
        if rva == 0x33F8399:
            if exe[offset : offset + 2] != b"\x0f\x84":
                raise ValueError("root gate false branch opcode differs")
            destination = rva + 6 + struct.unpack_from("<i", exe, offset + 2)[0]
        else:
            if exe[offset] != 0x74:
                raise ValueError("absent node gate branch opcode differs")
            destination = rva + 2 + struct.unpack_from("<b", exe, offset + 1)[0]
        if destination != target:
            raise ValueError(f"RVA 0x{rva:X}: branch target differs")
    print(json.dumps({
        "status": "static_generic_loser_effect_gate_and_child_dispatch_verified",
        "exe_sha256": EXE_SHA256,
        "on_action_sha256": ON_ACTION_SHA256,
        "combat_events_sha256": COMBAT_EVENTS_SHA256,
        "checked_instruction_anchors": len(ANCHORS),
        "checked_relative_calls": len(CALLS),
        "generic_node_gate_offset": "+0x338",
        "generic_node_gate_false_skips_child_dispatch": True,
        "vector_30_base_count": ["+0x2B0", "+0x2BC"],
        "vector_48_base_count": ["+0x2F8", "+0x304"],
        "vector_48_entry_gate_pointer_offset": "+0x20",
        "recursive_child_pointer_offset": "+0x348",
        "same_comparison_text_exists_in_other_stock_script": True,
        "actual_vfs_bytes_verified": False,
        "loser_root_to_script_line_563_trigger_bound": False,
        "loaded_loser_node_opcode_verified": False,
        "loaded_loser_node_rhs_raw_verified": False,
        "live_legitimacy_writeback_verified": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
