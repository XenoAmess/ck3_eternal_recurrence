"""Verify title/camera bindings against the frozen executable on disk only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP

from scan_anchors import PeImage


def verify(executable: Path, manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    binary = executable.read_bytes()
    digest = hashlib.sha256(binary).hexdigest().upper()
    if digest != manifest["executable_sha256"]:
        raise ValueError("Executable differs from the frozen 1.20.0.2 build")
    pe = PeImage(binary)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    spans = manifest["source_contract"]["exact_function_spans"]
    for row in spans:
        start, end = int(row["start_rva"], 0), int(row["end_rva"], 0)
        offset = pe.rva_to_offset(start)
        observed = hashlib.sha256(binary[offset:offset + end - start])
        if observed.hexdigest().upper() != row["sha256"]:
            raise ValueError(f"Function range differs: {row['name']}")
    for row in manifest["instruction_checks"]:
        rva = int(row["rva"], 0)
        offset = pe.rva_to_offset(rva)
        instruction = next(decoder.disasm(binary[offset:offset + 15], rva))
        observed = f"{instruction.mnemonic} {instruction.op_str}"
        rip_targets = [
            hex(instruction.address + instruction.size + operand.mem.disp)
            for operand in instruction.operands
            if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP
        ]
        if (instruction.bytes.hex(" ") != row["bytes"] or
                observed != row["instruction"] or
                rip_targets != row["rip_targets"]):
            raise ValueError(f"Instruction differs at {row['rva']}")
    for row in manifest["vtable_prefixes"]:
        offset = pe.rva_to_offset(int(row["rva"], 0))
        observed = [
            hex(struct.unpack_from("<Q", binary, offset + index * 8)[0] -
                0x140000000)
            for index in range(len(row["function_rvas"]))
        ]
        if observed != row["function_rvas"]:
            raise ValueError(f"Vtable prefix differs: {row['name']}")
    source_root = Path(__file__).resolve().parent.parent
    constant_count = 0
    for relative_path, constants in manifest["source_constants"].items():
        source = (source_root / relative_path).read_text(encoding="utf-8-sig")
        for name, value in constants.items():
            match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[\da-fA-F]+)",
                              source)
            if match is None or int(match.group(1), 0) != int(value, 0):
                raise ValueError(f"Source constant differs: {relative_path}:{name}")
            constant_count += 1
    return {
        "executable_sha256": digest,
        "function_ranges": len(spans),
        "instruction_checks": len(manifest["instruction_checks"]),
        "vtable_prefixes": len(manifest["vtable_prefixes"]),
        "source_constants": constant_count,
        "verification": "passed",
        "live_validated": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--manifest", type=Path,
                        default=Path(__file__).with_name(
                            "ck3_1_20_0_2_title_map.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.exe, args.manifest)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output is not None:
        args.output.write_text(rendered, encoding="utf-8-sig")
    print(rendered, end="")


if __name__ == "__main__":
    main()
