"""Verify CK3 1.20.0.2 phase bindings against the frozen executable, offline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP

from scan_anchors import PeImage, verify


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    path = Path(__file__).with_name("ck3_1_20_0_2_phase.json")
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    failures = verify(args.exe, path)
    data = args.exe.read_bytes()
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    for check in manifest["semantic_checks"]:
        rva = int(check["rva"], 0)
        offset = pe.rva_to_offset(rva)
        instruction = next(decoder.disasm(data[offset:offset + 15], rva))
        targets = [hex(instruction.address + instruction.size + op.mem.disp)
                   for op in instruction.operands
                   if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
        if (instruction.bytes.hex(" ").upper() != check["bytes"] or
                f"{instruction.mnemonic} {instruction.op_str}" != check["instruction"] or
                targets != check["rip_targets"]):
            failures.append(f"phase instruction differs at {rva:#x}")
    header = (Path(__file__).resolve().parents[1] /
              "include/xar_bridge/ck3_12002_phase.hpp").read_text(encoding="utf-8-sig")
    for name, value in manifest["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9a-fA-F]+)", header)
        if not match or int(match[1], 0) != int(value, 0):
            failures.append(f"phase C++ constant differs: {name}")
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"{'FAIL' if failures else 'PASS'} phase static bindings: "
          f"{len(manifest['semantic_checks'])} instructions; no live validation")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
