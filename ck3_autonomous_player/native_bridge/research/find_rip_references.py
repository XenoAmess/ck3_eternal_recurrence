"""Find candidate RIP-relative mov/lea references to an RVA in an EXE file."""

from __future__ import annotations

import argparse
from pathlib import Path
import re

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP

from scan_anchors import PeImage


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=lambda value: int(value, 0))
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    data = args.exe.read_bytes()
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    # Decode only possible RIP-relative mov/lea starts in code. References
    # remain candidates until the surrounding function/call chain is reviewed.
    pattern = rb"[\x40-\x4f]?[\x8b\x89\x8d][\x05\x0d\x15\x1d\x25\x2d\x35\x3d]...."
    for rva, _, offset, size in pe.sections:
        if rva != 0x1000:
            continue
        for match in re.finditer(pattern, data[offset:offset + size], re.DOTALL):
            start = rva + match.start()
            displacement = int.from_bytes(match.group()[-4:], "little", signed=True)
            if start + len(match.group()) + displacement != args.target:
                continue
            instruction = next(decoder.disasm(match.group(), start), None)
            if instruction is not None and any(
                operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP
                and instruction.address + instruction.size + operand.mem.disp == args.target
                for operand in instruction.operands
            ):
                print(f"0x{start:X} {instruction.bytes.hex(' ')} "
                      f"{instruction.mnemonic} {instruction.op_str}")


if __name__ == "__main__":
    main()
