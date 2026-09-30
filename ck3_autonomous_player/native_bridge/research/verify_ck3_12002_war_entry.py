"""Verify the frozen 1.20.0.2 war-entry ABI without opening a process."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scan_anchors import PeImage


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name(
        "ck3_1_20_0_2_war_entry.json"))
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    data = args.exe.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != manifest["ck3_exe_sha256"]:
        raise ValueError("CK3 executable is not the frozen 1.20.0.2 build")
    image = PeImage(data)
    for function in manifest["logical_function_ranges"]:
        start, end = int(function["start_rva"], 0), int(function["end_rva"], 0)
        offset = image.rva_to_offset(start)
        actual = hashlib.sha256(data[offset:offset + end - start]).hexdigest()
        if actual != function["sha256"]:
            raise ValueError(f"Changed logical function: {function['name']}")
    for check in manifest["instruction_evidence"]:
        offset = image.rva_to_offset(int(check["rva"], 0))
        expected = bytes.fromhex(check["bytes"])
        if data[offset:offset + len(expected)] != expected:
            raise ValueError(f"Changed ABI instruction at {check['rva']}")
    source = (Path(__file__).parents[1] / "include/xar_bridge/ck3_12002_war_entry.hpp").read_text(
        encoding="utf-8-sig")
    for name, value in manifest["source_constants"].items():
        if f"{name} = {value};" not in source:
            raise ValueError(f"Source constant differs: {name}")
    implementation = (Path(__file__).parents[1] / "src/ck3_12002_war_entry.cpp").read_text(
        encoding="utf-8-sig")
    for name, value in manifest["source_layout_constants"].items():
        if f"{name} = {value};" not in implementation:
            raise ValueError(f"Source layout differs: {name}")
    print(json.dumps({"status": "GREEN", "logical_functions": len(
        manifest["logical_function_ranges"]), "instructions": len(
        manifest["instruction_evidence"]), "source_constants": len(
        manifest["source_constants"]) + len(manifest["source_layout_constants"]),
        "live_verified": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
