#!/usr/bin/env python3
"""Locate MSVC x64 RTTI vtables in the pinned CK3 executable.

The tool is deliberately read-only and reports RVAs rather than process
addresses.  It is useful for turning an exact class name from CK3's embedded
RTTI into reproducible complete-object-locator and vtable anchors.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import struct

import pefile


HERE = Path(__file__).resolve().parent
DEFAULT_EXE = HERE.parents[2] / "Crusader Kings III" / "binaries" / "ck3.exe"


def occurrences(data: bytes, needle: bytes):
    start = 0
    while True:
        offset = data.find(needle, start)
        if offset < 0:
            return
        yield offset
        start = offset + 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pattern", help="case-insensitive regex for RTTI name")
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--slots", type=int, default=8)
    arguments = parser.parse_args()

    exe = arguments.exe.resolve()
    data = exe.read_bytes()
    image = pefile.PE(str(exe), fast_load=True)
    image_base = image.OPTIONAL_HEADER.ImageBase
    wanted = re.compile(arguments.pattern, re.IGNORECASE)

    def rva_to_offset(rva: int) -> int:
        return image.get_offset_from_rva(rva)

    def offset_to_rva(offset: int) -> int:
        return image.get_rva_from_offset(offset)

    names: list[tuple[int, str]] = []
    for match in re.finditer(rb"\.\?[A-Z][ -~]{3,240}?@@\x00", data):
        name = match.group().rstrip(b"\x00").decode("ascii", errors="replace")
        if wanted.search(name):
            # x64 TypeDescriptor has two pointers immediately before its name.
            names.append((offset_to_rva(match.start()) - 16, name))

    for type_rva, name in names:
        print(f"TYPE  rva=0x{type_rva:X} name={name}")
        encoded_type_rva = struct.pack("<I", type_rva)
        for reference in occurrences(data, encoded_type_rva):
            # CompleteObjectLocator::pTypeDescriptor is the fourth uint32.
            col_offset = reference - 12
            if col_offset < 0:
                continue
            signature, object_offset, cd_offset, candidate_type = (
                struct.unpack_from("<IIII", data, col_offset)
            )
            if signature != 1 or candidate_type != type_rva:
                continue
            try:
                col_rva = offset_to_rva(col_offset)
            except pefile.PEFormatError:
                continue
            self_rva = struct.unpack_from("<I", data, col_offset + 20)[0]
            if self_rva != col_rva:
                continue
            print(
                f"  COL rva=0x{col_rva:X} object_offset=0x{object_offset:X} "
                f"cd_offset=0x{cd_offset:X}"
            )
            encoded_col_va = struct.pack("<Q", image_base + col_rva)
            for col_reference in occurrences(data, encoded_col_va):
                vtable_offset = col_reference + 8
                try:
                    vtable_rva = offset_to_rva(vtable_offset)
                except pefile.PEFormatError:
                    continue
                functions: list[str] = []
                for slot in range(arguments.slots):
                    value = struct.unpack_from("<Q", data, vtable_offset + slot * 8)[0]
                    if value < image_base or value >= image_base + image.OPTIONAL_HEADER.SizeOfImage:
                        break
                    functions.append(f"0x{value - image_base:X}")
                print(
                    f"    VTABLE rva=0x{vtable_rva:X} functions=[{', '.join(functions)}]"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
