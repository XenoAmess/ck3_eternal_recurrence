"""Verify Feast cost ABI against an exact frozen EXE; never contact CK3."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64


def verify(executable: Path) -> dict:
    here = Path(__file__).resolve().parent
    manifest_path = here / "ck3_12002_activity_feast_costs_abi.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    data = executable.read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if digest != manifest["executable_sha256"]:
        raise ValueError("Feast cost executable does not match 1.20.0.2")
    pe = pefile.PE(data=data, fast_load=True)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    for row in manifest["instructions"]:
        rva = int(row["rva"], 0)
        offset = pe.get_offset_from_rva(rva)
        instruction = next(decoder.disasm(data[offset:offset + 15], rva))
        if (instruction.bytes.hex(" ").upper() != row["bytes"] or
                f"{instruction.mnemonic} {instruction.op_str}" != row["instruction"]):
            raise ValueError(f"Changed Feast cost instruction {row['rva']}")
    for row in manifest["spans"]:
        start, end = int(row["start"], 0), int(row["end"], 0)
        offset = pe.get_offset_from_rva(start)
        if hashlib.sha256(data[offset:offset + end-start]).hexdigest() != row["sha256"]:
            raise ValueError(f"Changed Feast cost span {row['name']}")
    for row in manifest["vtable_edges"]:
        offset = pe.get_offset_from_rva(int(row["slot_rva"], 0))
        actual = struct.unpack_from("<Q", data, offset)[0] - pe.OPTIONAL_HEADER.ImageBase
        if actual != int(row["function_rva"], 0):
            raise ValueError(f"Changed Feast cost vtable {row['slot_rva']}")
    header = (here.parent / "include/xar_bridge/ck3_12002_activity_feast_costs.hpp").read_text(encoding="utf-8-sig")
    for name, value in manifest["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9a-fA-F]+)", header)
        if not match or int(match.group(1), 0) != int(value, 0):
            raise ValueError(f"Cost source constant disagrees: {name}")
    return {
        "schema": "xar.ck3_12002.activity_feast_costs_abi_result.v1",
        "status": "PASS", "readiness": "static-ready",
        "local_ck3_contacted": False, "live_verified": False,
        "executable_sha256": digest,
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "instruction_count": len(manifest["instructions"]),
        "span_count": len(manifest["spans"]),
        "vtable_count": len(manifest["vtable_edges"]),
        "remaining_live": manifest["remaining_live"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    result = verify(args.exe)
    if args.result:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
