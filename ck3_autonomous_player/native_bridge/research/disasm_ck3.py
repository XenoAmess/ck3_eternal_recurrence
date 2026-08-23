#!/usr/bin/env python3
"""Print a bounded CK3 x64 disassembly range by RVA.

This helper is intentionally read-only.  It keeps reverse-engineering notes
reproducible without committing multi-megabyte dumpbin output.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
import pefile


HERE = Path(__file__).resolve().parent
DEFAULT_EXE = HERE.parents[2] / "Crusader Kings III" / "binaries" / "ck3.exe"


def integer(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rva", type=integer)
    parser.add_argument("--size", type=integer, default=0x200)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    arguments = parser.parse_args()

    image = pefile.PE(str(arguments.exe.resolve()), fast_load=True)
    offset = image.get_offset_from_rva(arguments.rva)
    data = Path(arguments.exe).read_bytes()[offset : offset + arguments.size]
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = False
    virtual_address = image.OPTIONAL_HEADER.ImageBase + arguments.rva
    for instruction in decoder.disasm(data, virtual_address):
        print(
            f"{instruction.address - image.OPTIONAL_HEADER.ImageBase:09X}  "
            f"{instruction.bytes.hex(' '):<32} "
            f"{instruction.mnemonic:<8} {instruction.op_str}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
