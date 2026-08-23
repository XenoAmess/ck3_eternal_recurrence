#!/usr/bin/env python3
"""Offline verifier for the pinned CK3 1.19.0.6 native anchors.

This script reads only an executable file. It never starts CK3, attaches to a
process, injects a DLL, or queries the desktop. It intentionally uses only the
Python standard library so the compatibility check can run on a clean host.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys


HERE = Path(__file__).resolve().parent
DEFAULT_MANIFEST = HERE / "ck3_1_19_0_6_anchors.json"
DEFAULT_EXE = HERE.parents[2] / "Crusader Kings III" / "binaries" / "ck3.exe"


class PeImage:
    def __init__(self, data: bytes) -> None:
        if len(data) < 0x100 or data[:2] != b"MZ":
            raise ValueError("not a DOS/PE image")
        pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
        if data[pe_offset : pe_offset + 4] != b"PE\0\0":
            raise ValueError("missing PE signature")
        coff = pe_offset + 4
        machine, section_count, self.timestamp, _, _, optional_size, _ = (
            struct.unpack_from("<HHIIIHH", data, coff)
        )
        if machine != 0x8664:
            raise ValueError(f"expected AMD64 PE, found machine 0x{machine:04X}")
        optional = coff + 20
        if struct.unpack_from("<H", data, optional)[0] != 0x20B:
            raise ValueError("expected PE32+ optional header")
        self.image_base = struct.unpack_from("<Q", data, optional + 24)[0]
        self.size_of_image = struct.unpack_from("<I", data, optional + 56)[0]
        section_table = optional + optional_size
        self.sections: list[tuple[int, int, int, int]] = []
        for index in range(section_count):
            entry = section_table + index * 40
            virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
                "<IIII", data, entry + 8
            )
            self.sections.append(
                (virtual_address, max(virtual_size, raw_size), raw_offset, raw_size)
            )

    def rva_to_offset(self, rva: int) -> int:
        for virtual_address, span, raw_offset, raw_size in self.sections:
            if virtual_address <= rva < virtual_address + span:
                delta = rva - virtual_address
                if delta >= raw_size:
                    raise ValueError(f"RVA 0x{rva:X} has no file-backed bytes")
                return raw_offset + delta
        if 0 <= rva < min(item[2] for item in self.sections):
            return rva
        raise ValueError(f"RVA 0x{rva:X} is outside PE sections")

    def offset_to_rva(self, offset: int) -> int:
        for virtual_address, _, raw_offset, raw_size in self.sections:
            if raw_offset <= offset < raw_offset + raw_size:
                return virtual_address + offset - raw_offset
        raise ValueError(f"file offset 0x{offset:X} is outside PE sections")


def integer(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(f"expected integer or integer string, found {value!r}")


def occurrences(data: bytes, needle: bytes) -> list[int]:
    result: list[int] = []
    start = 0
    while True:
        position = data.find(needle, start)
        if position < 0:
            return result
        result.append(position)
        start = position + 1


def verify(exe: Path, manifest_path: Path) -> list[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest["build"]
    data = exe.read_bytes()
    pe = PeImage(data)
    failures: list[str] = []

    actual_sha = hashlib.sha256(data).hexdigest().upper()
    checks = {
        "sha256": (actual_sha, expected["sha256"]),
        "file_size": (len(data), integer(expected["file_size"])),
        "pe_timestamp": (pe.timestamp, integer(expected["pe_timestamp"])),
        "image_base": (pe.image_base, integer(expected["image_base"])),
        "size_of_image": (pe.size_of_image, integer(expected["size_of_image"])),
    }
    for name, (actual, wanted) in checks.items():
        if actual != wanted:
            failures.append(f"build {name}: expected {wanted!r}, found {actual!r}")

    for anchor in manifest["signature_anchors"]:
        needle = bytes.fromhex(anchor["pattern"])
        matches = occurrences(data, needle)
        expected_rva = integer(anchor["rva"])
        if len(matches) != 1:
            failures.append(
                f"{anchor['name']}: expected one signature, found {len(matches)}"
            )
            continue
        actual_rva = pe.offset_to_rva(matches[0])
        if actual_rva != expected_rva:
            failures.append(
                f"{anchor['name']}: expected RVA 0x{expected_rva:X}, "
                f"found 0x{actual_rva:X}"
            )
        else:
            print(
                f"OK signature {anchor['name']} RVA=0x{actual_rva:X} "
                f"confidence={anchor['confidence']}"
            )

    for vtable in manifest["vtable_prefixes"]:
        rva = integer(vtable["rva"])
        offset = pe.rva_to_offset(rva)
        wanted_rvas = [integer(item) for item in vtable["function_rvas"]]
        actual_rvas = [
            struct.unpack_from("<Q", data, offset + index * 8)[0] - pe.image_base
            for index in range(len(wanted_rvas))
        ]
        if actual_rvas != wanted_rvas:
            failures.append(
                f"{vtable['name']}: vtable prefix differs at RVA 0x{rva:X}"
            )
        else:
            print(f"OK vtable   {vtable['name']} RVA=0x{rva:X}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    arguments = parser.parse_args()
    try:
        manifest_path = arguments.manifest.resolve()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        failures = verify(arguments.exe.resolve(), manifest_path)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 2
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print(
        "PASS: exact_build=1 "
        f"unique_signatures={len(manifest['signature_anchors'])} "
        f"vtable_prefixes={len(manifest['vtable_prefixes'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
