#!/usr/bin/env python3
"""Prove that two exact-build +0x260 offsets cannot identify one loser node.

The on-action *name registry* +0x260 receives ``on_birthday``.  The loser
dispatcher reads a +0x260 slot through a different base expression.  Neither
observation binds the loaded effect root to a particular script trigger.
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
    0x2504C2B: "488b4b50",        # registry base = [RBX+0x50]
    0x2504C2F: "4881c160020000",  # destination = registry +0x260
    0x2504C36: "41b80b000000",    # 11-byte name
    0x2504C3C: "488d159d53d901",  # source = on_birthday string
    0x2504C43: "e8e8482efe",      # name-copy routine
    0x2505287: "4881c160090000",  # actual winner name registry +0x960
    0x2505294: "488d158dcae001",  # on_combat_end_winner
    0x25052A4: "4881c180090000",  # actual loser name registry +0x980
    0x25052B1: "488d1558cae001",  # on_combat_end_loser
    0x230B0A9: "488b4738",        # dispatcher database = [RDI+0x38]
    0x230B0AD: "488b9860020000",  # loser effect root = database +0x260
    0x230B0E8: "488bd3",          # pass root as dispatcher RDX
    0x230B0EE: "e85dd20e01",      # call generic effect dispatcher
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
    base = image.OPTIONAL_HEADER.ImageBase
    if base != 0x140000000:
        raise ValueError("unexpected PE image base")
    for rva, expected_hex in ANCHORS.items():
        expected = bytes.fromhex(expected_hex)
        offset = image.get_offset_from_rva(rva)
        actual = exe[offset : offset + len(expected)]
        if actual != expected:
            raise ValueError(f"RVA 0x{rva:X}: expected {expected.hex()}, got {actual.hex()}")
    string_rvas = (
        (0x4299FE0, b"on_birthday\0"),
        (0x4311D28, b"on_combat_end_winner\0"),
        (0x4311D10, b"on_combat_end_loser\0"),
    )
    for rva, expected in string_rvas:
        offset = image.get_offset_from_rva(rva)
        if exe[offset : offset + len(expected)] != expected:
            raise ValueError(f"RVA 0x{rva:X}: on-action name differs")
    # Resolve the actual RIP-relative name source, rather than trusting the
    # string location merely because the bytes are present elsewhere in EXE.
    for instruction_rva, expected_string_rva in (
        (0x2504C3C, 0x4299FE0),
        (0x2505294, 0x4311D28),
        (0x25052B1, 0x4311D10),
    ):
        offset = image.get_offset_from_rva(instruction_rva + 3)
        displacement = struct.unpack_from("<i", exe, offset)[0]
        if instruction_rva + 7 + displacement != expected_string_rva:
            raise ValueError(f"RVA 0x{instruction_rva:X}: name source differs")
    print(json.dumps({
        "status": "static_name_slot_offset_collision_verified",
        "exe_sha256": EXE_SHA256,
        "on_action_sha256": ON_ACTION_SHA256,
        "checked_instruction_anchors": len(ANCHORS),
        "name_registry_plus_0x260": "on_birthday",
        "loser_name_registry_offset": "+0x980",
        "loser_loaded_root_database_offset": "+0x260",
        "registry_offset_identifies_loser_loaded_root": False,
        "loser_root_to_warscore_trigger_parent_chain_bound": False,
        "loaded_node_opcode_rhs_bound": False,
        "authoritative_attribution_hook_install_ready": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
