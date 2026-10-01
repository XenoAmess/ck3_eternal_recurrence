"""Verify the exact-build recovery variable-list ABI using files only.

No CK3 process, target code, mutator, desktop, or pipe is opened. Existing
PhaseDefinitionBindings and Character generic-target evidence are reused.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

from scan_anchors import PeImage

CONTRACT = Path(__file__).with_suffix(".json")


def file_sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def verify(exe: Path, *, game_root: Path | None = None):
    manifest = json.loads(CONTRACT.read_text(encoding="utf-8"))
    data = exe.read_bytes()
    build = manifest["build"]
    if hashlib.sha256(data).hexdigest().upper() != build["sha256"] or len(data) != build["file_size"]:
        raise ValueError("Exact CK3 executable identity differs")
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    checked = {"instruction_spans": 0, "semantic_instructions": 0,
               "call_edges": 0, "rip_edges": 0, "vtable_slots": 0,
               "stock_source_anchors": 0, "reused_contract_pins": 0}
    for row in manifest["instruction_spans"]:
        first, last = int(row["rva"], 0), int(row["end_rva"], 0)
        off = pe.rva_to_offset(first)
        payload = data[off:off + last - first]
        if hashlib.sha256(payload).hexdigest().upper() != row["sha256"]:
            raise ValueError(f"Instruction span differs: {row['name']}")
        checked["instruction_spans"] += 1
    for row in manifest["semantic_instructions"]:
        rva = int(row["rva"], 0)
        off = pe.rva_to_offset(rva)
        instruction = next(decoder.disasm(data[off:off + 15], rva))
        if (instruction.bytes.hex(" ").upper() != row["bytes"] or
                f"{instruction.mnemonic} {instruction.op_str}" != row["instruction"]):
            raise ValueError(f"Semantic instruction differs: {row['purpose']}")
        checked["semantic_instructions"] += 1
    for row in manifest["call_edges"]:
        rva = int(row["rva"], 0)
        off = pe.rva_to_offset(rva)
        ins = next(decoder.disasm(data[off:off + 15], rva))
        actual = [operand.imm for operand in ins.operands if operand.type == X86_OP_IMM]
        if ins.mnemonic != "call" or actual != [int(row["target_rva"], 0)]:
            raise ValueError(f"Direct call differs: {row['purpose']}")
        checked["call_edges"] += 1
    for row in manifest["rip_edges"]:
        rva = int(row["rva"], 0)
        off = pe.rva_to_offset(rva)
        ins = next(decoder.disasm(data[off:off + 15], rva))
        targets = [ins.address + ins.size + operand.mem.disp
                   for operand in ins.operands
                   if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP]
        if targets != [int(row["target_rva"], 0)]:
            raise ValueError(f"RIP edge differs: {row['purpose']}")
        checked["rip_edges"] += 1
    for row in manifest["vtable_slots"]:
        slot = int(row["table_rva"], 0) + row["slot"] * 8
        target = struct.unpack_from("<Q", data, pe.rva_to_offset(slot))[0] - pe.image_base
        if target != int(row["target_rva"], 0):
            raise ValueError(f"Vtable slot differs: {row['purpose']}")
        checked["vtable_slots"] += 1
    for row in manifest["reused_contracts"]:
        path = CONTRACT.parent / row["path"]
        if file_sha(path) != row["sha256"]:
            raise ValueError(f"Reused source contract changed: {row['path']}")
        checked["reused_contract_pins"] += 1
    if game_root is not None:
        for row in manifest["stock_source_anchors"]:
            path = game_root / row["relative_path"]
            if file_sha(path) != row["file_sha256"]:
                raise ValueError(f"Stock source changed: {row['relative_path']}")
            lines = path.read_text(encoding="utf-8-sig").splitlines()
            if lines[row["line"] - 1].strip() != row["text"]:
                raise ValueError(f"Stock source anchor differs: {row['purpose']}")
            checked["stock_source_anchors"] += 1
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--game-root", type=Path)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    checked = verify(args.exe, game_root=args.game_root)
    receipt = {"schema": "xar.ck3.event12002.recovery-variable-list.abi-receipt.v1",
               "contract_sha256": file_sha(CONTRACT),
               "verifier_sha256": file_sha(Path(__file__)),
               "exe_sha256": file_sha(args.exe),
               "checks": checked, "result": "GREEN",
               "readiness": "static-ready", "live_acceptance_performed": False,
               "native_functions_invoked": False,
               "readiness_boundary": "ABI source proof; native producer fixture/paused list values are owned by recovery provider and remain separate"}
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    args.artifact_dir.joinpath("abi-result.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
