"""Verify independent Feast counter sources using the frozen EXE and stock files."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile

CONTRACT = Path(__file__).with_name("ck3_12002_feast_outcome_values_abi.json")


def verify(game_root: Path) -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    raw = (game_root / "binaries/ck3.exe").read_bytes()
    if len(raw) != contract["file_size"] or hashlib.sha256(raw).hexdigest().upper() != contract["executable_sha256"]:
        raise ValueError("Feast outcome executable identity changed")
    pe = pefile.PE(data=raw, fast_load=True)
    if pe.OPTIONAL_HEADER.ImageBase != int(contract["image_base"], 0):
        raise ValueError("Feast outcome image base changed")
    for anchor in contract["anchors"] + contract["reused_phase_character_anchors"]:
        expected = bytes.fromhex(anchor["bytes"])
        offset = pe.get_offset_from_rva(int(anchor["rva"], 0))
        if raw[offset:offset + len(expected)] != expected:
            raise ValueError(f"Feast outcome anchor changed: {anchor['name']}")
    for name, source in contract["script_sources"].items():
        if hashlib.sha256((game_root / name).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError(f"Stock Feast outcome source changed: {name}")
    fixture = CONTRACT.parent / contract["actual_wire_fixture"]["path"]
    if hashlib.sha256(fixture.read_bytes()).hexdigest() != contract["actual_wire_fixture"]["sha256"]:
        raise ValueError("Recorded production counter wire changed; regenerate the actual fixture")
    return {"status": "GREEN", "product_version": contract["product_version"],
            "executable_sha256": contract["executable_sha256"],
            "native_counter_anchor_count": len(contract["anchors"]),
            "reused_trait_anchor_count": len(contract["reused_phase_character_anchors"]),
            "stock_source_count": len(contract["script_sources"]),
            "local_ck3_contacted": False, "live_verified": False,
            "wire_fixture_sha256": contract["actual_wire_fixture"]["sha256"]}


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
