#!/usr/bin/env python3
"""Verify the frozen CK3 1.19.0.6 nonreligious scheme evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


class PeImage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = path.read_bytes()
        if self.data[:2] != b"MZ":
            raise ValueError(f"{path}: missing MZ header")
        pe_offset = struct.unpack_from("<I", self.data, 0x3C)[0]
        if self.data[pe_offset : pe_offset + 4] != b"PE\0\0":
            raise ValueError(f"{path}: missing PE signature")
        coff = pe_offset + 4
        section_count = struct.unpack_from("<H", self.data, coff + 2)[0]
        optional_size = struct.unpack_from("<H", self.data, coff + 16)[0]
        optional = coff + 20
        if struct.unpack_from("<H", self.data, optional)[0] != 0x20B:
            raise ValueError(f"{path}: expected PE32+ image")
        self.image_base = struct.unpack_from("<Q", self.data, optional + 24)[0]
        section_table = optional + optional_size
        self.sections: list[tuple[int, int, int, int]] = []
        for index in range(section_count):
            row = section_table + index * 40
            virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
                "<IIII", self.data, row + 8
            )
            self.sections.append(
                (virtual_address, max(virtual_size, raw_size), raw_offset, raw_size)
            )

    def read_rva(self, rva: int, size: int) -> bytes:
        for virtual_address, mapped_size, raw_offset, raw_size in self.sections:
            if virtual_address <= rva and rva + size <= virtual_address + mapped_size:
                delta = rva - virtual_address
                if delta + size > raw_size:
                    raise ValueError(
                        f"RVA 0x{rva:X}+0x{size:X} reaches zero-filled section data"
                    )
                return self.data[raw_offset + delta : raw_offset + delta + size]
        raise ValueError(f"RVA 0x{rva:X}+0x{size:X} is outside mapped sections")


def parse_rva(value: str) -> int:
    return int(value, 0)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def verify_contract(contract: dict[str, Any], game_root: Path) -> list[str]:
    errors: list[str] = []
    build = contract["build"]
    exe_path = game_root / build["exe_relative_path"]
    if not exe_path.is_file():
        return [f"missing exact-build executable: {exe_path}"]
    if exe_path.stat().st_size != build["exe_size"]:
        fail(errors, f"EXE size mismatch: {exe_path.stat().st_size}")
    actual_exe_sha = sha256_file(exe_path)
    if actual_exe_sha != build["exe_sha256"]:
        fail(errors, f"EXE SHA-256 mismatch: {actual_exe_sha}")

    try:
        image = PeImage(exe_path)
    except ValueError as exc:
        return errors + [str(exc)]
    if image.image_base != parse_rva(build["image_base"]):
        fail(errors, f"image base mismatch: 0x{image.image_base:X}")

    for source in contract["sources"]:
        path = game_root / source["relative_path"]
        if not path.is_file():
            fail(errors, f"missing source: {path}")
            continue
        if path.stat().st_size != source["size"]:
            fail(errors, f"source size mismatch: {source['relative_path']}")
        actual_sha = sha256_file(path)
        if actual_sha != source["sha256"]:
            fail(
                errors,
                f"source SHA-256 mismatch: {source['relative_path']} {actual_sha}",
            )
            continue
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        for anchor in source["line_anchors"]:
            line_number = anchor["line"]
            if line_number < 1 or line_number > len(lines):
                fail(errors, f"line anchor out of range: {path}:{line_number}")
            elif lines[line_number - 1] != anchor["text"]:
                fail(errors, f"line anchor mismatch: {path}:{line_number}")

    for span in contract["native_spans"]:
        start = parse_rva(span["start_rva"])
        end = parse_rva(span["end_rva"])
        if end <= start:
            fail(errors, f"invalid native span: {span['name']}")
            continue
        actual = hashlib.sha256(image.read_rva(start, end - start)).hexdigest().upper()
        if actual != span["sha256"]:
            fail(errors, f"native span mismatch: {span['name']} {actual}")

    for literal in contract["native_strings"]:
        expected = literal["ascii_nul"].encode("ascii") + b"\0"
        actual = image.read_rva(parse_rva(literal["rva"]), len(expected))
        if actual != expected:
            fail(errors, f"native string mismatch: {literal['name']}")
            continue
        actual_sha = hashlib.sha256(actual).hexdigest().upper()
        if actual_sha != literal["sha256"]:
            fail(errors, f"native string hash mismatch: {literal['name']}")

    for prefix in contract["action_reuse_prefixes"]:
        expected = bytes.fromhex(prefix["hex"])
        actual = image.read_rva(parse_rva(prefix["rva"]), len(expected))
        if actual != expected:
            fail(errors, f"action seam prefix mismatch: {prefix['name']}")

    if contract.get("religion_scope", {}).get("status") != "owner-deferred":
        fail(errors, "religion scope must remain owner-deferred")
    proposed = contract.get("proposed_read_only_slice", {})
    required_fields = {
        "scheme_instance_id",
        "scheme_type_key",
        "target_kind",
        "target_id",
        "progress",
        "success_chance",
        "secrecy",
        "opportunity_charges",
        "breaches",
    }
    fields = proposed.get("same_frame_fields", [])
    if len(fields) != len(set(fields)):
        fail(errors, "proposed same-frame field list contains duplicates")
    if not required_fields.issubset(fields):
        fail(errors, "proposed read-only slice omits required scheme fields")
    action = contract.get("proposed_action_seam", {})
    if action.get("route") != "existing native character-interaction context validator and send-command path":
        fail(errors, "action seam must reuse the validated character-interaction route")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game-root",
        type=Path,
        required=True,
        help="Exact CK3 root containing binaries/ck3.exe and game/",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path(__file__).with_name("scheme_state_1_19_0_6_abi.json"),
    )
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8-sig"))
    errors = verify_contract(contract, args.game_root)
    if errors:
        for error in errors:
            print(f"RED: {error}", file=sys.stderr)
        return 1
    print(
        "GREEN: CK3 1.19.0.6 scheme-state static evidence, source anchors, "
        "and proposed P0 seams match"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
