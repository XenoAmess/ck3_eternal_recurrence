#!/usr/bin/env python3
"""Verify exact-build passive-probe ABI anchors, not a loaded script identity."""

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
    0x230AFF4: "488b9858020000",  # winner root: database +0x258
    0x230B0AD: "488b9860020000",  # loser root: database +0x260
    0x230B0E3: "4c8d442450",      # R8 = on-action context
    0x230B0E8: "488bd3",          # RDX = loser root
    0x230B0EB: "488bcf",          # RCX = effect manager
    0x230B0EE: "e85dd20e01",      # call generic effect dispatcher
    0x230B0F3: "90",              # return site (nop)
    0x33F8389: "488bfa",          # dispatcher saves current root in RDI
    0x33F8633: "488b9748030000", # recursive child from root +0x348
    0x33F8653: "e8f8fcffff",      # recursive dispatcher call
    0x53C3E6: "897810",          # registration key -> registry entry +0x10
    0x284F63E: "8b4f10",         # factory reads registry entry +0x10
    0x284F641: "894b08",         # factory stores key in trigger +0x08
    0x99FA62: "488d942498020000", # LHS output stack address
    0x99FA6D: "ff9000010000",    # virtual LHS accessor
    0x99FA77: "83bb2001000002",  # special +0x120 == 2 bypasses RHS compare
    0x99FAA1: "488d9424a0020000", # RHS output stack address
    0x99FAA9: "e8029efcff",      # evaluate RHS expression
    0x99FAAE: "8b5350",          # op from trigger +0x50
    0x99FAB1: "81facb030000",    # generic >= branch for 0x3CB
    0x99FAED: "488b00",          # RAX = evaluated RHS raw qword
    0x99FAF0: "4839842498020000", # compare stack LHS against RAX RHS
    0x99FAF8: "0f9dc0",          # signed inclusive setge AL
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
    declaration = "combat = { warscore_value >= 15 }"
    if on_action.count(declaration) != 1 or on_action.count("warscore_value") != 1:
        raise ValueError("stock on-action warscore declaration is not unique")
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
    offset = image.get_offset_from_rva(0x230B0EE + 1)
    displacement = struct.unpack_from("<i", exe, offset)[0]
    if 0x230B0EE + 5 + displacement != 0x33F8350:
        raise ValueError("loser call does not reach expected effect dispatcher")
    print(json.dumps({
        "status": "static_probe_abi_verified",
        "exe_sha256": EXE_SHA256,
        "on_action_sha256": ON_ACTION_SHA256,
        "checked_instruction_anchors": len(ANCHORS),
        "loser_root_dispatch_rva": "0x230B0EE",
        "comparator_operand_rva": "0x99FAF0",
        "trigger_plus_0x08_is_unique_source_identity": False,
        "loaded_loser_trigger_node_bound": False,
        "authoritative_attribution_hook_install_ready": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
