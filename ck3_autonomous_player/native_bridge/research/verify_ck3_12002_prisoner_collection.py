"""Verify the Crozier prisoner ABI using the frozen executable file only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from scan_anchors import PeImage


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "ck3_12002_prisoner_collection_abi.json"


def verify_prisoner_collection(exe: Path) -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data = exe.read_bytes()
    pe = PeImage(data)
    build = manifest["exact_build"]
    failures = []
    if (len(data) != build["executable_size"] or
            hashlib.sha256(data).hexdigest().upper() != build["executable_sha256"] or
            pe.image_base != int(build["image_base"], 0)):
        raise ValueError("Unsupported executable")

    def read(rva: str | int, size: int) -> bytes:
        address = int(rva, 0) if isinstance(rva, str) else rva
        offset = pe.rva_to_offset(address)
        return data[offset:offset + size]

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    for row in manifest["instruction_checks"]:
        expected = bytes.fromhex(row["bytes"])
        actual = read(row["rva"], len(expected))
        instruction = next(decoder.disasm(actual, int(row["rva"], 0)), None)
        text = f"{instruction.mnemonic} {instruction.op_str}" if instruction else None
        if actual != expected or text != row["instruction"]:
            failures.append(f"Instruction changed: {row['name']}")
    for row in manifest["function_spans"]:
        start, end = int(row["start_rva"], 0), int(row["end_rva_exclusive"], 0)
        if hashlib.sha256(read(start, end - start)).hexdigest().upper() != row["sha256"]:
            failures.append(f"Function changed: {row['name']}")
    for row in manifest["relative_edges"]:
        source = int(row["source_rva"], 0)
        displacement = struct.unpack("<i", read(source + row["displacement_offset"], 4))[0]
        if source + row["instruction_size"] + displacement != int(row["target_rva"], 0):
            failures.append(f"Relative edge changed at {source:#x}")
    for row in manifest["vtable_edges"]:
        actual = struct.unpack("<Q", read(row["slot_rva"], 8))[0] - pe.image_base
        if actual != int(row["target_rva"], 0):
            failures.append(f"Vtable changed: {row['role']}")
    for row in manifest["string_checks"]:
        expected = row["value"].encode("ascii") + b"\0"
        if read(row["rva"], len(expected)) != expected:
            failures.append(f"Reflected name changed: {row['value']}")
    for row in manifest["reused_evidence"]:
        if "sha256" in row and hashlib.sha256((HERE / row["path"]).read_bytes()).hexdigest() != row["sha256"]:
            failures.append(f"Reused lineage evidence changed: {row['path']}")
    if failures:
        raise ValueError("; ".join(failures))
    return {
        "status": "PASS", "readiness": "static-ready", "live_verified": False,
        "process_access": False, "game_access": False,
        "executable_sha256": build["executable_sha256"],
        "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "instruction_count": len(manifest["instruction_checks"]),
        "frozen_span_count": len(manifest["function_spans"]),
        "relative_edge_count": len(manifest["relative_edges"]),
        "vtable_edge_count": len(manifest["vtable_edges"]),
        "string_count": len(manifest["string_checks"]),
        "remaining_live": manifest["remaining_live"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    result = verify_prisoner_collection(args.exe)
    if args.result:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
