#!/usr/bin/env python3
"""Verify the frozen 1.20.0.2 council ABI using executable-file reads only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86_const import X86_OP_MEM, X86_REG_RIP

from scan_anchors import PeImage

HERE = Path(__file__).resolve().parent


def verify(exe: Path) -> dict[str, object]:
    contract = json.loads((HERE / "nonwar_council12002_abi.json").read_text(encoding="utf-8"))
    data = exe.read_bytes()
    pe = PeImage(data)
    failures: list[str] = []
    actual_sha = hashlib.sha256(data).hexdigest().upper()
    if actual_sha != contract["executable_sha256"]:
        failures.append("executable SHA-256 differs")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True

    for span in contract["spans"]:
        start, end = int(span["start"], 0), int(span["end"], 0)
        offset = pe.rva_to_offset(start)
        actual = hashlib.sha256(data[offset:offset + end - start]).hexdigest().upper()
        if actual != span["sha256"]:
            failures.append(f"span {span['name']} differs")

    for expected in contract["instructions"]:
        address = int(expected["rva"], 0)
        offset = pe.rva_to_offset(address)
        instruction = next(decoder.disasm(data[offset:offset + 15], address), None)
        if instruction is None or instruction.mnemonic != expected["mnemonic"] or instruction.op_str != expected["operand"]:
            failures.append(f"instruction {address:#x} differs")

    for expected in contract["global_loads"]:
        address = int(expected["instruction_rva"], 0)
        offset = pe.rva_to_offset(address)
        instruction = next(decoder.disasm(data[offset:offset + 15], address), None)
        targets = [] if instruction is None else [
            address + instruction.size + operand.mem.disp
            for operand in instruction.operands
            if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP
        ]
        if targets != [int(expected["target_rva"], 0)]:
            failures.append(f"global load {address:#x} differs")

    header = (HERE.parent / "include/xar_bridge/ck3_12002_nonwar_council.hpp").read_text(encoding="utf-8")
    bindings = {
        "kCampaignRootActiveCouncilTaskStorageSlotRva": contract["globals"]["active_task_storage_slot"],
        "kCampaignRootActiveCouncilTaskFallbackSlotRva": contract["globals"]["active_task_fallback_slot"],
        "kCampaignRootCouncilPositionLookupRva": contract["functions"]["position_lookup"],
        "kCampaignRootCouncilActiveTaskIdsEnumeratorRva": contract["functions"]["active_task_ids_enumerator"],
        "kCampaignRootCouncilValueProgressCurrentRva": contract["functions"]["value_progress_current"],
        "kCampaignRootCouncilValueProgressMaximumRva": contract["functions"]["value_progress_maximum"],
    }
    for name, expected in bindings.items():
        match = re.search(r"\b" + re.escape(name) + r"\s*=\s*(0x[0-9A-Fa-f]+)", header)
        if match is None or int(match.group(1), 0) != int(expected, 0):
            failures.append(f"header binding {name} differs")

    return {
        "status": "GREEN" if not failures else "RED",
        "game_version": "1.20.0.2",
        "executable_sha256": actual_sha,
        "verified_spans": len(contract["spans"]),
        "verified_instructions": len(contract["instructions"]),
        "verified_global_loads": len(contract["global_loads"]),
        "verified_bindings": len(bindings),
        "failures": failures,
        "evidence_level": "static-ready",
        "local_ck3_used": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.exe)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
