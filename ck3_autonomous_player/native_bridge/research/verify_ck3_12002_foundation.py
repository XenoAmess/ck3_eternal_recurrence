"""Verify the reviewed 1.20.0.2 foundation against an EXE on disk, offline."""

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
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("ck3_1_20_0_2_foundation.json"))
    args = parser.parse_args()
    failures = verify(args.exe, args.manifest)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    data = args.exe.read_bytes()
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    for check in manifest["semantic_checks"]:
        rva = int(check["rva"], 0)
        offset = pe.rva_to_offset(rva)
        instruction = next(decoder.disasm(data[offset:offset + 15], rva))
        actual = f"{instruction.mnemonic} {instruction.op_str}"
        targets = [hex(instruction.address + instruction.size + operand.mem.disp)
                   for operand in instruction.operands
                   if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP]
        if (actual != check["instruction"] or targets != check["rip_targets"] or
                instruction.bytes.hex(" ").upper() != check["bytes"]):
            failures.append(f"semantic check differs: {check['purpose']}")
    header = (Path(__file__).resolve().parents[1] / "include/xar_bridge/ck3_12002.hpp").read_text(encoding="utf-8-sig")
    if manifest["build"]["sha256"] not in header:
        failures.append("C++ executable hash differs")
    for name, expected in manifest["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9A-Fa-f]+)", header)
        if match is None or int(match[1], 0) != int(expected, 0):
            failures.append(f"C++ constant differs: {name}")
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"{'FAIL' if failures else 'PASS'} offline foundation: "
          f"{len(manifest['semantic_checks'])} instruction checks; no live validation")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
