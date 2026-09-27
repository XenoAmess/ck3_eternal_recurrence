#!/usr/bin/env python3
"""Verify the exact-build name/root index mapping for combat loser on-action.

This proves a database layout and loader relation, not a child trigger identity
or the operation/RHS of any loaded warscore comparison node.
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

# Each entry is an instruction boundary from this exact EXE.  The loader
# carries the matched name-table index to the root-table write unchanged.
ANCHORS = {
    0x132DE44: "488b05c5304904",        # singleton getter reads global
    0x132DE8B: "488b057e304904",        # getter returns same global
    0x230AF77: "e8c42e02ff",            # result effect obtains singleton
    0x230AF7C: "488bf8",                # singleton into RDI
    0x25048A4: "4863cf",                  # root table index, 8-byte stride
    0x25048A7: "488b4338",                # COnActionDataBase +0x38 root data
    0x25048AB: "488d0cc8",                # root element = base + index*8
    0x25048C1: "c74344c3000000",        # 195 root slots
    0x25049A4: "4863fe",                  # name table index
    0x25049A7: "48c1e705",              # 32-byte name stride
    0x25049AB: "48037b50",              # COnActionDataBase +0x50 names
    0x2504A10: "c7435cc3000000",        # 195 name slots
    0x25052A4: "4881c180090000",        # loser name at index 76*32
    0x25052B1: "488d1558cae001",        # loser string
    0x257EFA4: "b908010000",            # singleton allocation size 0x108
    0x257EFB1: "488905581f2403",        # store instance in same global
    0x257EFB8: "e81357f8ff",            # construct COnActionDataBase
    0x2506B5D: "488bf1",                # secondary subobject in RSI
    0x2506C9E: "488d8e78ffffff",        # pass primary base (RSI-0x88)
    0x2506CA5: "e81609ef00",            # call generic loader
    0x33F75EE: "4c8be1",                # preserve primary base in R12
    0x33F7B47: "458b74245c",            # name-table count
    0x33F7B51: "4d8b642450",            # name-table base
    0x33F7B74: "498d4d08",              # parsed name field
    0x33F7B83: "e8a8647900",            # compare parsed/name-table strings
    0x33F7B8A: "7564",                  # matched name skips to index
    0x33F7B8C: "ffc6",                  # nonmatch increments name index
    0x33F7B91: "4883c320",              # next name, 32-byte stride
    0x33F7B9A: "4c8ba590040000",        # reload primary base saved by prolog
    0x33F7BF0: "488d1cfd00000000",      # root byte offset = index*8
    0x33F7BFF: "488b4038",              # root table from primary base
    0x33F7CFA: "4c8ba590040000",        # reload primary base
    0x33F7D01: "498b442438",            # root table from primary base
    0x33F7D06: "4c892c03",              # write parsed on-action root
    0x230B0A9: "488b4738",              # dispatch root table
    0x230B0AD: "488b9860020000",        # dispatch element at 76*8
    0x230B0E8: "488bd3",                # pass candidate root
    0x230B0EE: "e85dd20e01",            # effect dispatcher
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
    on_action = checked(args.on_action, ON_ACTION_SHA256).decode("utf-8-sig")
    if on_action.count("combat = { warscore_value >= 15 }") != 1:
        raise ValueError("stock loser warscore declaration is not unique")
    if on_action.splitlines()[562].strip() != "combat = { warscore_value >= 15 }":
        raise ValueError("stock loser warscore declaration moved from line 563")
    combat_events = checked(args.combat_events, COMBAT_EVENTS_SHA256).decode("utf-8-sig")
    if combat_events.splitlines()[2237].strip() != "combat = { warscore_value >= 15 }":
        raise ValueError("stock combat event comparison moved from line 2238")
    image = pefile.PE(data=exe, fast_load=True)
    base = image.OPTIONAL_HEADER.ImageBase
    if base != 0x140000000:
        raise ValueError("unexpected PE image base")
    for rva, expected_hex in ANCHORS.items():
        expected = bytes.fromhex(expected_hex)
        offset = image.get_offset_from_rva(rva)
        actual = exe[offset : offset + len(expected)]
        if actual != expected:
            raise ValueError(f"RVA 0x{rva:X}: expected {expected.hex()}, got {actual.hex()}")
    for call_rva, target_rva in (
        (0x257EFB8, 0x25046D0),
        (0x230AF77, 0x132DE40),
        (0x2506CA5, 0x33F75C0),
        (0x230B0EE, 0x33F8350),
    ):
        offset = image.get_offset_from_rva(call_rva + 1)
        displacement = struct.unpack_from("<i", exe, offset)[0]
        if call_rva + 5 + displacement != target_rva:
            raise ValueError(f"RVA 0x{call_rva:X}: call target differs")
    for instruction_rva in (0x132DE44, 0x132DE8B, 0x257EFB1):
        offset = image.get_offset_from_rva(instruction_rva + 3)
        displacement = struct.unpack_from("<i", exe, offset)[0]
        if instruction_rva + 7 + displacement != 0x57C0F10:
            raise ValueError(f"RVA 0x{instruction_rva:X}: singleton global differs")
    loader_vtable_offset = image.get_offset_from_rva(0x4311948 + 8)
    loader_rva = struct.unpack_from("<Q", exe, loader_vtable_offset)[0] - base
    if loader_rva != 0x2506B30:
        raise ValueError("COnActionDataBase loader vtable slot differs")
    rtti = b".?AVCOnActionDataBase@@\0"
    rtti_offset = image.get_offset_from_rva(0x54AA430 + 0x10)
    if exe[rtti_offset : rtti_offset + len(rtti)] != rtti:
        raise ValueError("COnActionDataBase RTTI name differs")
    loser_string_offset = image.get_offset_from_rva(0x4311D10)
    if exe[loser_string_offset : loser_string_offset + 20] != b"on_combat_end_loser\0":
        raise ValueError("loser on-action name differs")
    name_lea_offset = image.get_offset_from_rva(0x25052B1 + 3)
    name_displacement = struct.unpack_from("<i", exe, name_lea_offset)[0]
    if 0x25052B1 + 7 + name_displacement != 0x4311D10:
        raise ValueError("loser name source differs")
    if 0x980 // 0x20 != 0x260 // 8 or 0x980 % 0x20 or 0x260 % 8:
        raise AssertionError("loser name/root indices differ")
    print(json.dumps({
        "status": "static_loser_on_action_name_root_index_map_verified",
        "exe_sha256": EXE_SHA256,
        "on_action_sha256": ON_ACTION_SHA256,
        "combat_events_sha256": COMBAT_EVENTS_SHA256,
        "checked_instruction_anchors": len(ANCHORS),
        "loser_name_table_offset": "+0x980",
        "name_stride": "0x20",
        "loser_root_table_offset": "+0x260",
        "root_stride": "0x08",
        "matched_index": 0x980 // 0x20,
        "on_action_loader_maps_name_index_to_root_index": True,
        "dispatch_database_instance_link_verified": True,
        "same_comparison_text_exists_in_other_stock_script": True,
        "actual_vfs_bytes_verified": False,
        "loser_root_to_script_line_563_trigger_bound": False,
        "loaded_loser_node_opcode_verified": False,
        "loaded_loser_node_rhs_raw_verified": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
