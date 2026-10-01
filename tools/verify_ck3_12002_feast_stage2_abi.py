"""Verify the migrated feast destination/confirm ABI using a file, never a process."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile

EXPECTED_SHA256 = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"
# The caller and layout instructions are recovered independently from the new
# image. These are neither fixed-delta addresses nor an old ABI with a new hash.
PROOFS = (
    ("can_select_destination", 0x11B6F50, "48 89 5c 24 10 55 56 57 41 54 41 55 41 56"),
    ("select_destination", 0x11B6C80, "48 89 5c 24 08 48 89 6c 24"),
    ("province_id_to_configuration_row", 0x11B6CB7, "8b 42 10 89 41 08"),
    ("single_location_type_flag", 0x11B6CD3, "40 38 bd ed 3b 00 00"),
    ("previous_planning_stage", 0x11B6CE0, "8b 8b ec 1a 00 00"),
    ("single_location_stage_five", 0x11B6D51, "ba 05 00 00 00 48 8b cb"),
    ("active_configuration_row", 0x11B6CA0, "48 8b 89 f8 1a 00 00"),
    ("selected_activity_type", 0x11B6CB0, "48 8b ab 00 15 00 00"),
    ("can_progress", 0x11B8670, "48 89 5c 24 10 48 89"),
    ("planning_stage", 0x11B8693, "48 63 81 e8 1a 00 00"),
    ("stage_two_row_vector_and_count", 0x11B86DF, "48 8b 89 b0 15 00 00 49 63 80 bc 15 00 00"),
    ("configuration_row_stride", 0x11B86ED, "48 6b d0 38"),
    ("stage_two_nonzero_province_gate", 0x11B8700, "83 79 08 00"),
    ("progress", 0x11B8CD0, "40 53 48 83 ec 20"),
    ("automatic_location_selection_flag", 0x11B8CFC, "80 bb 08 1b 00 00 00"),
    ("stage_two_progress_to_five", 0x11B8D53, "ba 05 00 00 00"),
    ("set_stage", 0x11B95D0, "40 53 48 81 ec a0 00 00 00 8b 81 e8 1a 00 00"),
    ("set_current_stage", 0x11B95F1, "89 91 e8 1a 00 00"),
    ("set_previous_stage", 0x11B95F7, "89 81 ec 1a 00 00"),
    ("set_stage_notifies_slot_25", 0x11B960A, "ff 90 c8 00 00 00"),
    ("find_automatic_row", 0x11B5950, "48 8b 81 b0 15 00 00"),
    ("phase_kind", 0x11B5978, "83 b9 60 11 00 00 00"),
    ("phase_active_flag", 0x11B5981, "80 b9 9c 06 00 00 00"),
    ("selected_option_category", 0x11B64C7, "48 8b 90 60 09 00 00"),
    ("selected_option_row_vector", 0x11B64D3, "48 8b 81 98 15 00 00"),
    ("selected_option_row_count", 0x11B64DA, "4c 63 81 a4 15 00 00"),
)


def verify(executable: Path) -> dict:
    binary = executable.read_bytes()
    sha = hashlib.sha256(binary).hexdigest()
    if sha != EXPECTED_SHA256:
        raise ValueError(f"exact build mismatch: {sha}")
    image = pefile.PE(data=binary, fast_load=True)
    rows = []
    for name, rva, expected_hex in PROOFS:
        expected = bytes.fromhex(expected_hex)
        offset = image.get_offset_from_rva(rva)
        actual = binary[offset:offset + len(expected)]
        if actual != expected:
            raise ValueError(f"{name} at {rva:#x}: {actual.hex()} != {expected.hex()}")
        rows.append({"name": name, "rva": hex(rva), "bytes": actual.hex(" ")})
    slot_offset = image.get_offset_from_rva(0x45325C8 + 0xC8)
    notification = struct.unpack_from("<Q", binary, slot_offset)[0] - image.OPTIONAL_HEADER.ImageBase
    return {"schema": "ck3-12002-feast-stage2-offline-abi-v1", "status": "GREEN",
            "executable_sha256": sha, "proofs": rows,
            "planner_stage_notification_rva": hex(notification),
            "verification": "exact file bytes and native field instructions",
            "readiness": "static-ready", "live_executed": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.executable)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"GREEN: {len(result['proofs'])} exact 1.20.0.2 feast Stage2 ABI proofs; notification {result['planner_stage_notification_rva']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
