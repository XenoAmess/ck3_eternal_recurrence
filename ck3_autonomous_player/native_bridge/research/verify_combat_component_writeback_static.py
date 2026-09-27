#!/usr/bin/env python3
"""Verify exact-build soldier-component writeback and no-route reset anchors.

Read-only: this checks stock ck3.exe bytes and emits no game calls or patches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile


EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
DEFAULT_EXE = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe")

# Each entry is an independently identifiable instruction in the original EXE.
SITES = {
    "entry_soft_add": (0x23CDFC3, "49015120"),
    "entry_current_sub": (0x23CDFCB, "49294118"),
    "component_current_set": (0x23D3099, "895104"),
    "component_max_compare": (0x23D309C, "3b11"),
    "component_sentinel_gate": (0x23D30A0, "837910ff"),
    "component_flag_gate": (0x23D30A6, "80791400"),
    "component_link_gate": (0x23D30E5, "83b93801000000"),
    "component_clear_both": (0x23D3100, "488903"),
    "reset_entry_soft_zero": (0x23D2E45, "4c897120"),
    "reset_entry_current_zero": (0x23D2E49, "4c897118"),
    "reset_component_current_zero": (0x23D2ED4, "44897004"),
    "reset_component_clear_both": (0x23D2F3B, "4c8933"),
}

CALLS = {
    "entry_to_hard_backing": (0x23CDFD5, 0x239C840),
    "hard_first_pass_to_setter": (0x239CA04, 0x23D3090),
    "hard_second_pass_to_setter": (0x239CAA2, 0x23D3090),
    "no_route_levy_to_reset": (0x230A10A, 0x23D2E30),
    "no_route_maa_to_reset": (0x230A133, 0x23D2E30),
    "reset_to_aggregate_rebuild": (0x23D2F5E, 0x239BAD0),
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

    checked_sites = {}
    for name, (rva, expected_hex) in SITES.items():
        expected = bytes.fromhex(expected_hex)
        actual = read(rva, len(expected))
        if actual != expected:
            raise SystemExit(f"{name} byte mismatch at RVA 0x{rva:X}")
        checked_sites[name] = {"rva": f"0x{rva:X}", "bytes": actual.hex()}

    checked_calls = {}
    for name, (rva, expected_target) in CALLS.items():
        instruction = read(rva, 5)
        if instruction[0] != 0xE8:
            raise SystemExit(f"{name} is not direct near call at RVA 0x{rva:X}")
        target = rva + 5 + struct.unpack("<i", instruction[1:])[0]
        if target != expected_target:
            raise SystemExit(f"{name} target 0x{target:X} != 0x{expected_target:X}")
        checked_calls[name] = {"rva": f"0x{rva:X}", "target_rva": f"0x{target:X}"}

    print(json.dumps({"exe_sha256": digest.upper(), "sites": checked_sites,
                      "calls": checked_calls}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
