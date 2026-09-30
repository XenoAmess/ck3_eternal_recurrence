"""Verify CK3 1.20.0.2 phase-definition bindings from an EXE file only."""

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
    manifest_path = Path(__file__).with_name("ck3_1_20_0_2_phase_definitions.json")
    failures = verify(args.exe, manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    data = args.exe.read_bytes()
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    for check in manifest["semantic_checks"]:
        rva = int(check["rva"], 0)
        offset = pe.rva_to_offset(rva)
        instruction = next(decoder.disasm(data[offset:offset + 15], rva))
        targets = [hex(instruction.address + instruction.size + operand.mem.disp)
                   for operand in instruction.operands
                   if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP]
        if (f"{instruction.mnemonic} {instruction.op_str}" != check["instruction"]
                or instruction.bytes.hex(" ").upper() != check["bytes"]
                or targets != check["rip_targets"]):
            failures.append(f"native semantic check differs: {check['purpose']}")
    for key in manifest["define_keys"]:
        offset = pe.rva_to_offset(int(key["rva"], 0))
        wanted = key["key"].encode("ascii") + b"\0"
        if data[offset:offset + len(wanted)] != wanted:
            failures.append(f"define key differs: {key['key']}")
    header = (Path(__file__).resolve().parents[1] /
              "include/xar_bridge/ck3_12002_phase_definitions.hpp").read_text(encoding="utf-8-sig")
    for name, wanted in manifest["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9A-Fa-f]+)", header)
        if match is None or int(match[1], 0) != int(wanted, 0):
            failures.append(f"C++ binding differs: {name}")
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"{'FAIL' if failures else 'PASS'} offline phase definitions: "
          f"{len(manifest['semantic_checks'])} instruction checks; no live validation")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
