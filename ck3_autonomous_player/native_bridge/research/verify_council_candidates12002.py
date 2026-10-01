#!/usr/bin/env python3
"""Verify the exact 1.20.0.2 council producer/lifetime ABI from frozen files."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86_const import X86_OP_MEM, X86_REG_RIP

from scan_anchors import PeImage

HERE = Path(__file__).resolve().parent


def verify(exe: Path, stock: Path) -> dict[str, object]:
    contract = json.loads((HERE / "council_candidates12002_abi.json").read_text(encoding="utf-8"))
    data = exe.read_bytes()
    pe = PeImage(data)
    actual_sha = hashlib.sha256(data).hexdigest().upper()
    failures: list[str] = []
    if actual_sha != contract["executable_sha256"]:
        failures.append("executable SHA-256 differs")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    for expected in contract["spans"]:
        start, end = int(expected["start"], 0), int(expected["end"], 0)
        at = pe.rva_to_offset(start)
        if hashlib.sha256(data[at:at + end - start]).hexdigest().upper() != expected["sha256"]:
            failures.append(f"span {expected['name']} differs")
    for expected in contract["instructions"]:
        address = int(expected["rva"], 0)
        at = pe.rva_to_offset(address)
        instruction = next(decoder.disasm(data[at:at + 15], address), None)
        if (instruction is None or instruction.bytes.hex().upper() != expected["bytes"]
                or instruction.mnemonic != expected["mnemonic"]
                or instruction.op_str != expected["operand"]):
            failures.append(f"instruction {address:#x} differs")
    for expected in contract["global_loads"]:
        address = int(expected["instruction_rva"], 0)
        at = pe.rva_to_offset(address)
        instruction = next(decoder.disasm(data[at:at + 15], address), None)
        targets = [] if instruction is None else [
            address + instruction.size + operand.mem.disp
            for operand in instruction.operands
            if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP
        ]
        if targets != [int(expected["target_rva"], 0)]:
            failures.append(f"global load {address:#x} differs")
    vtable = contract["vtable_prefix"]
    at = pe.rva_to_offset(int(vtable["rva"], 0))
    observed = [struct.unpack_from("<Q", data, at + index * 8)[0] - pe.image_base
                for index in range(len(vtable["entries"]))]
    if observed != [int(value, 0) for value in vtable["entries"]]:
        failures.append("inline allocator vtable differs")
    header = (HERE.parent / "include/xar_bridge/ck3_12002_council_candidates.hpp").read_text(encoding="utf-8-sig")
    for name, value in contract["source_constants"].items():
        match = re.search(r"\b" + re.escape(name) + r"\s*=\s*(0x[0-9A-Fa-f]+|[0-9]+)\s*;", header)
        if match is None or int(match.group(1), 0) != int(value, 0):
            failures.append(f"provider constant {name} differs")
    core_header = (HERE.parent / "include/xar_bridge/ck3_12002.hpp").read_text(encoding="utf-8-sig")
    match = re.search(r"\bkCharacterStorageSlotRva\s*=\s*(0x[0-9A-Fa-f]+)", core_header)
    if match is None or int(match.group(1), 0) != int(contract["globals"]["character_storage"], 0):
        failures.append("shared Character storage slot differs")
    for expected in contract["stock_inputs"]:
        if hashlib.sha256((stock / expected["path"]).read_bytes()).hexdigest().upper() != expected["sha256"]:
            failures.append(f"frozen stock input {expected['path']} differs")
    if int(contract["layout"]["character_stewardship"], 0) != (
            int(contract["layout"]["skill_array"], 0) + 4 * contract["layout"]["stewardship_enum"]):
        failures.append("stewardship array projection differs")
    return {
        "status": "GREEN" if not failures else "RED",
        "game_version": contract["game_version"],
        "executable_sha256": actual_sha,
        "verified_spans": len(contract["spans"]),
        "verified_instructions": len(contract["instructions"]),
        "verified_global_loads": len(contract["global_loads"]),
        "verified_allocator_vtable_entries": len(vtable["entries"]),
        "verified_source_constants": len(contract["source_constants"]) + 1,
        "verified_stock_inputs": len(contract["stock_inputs"]),
        "evidence_level": "static-ready",
        "local_ck3_used": False,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--stock", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    result = verify(arguments.exe, arguments.stock)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
