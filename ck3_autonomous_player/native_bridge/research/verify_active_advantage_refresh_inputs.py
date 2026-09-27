"""Pin the two active advantage refresh helpers on CK3 1.19.0.6."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile

from verify_active_advantage_pause_leaves import EXE_SHA256, verify_image as verify_pause_leaves


FUNCTION_SPANS = {
    "accolade_refresh_head": (0x23CBCE0, 0x23CBD67),
    "accolade_refresh_body": (0x23CBD67, 0x23CBEBA),
    "entry_refresh": (0x23CC2B0, 0x23CC339),
    "entry_materializer": (0x23D2CE0, 0x23D2D68),
    "accolade_apply_head": (0x251B8F0, 0x251B90D),
    "accolade_apply_body": (0x251B90D, 0x251B966),
}
SITES = {
    "reset_guard_count": (0x23CBCEF, "83B91C01000000"),
    "reset_first_modifier_count": (0x23CBD31, "89811C010000"),
    "reset_second_modifier_count": (0x23CBD37, "898184010000"),
    "reset_third_modifier_count": (0x23CBD3D, "8981EC010000"),
    "knight_entry_base": (0x23CBD4B, "488B7140"),
    "knight_entry_count": (0x23CBD4F, "4863414C"),
    "knight_entry_regiment_id": (0x23CBD7A, "8B5608"),
    "regiment_generation_match": (0x23CBDA4, "395310"),
    "regiment_knight_id": (0x23CBDB0, "8B9348010000"),
    "character_generation_match": (0x23CBDE9, "395118"),
    "character_validity_call": (0x23CBDFD, "FF5008"),
    "character_accolade_link": (0x23CBE44, "488B88A8010000"),
    "accolade_full_id": (0x23CBE5C, "8B9168050000"),
    "accolade_generation_match": (0x23CBE80, "395308"),
    "accolade_validity_call": (0x23CBE92, "FF5008"),
    "side_modifier_destination": (0x23CBE99, "488D9710010000"),
    "apply_accolade_to_side": (0x23CBEA3, "E848FA1400"),
    "next_knight_entry": (0x23CBEA8, "4883C660"),
    "accolade_source_gate": (0x251B900, "E8FB080000"),
    "accolade_row_count": (0x251B909, "48634764"),
    "accolade_row_base": (0x251B912, "488B5F58"),
    "accolade_row_source": (0x251B930, "488B5310"),
    "accolade_row_selector": (0x251B934, "8B4B08"),
    "accolade_source_lookup": (0x251B93E, "E85D793800"),
    "accolade_resolved_modifier": (0x251B94C, "488D9090030000"),
    "accolade_aggregator_append": (0x251B953, "E87884CBFF"),
    "next_accolade_row": (0x251B958, "4883C318"),
    "levy_entry_base": (0x23CC2C4, "488B5928"),
    "levy_entry_count": (0x23CC2CB, "48634134"),
    "levy_entry_refresh": (0x23CC2E8, "E8F3690000"),
    "maa_entry_base": (0x23CC2F6, "488B5D40"),
    "maa_entry_count": (0x23CC2FA, "4863454C"),
    "maa_entry_refresh": (0x23CC316, "E8C5690000"),
    "entry_attribute_source": (0x23D2D2F, "E8AC9DFCFF"),
    "entry_field_30_write": (0x23D2D37, "894B30"),
    "entry_field_38_write": (0x23D2D3E, "48894B38"),
    "entry_damage_write": (0x23D2D46, "48894B40"),
    "entry_toughness_write": (0x23D2D4E, "48894B48"),
    "entry_field_50_write": (0x23D2D56, "48894B50"),
    "entry_field_58_write": (0x23D2D5E, "48894358"),
}
CALL_TARGETS = {
    "apply_accolade_to_side": 0x251B8F0,
    "accolade_source_gate": 0x251C200,
    "accolade_source_lookup": 0x28A32A0,
    "accolade_aggregator_append": 0x21D3DD0,
    "levy_entry_refresh": 0x23D2CE0,
    "maa_entry_refresh": 0x23D2CE0,
    "entry_attribute_source": 0x239CAE0,
}


def verify_image(image: pefile.PE) -> dict[str, object]:
    verify_pause_leaves(image)
    rows = [(int(row.struct.BeginAddress), int(row.struct.EndAddress))
            for row in image.DIRECTORY_ENTRY_EXCEPTION]
    for name, expected in FUNCTION_SPANS.items():
        if rows.count(expected) != 1:
            raise ValueError(f"{name} .pdata owner differs")
    anchors = {}
    for name, (rva, expected_hex) in SITES.items():
        expected = bytes.fromhex(expected_hex)
        actual = image.get_data(rva, len(expected))
        if actual != expected:
            raise ValueError(f"{name} differs at 0x{rva:X}")
        if name in CALL_TARGETS and (
            actual[0] != 0xE8 or
            rva + 5 + int.from_bytes(actual[1:], "little", signed=True)
            != CALL_TARGETS[name]
        ):
            raise ValueError(f"{name} call target differs")
        anchors[name] = {"rva": f"0x{rva:X}", "bytes_hex": expected_hex}
    return {
        "schema": "ck3.native_active_advantage_refresh_inputs.v1",
        "game_build": "1.19.0.6",
        "exe_sha256": EXE_SHA256,
        "function_spans": {name: [f"0x{x:X}" for x in span]
                           for name, span in FUNCTION_SPANS.items()},
        "anchors": anchors,
        "proof_layer": "exact-build-instructions-calls-and-pdata",
    }


def verify_exe(exe: Path) -> dict[str, object]:
    raw = exe.read_bytes()
    sha = hashlib.sha256(raw).hexdigest().upper()
    if sha != EXE_SHA256:
        raise ValueError(f"ck3.exe SHA mismatch: {sha}")
    return verify_image(pefile.PE(data=raw, fast_load=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--output", type=Path,
                        help="exclusively create a new exact-build fixture")
    args = parser.parse_args()
    result = verify_exe(args.exe)
    if args.expected is not None:
        expected = json.loads(args.expected.read_text(encoding="utf-8"))
        if result != expected:
            raise ValueError("refresh fixture differs from exact EXE")
    body = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(body, end="")
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
