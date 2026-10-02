#!/usr/bin/env python3
"""Bounded, read-only CHudTopBar constructor callsite research.

Only scans direct CALL bytes in an explicitly bounded 0x600000-byte RVA window
around the known constructor. Candidate CALL sites are disassembled locally;
this script does not inspect a CK3 process or search the entire executable.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import mmap
from pathlib import Path
import struct

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP
import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
CONSTRUCTOR_RVA = 0xD465A0
WINDOW_BEGIN = 0x900000
WINDOW_END = 0xF00000


def find_exe() -> Path:
    import psutil

    paths = []
    for process in psutil.process_iter(("name", "exe")):
        try:
            if (process.info["name"] or "").lower() == "ck3.exe":
                paths.append(Path(process.info["exe"]))
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    if len(set(paths)) != 1:
        raise ValueError(f"expected one installed ck3.exe path; found {paths}")
    return paths[0]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path)
    parser.add_argument("--target-rva", type=lambda value: int(value, 0), default=CONSTRUCTOR_RVA)
    parser.add_argument("--window-begin", type=lambda value: int(value, 0), default=WINDOW_BEGIN)
    parser.add_argument("--window-end", type=lambda value: int(value, 0), default=WINDOW_END)
    parser.add_argument("--rdata-pointers", action="store_true")
    parser.add_argument("--data-start", type=lambda value: int(value, 0))
    parser.add_argument("--data-size", type=lambda value: int(value, 0), default=0x100)
    parser.add_argument("--col-rva", type=lambda value: int(value, 0))
    parser.add_argument("--string-rva", type=lambda value: int(value, 0))
    parser.add_argument("--rip-target", type=lambda value: int(value, 0))
    parser.add_argument("--dump-start", type=lambda value: int(value, 0))
    parser.add_argument("--dump-size", type=lambda value: int(value, 0), default=0x200)
    args = parser.parse_args()
    exe = args.exe or find_exe()
    if sha256(exe) != EXE_SHA256:
        raise ValueError("installed ck3.exe exact SHA mismatch")
    pe = pefile.PE(str(exe), fast_load=True)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.skipdata = True
    decoder.detail = args.rip_target is not None
    print(f"exe={exe} sha256={EXE_SHA256}")
    with exe.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        exception_directory = pe.OPTIONAL_HEADER.DATA_DIRECTORY[3]
        exception_offset = pe.get_offset_from_rva(exception_directory.VirtualAddress)
        count = exception_directory.Size // 12
        starts = [struct.unpack_from("<I", data, exception_offset + index * 12)[0]
                  for index in range(count)]
        index = bisect.bisect_right(starts, 0xA73800) - 1
        function_begin, function_end, unwind = struct.unpack_from(
            "<III", data, exception_offset + index * 12
        )
        print(f"topbar_factory_pdata=0x{function_begin:X}..0x{function_end:X} unwind=0x{unwind:X}")
        if args.dump_start is not None:
            offset = pe.get_offset_from_rva(args.dump_start)
            for instruction in decoder.disasm(
                data[offset:offset + args.dump_size], image_base + args.dump_start
            ):
                print(f"{instruction.address - image_base:09X} {instruction.mnemonic:8} {instruction.op_str}")
            return 0
        if args.data_start is not None:
            offset = pe.get_offset_from_rva(args.data_start)
            for displacement in range(0, args.data_size, 8):
                value = struct.unpack_from("<Q", data, offset + displacement)[0]
                print(f"0x{args.data_start + displacement:X}  0x{value:X}  rva=0x{value - image_base:X}")
            return 0
        if args.col_rva is not None:
            offset = pe.get_offset_from_rva(args.col_rva)
            col = struct.unpack_from("<6I", data, offset)
            type_offset = pe.get_offset_from_rva(col[3] + 0x10)
            name = bytes(data[type_offset:type_offset + 128]).split(b"\0", 1)[0]
            print(f"col={tuple(hex(value) for value in col)} type_name={name!r}")
            return 0
        if args.string_rva is not None:
            offset = pe.get_offset_from_rva(args.string_rva)
            print(f"string_rva=0x{args.string_rva:X}: {bytes(data[offset:offset + 128]).split(bytes((0,)), 1)[0]!r}")
            return 0
        if args.rdata_pointers:
            needle = struct.pack("<Q", image_base + args.target_rva)
            for section in pe.sections:
                name = section.Name.rstrip(b"\0")
                if name != b".rdata":
                    continue
                begin = section.PointerToRawData
                end = begin + section.SizeOfRawData
                cursor = data.find(needle, begin, end)
                while cursor >= 0:
                    print(f"rdata_pointer_rva=0x{section.VirtualAddress + cursor - begin:X}")
                    cursor = data.find(needle, cursor + 1, end)
            return 0
        for section in pe.sections:
            if not section.IMAGE_SCN_MEM_EXECUTE:
                continue
            begin = max(args.window_begin, section.VirtualAddress)
            end = min(args.window_end, section.VirtualAddress + section.SizeOfRawData)
            if begin >= end:
                continue
            start_offset = section.PointerToRawData + begin - section.VirtualAddress
            code = data[start_offset:start_offset + end - begin]
            if args.rip_target is not None:
                for instruction in decoder.disasm(code, image_base + begin):
                    if instruction.id == 0:
                        continue
                    source = instruction.address - image_base
                    for operand in instruction.operands:
                        if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                            target = source + instruction.size + operand.mem.disp
                            if target == args.rip_target:
                                print(f"rip_reference=0x{source:X}: {instruction.mnemonic} {instruction.op_str}")
                continue
            cursor = code.find(b"\xE8")
            while cursor >= 0:
                if cursor + 5 <= len(code):
                    displacement = struct.unpack_from("<i", code, cursor + 1)[0]
                    source = begin + cursor
                    if source + 5 + displacement == args.target_rva:
                        print(f"candidate_call=0x{source:X}")
                        context_begin = max(begin, source - 0x80)
                        context_end = min(end, source + 0x80)
                        context_offset = section.PointerToRawData + context_begin - section.VirtualAddress
                        for instruction in decoder.disasm(
                            data[context_offset:context_offset + context_end - context_begin],
                            image_base + context_begin,
                        ):
                            rva = instruction.address - image_base
                            if source - 0x50 <= rva <= source + 0x50:
                                print(f"  {rva:09X} {instruction.mnemonic:8} {instruction.op_str}")
                cursor = code.find(b"\xE8", cursor + 1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
