"""Verify the exact Feast opening and Stage1 ABI from a PE file only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile

EXPECTED_SHA256 = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"
# Recovered from exact 1.20.0.2 callers, constructors and virtual tables.
PROOFS = (
    ("selected_option", 0x11B64C0, "48 8b 81 00 15 00 00"),
    ("selected_option_category", 0x11B64C7, "48 8b 90 60 09 00 00"),
    ("option_rows", 0x11B64D3, "48 8b 81 98 15 00 00"),
    ("option_row_count", 0x11B64DA, "4c 63 81 a4 15 00 00"),
    ("is_shown", 0x9DEA70, "4c 8b dc 49 89 5b 10"),
    ("is_valid", 0x9DEB70, "4c 8b dc 49 89 5b 10"),
    ("can_progress", 0x11B8670, "48 89 5c 24 10 48 89"),
    ("planning_stage", 0x11B8693, "48 63 81 e8 1a 00 00"),
    ("set_stage", 0x11B95D0, "40 53 48 81 ec a0 00 00 00 8b 81 e8 1a 00 00"),
    ("selected_option_row_store", 0x11B9817, "48 89 8b 00 1b 00 00"),
    ("find_automatic_row", 0x11B5950, "48 8b 81 b0 15 00 00 48 63 89 bc 15 00"),
    ("progress_planning_stage", 0x11B8CD0, "40 53 48 83 ec 20 48 63 81 e8"),
    ("automatic_location_flag", 0x11B8CFC, "80 bb 08 1b 00 00 00"),
    ("typed_dispatch", 0xAF39E0, "48 89 5c 24 08 48 89 74"),
    ("new_delivery_branch", 0xAF39FD, "e8 4e ff ff ff 33 f6 81 ff ac 00 00 00"),
    ("stock_open_event_65", 0x1643A17, "ba 65 00 00 00 48 8b cd e8 bc ff 4a ff"),
    ("handler_event_window_lookup", 0xB0F21E, "48 8b 9c f3 98 00 00 00"),
    ("const_activity_type_descriptor", 0xD51E70, "48 8d 05 79 58 78 04"),
    ("stock_activity_type_database_rows", 0x1642F05, "e8 f6 92 2b ff 48 8b 78 50 48 63 48 5c"),
    ("initial_activity_type", 0x23FC85A, "48 8b 05 df 32 92 03"),
    ("activity_type_database_publish", 0x3060B13, "48 89 05 ee 66 c0 02"),
    ("activity_type_stable_string", 0x3110394, "48 8d 4f 18"),
    ("activity_type_vtable_install", 0x31103CE, "48 8d 05 7b fa 7a 01"),
    ("option_script_id_initialization", 0x311C89E, "c7 41 08 ff ff ff ff"),
    ("option_magic", 0x311C8A5, "c7 41 0c 4f 50 6d 4e"),
    ("option_vtable_install", 0x311C8AC, "48 8d 0d 65 34 7a 01"),
    ("option_ordinal_is_distinct_from_script_id", 0x311C8C7, "89 47 18"),
    ("option_shown_trigger", 0x311C8CA, "48 8d 4f 20"),
    ("option_valid_trigger", 0x311C8FE, "48 8d 8f f0 00 00 00"),
    ("category_calls_option_parser_slot_three", 0x31159D8, "48 ff 60 18"),
    ("option_parser_gets_script_identifier_table", 0x284ACAA, "e8 51 fb 73 01"),
    ("option_parser_resolves_script_identifier", 0x284ACBC, "e8 ef f7 73 01"),
    ("option_parser_stores_script_id", 0x284ACCF, "89 47 08"),
    ("option_copy_preserves_script_id", 0x3124DD4, "8b 42 08 89 41 08"),
)
POINTER_PROOFS = (
    ("planner_notification_slot_25", 0x45325C8 + 0xC8, 0x11B6550),
    ("option_parser_slot_three", 0x48BFD18 + 0x18, 0x284AC70),
    ("typed_descriptor_vtable", 0x54D76F0, 0x44E6F38),
    ("typed_descriptor_copy", 0x44E6F38 + 0x58, 0x878290),
    ("typed_descriptor_move", 0x44E6F38 + 0x60, 0x878290),
)
RVA_MAP = {
    "selected_option": ["0x10AEAE0", "0x11B64C0"],
    "is_shown": ["0x971270", "0x9DEA70"],
    "is_valid": ["0x971370", "0x9DEB70"],
    "can_progress": ["0x10B0DA0", "0x11B8670"],
    "set_stage": ["0x10B1BD0", "0x11B95D0"],
    "find_auto_row": ["0x10ADFA0", "0x11B5950"],
    "progress_planning": ["0x10B1330", "0x11B8CD0"],
    "stage_notification": ["0x10AEC20", "0x11B6550"],
    "type_descriptor_provider": ["0xCAF920", "0xD51E50"],
    "typed_dispatch": ["0xA79700", "0xAF39E0"],
    "activity_type_database": ["0x570BE98", "0x5C67208"],
    "initial_activity_type": ["0x57BFF28", "0x5D1FB40"],
    "type_vtable": ["0x440E308", "0x48BFE50"],
    "option_vtable": ["0x440E1D0", "0x48BFD18"],
}
LAYOUT_MAP = {
    "handler_planner": ["0x3C0", "0x3C0"],
    "planner_type": ["0x1530", "0x1500"],
    "type_special_option_category": ["0xA88", "0x960"],
    "option_rows": ["0x1560", "0x1598"],
    "option_count": ["0x156C", "0x15A4"],
    "selected_option_row": ["0x1AC8", "0x1B00"],
    "location_rows": ["0x1578", "0x15B0"],
    "location_count": ["0x1584", "0x15BC"],
    "active_location_row": ["0x1AC0", "0x1AF8"],
    "stage_auto": ["0x1AD0", "0x1B08"],
    "type_db_entries": ["0x68", "0x50"],
    "type_db_count": ["0x74", "0x5C"],
    "type_key_string": ["0x18", "0x18"],
    "option_script_id": ["0x8", "0x8"],
    "option_shown_trigger": ["0x18", "0x20"],
    "option_valid_trigger": ["0xF8", "0xF0"],
}


def verify(executable: Path) -> dict:
    binary = executable.read_bytes()
    digest = hashlib.sha256(binary).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"exact build mismatch: {digest}")
    image = pefile.PE(data=binary, fast_load=True)
    rows = []
    for name, rva, expected_hex in PROOFS:
        expected = bytes.fromhex(expected_hex)
        offset = image.get_offset_from_rva(rva)
        actual = binary[offset:offset + len(expected)]
        if actual != expected:
            raise ValueError(f"{name} at {rva:#x}: {actual.hex()} != {expected.hex()}")
        rows.append({"name": name, "rva": hex(rva), "bytes": actual.hex(" ")})
    pointers = []
    for name, rva, expected in POINTER_PROOFS:
        offset = image.get_offset_from_rva(rva)
        actual = struct.unpack_from("<Q", binary, offset)[0] - image.OPTIONAL_HEADER.ImageBase
        if actual != expected:
            raise ValueError(f"{name} at {rva:#x}: {actual:#x} != {expected:#x}")
        pointers.append({"name": name, "slot_rva": hex(rva), "target_rva": hex(actual)})
    return {"schema": "ck3-12002-feast-stage1-open-offline-abi-v1", "status": "GREEN",
            "executable_sha256": digest, "byte_proofs": rows, "pointer_proofs": pointers,
            "rva_map_11906_to_12002": RVA_MAP, "layout_map_11906_to_12002": LAYOUT_MAP,
            "stock_open_event": "0x65", "option_row_stride": "0x10",
            "location_row_stride": "0x38", "readiness": "static-ready",
            "local_ck3_contacted": False, "live_executed": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.executable)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"GREEN: {len(result['byte_proofs'])} exact byte proofs and "
          f"{len(result['pointer_proofs'])} native pointer proofs; stock OpenFeast event 0x65")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
