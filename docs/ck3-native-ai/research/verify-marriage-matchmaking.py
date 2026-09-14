#!/usr/bin/env python3
"""Verify the CK3 1.19.0.6 marriage-matchmaking research freeze.

The verifier is read-only and deliberately takes a game root rather than
embedding one operator's installation path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
from pathlib import Path


ARTIFACT = Path(__file__).with_name("marriage-matchmaking-1.19.0.6.json")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def integer(value: str | int) -> int:
    return int(value, 0) if isinstance(value, str) else value


class PeImage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = path.read_bytes()
        pe_offset = struct.unpack_from("<I", self.data, 0x3C)[0]
        if self.data[pe_offset : pe_offset + 4] != b"PE\0\0":
            raise ValueError(f"not a PE image: {path}")
        section_count = struct.unpack_from("<H", self.data, pe_offset + 6)[0]
        optional_size = struct.unpack_from("<H", self.data, pe_offset + 20)[0]
        section_offset = pe_offset + 24 + optional_size
        self.sections: list[tuple[int, int, int, int]] = []
        for index in range(section_count):
            offset = section_offset + index * 40
            virtual_size, virtual_address, raw_size, raw_offset = (
                struct.unpack_from("<IIII", self.data, offset + 8)
            )
            self.sections.append(
                (virtual_address, max(virtual_size, raw_size), raw_offset, raw_size)
            )

    def read_rva(self, rva: int, size: int) -> bytes:
        for virtual_address, span, raw_offset, raw_size in self.sections:
            if virtual_address <= rva and rva + size <= virtual_address + span:
                delta = rva - virtual_address
                if delta + size > raw_size:
                    raise ValueError(f"RVA 0x{rva:X} crosses unbacked section data")
                return self.data[raw_offset + delta : raw_offset + delta + size]
        raise ValueError(f"RVA 0x{rva:X} is outside file-backed PE sections")


def relative_target(pe: PeImage, source: int, instruction: str) -> int:
    if instruction in {"call", "jmp"}:
        raw = pe.read_rva(source, 5)
        expected_opcode = 0xE8 if instruction == "call" else 0xE9
        if raw[0] != expected_opcode:
            raise ValueError(
                f"0x{source:X}: expected {instruction} opcode, got {raw.hex(' ')}"
            )
        return source + 5 + struct.unpack_from("<i", raw, 1)[0]
    if instruction == "lea":
        raw = pe.read_rva(source, 7)
        if raw[0] not in {0x48, 0x4C} or raw[1] != 0x8D or raw[2] & 0xC7 != 0x05:
            raise ValueError(
                f"0x{source:X}: expected RIP-relative lea, got {raw.hex(' ')}"
            )
        return source + 7 + struct.unpack_from("<i", raw, 3)[0]
    raise ValueError(f"unsupported instruction kind: {instruction}")


def check(condition: bool, success: str, failure: str, errors: list[str]) -> None:
    if condition:
        print(f"GREEN {success}")
    else:
        errors.append(failure)
        print(f"RED   {failure}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game-root",
        type=Path,
        default=Path(os.environ["CK3_GAME_ROOT"])
        if os.environ.get("CK3_GAME_ROOT")
        else None,
        help="CK3 install root; CK3_GAME_ROOT is also accepted",
    )
    parser.add_argument("--artifact", type=Path, default=ARTIFACT)
    args = parser.parse_args()
    if args.game_root is None:
        parser.error("provide --game-root or CK3_GAME_ROOT")

    artifact = json.loads(args.artifact.read_text(encoding="utf-8"))
    game_root = args.game_root.resolve()
    errors: list[str] = []

    build = artifact["build"]
    exe_path = game_root / build["exe_relative_path"]
    try:
        pe = PeImage(exe_path)
    except (OSError, ValueError, struct.error) as exc:
        print(f"RED   unable to open exact executable: {exc}")
        return 1
    check(
        len(pe.data) == build["exe_size"],
        f"EXE size {len(pe.data)}",
        f"EXE size mismatch: {len(pe.data)} != {build['exe_size']}",
        errors,
    )
    actual_exe_hash = sha256(pe.data)
    check(
        actual_exe_hash == build["exe_sha256"],
        f"EXE SHA-256 {actual_exe_hash}",
        f"EXE SHA-256 mismatch: {actual_exe_hash}",
        errors,
    )

    for source in artifact["sources"]:
        path = game_root / source["relative_path"]
        try:
            raw = path.read_bytes()
        except OSError as exc:
            errors.append(f"missing source {source['relative_path']}: {exc}")
            print(f"RED   {errors[-1]}")
            continue
        actual_hash = sha256(raw)
        check(
            len(raw) == source["size"] and actual_hash == source["sha256"],
            f"source {source['relative_path']} is frozen",
            f"source drift {source['relative_path']}: size={len(raw)}, sha256={actual_hash}",
            errors,
        )
        lines = raw.decode("utf-8-sig").splitlines()
        for anchor in source["anchors"]:
            start = anchor["line_start"] - 1
            end = anchor["line_end"]
            found = anchor["contains"] in "\n".join(lines[start:end])
            check(
                found,
                f"source anchor {source['relative_path']}:{anchor['line_start']}-{anchor['line_end']}",
                f"missing source anchor {source['relative_path']}: {anchor['contains']}",
                errors,
            )

    for string in artifact["ascii_strings"]:
        rva = integer(string["rva"])
        expected = string["value"].encode("ascii") + b"\0"
        try:
            actual = pe.read_rva(rva, len(expected))
        except ValueError as exc:
            errors.append(str(exc))
            print(f"RED   {exc}")
            continue
        check(
            actual == expected,
            f"ASCII 0x{rva:X} {string['value']}",
            f"ASCII mismatch at 0x{rva:X}: {actual!r}",
            errors,
        )

    for item in artifact["native_byte_ranges"]:
        rva, size = integer(item["rva"]), item["size"]
        try:
            actual_hash = sha256(pe.read_rva(rva, size))
        except ValueError as exc:
            errors.append(str(exc))
            print(f"RED   {exc}")
            continue
        check(
            actual_hash == item["sha256"],
            f"native range {item['name']} 0x{rva:X}+0x{size:X}",
            f"native range drift {item['name']}: {actual_hash}",
            errors,
        )

    for edge in artifact["direct_call_edges"]:
        source, expected = integer(edge["source"]), integer(edge["target"])
        try:
            actual = relative_target(pe, source, edge["instruction"])
        except ValueError as exc:
            errors.append(str(exc))
            print(f"RED   {exc}")
            continue
        check(
            actual == expected,
            f"{edge['instruction']} 0x{source:X} -> 0x{actual:X}",
            f"edge mismatch 0x{source:X}: 0x{actual:X} != 0x{expected:X}",
            errors,
        )

    if errors:
        print(f"\nRED marriage matchmaking freeze: {len(errors)} failure(s)")
        return 1
    print("\nGREEN marriage matchmaking freeze: exact build, sources, RVAs and edges match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
