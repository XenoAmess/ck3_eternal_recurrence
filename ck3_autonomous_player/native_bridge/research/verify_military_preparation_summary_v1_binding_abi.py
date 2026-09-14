#!/usr/bin/env python3
"""Verify the MIL4 exact-build session binding spans without launching CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


def parse_sections(image: bytes) -> list[tuple[int, int, int]]:
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    section_count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    table = pe + 24 + optional_size
    sections: list[tuple[int, int, int]] = []
    for index in range(section_count):
        offset = table + index * 40
        virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from(
            "<IIII", image, offset + 8
        )
        sections.append((virtual_address, max(virtual_size, raw_size), raw_pointer))
    return sections


def rva_bytes(
    image: bytes, sections: list[tuple[int, int, int]], rva: int, size: int
) -> bytes:
    for virtual_address, span, raw_pointer in sections:
        if virtual_address <= rva and rva + size <= virtual_address + span:
            start = raw_pointer + rva - virtual_address
            return image[start : start + size]
    raise ValueError(f"RVA span is outside image sections: {rva:#x}+{size:#x}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    args = parser.parse_args()

    image = args.exe.read_bytes()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    expected_exe = fixture["build"]["executable_sha256"]
    actual_exe = hashlib.sha256(image).hexdigest().upper()
    if actual_exe != expected_exe:
        raise SystemExit(f"executable SHA mismatch: {actual_exe}")

    sections = parse_sections(image)
    spans = [
        fixture["session"]["constructor"],
        fixture["evaluation"]["context_owner"],
        fixture["evaluation"]["support_118_constructor"],
        fixture["evaluation"]["support_2a8_constructor"],
        fixture["evaluation"]["fixed_evaluator"],
        fixture["teardown"]["tail_destructor"],
        fixture["teardown"]["rows48_destructor"],
        fixture["teardown"]["support_2a8_row_destructor"],
    ]
    for span in spans:
        rva = int(span["rva"], 16)
        size = span["size"]
        data = rva_bytes(image, sections, rva, size)
        actual = hashlib.sha256(data).hexdigest().upper()
        if actual != span["sha256"]:
            raise SystemExit(f"span SHA mismatch at {rva:#x}: {actual}")
        expected_bytes = span.get("bytes_hex")
        if expected_bytes is not None and data.hex().upper() != expected_bytes:
            raise SystemExit(f"span bytes mismatch at {rva:#x}")
    print(f"MIL4 binding ABI GREEN: {len(spans)} spans, exact CK3 1.19.0.6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
