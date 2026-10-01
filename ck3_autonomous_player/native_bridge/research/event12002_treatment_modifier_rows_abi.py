#!/usr/bin/env python3
"""Verify only the 1.20.0.2 treatment character-modifier rows ABI, file-only."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

from scan_anchors import PeImage, occurrences


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "event12002_treatment_modifier_rows_abi.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def verify(exe: Path) -> dict:
    contract = json.loads(MANIFEST.read_text(encoding="utf-8"))
    raw = exe.read_bytes()
    require(len(raw) == contract["file_size"], "EXE size differs")
    require(digest(raw) == contract["executable_sha256"], "EXE SHA differs")
    pe = PeImage(raw)
    require(pe.image_base == int(contract["image_base"], 0), "Image base differs")
    anchor = contract["signature_anchor"]
    hits = occurrences(raw, bytes.fromhex(anchor["bytes"]))
    require(len(hits) == 1 and pe.offset_to_rva(hits[0]) == int(anchor["rva"], 0),
            "Native modifier trigger signature is not uniquely bound")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    instructions = []
    for row in contract["instruction_checks"]:
        rva = int(row["rva"], 0)
        wanted = bytes.fromhex(row["bytes"])
        offset = pe.rva_to_offset(rva)
        actual = raw[offset:offset + len(wanted)]
        require(actual == wanted, f"Instruction bytes differ: {row['name']}")
        decoded = list(decoder.disasm(actual, rva))
        require(len(decoded) == 1, f"Not a single instruction: {row['name']}")
        ins = decoded[0]
        text = f"{ins.mnemonic} {ins.op_str}".rstrip()
        require(text == row["instruction"], f"Instruction meaning differs: {row['name']}")
        if "rip_target" in row:
            targets = [ins.address + ins.size + op.mem.disp for op in ins.operands
                       if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
            require(targets == [int(row["rip_target"], 0)], f"RIP target differs: {row['name']}")
        if "branch_target" in row:
            targets = [op.imm for op in ins.operands if op.type == X86_OP_IMM]
            require(targets == [int(row["branch_target"], 0)], f"Branch target differs: {row['name']}")
        instructions.append({"name": row["name"], "rva": row["rva"], "bytes": actual.hex().upper(),
                             "instruction": text})
    source_path = HERE.parent / contract["source_constants_path"]
    source = source_path.read_text(encoding="utf-8-sig")
    constants = {}
    for name, expected in contract["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0[xX][0-9A-Fa-f]+|\d+)\s*;", source)
        require(match is not None and int(match.group(1), 0) == int(expected, 0),
                f"Producer source constant differs: {name}")
        constants[name] = expected
    return {
        "schema": "xar.ck3.event12002.treatment-modifier-rows.abi-verification.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(), "status": "GREEN",
        "executable_path": str(exe), "executable_sha256": contract["executable_sha256"],
        "manifest_sha256": digest(MANIFEST.read_bytes()), "unique_signature_count": 1,
        "instruction_count": len(instructions), "rip_target_count": 2, "branch_target_count": 4,
        "instructions": instructions, "producer_header_path": str(source_path),
        "producer_header_sha256_at_verification": digest(source_path.read_bytes()),
        "producer_constant_values": constants, "producer_constant_count": len(constants),
        "readiness": contract["readiness"], "local_ck3_contacted": False, "live_verified": False,
        "fixture_boundary": "This verifies native ABI bytes and five producer header constants; scanner fixtures are a separate package.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "unique_signatures": 1,
                      "instruction_checks": result["instruction_count"],
                      "source_constants": result["producer_constant_count"],
                      "proof_path": str(args.output), "proof_sha256": digest(args.output.read_bytes())}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
