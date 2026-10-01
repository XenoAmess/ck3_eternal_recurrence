"""Verify exact readonly break-betrothal predicate ABI and frozen stock branches."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "ck3_12002_family_obligations_break_penalty_abi.json"
HEADER = HERE.parent / "include/xar_bridge/ck3_12002_family_obligations_break_penalty.hpp"


def verify(exe: Path, stock_root: Path) -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data = exe.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha.upper() != manifest["executable_sha256"].upper():
        raise ValueError("Exact 1.20.0.2 EXE differs")
    pe = PeImage(data)
    header = HEADER.read_text(encoding="utf-8")
    unique = 0
    for row in manifest["native_methods"]:
        rva, end = int(row["rva"], 0), int(row["end_rva"], 0)
        constant = re.search(rf"\b{re.escape(row['name'])}\s*=\s*(0x[0-9A-Fa-f]+)", header)
        if constant is None or int(constant.group(1), 0) != rva:
            raise ValueError(f"Changed header binding {row['name']}")
        prefix = bytes.fromhex(row["prefix_bytes"])
        offset = pe.rva_to_offset(rva)
        if data[offset:offset + len(prefix)] != prefix or data.count(prefix) != row["prefix_occurrences"]:
            raise ValueError(f"Changed native method {row['name']}")
        if hashlib.sha256(data[offset:offset + end-rva]).hexdigest() != row["function_sha256"]:
            raise ValueError(f"Changed complete native function {row['name']}")
        unique += row["prefix_occurrences"] == 1
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    instructions = {}
    for row in manifest["semantic_checks"]:
        rva = int(row["rva"], 0)
        off = pe.rva_to_offset(rva)
        ins = next(decoder.disasm(data[off:off + 15], rva))
        rip = [hex(ins.address + ins.size + op.mem.disp) for op in ins.operands
               if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
        direct = [hex(op.imm) for op in ins.operands
                  if op.type == X86_OP_IMM and ins.mnemonic in ("call", "jmp")]
        actual = (ins.bytes.hex(" ").upper(), f"{ins.mnemonic} {ins.op_str}", rip, direct)
        expected = (row["bytes"], row["instruction"], row["rip_targets"], row["direct_targets"])
        if actual != expected:
            raise ValueError(f"Changed semantic source {row['name']}")
        instructions[row["name"]] = ins
    # The generic integer set predicate has four equal prefixes. Its exact
    # CRite caller is independently bound rather than calling it unique.
    if instructions["rite_parameter_native_contains"].operands[0].imm != int(
            next(row["rva"] for row in manifest["native_methods"]
                 if row["name"] == "kRiteParameterSetContainsRva"), 0):
        raise ValueError("Rite final parameter predicate call differs")
    offset = re.search(r"\bkRiteParameterSetOffset\s*=\s*(0x[0-9A-Fa-f]+)", header)
    if offset is None or int(offset.group(1), 0) != instructions["rite_parameter_set_address"].operands[1].imm:
        raise ValueError("Rite parameter set offset differs")
    for row in manifest["stock_files"]:
        if hashlib.sha256((stock_root / row["path"]).read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"Frozen stock source differs: {row['path']}")
    basic = (stock_root / "common/script_values/00_basic_values.txt").read_text(encoding="utf-8-sig")
    keys = ("miniscule", "minor", "medium", "major", "massive", "monumental")
    values = [int(re.search(rf"\b{key}_prestige_value\s*=\s*(\d+)", basic).group(1)) for key in keys]
    if values != manifest["stock_prestige_values"]:
        raise ValueError("Frozen base prestige values differ")
    wedding = (stock_root / "common/scripted_triggers/04_ep2_wedding_triggers.txt").read_text(encoding="utf-8-sig")
    if re.search(r"has_been_promised_grand_wedding\s*=\s*\{\s*has_variable\s*=\s*promised_grand_wedding_by\s*\}", wedding) is None:
        raise ValueError("Grand Wedding promise presence branch differs")
    return {"status": "GREEN", "readiness": "static-ready", "local_ck3_touched": False,
            "live_verified": False, "executable_sha256": sha,
            "native_function_bodies": len(manifest["native_methods"]),
            "source_rva_constants": len(manifest["native_methods"]),
            "unique_native_prefixes": unique,
            "semantic_instructions": len(manifest["semantic_checks"]),
            "frozen_stock_sources": len(manifest["stock_files"]),
            "stock_branch_amounts": values, "effects_complete": False,
            "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--stock-root", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.exe, args.stock_root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
