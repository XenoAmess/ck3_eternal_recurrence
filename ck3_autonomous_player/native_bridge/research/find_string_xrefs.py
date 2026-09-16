#!/usr/bin/env python3
"""Find exact-build x64 RIP references to a literal string.

This is a read-only reverse-engineering helper. It resolves file-backed string
occurrences to RVAs, scans executable sections for RIP-relative operands, and
reports the enclosing PE exception-directory function when available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile


HERE = Path(__file__).resolve().parent
DEFAULT_EXE = HERE.parents[2] / "Crusader Kings III" / "binaries" / "ck3.exe"


def _runtime_functions(image: pefile.PE) -> list[tuple[int, int]]:
    image.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]]
    )
    entries = getattr(image, "DIRECTORY_ENTRY_EXCEPTION", [])
    return sorted(
        (
            int(entry.struct.BeginAddress),
            int(entry.struct.EndAddress),
        )
        for entry in entries
        if int(entry.struct.BeginAddress) < int(entry.struct.EndAddress)
    )


def _enclosing_function(
    functions: list[tuple[int, int]], source_rva: int
) -> dict[str, int] | None:
    # The exception directory is ordered by BeginAddress. A linear reverse walk
    # is adequate for this bounded research helper and avoids another index.
    for begin, end in reversed(functions):
        if begin <= source_rva < end:
            return {"begin_rva": begin, "end_rva": end, "size": end - begin}
        if begin < source_rva:
            break
    return None


def inspect(executable: Path, literal: str) -> dict[str, object]:
    raw = executable.read_bytes()
    image = pefile.PE(data=raw, fast_load=False)
    image_base = int(image.OPTIONAL_HEADER.ImageBase)
    needle = literal.encode("utf-8")
    if not needle:
        raise ValueError("literal must not be empty")

    occurrences: list[dict[str, int]] = []
    cursor = 0
    while True:
        offset = raw.find(needle, cursor)
        if offset < 0:
            break
        try:
            rva = int(image.get_rva_from_offset(offset))
        except pefile.PEFormatError:
            cursor = offset + 1
            continue
        occurrences.append({"file_offset": offset, "rva": rva})
        cursor = offset + 1

    targets = {row["rva"] for row in occurrences}
    functions = _runtime_functions(image)
    references: list[dict[str, object]] = []
    for section in image.sections:
        if not section.IMAGE_SCN_MEM_EXECUTE:
            continue
        section_rva = int(section.VirtualAddress)
        raw_start = int(section.PointerToRawData)
        raw_size = int(section.SizeOfRawData)
        code = raw[raw_start : raw_start + raw_size]
        # CK3 log literals are materialized through the usual x64
        # LEA/MOV reg,[RIP+disp32] form. Scan that bounded encoding directly;
        # decoding the entire 95 MB image with Capstone takes minutes and is
        # unnecessary for a literal-reference locator.
        for rex in [b""] + [bytes([value]) for value in range(0x40, 0x50)]:
            for opcode in (0x8B, 0x8D):
                for register in range(8):
                    prefix = rex + bytes([opcode, (register << 3) | 0x05])
                    cursor = 0
                    while True:
                        offset = code.find(prefix, cursor)
                        if offset < 0:
                            break
                        # Without this guard the no-REX scan reports the same
                        # instruction a second time starting at its opcode.
                        if (
                            not rex
                            and offset > 0
                            and 0x40 <= code[offset - 1] <= 0x4F
                        ):
                            cursor = offset + 1
                            continue
                        instruction_size = len(prefix) + 4
                        if offset + instruction_size <= len(code):
                            displacement = struct.unpack_from(
                                "<i", code, offset + len(prefix)
                            )[0]
                            source_rva = section_rva + offset
                            target_rva = (
                                source_rva + instruction_size + displacement
                            )
                            if target_rva in targets:
                                instruction = code[
                                    offset : offset + instruction_size
                                ]
                                references.append(
                                    {
                                        "source_rva": source_rva,
                                        "target_rva": target_rva,
                                        "instruction_size": instruction_size,
                                        "instruction_hex": instruction.hex(" "),
                                        "mnemonic": (
                                            "lea" if opcode == 0x8D else "mov"
                                        ),
                                        "function": _enclosing_function(
                                            functions, source_rva
                                        ),
                                    }
                                )
                        cursor = offset + 1

    return {
        "schema": "xar.ck3_string_xrefs.v1",
        "executable": str(executable),
        "executable_size": len(raw),
        "executable_sha256": hashlib.sha256(raw).hexdigest().upper(),
        "literal": literal,
        "literal_utf8_hex": needle.hex(" "),
        "occurrences": occurrences,
        "references": references,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("literal")
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    args = parser.parse_args()
    print(
        json.dumps(
            inspect(args.exe.resolve(), args.literal),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
