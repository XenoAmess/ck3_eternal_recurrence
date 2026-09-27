#!/usr/bin/env python3
"""Check the exact CK3 build and frozen pending-manager spans used by C198."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scan_anchors import PeImage


HERE = Path(__file__).resolve().parent
ABI = HERE / "pending_character_interaction_context_v1_abi.json"
HEADER = HERE.parent / "include" / "xar_bridge" / "marriage_proposal_resolution_journal_v1.hpp"
SPANS = {
    "pending_constructor",
    "pending_manager_response_transition",
    "pending_daily_age_and_expiry",
}
CONSTANTS = {
    "kMarriagePendingStorageSlotRvaV1 = 0x57BF1C8",
    "kMarriagePendingObjectVtableRvaV1 = 0x431C550",
    "kMarriagePendingSpecialVtableRvaV1 = 0x40B0F20",
    "kMarriagePendingComponentAliveRvaV1 =",
    "0x10495A0",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    data = args.exe.read_bytes()
    contract = json.loads(ABI.read_text(encoding="utf-8"))
    exe_sha = hashlib.sha256(data).hexdigest().upper()
    if exe_sha != contract["ck3_exe_sha256"].upper():
        raise SystemExit("CK3 executable SHA-256 differs from the frozen ABI")

    image = PeImage(data)
    spans = {row["name"]: row for row in
             contract["source_contract"]["exact_byte_spans"]}
    for name in sorted(SPANS):
        row = spans[name]
        start, end = int(row["start_rva"], 0), int(row["end_rva"], 0)
        actual = hashlib.sha256(data[image.rva_to_offset(start):
                                     image.rva_to_offset(start) + end - start]
                                ).hexdigest().upper()
        if actual != row["sha256"].upper():
            raise SystemExit(f"{name} no longer matches the exact-build ABI")
        print(f"OK {name} RVA=0x{start:X}..0x{end:X} SHA256={actual}")

    alive_rva = 0x10495A0
    alive_offset = image.rva_to_offset(alive_rva)
    if data[alive_offset:alive_offset + 8] != bytes.fromhex(
        "83 79 08 FF 0F 95 C0 C3"
    ):
        raise SystemExit("component-alive leaf no longer matches exact ABI")
    print("OK component-alive RVA=0x10495A0: component+8 != -1")

    header = HEADER.read_text(encoding="utf-8")
    for declaration in CONSTANTS:
        if declaration not in header:
            raise SystemExit(f"missing frozen source binding: {declaration}")
    print(f"OK CK3 1.19.0.6 SHA256={exe_sha}; C198 source bindings present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
