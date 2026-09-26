#!/usr/bin/env python3
"""Find common x64 direct-call and RIP-relative references to CK3 RVAs."""

from __future__ import annotations

import argparse
from pathlib import Path
import struct

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP
import pefile


HERE = Path(__file__).resolve().parent
DEFAULT_EXE = HERE.parents[2] / "Crusader Kings III" / "binaries" / "ck3.exe"
DECODE_CHUNK_BYTES = 64 * 1024
X64_MAX_INSTRUCTION_BYTES = 15


def integer(value: str) -> int:
    return int(value, 0)


def iter_code_refs(code: bytes, scan_rva_start: int, image_base: int,
                   targets: set[int], *, direct_only: bool = False):
    """Yield direct-call candidates and decoded RIP references at bounded RAM.

    A CK3 .text section can be too large for one Capstone allocation.  Decode
    from the previous instruction boundary, with room for a maximal x64
    instruction beyond each chunk.  The raw E8/E9 scan remains a candidate
    scan, not an instruction-boundary proof.
    """
    for opcode, kind in ((0xE8, "call"), (0xE9, "jmp ")):
        position = code.find(bytes((opcode,)))
        while position >= 0:
            if position + 5 <= len(code):
                displacement = struct.unpack_from("<i", code, position + 1)[0]
                target = scan_rva_start + position + 5 + displacement
                if target in targets:
                    yield f"{kind} source=0x{scan_rva_start + position:X} target=0x{target:X}"
            position = code.find(bytes((opcode,)), position + 1)

    if direct_only:
        return

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    decoder.skipdata = True
    position = 0
    while position < len(code):
        limit = min(len(code), position + DECODE_CHUNK_BYTES)
        view_end = min(len(code), limit + X64_MAX_INSTRUCTION_BYTES)
        next_position = position
        for instruction in decoder.disasm(
            code[position:view_end], image_base + scan_rva_start + position
        ):
            offset = instruction.address - image_base - scan_rva_start
            if offset >= limit:
                break
            next_position = offset + instruction.size
            if instruction.id == 0:
                continue
            source_rva = instruction.address - image_base
            for operand in instruction.operands:
                if operand.type != X86_OP_MEM or operand.mem.base != X86_REG_RIP:
                    continue
                target = source_rva + instruction.size + operand.mem.disp
                if target in targets:
                    yield (f"{instruction.mnemonic:4} source=0x{source_rva:X} "
                           f"target=0x{target:X}")
        if next_position <= position:
            raise RuntimeError("Capstone did not advance inside executable section")
        position = next_position


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rva", nargs="+", type=integer)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--source-rva-start", type=integer)
    parser.add_argument("--source-rva-end", type=integer)
    parser.add_argument("--direct-only", action="store_true",
                        help="scan E8/E9 call/jump candidates and absolute pointers without RIP decoding")
    arguments = parser.parse_args()

    exe = arguments.exe.resolve()
    data = exe.read_bytes()
    image = pefile.PE(str(exe), fast_load=True)
    image_base = image.OPTIONAL_HEADER.ImageBase
    targets = set(arguments.rva)

    for target in sorted(targets):
        needle = struct.pack("<Q", image_base + target)
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
        section_rva = section.VirtualAddress
        scan_rva_start = section_rva
        scan_rva_end = section_rva + section.SizeOfRawData
        if arguments.source_rva_start is not None:
            scan_rva_start = max(scan_rva_start, arguments.source_rva_start)
        if arguments.source_rva_end is not None:
            scan_rva_end = min(scan_rva_end, arguments.source_rva_end)
        if scan_rva_start >= scan_rva_end:
            continue
        start = section.PointerToRawData + scan_rva_start - section_rva
        end = section.PointerToRawData + scan_rva_end - section_rva
        code = data[start:end]
        for match in iter_code_refs(code, scan_rva_start, image_base, targets,
                                    direct_only=arguments.direct_only):
            print(match)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
