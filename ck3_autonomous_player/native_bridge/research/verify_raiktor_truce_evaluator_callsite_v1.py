#!/usr/bin/env python3
"""Verify the bounded, read-only Raiktor truce evaluator call-site slice.

The checker reads one pinned CK3 executable and a small JSON contract.  It
does not start CK3, attach to a process, load the native bridge, or write the
executable.  The result is static evidence only; it cannot promote GEN-034.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from scan_anchors import PeImage


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "raiktor_truce_evaluator_callsite_v1_abi.json"
DEFAULT_EXE = HERE.parents[2] / "Crusader Kings III" / "binaries" / "ck3.exe"


def integer(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(f"expected integer or integer string, got {value!r}")


def span(data: bytes, image: PeImage, start: int, end: int) -> bytes:
    if end <= start:
        raise ValueError(f"invalid span 0x{start:X}..0x{end:X}")
    offset = image.rva_to_offset(start)
    value = data[offset : offset + end - start]
    if len(value) != end - start:
        raise ValueError(f"short file-backed span at 0x{start:X}")
    return value


def verify(executable: Path, contract_path: Path) -> list[str]:
    data = executable.read_bytes()
    image = PeImage(data)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    build = contract["build"]
    checks = (
        ("sha256", hashlib.sha256(data).hexdigest().upper(), build["executable_sha256"]),
        ("file_size", len(data), integer(build["file_size"])),
        ("pe_timestamp", image.timestamp, integer(build["pe_timestamp"])),
        ("image_base", image.image_base, integer(build["image_base"])),
        ("size_of_image", image.size_of_image, integer(build["size_of_image"])),
    )
    for name, actual, expected in checks:
        if actual != expected:
            failures.append(f"build {name}: expected {expected!r}, found {actual!r}")

    evaluator = contract["evaluator"]
    evaluator_start = integer(evaluator["rva"])
    evaluator_end = integer(evaluator["entry_span_end_rva_exclusive"])
    evaluator_bytes = span(data, image, evaluator_start, evaluator_end)
    if evaluator_bytes.hex().upper() != evaluator["entry_bytes_hex"]:
        failures.append("evaluator entry bytes differ from the pinned contract")
    if hashlib.sha256(evaluator_bytes).hexdigest().upper() != evaluator["entry_span_sha256"]:
        failures.append("evaluator entry span digest differs from the pinned contract")
    if evaluator["return_kind"] != "int32_in_EAX":
        failures.append("unexpected evaluator return-kind claim")
    return_rva = integer(evaluator["return_rva"])
    if span(data, image, return_rva, return_rva + 1) != b"\xC3":
        failures.append("evaluator return RVA is not a RET instruction")

    for row in contract["call_sites"]:
        start = integer(row["sequence_start_rva"])
        call_rva = integer(row["call_instruction_rva"])
        end = integer(row["sequence_end_rva_exclusive"])
        actual = span(data, image, start, end)
        if actual.hex().upper() != row["bytes_hex"]:
            failures.append(f"call-site bytes differ at 0x{start:X}")
        if hashlib.sha256(actual).hexdigest().upper() != row["sequence_sha256"]:
            failures.append(f"call-site digest differs at 0x{start:X}")
        call_offset = image.rva_to_offset(call_rva)
        if data[call_offset] != 0xE8:
            failures.append(f"call opcode missing at 0x{call_rva:X}")
            continue
        displacement = struct.unpack_from("<i", data, call_offset + 1)[0]
        actual_target = call_rva + 5 + displacement
        expected_target = integer(row["operands"]["target_rva"])
        if actual_target != expected_target:
            failures.append(
                f"call target at 0x{call_rva:X}: expected 0x{expected_target:X}, "
                f"found 0x{actual_target:X}"
            )
        post = span(data, image, end, end + len(bytes.fromhex(row["post_call_bytes_hex"])))
        if post.hex().upper() != row["post_call_bytes_hex"]:
            failures.append(f"post-call consumer bytes differ at 0x{end:X}")
        if hashlib.sha256(post).hexdigest().upper() != row["post_call_sha256"]:
            failures.append(f"post-call consumer digest differs at 0x{end:X}")

    if contract["shared_contract"]["direct_call_target_rva"] != evaluator["rva"]:
        failures.append("shared call target is not the evaluator RVA")
    if not contract["read_only"] or contract["production_installed"] or contract["production_abi_changed"]:
        failures.append("contract is not marked as static read-only evidence")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    args = parser.parse_args()
    try:
        failures = verify(args.exe.resolve(), args.contract.resolve())
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("PASS: exact_build=1 evaluator=1 call_sites=2 read_only=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
