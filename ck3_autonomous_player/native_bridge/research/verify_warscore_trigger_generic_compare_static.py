#!/usr/bin/env python3
"""Verify exact-build generic CCombatWarscoreTrigger comparison wiring.

The loaded on-action node is runtime data. This deliberately does not claim
that its operator or right-hand value have been read from a live game.
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
VTABLE_RVA = 0x437D490
ANCHORS = {
    0x53C371: "488d05f0dce303",  # registered warscore_value name
    0x284F631: "488d0558deb201",  # construct this trigger's vtable
    0x99FA6D: "ff9000010000",  # virtual +0x100: obtain lhs raw qword
    0x99FA92: "488d4310",  # runtime rhs expression input
    0x99FAA9: "e8029efcff",  # evaluate rhs expression
    0x99FAAE: "8b5350",  # runtime comparison opcode
    0x99FAB1: "81facb030000",  # opcode 0x3CB dispatch
    0x99FAED: "488b00",  # rhs qword from expression result
    0x99FAF0: "4839842498020000",  # lhs qword compared with rhs
    0x99FAF8: "0f9dc0",  # signed >=, equality included
    0x99FB81: "8b9a60010000",  # parse path reads operator token
    0x99FBA5: "895f50",  # stores it in runtime trigger +0x50
    0x284C830: "488b4040",  # accessor reads ResultData+0x40
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
    if "combat = { warscore_value >= 15 }" not in on_action:
        raise ValueError("stock on-action declaration differs")
    image = pefile.PE(data=exe, fast_load=True)
    if image.OPTIONAL_HEADER.ImageBase != 0x140000000:
        raise ValueError("unexpected PE image base")
    for rva, expected_hex in ANCHORS.items():
        expected = bytes.fromhex(expected_hex)
        offset = image.get_offset_from_rva(rva)
        actual = exe[offset : offset + len(expected)]
        if actual != expected:
            raise ValueError(f"RVA 0x{rva:X}: expected {expected.hex()}, got {actual.hex()}")
    for slot, target in ((0xC8, 0x99F920), (0x100, 0x284C7A0)):
        offset = image.get_offset_from_rva(VTABLE_RVA + slot)
        actual = struct.unpack_from("<Q", exe, offset)[0] - image.OPTIONAL_HEADER.ImageBase
        if actual != target:
            raise ValueError(f"vtable +0x{slot:X}: expected 0x{target:X}, got 0x{actual:X}")
    name_rva = 0x437A068
    offset = image.get_offset_from_rva(name_rva)
    if exe[offset : offset + len(b"warscore_value\0")] != b"warscore_value\0":
        raise ValueError("registration name differs")
    print(json.dumps({
        "status": "static_generic_compare_verified",
        "exe_sha256": EXE_SHA256,
        "on_action_sha256": ON_ACTION_SHA256,
        "trigger_vtable_rva": f"0x{VTABLE_RVA:X}",
        "generic_ge_opcode": "0x3CB",
        "generic_ge_is_inclusive": True,
        "script_nominal_threshold": 15,
        "projected_q100000_threshold_raw": 1500000,
        "loaded_loser_node_opcode_verified": False,
        "loaded_loser_node_rhs_raw_verified": False,
        "live_effect_writeback_verified": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
