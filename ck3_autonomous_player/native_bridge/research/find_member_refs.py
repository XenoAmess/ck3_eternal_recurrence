#!/usr/bin/env python3
"""Find x64 instructions whose memory operand uses selected displacements.

This helper is intentionally read-only.  It is useful for reconstructing a
native structure field's consumers without relying on brittle byte searches.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM
import pefile


HERE = Path(__file__).resolve().parent
DEFAULT_EXE = HERE.parents[2] / "Crusader Kings III" / "binaries" / "ck3.exe"


def integer(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("displacement", nargs="+", type=integer)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    arguments = parser.parse_args()

    image = pefile.PE(str(arguments.exe.resolve()), fast_load=True)
    image_base = image.OPTIONAL_HEADER.ImageBase
    targets = set(arguments.displacement)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    decoder.skipdata = True

    for section in image.sections:
        if not section.IMAGE_SCN_MEM_EXECUTE:
            continue
        code = section.get_data()
        virtual_address = image_base + section.VirtualAddress
        for instruction in decoder.disasm(code, virtual_address):
            if instruction.id == 0:
                continue
            hits = {
                operand.mem.disp
                for operand in instruction.operands
                if operand.type == X86_OP_MEM and operand.mem.disp in targets
            }
            if not hits:
                continue
            formatted_hits = ",".join(f"0x{hit:X}" for hit in sorted(hits))
            print(
                f"{instruction.address - image_base:09X}  "
                f"{instruction.bytes.hex(' '):<32} "
                f"{instruction.mnemonic:<8} {instruction.op_str:<48} "
                f"; {formatted_hits}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
