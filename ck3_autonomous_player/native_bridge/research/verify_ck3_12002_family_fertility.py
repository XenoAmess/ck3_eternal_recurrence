"""Verify 1.20.0.2 effective marriage fertility ABI from frozen file bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage, verify


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "fixtures/ck3_12002_family_fertility_abi.json"


def verify_family_fertility(exe: Path, manifest_path: Path = MANIFEST) -> dict:
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
        immediate = [hex(op.imm) for op in ins.operands if op.type == X86_OP_IMM]
        if (ins.bytes.hex(" ").upper() != row["bytes"] or
                f"{ins.mnemonic} {ins.op_str}" != row["instruction"] or
                rip_targets != row["rip_targets"] or
                immediate != row["immediate_operands"]):
            raise ValueError(f"Changed fertility instruction at {row['rva']}")
        instructions[rva] = ins
    for name, row in manifest["frozen_spans"].items():
        offset = pe.rva_to_offset(int(row["rva"], 0))
        span = data[offset:offset + row["length"]]
        if hashlib.sha256(span).hexdigest() != row["sha256"]:
            raise ValueError(f"Changed fertility source span {name}")
    constants = {name: int(value, 0)
                 for name, value in manifest["runtime_bindings"].items()}
    for row in manifest["native_constant_bindings"]:
        ins = instructions[int(row["rva"], 0)]
        if row["kind"] == "immediate":
            values = [op.imm for op in ins.operands if op.type == X86_OP_IMM]
        elif row["kind"] == "displacement":
            values = [op.mem.disp for op in ins.operands if op.type == X86_OP_MEM]
        else:
            raise ValueError(f"Unknown binding type {row['kind']}")
        if values != [constants[row["constant"]]]:
            raise ValueError(f"Native operand disagrees with {row['constant']}")

    # Reproduce the decoded signed high-product sequence, then compare it to
    # integer truncation. This establishes its denominator without game access.
    scale = manifest["raw_scale"]
    denominator = scale["denominator"]
    magic = int(scale["multiply_divide_magic"], 0)
    shift = scale["multiply_shift"]
    vectors = [-(2**63) + 1, -1000001, -100000, -99999, -1,
               0, 1, 40000, 50000, 99999, 100000, 100001, 1000001, 2**63 - 1]
    for value in vectors:
        high = (value * magic) >> 64
        signed = high >> shift
        actual = signed + (1 if signed < 0 else 0)
        expected = abs(value) // denominator * (-1 if value < 0 else 1)
        if actual != expected:
            raise ValueError(f"Fixed-point divisor mismatch for {value}")
    residual = instructions[0x2B953AD]
    residual_scale = [op.imm for op in residual.operands if op.type == X86_OP_IMM]
    if residual_scale != [denominator]:
        raise ValueError("Native residual multiplier does not match raw scale")
    return {
        "status": "PASS", "readiness": "static-ready",
        "game_version": manifest["build"]["product_version"],
        "executable_sha256": hashlib.sha256(data).hexdigest(),
        "signature_count": len(manifest["signature_anchors"]),
        "instruction_count": len(manifest["semantic_checks"]),
        "source_span_count": len(manifest["frozen_spans"]),
        "direct_native_binding_count": len(manifest["native_constant_bindings"]),
        "runtime_bindings": manifest["runtime_bindings"],
        "raw_scale_denominator": denominator,
        "fixed_point_vectors": len(vectors),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "process_access": False, "local_ck3_touched": False,
        "live_validation": False,
        "boundary": "Individual native effective fertility input; no future pair birth probability.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    result = verify_family_fertility(args.exe)
    if args.result:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
