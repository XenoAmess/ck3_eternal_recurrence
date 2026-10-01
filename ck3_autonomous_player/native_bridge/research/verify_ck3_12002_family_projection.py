"""Verify the actual 1.20.0.2 marriage pair producer and consumer file ABI."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "fixtures/ck3_12002_family_projection_abi.json"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def verify(executable: Path) -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    data = executable.read_bytes()
    pe = PeImage(data)
    build = contract["exact_build"]
    require(len(data) == build["executable_size"], "EXE size drift")
    require(hashlib.sha256(data).hexdigest().upper() ==
            build["executable_sha256"], "EXE SHA-256 drift")

    def read(rva: int, size: int) -> bytes:
        offset = pe.rva_to_offset(rva)
        return data[offset:offset + size]

    for row in contract["native_spans"]:
        start, end = int(row["rva_start"], 0), int(row["rva_end_exclusive"], 0)
        actual = read(start, end - start)
        require(actual.hex() == row["raw_hex"] and
                hashlib.sha256(actual).hexdigest().upper() == row["sha256"],
                f"Changed native {row['name']}")
    for row in contract["direct_calls"]:
        site, target = int(row["site"], 0), int(row["target"], 0)
        call = read(site, 5)
        require(call[0] == 0xE8 and
                site + 5 + struct.unpack_from("<i", call, 1)[0] == target,
                f"Changed native call {row['site']}")
    table = contract["vtable_prefix"]
    base = pe.image_base
    actual = struct.unpack("<8Q", read(int(table["rva"], 0), 64))
    require(list(actual) == [base + int(v, 0) for v in table["function_rvas"]],
            "Changed native three-row owner vtable")
    source = (HERE.parent / "include/xar_bridge/ck3_12002_family_projection.hpp").read_text(
        encoding="utf-8-sig")
    constants = {}
    for name, expected in contract["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9a-fA-F]+)", source)
        require(match is not None and int(match.group(1), 0) == int(expected, 0),
                f"Changed source constant {name}")
        constants[name] = int(expected, 0)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    for row in contract["native_operand_bindings"]:
        rva = int(row["rva"], 0)
        instruction = next(decoder.disasm(read(rva, 15), rva))
        require(instruction.bytes.hex() == row["bytes"] and
                f"{instruction.mnemonic} {instruction.op_str}" == row["instruction"],
                f"Changed native binding instruction at {row['rva']}")
        if row["kind"] == "rip":
            values = [instruction.address + instruction.size + op.mem.disp
                      for op in instruction.operands if op.type == X86_OP_MEM and
                      op.mem.base == X86_REG_RIP]
        elif row["kind"] == "immediate":
            values = [op.imm for op in instruction.operands if op.type == X86_OP_IMM]
        elif row["kind"] == "displacement":
            values = [op.mem.disp for op in instruction.operands if op.type == X86_OP_MEM]
        else:
            raise ValueError(f"Unknown binding type {row['kind']}")
        require(constants[row["constant"]] in values,
                f"Source constant not present in native operand {row['constant']}")
    layout = contract["layout"]
    require(layout["inline_capacity"] == 3 and layout["pair_row_stride"] == 32 and
            layout["inline_owner_bytes"] == 104 and layout["vector_header_bytes"] == 24,
            "Changed bounded native vector layout")
    return {
        "status": "GREEN", "readiness": "static-ready",
        "live_validation": False, "process_access": False,
        "executable_sha256": hashlib.sha256(data).hexdigest(),
        "native_span_count": len(contract["native_spans"]),
        "direct_call_count": len(contract["direct_calls"]),
        "source_constant_count": len(constants),
        "native_operand_binding_count": len(contract["native_operand_bindings"]),
        "contract_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    result = verify(args.exe.resolve())
    if args.result:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
