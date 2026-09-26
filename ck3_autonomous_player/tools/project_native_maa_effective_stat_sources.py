"""Verify bounded CK3 1.19.0.6 MAA effective-stat source anchors.

This is a static source map, not a reconstruction of any live regiment's
modifier values or a proof of why a cached stat changed at daily refresh.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
REFERENCE_ENUM = 0xB6
REFERENCE_POINTER_RVA = 0x43C7AE0
REQUESTED_MODIFIERS = {
    0x1A6: "MOD_ARMY_DAMAGE_MULT",
    0x1A7: "MOD_ARMY_TOUGHNESS_MULT",
    0x1AA: "MOD_MAA_DAMAGE_ADD",
    0x1AB: "MOD_MAA_DAMAGE_MULT",
    0x1AC: "MOD_MAA_TOUGHNESS_ADD",
    0x1AD: "MOD_MAA_TOUGHNESS_MULT",
}
CALLS = {
    0x23D2D2F: 0x239CAE0,  # live side entry to target-effective evaluator
    0x239CCE2: 0x2C8F1A0,  # non-knight evaluator to MAA aggregator
    0x2C8F78D: 0x2C8D6A0,  # aggregator to class/modifier reader
    0x2C8F7B9: 0x23C2DF0,  # apply the accumulated stat modifier structure
}
READER_SITES = {
    0x1A6: 0x2C8D84C,
    0x1A7: 0x2C8D92B,
    0x1AA: 0x2C8D801,
    0x1AB: 0x2C8D823,
    0x1AC: 0x2C8D8E0,
    0x1AD: 0x2C8D902,
}


def _call_target(pe: pefile.PE, site: int) -> int:
    code = pe.get_data(site, 5)
    if len(code) != 5 or code[0] != 0xE8:
        raise ValueError(f"expected relative call at {site:#x}")
    return site + 5 + int.from_bytes(code[1:], "little", signed=True)


def project(exe: Path) -> dict:
    raw = exe.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest().upper()
    if actual_sha != EXE_SHA256:
        raise ValueError(f"CK3 EXE is not the exact 1.19.0.6 build: {actual_sha}")
    pe = pefile.PE(data=raw, fast_load=True)
    for site, expected in CALLS.items():
        if _call_target(pe, site) != expected:
            raise ValueError(f"MAA stat call target drifted at {site:#x}")
    # CMenAtArmsType +0x270 -> class index; the same helper uses that class
    # to select its 0x58-byte modifier row before reading the enums below.
    class_site = 0x2C8D6B7
    if pe.get_data(class_site, 7) != bytes.fromhex("49638070020000"):
        raise ValueError("MAA class-index operand drifted")
    for native_enum, site in READER_SITES.items():
        if pe.get_data(site, 6) != b"\x41\xB8" + native_enum.to_bytes(4, "little"):
            raise ValueError(f"MAA modifier enum operand drifted at {site:#x}")
    # The modifier metadata has 0x38-byte rows, but contains gaps in enum
    # order. Scan only 400 rows from a separately calibrated B6 pointer.
    found = {}
    for ordinal in range(400):
        row_rva = REFERENCE_POINTER_RVA + ordinal * 0x38
        native_enum = int.from_bytes(pe.get_data(row_rva - 16, 4), "little") + 1
        if native_enum not in REQUESTED_MODIFIERS and native_enum != REFERENCE_ENUM:
            continue
        literal_va = int.from_bytes(pe.get_data(row_rva, 8), "little")
        literal_rva = literal_va - pe.OPTIONAL_HEADER.ImageBase
        name = pe.get_data(literal_rva, 96).split(b"\0", 1)[0].decode("ascii")
        if native_enum in found:
            raise ValueError(f"duplicate modifier metadata enum {native_enum:#x}")
        found[native_enum] = (name, row_rva, literal_rva)
    if found.get(REFERENCE_ENUM, (None,))[0] != "MOD_KNIGHT_EFFECTIVENESS_MULT":
        raise ValueError("modifier metadata calibration failed")
    if any(found.get(enum, (None,))[0] != name
           for enum, name in REQUESTED_MODIFIERS.items()):
        raise ValueError("MAA modifier metadata names do not match exact-build operands")
    components = [
        {"native_enum": f"0x{enum:X}", "name": name,
         "reader_operand_rva": f"0x{READER_SITES[enum]:X}",
         "metadata_name_pointer_rva": f"0x{found[enum][1]:X}",
         "literal_rva": f"0x{found[enum][2]:X}"}
        for enum, name in REQUESTED_MODIFIERS.items()
    ]
    return {
        "schema": "ck3.native_maa_effective_stat_sources.v1",
        "game_build": "1.19.0.6", "exe_sha256": EXE_SHA256,
        "non_knight_maa_aggregator_rva": "0x2C8F1A0",
        "class_modifier_reader_rva": "0x2C8D6A0",
        "class_index_operand_rva": f"0x{class_site:X}",
        "modifier_value_helper_rva": "0x2940E80",
        "accumulated_stats_applier_rva": "0x23C2DF0",
        "source_modifiers": components,
        "target_province_forwarded_from_evaluator": True,
        "live_modifier_values_sampled": False,
        "cause_of_day11_or_day21_cached_stat_changes_proven": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(project(args.exe), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
