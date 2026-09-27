#!/usr/bin/env python3
"""Verify the exact-build on-action root factory and generic parser source chain.

The verified edges stop at the parser callback: they do not identify a loaded
child with a source line, decode parser provenance fields, or prove VFS bytes.
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
IMAGE_BASE = 0x140000000

ANCHORS = {
    0x2506C3C: "488b5590",          # dynamic directory entry string
    0x2506C40: "4803d7",            # selected directory entry offset
    0x2506C99: "488d542450",        # path view passed to loader
    0x2506C9E: "488d8e78ffffff",    # same database primary base
    0x2506CA5: "e81609ef00",        # generic on-action loader
    0x33F7473: "b958030000",        # allocate 0x358-byte root
    0x33F74B9: "e862bbffff",        # construct root object
    0x33F76C8: "498b0424",          # database primary vtable
    0x33F76E5: "ff5028",            # factory virtual call
    0x33F76E8: "4c8be8",            # returned root in R13
    0x33F781C: "488b9540010000",    # parser node context
    0x33F7823: "488b4230",          # parser node +0x30
    0x33F7906: "488b4230",          # same parser node +0x30
    0x33F79EB: "498d4d30",          # destination: root +0x30
    0x33F79EF: "0f1131",            # first 16 bytes
    0x33F79F6: "0f114110",          # next 16 bytes
    0x33F79FE: "f20f114920",        # final 8 bytes
    0x33F7A08: "498b4500",          # root vtable
    0x33F7A10: "498bcd",            # RCX = root
    0x33F7A13: "ff5018",            # root parser method
    0x33F3033: "488d0576930e01",    # root object's vtable
    0x33F308D: "48897730",          # root +0x30 initially null
    0x3B8B110: "4883ec28",          # root parser thunk
    0x3B8B129: "488d542440",        # root object pointer to parser
    0x3B8B165: "488d50b0",          # source record destination
    0x3B8B1D5: "ff5020",            # generic parser invokes root callback
    0x3B91D2F: "488b81e0000000",    # parser context +0xE0
    0x3B91D41: "4c8b4030",          # current parse node +0x30
    0x3B91D45: "418b4028",          # current parse node's dword
    0x3B91D94: "4883781810",        # parser +0x258 string (SSO test)
    0x3B91DCF: "897310",            # record dword +0x10
    0x334B569: "e8b2678400",        # trigger parser record builder
    0x334B56E: "488d4e10",          # trigger record destination +0x10
    0x334B572: "0f1000",            # copy record first 16 bytes
    0x334B57C: "0f114910",          # copy record next 16 bytes
    0x334B585: "f20f114120",        # copy record final 8 bytes
}

DIRECT_CALLS = {
    0x2506CA5: 0x33F75C0,
    0x33F74B9: 0x33F3020,
    0x3B8B12E: 0x3B8B140,
    0x3B8B169: 0x3B91D20,
    0x334B569: 0x3B91D20,
    0x3B91D7A: 0x3BA2750,
    0x3B91DC7: 0x3BA2750,
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
    event = checked(args.combat_events, COMBAT_EVENTS_SHA256).decode("utf-8-sig").splitlines()
    if on_action[518].strip() != "on_combat_end_loser = {":
        raise ValueError("stock on-action root moved")
    if on_action[562].strip() != "combat = { warscore_value >= 15 }":
        raise ValueError("stock loser comparison moved")
    if event[2237].strip() != "combat = { warscore_value >= 15 }":
        raise ValueError("same-text event control moved")
    image = pefile.PE(data=exe, fast_load=True)
    if image.OPTIONAL_HEADER.ImageBase != IMAGE_BASE:
        raise ValueError("unexpected image base")
    for rva, expected_hex in ANCHORS.items():
        expected = bytes.fromhex(expected_hex)
        offset = image.get_offset_from_rva(rva)
        actual = exe[offset : offset + len(expected)]
        if actual != expected:
            raise ValueError(f"RVA 0x{rva:X}: expected {expected.hex()}, got {actual.hex()}")
    for rva, target in DIRECT_CALLS.items():
        offset = image.get_offset_from_rva(rva)
        if exe[offset] != 0xE8:
            raise ValueError(f"RVA 0x{rva:X}: expected relative call")
        displacement = struct.unpack_from("<i", exe, offset + 1)[0]
        if rva + 5 + displacement != target:
            raise ValueError(f"RVA 0x{rva:X}: call target differs")
    for slot, target in (
        (0x4311910 + 0x28, 0x33F73E0),  # database root factory
        (0x44DC3B0 + 0x18, 0x3B8B110),  # root generic parser
        (0x44DC3B0 + 0x20, 0x33F3660),  # root parser callback
        (0x437D490 + 0x28, 0x334B490), # warscore trigger parser
    ):
        offset = image.get_offset_from_rva(slot)
        actual = struct.unpack_from("<Q", exe, offset)[0] - IMAGE_BASE
        if actual != target:
            raise ValueError(f"vtable slot RVA 0x{slot:X}: target 0x{actual:X} differs")
    lea_offset = image.get_offset_from_rva(0x33F3033 + 3)
    displacement = struct.unpack_from("<i", exe, lea_offset)[0]
    if 0x33F3033 + 7 + displacement != 0x44DC3B0:
        raise ValueError("root constructor vtable target differs")
    print(json.dumps({
        "status": "static_loser_root_factory_parser_source_chain_verified",
        "exe_sha256": EXE_SHA256,
        "on_action_sha256": ON_ACTION_SHA256,
        "combat_events_sha256": COMBAT_EVENTS_SHA256,
        "checked_instruction_anchors": len(ANCHORS),
        "checked_relative_calls": len(DIRECT_CALLS),
        "checked_vtable_slots": 4,
        "database_factory_to_same_root_parser_verified": True,
        "root_record_offset": "+0x30",
        "root_record_size_bytes": 40,
        "trigger_record_offset": "+0x10",
        "trigger_record_size_bytes": 40,
        "record_fields_decoded_as_source_file_and_line": False,
        "actual_vfs_path_and_bytes_verified": False,
        "source_line_563_to_loaded_trigger_unique": False,
        "runtime_trigger_opcode_rhs_verified": False,
        "same_literal_in_other_stock_script": True,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
