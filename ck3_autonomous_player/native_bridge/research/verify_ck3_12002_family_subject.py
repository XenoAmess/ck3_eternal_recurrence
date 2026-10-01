"""Verify 1.20.0.2 player-child query ABI from frozen files; no process access."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage, verify


def verify_subject(exe: Path) -> dict:
    here = Path(__file__).resolve().parent
    path = here / "ck3_12002_family_subject_abi.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    errors = verify(exe, path)
    if errors:
        raise ValueError("; ".join(errors))
    data = exe.read_bytes()
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
            raise ValueError(f"Changed native subject instruction {row['rva']}")
        decoded[row["rva"]] = ins
    for row in manifest["frozen_spans"]:
        start, end = int(row["start_rva"], 0), int(row["end_rva_exclusive"], 0)
        offset = pe.rva_to_offset(start)
        if hashlib.sha256(data[offset:offset + end - start]).hexdigest() != row["sha256"]:
            raise ValueError(f"Changed native subject span {row['name']}")
    for row in manifest["vtable_checks"]:
        pointer = struct.unpack_from("<Q", data, pe.rva_to_offset(int(row["slot_rva"], 0)))[0]
        if pointer - pe.image_base != int(row["function_rva"], 0):
            raise ValueError(f"Changed native subject vtable {row['role']}")
    for row in manifest["string_checks"]:
        wanted = row["value"].encode("utf-8") + b"\0"
        offset = pe.rva_to_offset(int(row["rva"], 0))
        if data[offset:offset + len(wanted)] != wanted:
            raise ValueError(f"Changed native subject name {row['value']}")
    source = (here.parent / "include/xar_bridge/ck3_12002_family_subject_abi.hpp").read_text(encoding="utf-8-sig")
    constants = {}
    for name, wanted in manifest["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9a-fA-F]+)", source)
        if match is None or int(match.group(1), 0) != int(wanted, 0):
            raise ValueError(f"Changed subject constant {name}")
        constants[name] = int(match.group(1), 0)
    for row in manifest["native_constant_bindings"]:
        ins = decoded[row["rva"]]
        if row["kind"] == "displacement":
            values = [op.mem.disp for op in ins.operands if op.type == X86_OP_MEM]
        elif row["kind"] == "rip":
            values = [ins.address + ins.size + op.mem.disp for op in ins.operands
                      if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
        elif row["kind"] == "immediate":
            values = [op.imm for op in ins.operands if op.type == X86_OP_IMM]
        else:
            raise ValueError("Unknown operand binding")
        if values != [constants[row["constant"]]]:
            raise ValueError(f"Source subject constant disagrees with native {row['constant']}")
    return {
        "status": "PASS", "readiness": "static-ready", "live_verified": False,
        "process_access": False, "game_access": False,
        "executable_sha256": hashlib.sha256(data).hexdigest(),
        "manifest_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "instruction_count": len(manifest["semantic_checks"]),
        "frozen_span_count": len(manifest["frozen_spans"]),
        "vtable_edge_count": len(manifest["vtable_checks"]),
        "string_count": len(manifest["string_checks"]),
        "source_constant_count": len(constants),
        "direct_binding_count": len(manifest["native_constant_bindings"]),
        "remaining_live": manifest["remaining_live"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    result = verify_subject(args.exe)
    if args.result:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
