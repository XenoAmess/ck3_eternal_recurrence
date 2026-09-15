#!/usr/bin/env python3
"""Verify SCHEME10 exact-build native callback and source evidence."""

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
        self.data = path.read_bytes()
        if self.data[:2] != b"MZ":
            raise ValueError("missing MZ header")
        pe = struct.unpack_from("<I", self.data, 0x3C)[0]
        if self.data[pe : pe + 4] != b"PE\0\0":
            raise ValueError("missing PE signature")
        coff = pe + 4
        count = struct.unpack_from("<H", self.data, coff + 2)[0]
        optional_size = struct.unpack_from("<H", self.data, coff + 16)[0]
        optional = coff + 20
        if struct.unpack_from("<H", self.data, optional)[0] != 0x20B:
            raise ValueError("expected PE32+")
        self.image_base = struct.unpack_from("<Q", self.data, optional + 24)[0]
        table = optional + optional_size
        self.sections: list[tuple[int, int, int, int]] = []
        for index in range(count):
            row = table + index * 40
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
                    raise ValueError(f"RVA 0x{rva:X}+0x{size:X} reaches zero-fill")
                return self.data[raw_offset + delta : raw_offset + delta + size]
        raise ValueError(f"RVA 0x{rva:X}+0x{size:X} is outside the image")


def number(value: str) -> int:
    return int(value, 0)


def verify(contract: dict[str, Any], game_root: Path) -> list[str]:
    errors: list[str] = []
    build = contract["build"]
    executable = game_root / build["exe_relative_path"]
    if not executable.is_file():
        return [f"missing exact executable: {executable}"]
    if executable.stat().st_size != build["exe_size"]:
        errors.append("EXE size mismatch")
    actual_exe_sha = sha256_file(executable)
    if actual_exe_sha != build["exe_sha256"]:
        errors.append(f"EXE SHA mismatch: {actual_exe_sha}")
    image = PeImage(executable)
    if image.image_base != number(build["image_base"]):
        errors.append(f"image base mismatch: 0x{image.image_base:X}")

    source = contract["source"]
    source_path = game_root / source["relative_path"]
    if not source_path.is_file():
        errors.append(f"missing source: {source_path}")
    else:
        if source_path.stat().st_size != source["size"]:
            errors.append("source size mismatch")
        actual_source_sha = sha256_file(source_path)
        if actual_source_sha != source["sha256"]:
            errors.append(f"source SHA mismatch: {actual_source_sha}")
        else:
            lines = source_path.read_text(encoding="utf-8-sig").splitlines()
            for anchor in source["line_anchors"]:
                line = anchor["line"]
                if line < 1 or line > len(lines) or lines[line - 1] != anchor["text"]:
                    errors.append(f"source anchor mismatch at line {line}")

    for span in contract["native_spans"]:
        start = number(span["start_rva"])
        end = number(span["end_rva"])
        if end <= start:
            errors.append(f"invalid span: {span['name']}")
            continue
        actual = hashlib.sha256(image.read_rva(start, end - start)).hexdigest().upper()
        if actual != span["sha256"]:
            errors.append(f"span mismatch {span['name']}: {actual}")

    addresses = contract["native_addresses"]
    for prefix in ("primary", "secondary"):
        slot = number(addresses[f"send_command_{prefix}_vtable_rva"])
        observed = struct.unpack("<Q", image.read_rva(slot, 8))[0]
        expected = image.image_base + number(
            addresses[f"send_command_{prefix}_vtable_first_target_rva"]
        )
        if observed != expected:
            errors.append(f"send-command {prefix} vtable mismatch")
    if addresses["submit_channel"] != 14:
        errors.append("submit channel must remain 0x0E")

    expected_layout = {
        "context_size": "0x338",
        "command_size": "0x368",
        "actor_full_id_offset": "0x2D8",
        "recipient_full_id_offset": "0x2DC",
        "selected_option_vector_offset": "0x300",
        "selected_option_count_offset": "0x30C",
        "definition_option_rows_offset": "0x2548",
        "definition_option_count_offset": "0x2554",
        "definition_options_exclusive_offset": "0x2A4E",
        "definition_option_stride": "0x7D0",
        "definition_option_flag_id_offset": "0x3A8",
        "copied_command_context_offset": "0x20",
    }
    if contract["context_layout"] != expected_layout:
        errors.append("context/command layout contract mismatch")
    lifecycle = contract["lifecycle"]
    if lifecycle.get("pointer_cache") != "forbidden":
        errors.append("native pointer caching must remain forbidden")
    if "not a native or monotonic" not in lifecycle.get("route_generation", ""):
        errors.append("transaction-only route generation boundary is missing")
    semantics = contract["precondition_semantics"]
    if "explicitly_unavailable" not in semantics.get("previews", ""):
        errors.append("unproven native previews must remain explicit")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path(__file__).with_name(
            "active_scheme_precondition_command_binders_1_19_0_6_abi.json"
        ),
    )
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8-sig"))
    try:
        errors = verify(contract, args.game_root)
    except (OSError, ValueError, KeyError, TypeError, struct.error) as exc:
        errors = [str(exc)]
    if errors:
        for error in errors:
            print(f"RED: {error}", file=sys.stderr)
        return 1
    print("GREEN: SCHEME10 exact spans, layouts, vtables and stock source match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
