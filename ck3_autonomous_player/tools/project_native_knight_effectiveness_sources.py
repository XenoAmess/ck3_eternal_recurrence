"""Bind CK3 1.19.0.6 knight-effectiveness modifier enum IDs to native names.

This is a static source contract. It does not sample a character's modifier
values or explain the 185000 Q100000 effectiveness in the live Messina trace.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
COMPONENTS = (
    (0xB6, "MOD_KNIGHT_EFFECTIVENESS_MULT", 0x28FD9B3, "constant 100000 Q100000"),
    (0xB7, "MOD_KNIGHT_EFFECTIVENESS_PER_DREAD", 0x28FDA01, "military+0x350"),
    (0xB8, "MOD_KNIGHT_EFFECTIVENESS_PER_TYRANNY", 0x28FDA3D, "military+0x358"),
    (0xB9, "MOD_KNIGHT_EFFECTIVENESS_PER_PROWESS", 0x28FDA74, "character+0xE8"),
    (0xBA, "MOD_KNIGHT_EFFECTIVENESS_PER_DIPLOMACY", 0x28FDAAB, "character+0xD4"),
    (0xBB, "MOD_KNIGHT_EFFECTIVENESS_PER_INTRIGUE", 0x28FDAE2, "character+0xE0"),
    (0xBC, "MOD_KNIGHT_EFFECTIVENESS_PER_LEARNING", 0x28FDB19, "character+0xE4"),
    (0xBD, "MOD_KNIGHT_EFFECTIVENESS_PER_MARTIAL", 0x28FDB50, "character+0xD8"),
    (0xBE, "MOD_KNIGHT_EFFECTIVENESS_PER_STEWARDSHIP", 0x28FDB87, "character+0xDC"),
)
CALIBRATION = (
    (0x106, "MOD_COMBAT_COUNTER_EFFICIENCY"),
    (0x107, "MOD_COMBAT_COUNTER_RESISTANCE"),
)
FIELD_SITE_BYTES = (
    (0x28FD9E1, "488B9FB8010000"),
    (0x28FD9ED, "488B9B50030000"),
    (0x28FDA22, "488B87B8010000"),
    (0x28FDA2E, "488BA858030000"),
    (0x28FDA61, "486387E8000000"),
    (0x28FDA98, "486387D4000000"),
    (0x28FDACF, "486387E0000000"),
    (0x28FDB06, "486387E4000000"),
    (0x28FDB3D, "486387D8000000"),
    (0x28FDB74, "486387DC000000"),
)


def _unique_offset(raw: bytes, token: bytes) -> int:
    first = raw.find(token)
    if first < 0 or raw.find(token, first + 1) >= 0:
        raise ValueError("modifier literal is missing or nonunique")
    return first


def project(exe: Path) -> dict:
    raw = exe.read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != EXE_SHA256:
        raise ValueError("CK3 executable differs from the 1.19.0.6 exact build")
    pe = pefile.PE(data=raw, fast_load=True)
    mappings = []
    for native_enum, name, callsite, operand in (*COMPONENTS, *(
        (enum, key, None, "calibration from prior counter-helper research")
        for enum, key in CALIBRATION
    )):
        literal_offset = _unique_offset(raw, name.encode() + b"\0")
        literal_rva = pe.get_rva_from_offset(literal_offset)
        pointer = (pe.OPTIONAL_HEADER.ImageBase + literal_rva).to_bytes(8, "little")
        pointer_offset = _unique_offset(raw, pointer)
        pointer_rva = pe.get_rva_from_offset(pointer_offset)
        stored_index = int.from_bytes(raw[pointer_offset - 16:pointer_offset - 12],
                                      "little", signed=False)
        if stored_index + 1 != native_enum:
            raise ValueError(f"modifier enum-to-metadata ordinal drift: {name}")
        if callsite is not None:
            expected = b"\x41\xB8" + native_enum.to_bytes(4, "little")
            if pe.get_data(callsite, 6) != expected:
                raise ValueError(f"modifier operand drift: {name}")
        mappings.append({"native_enum": f"0x{native_enum:X}", "metadata_index": stored_index,
                         "name": name, "literal_rva": f"0x{literal_rva:X}",
                         "metadata_name_pointer_rva": f"0x{pointer_rva:X}",
                         "reader_callsite_rva": f"0x{callsite:X}" if callsite else None,
                         "input_operand": operand})
    pointer_rvas = [int(row["metadata_name_pointer_rva"], 16) for row in mappings[:9]]
    if any(right - left != 0x38 for left, right in zip(pointer_rvas, pointer_rvas[1:])):
        raise ValueError("knight modifier metadata is not a consecutive nine-row table")
    field_sites = []
    for site, expected_hex in FIELD_SITE_BYTES:
        expected = bytes.fromhex(expected_hex)
        if pe.get_data(site, len(expected)) != expected:
            raise ValueError(f"knight effectiveness character operand drift at {site:#x}")
        field_sites.append({"rva": f"0x{site:X}", "bytes_hex": expected_hex})
    if (pe.get_data(0x28FD9AE, 5) != bytes.fromhex("E80D99D1FF")
            or pe.get_data(0x28FD9CD, 5) != bytes.fromhex("E8AE340400")
            or pe.get_data(0x28FDBE6, 5) != bytes.fromhex("E8A5FDFFFF")):
        raise ValueError("knight modifier or final formula helper call drifted")
    return {"schema": "ck3.native_knight_effectiveness_modifier_sources.v1",
            "game_build": "1.19.0.6", "exe_sha256": EXE_SHA256,
            "reader_rva": "0x28FD990", "modifier_set_resolver_rva": "0x26172C0",
            "modifier_value_helper_rva": "0x2940E80",
            "knight_stat_writer_rva": "0x28FDBC0",
            "metadata_index_to_native_enum_offset": 1,
            "metadata_offset_calibration": mappings[9:],
            "modifier_components_in_reader_order": mappings[:9],
            "character_operand_instruction_bytes": field_sites,
            "specific_modifier_values_sampled_in_live_battle": False,
            "observed_185000_effectiveness_decomposition_proven": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.exe)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
                      "components": len(report["modifier_components_in_reader_order"])}))


if __name__ == "__main__":
    main()
