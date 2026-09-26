#!/usr/bin/env python3
"""Read-only, exact-build checks for one raid-cleanup movement candidate.

The instruction anchors prove control-flow possibilities, not a live AI order.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"

# RVA -> exact instruction bytes in CK3 1.19.0.6. The whole-image SHA prevents
# accidental reinterpretation of these narrow anchors under another build.
ANCHORS = {
    0x18CF047: "e814fcffff",  # raid main-task helper
    0x18CF05B: "84c0",  # use helper result
    0x18CF05D: "0f85f7000000",  # success skips cleanup loop
    0x18CF11B: "80b8d401000000",  # CArmy +0x1D4 nonzero gate
    0x18CF122: "7424",  # zero skips the candidate
    0x18CF127: "e884a2faff",  # return/movement helper
    0x1879429: "e832d3d800",  # resolve owner province
    0x1879454: "394b10",  # compare current and target Province IDs
    0x1879457: "0f8446030000",  # same province returns
    0x1879475: "e8e6f39c00",  # generic movement validator
    0x187947C: "0f8421030000",  # validator rejection returns
    0x187948D: "e8fe1cffff",  # movement builder
    0x1879492: "807c243800",  # builder status
    0x1879497: "0f8506030000",  # bad status returns
    0x1879509: "e8c29eb400",  # first path-builder attempt
    0x1879510: "0f8537010000",  # first success enters command branch
    0x1879542: "e8899eb400",  # second path-builder attempt
    0x1879549: "0f85fe000000",  # second success enters command branch
    0x18795A8: "e863c1e300",  # alternative helper: semantics unresolved
    0x187965A: "b902000000",  # command-kind argument 2
    0x187965F: "e81cbae300",  # kind-2 validator
    0x18796C2: "f605b78dee03fd",  # global dispatch-path flag test
    0x18796C9: "755c",  # choose alternate path
    0x187971B: "e8e0a60fff",  # only one of two downstream paths
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    args = parser.parse_args()
    exe = args.exe.read_bytes()
    digest = hashlib.sha256(exe).hexdigest().upper()
    if digest != EXE_SHA256:
        raise ValueError(f"unexpected EXE SHA-256: {digest}")
    image = pefile.PE(data=exe, fast_load=True)
    for rva, expected_hex in ANCHORS.items():
        expected = bytes.fromhex(expected_hex)
        offset = image.get_offset_from_rva(rva)
        actual = exe[offset : offset + len(expected)]
        if actual != expected:
            raise ValueError(f"RVA 0x{rva:X}: expected {expected.hex()}, got {actual.hex()}")
    print(
        json.dumps(
            {
                "status": "static_source_verified",
                "exe_sha256": EXE_SHA256,
                "verified_rvas": [f"0x{rva:X}" for rva in ANCHORS],
                "scope": "raid_main_task_failed_cleanup_movement_candidate",
                "army_0x1d4_semantics_proven": False,
                "ordinary_war_ai_loss_or_timing_policy_proven": False,
                "live_active_combat_order_proven": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
