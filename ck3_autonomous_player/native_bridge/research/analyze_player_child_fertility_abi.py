"""Verify the exact-build native marriage fertility input call sites."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"


def _disassemble(pe: pefile.PE, data: bytes, start: int, size: int = 160) -> None:
    engine = Cs(CS_ARCH_X86, CS_MODE_64)
    chunk = data[pe.get_offset_from_rva(start): pe.get_offset_from_rva(start) + size]
    for ins in engine.disasm(chunk, pe.OPTIONAL_HEADER.ImageBase + start):
        print(f"{ins.address - pe.OPTIONAL_HEADER.ImageBase:08X}: {ins.mnemonic:8s} {ins.op_str}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("exe", type=Path)
    parser.add_argument("--around", type=lambda text: int(text, 0))
    parser.add_argument("--contract", action="store_true")
    args = parser.parse_args()
    data = args.exe.read_bytes()
    assert hashlib.sha256(data).hexdigest().upper() == EXE_SHA256
    pe = pefile.PE(data=data, fast_load=True)
    if args.around is not None:
        _disassemble(pe, data, args.around, 256)
        return
    if args.contract:
        contract = json.loads(Path(__file__).with_name(
            "player_child_marriage_fertility_1_19_0_6_abi.json").read_text())
        assert contract["exact_build"]["executable_sha256"] == EXE_SHA256
        for name, rva, length in (
            ("ui_filter", 0x127065C, 0x4B),
            ("ai_marriage_score", 0x1890FA9, 0x2F),
            ("fertility_gate", 0x260FAF0, 0x144),
        ):
            offset = pe.get_offset_from_rva(rva)
            span = data[offset:offset + length]
            key = {"ui_filter": "ui_fertility_filter",
                   "ai_marriage_score": "ai_marriage_candidate_score",
                   "fertility_gate": "fertility_eligibility_gate"}[name]
            expected = contract["native_sources"][key]
            assert int(expected["rva"], 16) == rva
            assert expected["length"] == length
            assert expected["sha256"] == hashlib.sha256(span).hexdigest().upper()
            if name == "fertility_gate":
                assert expected["first_16_bytes"] == span[:16].hex().upper()
            print(name, "verified", hex(rva), length)
        return
    targets = {}
    for term in (b"GetFertility", b"fertility\x00", b"CanHaveChildrenWith"):
        positions = [pe.get_rva_from_offset(match.start())
                     for match in re.finditer(re.escape(term), data)]
        targets[term] = positions
        print(term.decode(), [hex(value) for value in positions[:20]])
    text = next(section for section in pe.sections if section.Name.startswith(b".text"))
    code = data[text.PointerToRawData: text.PointerToRawData + text.SizeOfRawData]
    for target in targets[b"fertility\x00"]:
        literal = pe.OPTIONAL_HEADER.ImageBase + target
        pointers = [pe.get_rva_from_offset(match.start()) for match in
                    re.finditer(re.escape(struct.pack("<Q", literal)), data)]
        print("pointer references", hex(target), [hex(item) for item in pointers])
        xrefs = []
        for match in re.finditer(b"\x8d", code):
            index = match.start()
            if (index + 6 < len(code) and code[index + 1] in
                    (0x05, 0x0D, 0x15, 0x1D, 0x25, 0x2D, 0x35, 0x3D)):
                start = text.VirtualAddress + index
                displacement = struct.unpack_from("<i", code, index + 2)[0]
                if start + 6 + displacement == target:
                    xrefs.append(start)
        print("lea rip references", hex(target), [hex(item) for item in xrefs])
        for xref in xrefs:
            print("-- around", hex(xref))
            _disassemble(pe, data, xref - 16, 96)


if __name__ == "__main__":
    main()
