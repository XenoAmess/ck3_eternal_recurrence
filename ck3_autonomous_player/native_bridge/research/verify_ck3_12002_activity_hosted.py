"""Verify the frozen hosted Feast source map from files without game access."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile

CONTRACT = Path(__file__).with_name("ck3_12002_activity_hosted_abi.json")


def verify(game_root: Path) -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    raw = (game_root / "binaries/ck3.exe").read_bytes()
    if len(raw) != contract["file_size"] or hashlib.sha256(raw).hexdigest().upper() != contract["executable_sha256"]:
        raise ValueError("Hosted activity executable identity changed")
    pe = pefile.PE(data=raw, fast_load=True)
    base = int(contract["image_base"], 0)
    if pe.OPTIONAL_HEADER.ImageBase != base:
        raise ValueError("Image base changed")

    def at(rva: int, size: int) -> bytes:
        offset = pe.get_offset_from_rva(rva)
        return raw[offset:offset + size]

    for anchor in contract["anchors"]:
        expected = bytes.fromhex(anchor["bytes"])
        if at(int(anchor["rva"], 0), len(expected)) != expected:
            raise ValueError(f"Hosted anchor changed: {anchor['name']}")
    for table in contract["vtables"]:
        rva = int(table["rva"], 0)
        col = int(table["col_rva"], 0)
        type_rva = int(table["type_rva"], 0)
        if struct.unpack("<Q", at(rva - 8, 8))[0] != base + col:
            raise ValueError(f"COL changed: {table['name']}")
        if struct.unpack("<I", at(col + 4, 4))[0] != table["object_offset"]:
            raise ValueError(f"Object offset changed: {table['name']}")
        if struct.unpack("<I", at(col + 12, 4))[0] != type_rva:
            raise ValueError(f"Type descriptor changed: {table['name']}")
        name = f".?AV{table['name']}@@".encode("ascii") + b"\0"
        if at(type_rva + 16, len(name)) != name:
            raise ValueError(f"RTTI identity changed: {table['name']}")
        if struct.unpack("<Q", at(rva, 8))[0] != base + int(table["entry0_rva"], 0):
            raise ValueError(f"Vtable first entry changed: {table['name']}")
    for name, source in contract["script_sources"].items():
        if hashlib.sha256((game_root / name).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError(f"Stock activity source changed: {name}")
    return {"status": "GREEN", "product_version": contract["product_version"],
            "executable_sha256": contract["executable_sha256"],
            "anchor_count": len(contract["anchors"]), "vtable_count": len(contract["vtables"]),
            "source_count": len(contract["script_sources"]), "local_ck3_contacted": False,
            "live_verified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.game_root.resolve())
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
