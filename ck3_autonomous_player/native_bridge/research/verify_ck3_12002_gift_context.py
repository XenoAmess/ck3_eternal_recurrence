#!/usr/bin/env python3
"""Verify CK3 1.20.0.2 gift context ABI using executable bytes only.

No process, pipe, desktop, launcher or Steam access occurs.  --exe supplies a
frozen file; --stock-root optionally supplies the same build's game directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

from scan_anchors import PeImage, integer, verify as verify_anchors


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "ck3_12002_gift_context_abi.json"
HEADER = HERE.parent / "include/xar_bridge/ck3_12002_faction_gift.hpp"


def rotate_left(value: int, amount: int) -> int:
    return ((value << amount) | (value >> (32 - amount))) & 0xFFFFFFFF


def stable_key_hash(key: str) -> int:
    """Translate the pinned zero-seed Murmur3 x86/32 native instruction chain."""
    data = key.encode("utf-8")
    result = 0
    full = len(data) & ~3
    for position in range(0, full, 4):
        block = int.from_bytes(data[position : position + 4], "little")
        block = (block * 0xCC9E2D51) & 0xFFFFFFFF
        block = rotate_left(block, 15)
        block = (block * 0x1B873593) & 0xFFFFFFFF
        result ^= block
        result = rotate_left(result, 13)
        result = (result * 5 + 0xE6546B64) & 0xFFFFFFFF
    tail = int.from_bytes(data[full:], "little")
    if len(data) != full:
        tail = (tail * 0xCC9E2D51) & 0xFFFFFFFF
        tail = rotate_left(tail, 15)
        tail = (tail * 0x1B873593) & 0xFFFFFFFF
        result ^= tail
    result ^= len(data)
    result ^= result >> 16
    result = (result * 0x85EBCA6B) & 0xFFFFFFFF
    result ^= result >> 13
    result = (result * 0xC2B2AE35) & 0xFFFFFFFF
    result ^= result >> 16
    return result


def verify_direct_operand(row: dict[str, object], actual: bytes) -> list[str]:
    failures: list[str] = []
    rva = integer(row["rva"])
    if "direct_call_target" in row:
        target = integer(row["direct_call_target"])
        if len(actual) != 5 or actual[0] != 0xE8:
            failures.append(f"{row['purpose']}: not a direct rel32 call")
        elif rva + 5 + struct.unpack_from("<i", actual, 1)[0] != target:
            failures.append(f"{row['purpose']}: direct call target differs")
    rip_target = row.get("rip_relative_target")
    if rip_target is None:
        old_targets = row.get("rip_targets", [])
        if isinstance(old_targets, list) and old_targets:
            rip_target = old_targets[0]
    if rip_target is not None:
        # Every RIP-relative proof in this manifest uses a final disp32 and
        # has no immediate operand after it (MOV/LEA).
        target = rva + len(actual) + struct.unpack_from("<i", actual, len(actual) - 4)[0]
        if target != integer(rip_target):
            failures.append(f"{row['purpose']}: RIP-relative target differs")
    return failures


def self_test() -> list[str]:
    failures: list[str] = []
    for key, wanted in (("", 0), ("gift_opinion", 0xCA82155B),
                        ("send_gift_opinion", 0xF8A1F946)):
        if stable_key_hash(key) != wanted:
            failures.append(f"stable hash reference vector differs: {key!r}")
    row = {"purpose": "rel32 receiver", "rva": "0xA811D6",
           "direct_call_target": "0xA055E0"}
    call = b"\xe8" + struct.pack("<i", 0xA055E0 - 0xA811D6 - 5)
    if verify_direct_operand(row, call):
        failures.append("direct native lookup call fixture failed")
    wrong = b"\xe8" + struct.pack("<i", 0xA055E1 - 0xA811D6 - 5)
    if not verify_direct_operand(row, wrong):
        failures.append("direct native lookup call fixture missed a changed receiver")
    return failures


def verify(exe: Path, manifest_path: Path, header: Path,
           stock_root: Path | None = None) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures = verify_anchors(exe, manifest_path)
    failures.extend(self_test())
    data = exe.read_bytes()
    pe = PeImage(data)
    for span in manifest["native_spans"]:
        offset = pe.rva_to_offset(integer(span["rva"]))
        actual = data[offset : offset + integer(span["length"])]
        if hashlib.sha256(actual).hexdigest().upper() != span["sha256"]:
            failures.append(f"{span['name']}: native span hash differs")
    for row in manifest["semantic_checks"]:
        expected = bytes.fromhex(row["bytes"])
        offset = pe.rva_to_offset(integer(row["rva"]))
        actual = data[offset : offset + len(expected)]
        if actual != expected:
            failures.append(f"{row['purpose']}: native instruction bytes differ")
        failures.extend(verify_direct_operand(row, actual))
    header_text = header.read_text(encoding="utf-8-sig")
    for name, expected in manifest["source_constants"].items():
        match = re.search(r"\b" + re.escape(name) + r"\s*=\s*(0[xX][0-9a-fA-F]+)", header_text)
        if match is None or integer(match.group(1)) != integer(expected):
            failures.append(f"{name}: production binding constant differs")
    stock_checked = stock_root is not None
    if stock_root is not None:
        stock = stock_root / "common/character_interactions/00_gift.txt"
        if hashlib.sha256(stock.read_bytes()).hexdigest().upper() != manifest["stock_evidence"]["sha256"]:
            failures.append("stock gift definition hash differs")
    return {"status": "GREEN" if not failures else "RED",
            "exact_build": manifest["build"]["product_version"],
            "executable_sha256": hashlib.sha256(data).hexdigest().upper(),
            "signature_anchors": len(manifest["signature_anchors"]),
            "native_spans": len(manifest["native_spans"]),
            "semantic_checks": len(manifest["semantic_checks"]),
            "production_constants": len(manifest["source_constants"]),
            "vtable_prefixes": len(manifest["vtable_prefixes"]),
            "gift_interaction_stable_hash": f"0x{stable_key_hash('gift_interaction'):08X}",
            "stock_definition_checked": stock_checked,
            "live_verified": False, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--header", type=Path, default=HEADER)
    parser.add_argument("--stock-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.self_test:
            failures = self_test()
            result: dict[str, object] = {"status": "GREEN" if not failures else "RED",
                "hash_reference_vectors": 3, "direct_call_operand_cases": 2,
                "gift_interaction_stable_hash": f"0x{stable_key_hash('gift_interaction'):08X}",
                "live_verified": False, "failures": failures}
        else:
            if arguments.exe is None:
                parser.error("--exe is required unless --self-test is selected")
            result = verify(arguments.exe, arguments.manifest, arguments.header, arguments.stock_root)
        if arguments.output is not None:
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            arguments.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "GREEN" else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
