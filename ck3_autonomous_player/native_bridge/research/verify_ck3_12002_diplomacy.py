"""Verify frozen Crozier termination ABI evidence without opening a process."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage, verify


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    manifest_path = here / "ck3_1_20_0_2_diplomacy.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    data = args.exe.read_bytes()
    failures = verify(args.exe, manifest_path)
    if failures:
        raise ValueError("; ".join(failures))
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    for row in manifest["semantic_checks"]:
        rva = int(row["rva"], 0)
        offset = pe.rva_to_offset(rva)
        ins = next(decoder.disasm(data[offset:offset + 15], rva))
        targets = [hex(ins.address + ins.size + op.mem.disp)
                   for op in ins.operands
                   if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
        if (ins.bytes.hex(" ").upper() != row["bytes"] or
                f"{ins.mnemonic} {ins.op_str}" != row["instruction"] or
                targets != row["rip_targets"]):
            raise ValueError(f"Changed termination ABI at {row['rva']}")
    source = (here.parent / "include/xar_bridge/ck3_12002_diplomacy.hpp").read_text(
        encoding="utf-8-sig")
    constants = {}
    for name, wanted in manifest["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9a-fA-F]+)", source)
        if match is None or int(match.group(1), 0) != int(wanted, 0):
            raise ValueError(f"Changed source constant {name}")
        constants[name] = int(match.group(1), 0)
    # The observed live failure was a mistranscribed global RVA even though
    # both the frozen instruction and its independently recorded target passed.
    # Bind the actual producer instruction to the runtime constant directly.
    for row in manifest["rip_source_constants"]:
        rva = int(row["rva"], 0)
        offset = pe.rva_to_offset(rva)
        ins = next(decoder.disasm(data[offset:offset + 15], rva))
        targets = [ins.address + ins.size + op.mem.disp
                   for op in ins.operands
                   if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
        if targets != [constants[row["constant"]]]:
            raise ValueError(f"Native RIP target disagrees with {row['constant']}")
    print(f"PASS {len(manifest['semantic_checks'])} termination instruction checks; "
          f"{len(manifest['source_constants'])} source constants; "
          f"{len(manifest['rip_source_constants'])} direct native/global bindings; "
          "no live validation")


if __name__ == "__main__":
    main()
