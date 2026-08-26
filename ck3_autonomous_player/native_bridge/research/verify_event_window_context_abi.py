#!/usr/bin/env python3
"""Verify pinned CK3 event-window-context byte spans without starting CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from scan_anchors import PeImage


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "event_window_context_1_19_0_6_abi.json"
DEFAULT_EXE = HERE.parents[2] / "Crusader Kings III" / "binaries" / "ck3.exe"


def integer(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(f"expected integer or integer string, found {value!r}")


def runtime_function_ranges(data: bytes, image: PeImage) -> set[tuple[int, int]]:
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    optional = pe_offset + 24
    if struct.unpack_from("<H", data, optional)[0] != 0x20B:
        raise ValueError("expected PE32+ optional header")
    exception_rva, exception_size = struct.unpack_from(
        "<II", data, optional + 112 + 3 * 8
    )
    if exception_size % 12:
        raise ValueError("malformed AMD64 exception directory")
    offset = image.rva_to_offset(exception_rva)
    return {
        struct.unpack_from("<II", data, offset + delta)
        for delta in range(0, exception_size, 12)
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    arguments = parser.parse_args()

    executable = arguments.exe.resolve()
    contract_path = arguments.contract.resolve()
    data = executable.read_bytes()
    image = PeImage(data)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    executable_sha = hashlib.sha256(data).hexdigest().upper()
    expected_executable_sha = contract["executable_sha256"].upper()
    if executable_sha != expected_executable_sha:
        failures.append(
            "executable SHA mismatch: "
            f"expected {expected_executable_sha}, found {executable_sha}"
        )

    pdata_ranges = runtime_function_ranges(data, image)
    spans = contract["source_contract"]["exact_function_spans"]
    for span in spans:
        declared_regions = span.get("runtime_function_regions")
        if declared_regions:
            regions = []
            for region in declared_regions:
                start_text, end_text = region.split("..", maxsplit=1)
                regions.append((integer(start_text), integer(end_text)))
        else:
            regions = [(integer(span["start_rva"]), integer(span["end_rva"]))]
        for begin, end in regions:
            if (begin, end) not in pdata_ranges:
                failures.append(
                    f"{span['name']}: 0x{begin:X}..0x{end:X} "
                    "is not an exact .pdata runtime-function extent"
                )

        start = integer(span["start_rva"])
        end = integer(span["end_rva"])
        expected_length = integer(span["byte_length"])
        actual_length = end - start
        if actual_length != expected_length:
            failures.append(
                f"{span['name']}: declared length 0x{expected_length:X}, "
                f"RVA range length 0x{actual_length:X}"
            )
            continue
        offset = image.rva_to_offset(start)
        blob = data[offset : offset + actual_length]
        if len(blob) != actual_length:
            failures.append(f"{span['name']}: range is not fully file-backed")
            continue
        actual_sha = hashlib.sha256(blob).hexdigest().upper()
        expected_sha = span["sha256"].upper()
        if actual_sha != expected_sha:
            failures.append(
                f"{span['name']}: expected {expected_sha}, found {actual_sha}"
            )
            continue
        print(
            f"OK {span['name']} RVA=0x{start:X}..0x{end:X} "
            f"bytes=0x{actual_length:X} SHA256={actual_sha}"
        )

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print(f"PASS spans={len(spans)} pdata=1 exact_build=1 read_only=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
