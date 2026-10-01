"""Verify exact 1.20 ranked producer, native container lifecycle and source pins."""
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
from verify_ck3_12002_family_ranked_producer import verify as verify_producer

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "fixtures/ck3_12002_family_ranked_lifecycle_abi.json"


def verify(executable: Path) -> dict:
    producer = verify_producer(executable)
    manifest = json.loads(CONTRACT.read_text(encoding="utf-8"))
    data = executable.read_bytes()
    build = manifest["exact_build"]
    if len(data) != build["executable_size"] or hashlib.sha256(data).hexdigest().upper() != build["executable_sha256"]:
        raise ValueError("Changed ranked lifecycle EXE identity")
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    decoded = {}
    for row in manifest["semantic_checks"]:
        rva = int(row["rva"], 0)
        offset = pe.rva_to_offset(rva)
        ins = next(decoder.disasm(data[offset:offset + 15], rva))
        rip = [hex(ins.address + ins.size + op.mem.disp) for op in ins.operands
               if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
        immediate = [hex(op.imm) for op in ins.operands if op.type == X86_OP_IMM]
        if (ins.bytes.hex(" ").upper() != row["bytes"] or
                f"{ins.mnemonic} {ins.op_str}" != row["instruction"] or
                rip != row["rip_targets"] or immediate != row["immediate_operands"]):
            raise ValueError(f"Changed ranked lifecycle instruction {row['rva']}")
        decoded[rva] = ins
    for row in manifest["function_spans"]:
        start, end = int(row["start_rva"], 0), int(row["end_rva_exclusive"], 0)
        offset = pe.rva_to_offset(start)
        if hashlib.sha256(data[offset:offset + end - start]).hexdigest() != row["sha256"]:
            raise ValueError(f"Changed ranked lifecycle span {row['role']}")
    for row in manifest["vtable_and_allocator_checks"]:
        pointer = struct.unpack_from("<Q", data, pe.rva_to_offset(int(row["slot_rva"], 0)))[0]
        if pointer - pe.image_base != int(row["target_rva"], 0):
            raise ValueError(f"Changed ranked lifecycle vtable {row['role']}")
    header = (HERE.parent / "include/xar_bridge/ck3_12002_family_ranked_abi.hpp").read_text(encoding="utf-8-sig")
    constants = {}
    for name, wanted in manifest["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9a-fA-F]+)", header)
        if match is None or int(match.group(1), 0) != int(wanted, 0):
            raise ValueError(f"Changed ranked lifecycle source constant {name}")
        constants[name] = int(wanted, 0)
    for row in manifest["native_constant_bindings"]:
        ins = decoded[int(row["rva"], 0)]
        if row["kind"] == "rip":
            values = [ins.address + ins.size + op.mem.disp for op in ins.operands
                      if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
        elif row["kind"] == "immediate":
            values = [op.imm for op in ins.operands if op.type == X86_OP_IMM]
        else:
            raise ValueError("Unknown ranked lifecycle operand binding")
        if constants[row["constant"]] not in values:
            raise ValueError(f"Source disagrees with native ranked lifecycle {row['constant']}")
    for row in manifest["source_vtable_bindings"]:
        pointer = struct.unpack_from("<Q", data, pe.rva_to_offset(int(row["slot_rva"], 0)))[0]
        if pointer - pe.image_base != constants[row["constant"]]:
            raise ValueError(f"Source disagrees with native ranked vtable {row['constant']}")
    return {
        "status": "PASS", "readiness": "static-ready", "live_verified": False,
        "process_access": False, "game_access": False,
        "executable_sha256": hashlib.sha256(data).hexdigest(),
        "producer": producer,
        "lifecycle_manifest_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "lifecycle_instruction_count": len(manifest["semantic_checks"]),
        "lifecycle_span_count": len(manifest["function_spans"]),
        "lifecycle_vtable_allocator_edge_count": len(manifest["vtable_and_allocator_checks"]),
        "lifecycle_source_constant_count": len(constants),
        "lifecycle_native_constant_binding_count": len(manifest["native_constant_bindings"]) + len(manifest["source_vtable_bindings"]),
        "remaining_live": [
            "Paused actual played-character ranked query and actual native Strategy absence/presence.",
            "Native producer/sort rows versus stock AIWatch CalculateSpouseCandidates on a Strategy-bearing subject, when available.",
            "Actual redirected pair legality/acceptance/outcome and same-frame receipt through slot 38.",
        ],
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
