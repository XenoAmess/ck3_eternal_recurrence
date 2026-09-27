#!/usr/bin/env python3
"""Pin the exact-build on-action names and bounded effect traversal fields.

This cannot identify a runtime trigger node with a source line.
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
ANCHORS = {
    0x25047F0: "488d0519d1e001",  # COnActionDataBase primary vtable
    0x25047F7: "488903",          # install primary vtable into RBX
    0x25047FA: "488d0547d1e001",  # secondary vtable
    0x2504801: "48898388000000",  # install secondary vtable
    0x2504808: "488d0569d1e001",  # tertiary vtable
    0x250480F: "488983c0000000",  # install tertiary vtable
    0x2505287: "4881c160090000",  # adjacent winner name slot +0x960
    0x2505294: "488d158dcae001",  # on_combat_end_winner
    0x25052A4: "4881c180090000",  # adjacent loser name slot +0x980
    0x25052B1: "488d1558cae001",  # on_combat_end_loser
    0x33F8DA7: "498b9fb0020000", # vector A data: root +0x2B0
    0x33F8DAE: "496387bc020000", # vector A count: root +0x2BC
    0x33F8E16: "4883c330",       # vector A entry stride 0x30
    0x33F87C7: "488b9ef8020000", # vector B data: root +0x2F8
    0x33F87CE: "48638604030000", # vector B count: root +0x304
    0x33F8831: "4883c348",       # vector B entry stride 0x48
    0x33F8633: "488b9748030000", # recursive child pointer +0x348
    0x33F8653: "e8f8fcffff",     # recursive dispatcher call
    0x334B55B: "837e1800",       # conditional parser metadata/value path
    0x334B569: "e8b2678400",     # parser record builder call
    0x334B56E: "488d4e10",       # copy record into trigger +0x10
    0x3B91D2F: "488b81e0000000", # parser context +0xE0
    0x3B91D89: "488b4830",       # nested parse item +0x30
    0x3B91DCF: "897310",         # record third field: dword from parse item +0x08
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
    args = parser.parse_args()
    exe = checked(args.exe, EXE_SHA256)
    on_action = checked(args.on_action, ON_ACTION_SHA256).decode("utf-8-sig")
    if on_action.count("combat = { warscore_value >= 15 }") != 1:
        raise ValueError("stock loser declaration is not unique")
    image = pefile.PE(data=exe, fast_load=True)
    if image.OPTIONAL_HEADER.ImageBase != 0x140000000:
        raise ValueError("unexpected PE image base")
    for rva, expected_hex in ANCHORS.items():
        expected = bytes.fromhex(expected_hex)
        offset = image.get_offset_from_rva(rva)
        actual = exe[offset : offset + len(expected)]
        if actual != expected:
            raise ValueError(f"RVA 0x{rva:X}: expected {expected.hex()}, got {actual.hex()}")
    for rva, name in ((0x4311D28, b"on_combat_end_winner\0"),
                      (0x4311D10, b"on_combat_end_loser\0")):
        offset = image.get_offset_from_rva(rva)
        if exe[offset : offset + len(name)] != name:
            raise ValueError(f"RVA 0x{rva:X}: on-action name differs")
    rtti = b".?AVCOnActionDataBase@@\0"
    # MSVC type descriptor starts with two pointers; the name begins at +0x10.
    offset = image.get_offset_from_rva(0x54AA430 + 0x10)
    if exe[offset : offset + len(rtti)] != rtti:
        raise ValueError("COnActionDataBase RTTI name differs")
    offset = image.get_offset_from_rva(0x437D490 + 0x28)
    parse_method = struct.unpack_from("<Q", exe, offset)[0] - image.OPTIONAL_HEADER.ImageBase
    if parse_method != 0x334B490:
        raise ValueError("CCombatWarscoreTrigger parser slot differs")
    print(json.dumps({
        "status": "static_loaded_effect_tree_subset_verified",
        "exe_sha256": EXE_SHA256,
        "on_action_sha256": ON_ACTION_SHA256,
        "checked_instruction_anchors": len(ANCHORS),
        "winner_name_slot_offset": "0x960",
        "loser_name_slot_offset": "0x980",
        "effect_vector_a": {"data": "+0x2B0", "count": "+0x2BC", "stride": "0x30"},
        "effect_vector_b": {"data": "+0x2F8", "count": "+0x304", "stride": "0x48"},
        "recursive_child_offset": "+0x348",
        "parser_record_semantics_verified": False,
        "source_line_field_verified": False,
        "complete_root_to_trigger_parent_chain_verified": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
