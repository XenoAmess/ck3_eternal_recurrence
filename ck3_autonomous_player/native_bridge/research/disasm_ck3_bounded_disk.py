#!/usr/bin/env python3
"""Disassemble a small CK3 RVA span without loading or scanning the whole EXE.

Static research helper only. A frozen build identity must be supplied separately;
file size plus anchor bytes here are a guard against accidental build mismatch,
not a replacement for a complete build hash.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import struct

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


EXPECTED_SIZE = 95_206_008
IMAGE_BASE = 0x140000000
DEFAULT_EXE = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe")
ANCHORS = {
    0x2E9F70B: bytes.fromhex("E820080000"),
    0x2E9F722: bytes.fromhex("E899FBFFFF"),
    0x2E9F319: bytes.fromhex("E8B29D4B00"),
    0x336AC47: bytes.fromhex("FF5030"),
    0x336AC8B: bytes.fromhex("FF5020"),
}


def sections(stream) -> tuple[int, list[tuple[int, int, int]]]:
    stream.seek(0)
    header = stream.read(0x1000)
    if header[:2] != b"MZ":
        raise ValueError("missing DOS header")
    pe_offset = struct.unpack_from("<I", header, 0x3C)[0]
    if pe_offset + 0x18 > len(header) or header[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise ValueError("missing PE header in bounded header read")
    count = struct.unpack_from("<H", header, pe_offset + 6)[0]
    opt_size = struct.unpack_from("<H", header, pe_offset + 20)[0]
    opt = pe_offset + 24
    image_base = struct.unpack_from("<Q", header, opt + 24)[0]
    section_offset = opt + opt_size
    if section_offset + count * 40 > len(header):
        raise ValueError("section table exceeds bounded header read")
    result = []
    for index in range(count):
        offset = section_offset + index * 40
        virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from(
            "<IIII", header, offset + 8
        )
        result.append((virtual_address, min(virtual_size, raw_size), raw_pointer))
    return image_base, result


def read_rva(stream, mapped_sections: list[tuple[int, int, int]], rva: int, size: int) -> bytes:
    for start, length, file_offset in mapped_sections:
        if start <= rva and rva + size <= start + length:
            stream.seek(file_offset + rva - start)
            data = stream.read(size)
            if len(data) != size:
                raise ValueError(f"short read at 0x{rva:X}")
            return data
    raise ValueError(f"RVA span 0x{rva:X}+0x{size:X} is not in one raw section")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rva", type=lambda value: int(value, 0))
    parser.add_argument("--size", type=lambda value: int(value, 0), default=0x100)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--hex", action="store_true", help="print bounded raw bytes instead of disassembly")
    args = parser.parse_args()
    if not 0 < args.size <= 0x1000:
        parser.error("size must be 1..0x1000 bytes")
    with args.exe.open("rb") as stream:
        stream.seek(0, 2)
        if stream.tell() != EXPECTED_SIZE:
            raise ValueError("EXE size differs from frozen CK3 1.19.0.6")
        image_base, mapped_sections = sections(stream)
        if image_base != IMAGE_BASE:
            raise ValueError("unexpected image base")
        for anchor_rva, expected in ANCHORS.items():
            if read_rva(stream, mapped_sections, anchor_rva, len(expected)) != expected:
                raise ValueError(f"anchor mismatch at 0x{anchor_rva:X}")
        data = read_rva(stream, mapped_sections, args.rva, args.size)
    if args.hex:
        print(f"{args.rva:09X}  {data.hex(' ')}")
        return 0
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    for instruction in decoder.disasm(data, IMAGE_BASE + args.rva):
        print(
            f"{instruction.address - IMAGE_BASE:09X}  "
            f"{instruction.bytes.hex(' '):<32} "
            f"{instruction.mnemonic:<8} {instruction.op_str}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
