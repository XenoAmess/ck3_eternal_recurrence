#!/usr/bin/env python3
"""Find common x64 direct-call and RIP-relative references to CK3 RVAs."""

from __future__ import annotations

import argparse
from pathlib import Path
import struct

import pefile


HERE = Path(__file__).resolve().parent
DEFAULT_EXE = HERE.parents[2] / "Crusader Kings III" / "binaries" / "ck3.exe"


def integer(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rva", nargs="+", type=integer)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    arguments = parser.parse_args()

    exe = arguments.exe.resolve()
    data = exe.read_bytes()
    image = pefile.PE(str(exe), fast_load=True)
    targets = set(arguments.rva)

    for target in sorted(targets):
        needle = struct.pack("<Q", image.OPTIONAL_HEADER.ImageBase + target)
        start = 0
        while True:
            offset = data.find(needle, start)
            if offset < 0:
                break
            try:
                source_rva = image.get_rva_from_offset(offset)
            except pefile.PEFormatError:
                source_rva = -1
            if source_rva >= 0:
                print(f"abs  source=0x{source_rva:X} target=0x{target:X}")
            start = offset + 1

    for section in image.sections:
        if not section.IMAGE_SCN_MEM_EXECUTE:
            continue
        start = section.PointerToRawData
        end = start + section.SizeOfRawData
        section_rva = section.VirtualAddress
        code = data[start:end]
        for offset in range(len(code) - 7):
            source_rva = section_rva + offset
            opcode = code[offset]
            if opcode in (0xE8, 0xE9):
                displacement = struct.unpack_from("<i", code, offset + 1)[0]
                target = source_rva + 5 + displacement
                if target in targets:
                    kind = "call" if opcode == 0xE8 else "jmp"
                    print(f"{kind:4} source=0x{source_rva:X} target=0x{target:X}")
            # The CK3 constructors predominantly load static vtables and
            # singleton slots with REX.W + LEA/MOV r64,[RIP+disp32].
            if (
                code[offset] in range(0x48, 0x50)
                and code[offset + 1] in (0x8D, 0x8B)
                and code[offset + 2] & 0xC7 == 0x05
            ):
                displacement = struct.unpack_from("<i", code, offset + 3)[0]
                target = source_rva + 7 + displacement
                if target in targets:
                    kind = "lea" if code[offset + 1] == 0x8D else "mov"
                    print(f"{kind:4} source=0x{source_rva:X} target=0x{target:X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
