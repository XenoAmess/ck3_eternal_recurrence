"""Verify frozen 1.20.0.2 family-query ABI using only executable file bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage, verify


def verify_family_query(exe: Path, manifest_path: Path | None = None) -> dict:
    here = Path(__file__).resolve().parent
    manifest_path = manifest_path or here / "ck3_12002_family_query_abi.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures = verify(exe, manifest_path)
    if failures:
        raise ValueError("; ".join(failures))
    data = exe.read_bytes()
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    instructions = {}
    for row in manifest["semantic_checks"]:
        rva = int(row["rva"], 0)
        offset = pe.rva_to_offset(rva)
        ins = next(decoder.disasm(data[offset:offset + 15], rva))
        rip_targets = [hex(ins.address + ins.size + op.mem.disp)
                       for op in ins.operands
                       if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
        immediate_targets = [hex(op.imm) for op in ins.operands if op.type == X86_OP_IMM]
        if (ins.bytes.hex(" ").upper() != row["bytes"] or
                f"{ins.mnemonic} {ins.op_str}" != row["instruction"] or
                rip_targets != row["rip_targets"] or
                immediate_targets != row["immediate_operands"]):
            raise ValueError(f"Changed family query ABI at {row['rva']}")
        instructions[row["rva"]] = ins
    source = (here.parent / "include/xar_bridge/ck3_12002_family_query_abi.hpp").read_text(
        encoding="utf-8-sig")
    constants = {}
    for name, wanted in manifest["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9a-fA-F]+)", source)
        if match is None or int(match.group(1), 0) != int(wanted, 0):
            raise ValueError(f"Changed source constant {name}")
        constants[name] = int(match.group(1), 0)
    for row in manifest["native_constant_bindings"]:
        ins = instructions[row["rva"]]
        kind = row["kind"]
        operands = [op for op in ins.operands if op.type ==
                    (X86_OP_IMM if kind == "immediate" else X86_OP_MEM)]
        if kind == "rip":
            values = [ins.address + ins.size + op.mem.disp for op in operands
                      if op.mem.base == X86_REG_RIP]
        elif kind == "displacement":
            values = [op.mem.disp for op in operands]
        elif kind == "immediate":
            values = [op.imm for op in operands]
        else:
            raise ValueError(f"Unknown operand kind {kind}")
        if values != [constants[row["constant"]]]:
            raise ValueError(f"Native operand disagrees with {row['constant']}")
    result = {
        "status": "PASS", "readiness": "static-ready",
        "live_validation": False, "process_access": False,
        "game_version": manifest["build"]["product_version"],
        "executable_sha256": hashlib.sha256(data).hexdigest(),
        "signature_count": len(manifest["signature_anchors"]),
        "instruction_count": len(manifest["semantic_checks"]),
        "source_constant_count": len(constants),
        "direct_native_binding_count": len(manifest["native_constant_bindings"]),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    result = verify_family_query(args.exe)
    if args.result:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
