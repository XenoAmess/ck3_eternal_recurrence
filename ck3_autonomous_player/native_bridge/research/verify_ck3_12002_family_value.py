"""Check family lineage/age/fertility field sources against the frozen CK3 EXE."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage, verify

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures/ck3_12002_family_value_abi.json"


def verify_family_value(exe: Path, fixture: Path = FIXTURE) -> dict:
    manifest = json.loads(fixture.read_text(encoding="utf-8-sig"))
    failures = verify(exe, fixture)
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
        actual = (ins.bytes.hex(" ").upper(), f"{ins.mnemonic} {ins.op_str}",
                  [hex(ins.address + ins.size + op.mem.disp)
                   for op in ins.operands
                   if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP],
                  [hex(op.imm) for op in ins.operands
                   if op.type == X86_OP_IMM and ins.mnemonic == "call"])
        expected = (row["bytes"], row["instruction"], row["rip_targets"],
                    row["direct_target"])
        if actual != expected:
            raise ValueError(f"Changed native family input {row['name']}")
        instructions[row["name"]] = ins
    header = (HERE.parent / "include/xar_bridge/ck3_12002_family_value.hpp").read_text(
        encoding="utf-8-sig")
    constants = {}
    for name, value in manifest["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9A-Fa-f]+)", header)
        wanted = int(value, 0)
        if match is None or int(match.group(1), 0) != wanted:
            raise ValueError(f"Changed family value source constant {name}")
        constants[name] = wanted
    for native_name, constant in manifest["field_source_bindings"].items():
        ins = instructions[native_name]
        displacements = [op.mem.disp for op in ins.operands
                         if op.type == X86_OP_MEM and op.mem.base != X86_REG_RIP]
        if displacements != [constants[constant]]:
            raise ValueError(f"Native field disagrees with {constant}")
    for native_name, constant in manifest["global_source_bindings"].items():
        ins = instructions[native_name]
        targets = [ins.address + ins.size + op.mem.disp for op in ins.operands
                   if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
        if targets != [constants[constant]]:
            raise ValueError(f"Native global disagrees with {constant}")
    for native_name, constant in manifest["native_call_bindings"].items():
        targets = [op.imm for op in instructions[native_name].operands
                   if op.type == X86_OP_IMM]
        if targets != [constants[constant]]:
            raise ValueError(f"Native eligibility call disagrees with {constant}")
    return {
        "status": "GREEN", "readiness": "static-ready", "live_verified": False,
        "game_version": "1.20.0.2", "local_ck3_touched": False,
        "executable_sha256": hashlib.sha256(data).hexdigest(),
        "fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        "unique_signatures": len(manifest["signature_anchors"]),
        "semantic_instructions": len(instructions), "source_constants": len(constants),
        "native_source_bindings": sum(len(manifest[name]) for name in
            ("field_source_bindings", "global_source_bindings", "native_call_bindings")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify_family_value(args.exe)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS family values: {result['unique_signatures']} unique signatures, "
          f"{result['semantic_instructions']} native instructions, "
          f"{result['source_constants']} source constants, "
          f"{result['native_source_bindings']} direct source bindings; offline only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
