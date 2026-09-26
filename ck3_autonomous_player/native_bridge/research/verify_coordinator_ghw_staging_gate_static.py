#!/usr/bin/env python3
"""Fail-closed source check for the exact-build coordinator staging gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
DEFINE_SHA256 = "C78F9CD8DF9938CC9F38E817BCB6E32CD13720B5BD9DE077B85E3E1C6F030293"
NAME_RVA = 0x4196630
NAME = b"MIN_POWER_ARRIVED_TO_STOP_STAGING_FOR_GREAT_HOLY_WAR\0"
ANCHORS = {
    0x18552F5: "e8f64c0000",  # stack merge/reassignment
    0x1855305: "e876540000",  # target recomputation
    0x1855359: "e892010000",  # this bounded staging gate
    0x18554FF: "0fb64168",  # coordinator mode flags
    0x1855506: "2444",  # require mask 0x44
    0x1855508: "3c44",
    0x185550A: "0f85ac020000",  # otherwise return
    0x1855510: "8b81b0000000",  # first timer
    0x185554D: "8b83c0000000",  # second timer
    0x18555D3: "e8c8ee0100",  # per-subunit magnitude helper
    0x18556C3: "4d3bf2",  # denominator max(total, 100000)
    0x18557A4: "483b0d9d87eb03",  # strict threshold compare
    0x18557B0: "7e0a",  # <= threshold skips state change
    0x18557B2: "c783c0000000ffffffff",  # timer/state -1
    0x18B5DE3: "4c8d0d5e81e503",  # same runtime global as consumer
    0x18B5DF1: "4c8d0538088e02",  # define name string
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--ai-defines", required=True, type=Path)
    args = parser.parse_args()
    exe = args.exe.read_bytes()
    exe_sha = hashlib.sha256(exe).hexdigest().upper()
    if exe_sha != EXE_SHA256:
        raise ValueError(f"unexpected EXE SHA-256: {exe_sha}")
    define = args.ai_defines.read_bytes()
    define_sha = hashlib.sha256(define).hexdigest().upper()
    if define_sha != DEFINE_SHA256:
        raise ValueError(f"unexpected AI define SHA-256: {define_sha}")
    image = pefile.PE(data=exe, fast_load=True)
    for rva, expected_hex in ANCHORS.items():
        expected = bytes.fromhex(expected_hex)
        offset = image.get_offset_from_rva(rva)
        actual = exe[offset : offset + len(expected)]
        if actual != expected:
            raise ValueError(f"RVA 0x{rva:X}: expected {expected.hex()}, got {actual.hex()}")
    name_offset = image.get_offset_from_rva(NAME_RVA)
    if exe[name_offset : name_offset + len(NAME)] != NAME:
        raise ValueError("registered define name string differs")
    text = define.decode("utf-8-sig")
    if not re.search(r"(?m)^\s*MIN_POWER_ARRIVED_TO_STOP_STAGING_FOR_GREAT_HOLY_WAR\s*=\s*0\.9\s*$", text):
        raise ValueError("staging threshold declaration differs")
    print(json.dumps({
        "status": "static_source_verified",
        "exe_sha256": EXE_SHA256,
        "ai_define_sha256": DEFINE_SHA256,
        "registered_name_rva": f"0x{NAME_RVA:X}",
        "threshold_nominal": 0.9,
        "verified_rvas": [f"0x{rva:X}" for rva in ANCHORS],
        "same_branch_active_combat_retreat_order_proven": False,
        "ordinary_war_loss_policy_excluded_globally": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
