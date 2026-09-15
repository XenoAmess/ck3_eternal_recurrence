#!/usr/bin/env python3
"""Verify the frozen, private CK3 1.19.0.6 council final-gate ABI."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

from verify_council_assignment_action_1_19_0_6 import (
    PeImage,
    VerificationError,
    file_sha256,
    parse_integer,
)


def verify(executable: Path, manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("contract") != "council_final_gates_1_19_0_6_abi":
        raise VerificationError("manifest contract mismatch")

    build = manifest["build"]
    if executable.stat().st_size != parse_integer(build["file_size"]):
        raise VerificationError("EXE size mismatch")
    actual_sha = file_sha256(executable)
    if actual_sha != str(build["executable_sha256"]).upper():
        raise VerificationError("EXE SHA-256 mismatch")
    image = PeImage(executable)
    if image.machine != parse_integer(build["machine"]):
        raise VerificationError("PE machine mismatch")
    if image.image_base != parse_integer(build["preferred_image_base"]):
        raise VerificationError("PE image base mismatch")
    if image.image_size != parse_integer(build["image_size"]):
        raise VerificationError("PE image size mismatch")

    game_root = executable.parent.parent / "game"
    source = manifest["source_file"]
    gui_path = game_root / str(source["path_from_game_root"])
    if gui_path.stat().st_size != parse_integer(source["size"]):
        raise VerificationError("vanilla council GUI size mismatch")
    if file_sha256(gui_path) != str(source["sha256"]).upper():
        raise VerificationError("vanilla council GUI SHA-256 mismatch")
    gui_text = gui_path.read_text(encoding="utf-8-sig")
    for expression in source["required_gui_expressions"]:
        if str(expression) not in gui_text:
            raise VerificationError(f"vanilla council GUI expression missing: {expression}")

    for span in manifest["instruction_spans"]:
        start = parse_integer(span["rva"])
        end = parse_integer(span["end_rva"])
        if end <= start:
            raise VerificationError(f"{span['name']}: invalid instruction span")
        actual = hashlib.sha256(image.read_rva(start, end - start)).hexdigest().upper()
        if actual != str(span["sha256"]).upper():
            raise VerificationError(f"{span['name']}: instruction SHA-256 mismatch")

    for edge in manifest["relative_edges"]:
        at = parse_integer(edge["instruction_rva"])
        size = parse_integer(edge["instruction_size"])
        offset = parse_integer(edge["displacement_offset"])
        if size not in (5, 7) or offset + 4 > size:
            raise VerificationError(f"{edge['name']}: invalid relative-edge shape")
        displacement = struct.unpack("<i", image.read_rva(at + offset, 4))[0]
        target = at + size + displacement
        if target != parse_integer(edge["target_rva"]):
            raise VerificationError(f"{edge['name']}: relative target mismatch")

    for anchor in manifest["ascii_evidence"]:
        expected = str(anchor["value"]).encode("ascii") + b"\0"
        if image.read_rva(parse_integer(anchor["rva"]), len(expected)) != expected:
            raise VerificationError(f"{anchor['name']}: method-name anchor mismatch")

    footprint = manifest["predicates"]["replacement_fireability"]["synthetic_context"]
    if (
        parse_integer(footprint["minimum_readable_size"]) != 0x168
        or parse_integer(footprint["recommended_footprint"]) != 0x170
        or parse_integer(footprint["incumbent_signed_full_character_id_offset"])
        != 0x160
        or parse_integer(footprint["active_task_signed_full_id_offset"]) != 0x164
    ):
        raise VerificationError("fire confirmation footprint contract mismatch")

    return {
        "status": "GREEN",
        "contract": manifest["contract"],
        "game_version": build["game_version"],
        "executable_sha256": actual_sha,
        "vanilla_gui_verified": True,
        "native_predicates_verified": 4,
        "instruction_spans_verified": len(manifest["instruction_spans"]),
        "relative_edges_verified": len(manifest["relative_edges"]),
        "method_name_anchors_verified": len(manifest["ascii_evidence"]),
        "live_verified": False,
        "advertised": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("council_final_gates_1_19_0_6_abi.json"),
    )
    args = parser.parse_args()
    try:
        result = verify(args.exe, args.manifest)
    except (OSError, KeyError, ValueError, json.JSONDecodeError, VerificationError) as error:
        print(json.dumps({"status": "RED", "reason": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
