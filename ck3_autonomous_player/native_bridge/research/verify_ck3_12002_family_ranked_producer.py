"""Check exact 1.20.0.2 ranked marriage producer/order from frozen EXE bytes."""
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
CONTRACT = HERE / "fixtures/ck3_12002_family_ranked_producer_abi.json"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def verify(executable: Path) -> dict:
    manifest = json.loads(CONTRACT.read_text(encoding="utf-8"))
    data = executable.read_bytes()
    pe = PeImage(data)
    build = manifest["build"]
    require(len(data) == build["file_size"], "EXE size changed")
    require(hashlib.sha256(data).hexdigest().upper() == build["sha256"],
            "EXE SHA-256 changed")

    def read(rva: int, size: int) -> bytes:
        offset = pe.rva_to_offset(rva)
        return data[offset:offset + size]

    for row in manifest["frozen_spans"]:
        start, end = int(row["rva_start"], 0), int(row["rva_end_exclusive"], 0)
        require(hashlib.sha256(read(start, end - start)).hexdigest().upper() ==
                row["sha256"], f"Changed native span {row['name']}")
    for row in manifest["direct_call_edges"]:
        site, target = int(row["source"], 0), int(row["target"], 0)
        code = read(site, 5)
        require(code[0] == 0xE8 and
                site + 5 + struct.unpack_from("<i", code, 1)[0] == target,
                f"Changed native call {row['source']}")
    for row in manifest["string_checks"]:
        expected = bytes.fromhex(row["bytes"])
        require(read(int(row["rva"], 0), len(expected)) == expected,
                f"Changed native registration string {row['text']}")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    instructions = {}
    for row in manifest["semantic_checks"]:
        rva = int(row["rva"], 0)
        instruction = next(decoder.disasm(read(rva, 15), rva))
        rip_targets = [hex(instruction.address + instruction.size + op.mem.disp)
                       for op in instruction.operands if op.type == X86_OP_MEM and
                       op.mem.base == X86_REG_RIP]
        immediate_operands = [hex(op.imm) for op in instruction.operands
                              if op.type == X86_OP_IMM]
        require(instruction.bytes.hex(" ").upper() == row["bytes"] and
                f"{instruction.mnemonic} {instruction.op_str}" == row["instruction"] and
                rip_targets == row["rip_targets"] and
                immediate_operands == row["immediate_operands"],
                f"Changed native instruction {row['rva']}")
        instructions[rva] = instruction
    header = (HERE.parent / "include/xar_bridge/ck3_12002_family_ranked_abi.hpp").read_text(
        encoding="utf-8-sig")
    constants = {}
    for name, expected in manifest["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9A-Fa-f]+)", header)
        require(match is not None and int(match.group(1), 0) == int(expected, 0),
                f"Changed ranked provider source constant {name}")
        constants[name] = int(expected, 0)
    for row in manifest["native_constant_bindings"]:
        instruction = instructions[int(row["rva"], 0)]
        if row["kind"] == "rip":
            values = [instruction.address + instruction.size + op.mem.disp
                      for op in instruction.operands if op.type == X86_OP_MEM and
                      op.mem.base == X86_REG_RIP]
        elif row["kind"] == "immediate":
            values = [op.imm for op in instruction.operands if op.type == X86_OP_IMM]
        elif row["kind"] == "displacement":
            values = [op.mem.disp for op in instruction.operands if op.type == X86_OP_MEM]
        else:
            raise ValueError(f"Unknown binding kind {row['kind']}")
        require(constants[row["constant"]] in values,
                f"Source differs from native operand {row['constant']}")
    return {
        "status": "GREEN", "readiness": "static-ready",
        "live_validation": False, "process_access": False,
        "executable_sha256": hashlib.sha256(data).hexdigest(),
        "frozen_span_count": len(manifest["frozen_spans"]),
        "semantic_instruction_count": len(manifest["semantic_checks"]),
        "direct_call_count": len(manifest["direct_call_edges"]),
        "source_constant_count": len(constants),
        "native_source_binding_count": len(manifest["native_constant_bindings"]),
        "contract_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "ordering": manifest["native_ordering"],
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
