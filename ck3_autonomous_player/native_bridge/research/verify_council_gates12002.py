"""Verify CK3 1.20.0.2 four council gates from files only."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import struct

from scan_anchors import PeImage

HERE = Path(__file__).resolve().parent
DEFAULT_EXE = Path("Z:/ck3_mod_rewrite/artifacts/migrations/2026-09-30/post-update-1.20.0.2/installation/binaries/ck3.exe")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--game-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest = json.loads((HERE / "council_gates12002_abi.json").read_text(encoding="utf-8"))
    data = args.exe.read_bytes()
    pe = PeImage(data)
    sha = hashlib.sha256(data).hexdigest().upper()
    if sha != manifest["build"]["sha256"]:
        raise ValueError("frozen executable SHA mismatch")
    game_root = args.game_root or args.exe.parent.parent / "game"
    for row in manifest["stock_sources"]:
        source = (game_root / row["path_from_game_root"]).read_bytes()
        if len(source) != row["size"] or hashlib.sha256(source).hexdigest().upper() != row["sha256"]:
            raise ValueError(row["path_from_game_root"])
    for row in manifest["code_spans"]:
        start, end = int(row["start_rva"], 0), int(row["end_rva"], 0)
        off = pe.rva_to_offset(start)
        if hashlib.sha256(data[off:off + end - start]).hexdigest().upper() != row["sha256"]:
            raise ValueError(row["name"])
    for row in manifest["relative_edges"]:
        rva = int(row["instruction_rva"], 0)
        off = pe.rva_to_offset(rva)
        target = rva + row["size"] + struct.unpack_from("<i", data, off + row["displacement_offset"])[0]
        if target != int(row["target_rva"], 0):
            raise ValueError(row["name"])
    for row in manifest["vtable_slots"]:
        off = pe.rva_to_offset(int(row["slot_rva"], 0))
        if struct.unpack_from("<Q", data, off)[0] - pe.image_base != int(row["target_rva"], 0):
            raise ValueError(row["name"])
    for row in manifest["literal_checks"]:
        off = pe.rva_to_offset(int(row["rva"], 0))
        needle = row["value"].encode() + b"\0"
        if data[off:off + len(needle)] != needle:
            raise ValueError(row["name"])
    for row in manifest["instruction_checks"]:
        off = pe.rva_to_offset(int(row["rva"], 0))
        needle = bytes.fromhex(row["bytes"])
        if data[off:off + len(needle)] != needle:
            raise ValueError(row["name"])
    header = (HERE.parent / "include/xar_bridge/ck3_12002_council_gates.hpp").read_text(encoding="utf-8")
    constants = {
        "played_character_id": "kCouncilGatesPlayedCharacterIdRva12002",
        "is_councillor": "kCouncilGatesIsCouncillorRva12002",
        "is_guest": "kCouncilGatesIsGuestRva12002",
        "pending_manager_setup": "kCouncilGatesPendingSetupRva12002",
        "has_pending_interaction": "kCouncilGatesHasPendingRva12002",
        "can_confirm": "kCouncilGatesCanConfirmRva12002",
    }
    for key, name in constants.items():
        match = re.search(rf"{name}\s*=\s*(0x[0-9a-fA-F]+)", header)
        if match is None or int(match[1], 0) != int(manifest["bindings"][key], 0):
            raise ValueError(name)
    result = dict(status="GREEN", game_version="1.20.0.2", exe_sha256=sha,
                  code_spans=len(manifest["code_spans"]), relative_edges=len(manifest["relative_edges"]),
                  vtable_slots=len(manifest["vtable_slots"]), literal_checks=len(manifest["literal_checks"]),
                  instruction_checks=len(manifest["instruction_checks"]), production_bindings=len(constants),
                  stock_sources=len(manifest["stock_sources"]),
                  live_verified=False)
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
