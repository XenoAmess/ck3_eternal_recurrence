"""Focused CK3 1.19.0.6 county CBuildingType source verifier.

It checks exact source bytes and the direct call/global/RTTI anchors used by
the default-OFF private world building-definition reader. It never starts CK3.
Success verifies the frozen static chain, not live behavior or complete semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile


ABI = Path(__file__).with_name("player_world_building_definition_source_v1_abi.json")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"RED: {message}")


def _require_equal(actual: object, expected: object, name: str) -> None:
    _require(actual == expected, f"{name} mismatch: expected {expected!r}, found {actual!r}")


def rva(value: str) -> int:
    return int(value, 16)


def call_target(pe: pefile.PE, source: int) -> int:
    raw = pe.get_data(source, 5)
    _require(len(raw) == 5 and raw[0] == 0xE8,
             f"not a complete direct stock call at {source:#x}")
    return source + 5 + struct.unpack_from("<i", raw, 1)[0]


def rip_target(pe: pefile.PE, source: int) -> int:
    raw = pe.get_data(source, 7)
    _require(len(raw) == 7 and raw[:2] in (b"\x48\x8b", b"\x48\x8d"),
             f"not a complete RIP-relative MOV/LEA at {source:#x}")
    _require(raw[2] & 0xC7 == 0x05, f"not a RIP-relative operand at {source:#x}")
    return source + 7 + struct.unpack_from("<i", raw, 3)[0]


def verify(exe: Path) -> None:
    abi = json.loads(ABI.read_text(encoding="utf-8"))
    raw = exe.read_bytes()
    _require_equal(hashlib.sha256(raw).hexdigest().upper(), abi["exe_sha256"],
                   "executable SHA-256")
    pe = pefile.PE(data=raw, fast_load=True)
    for region in abi["exact_regions"]:
        start, end = rva(region["start_rva"]), rva(region["end_rva_exclusive"])
        _require_equal(hashlib.sha256(pe.get_data(start, end - start)).hexdigest().upper(),
                       region["sha256"], f"source span {region['name']} SHA-256")
    _require_equal(pe.OPTIONAL_HEADER.SizeOfImage, 0x5C2D000, "PE image size")
    world = abi["world_source"]
    _require_equal(rip_target(pe, 0x864754), rva(world["global_slot_rva"]), "world global load")
    _require_equal(rip_target(pe, 0x86479B), rva(world["global_slot_rva"]), "world global address")
    _require_equal(call_target(pe, 0x1922C52), rva(world["accessor_rva"]), "world accessor call")
    _require_equal(pe.get_data(0x1922C57, 8), b"\x48\x8b\x50\x68\x48\x63\x40\x74", "world vector reads")
    _require_equal(pe.get_data(0x2C605CE, 4), b"\x48\x8d\x4e\x68", "parser vector destination")
    _require_equal(call_target(pe, 0x2C605D9), 0x8154D0, "parser vector append call")
    _require_equal(call_target(pe, 0x2C60586), 0x2C543C0, "parser constructor call")
    # The stock typed-ID lookup uses the same manager and falls back to a
    # separately constructed default CBuildingType object, never a court row.
    _require_equal(rip_target(pe, 0xC8F84A), 0x570CBA8, "typed-ID fallback global")
    court = abi["r735_wrong_court_source"]
    _require_equal(rip_target(pe, 0xC8CE84), rva(court["global_slot_rva"]), "excluded court global")
    _require_equal(call_target(pe, 0x176EFD5), rva(court["accessor_rva"]), "excluded court accessor")
    _require_equal(call_target(pe, 0x14D0B94), 0x176EFB0, "court refresh caller 1")
    _require_equal(call_target(pe, 0x14D1BB0), 0x176EFB0, "court refresh caller 2")
    court_vtable_rva = rva(court["observed_first_vtable_rva"])
    court_col_va = struct.unpack("<Q", pe.get_data(court_vtable_rva - 8, 8))[0]
    _require_equal(court_col_va - pe.OPTIONAL_HEADER.ImageBase, rva(court["first_vtable_col_rva"]), "court COL address")
    court_col_rva = rva(court["first_vtable_col_rva"])
    signature, offset, _, court_type_rva, hierarchy_rva, self_rva = struct.unpack(
        "<6I", pe.get_data(court_col_rva, 24))
    _require(signature == 1 and offset == 0 and self_rva == court_col_rva, "invalid court COL layout")
    _require_equal(court_type_rva, rva(court["type_descriptor_rva"]), "court type descriptor")
    _require_equal(pe.get_string_at_rva(court_type_rva + 16), b".?AVCCourtTypeSetting@@", "court RTTI name")
    _, _, base_count, base_array_rva = struct.unpack("<4I", pe.get_data(hierarchy_rva, 16))
    court_bases = []
    for index in range(base_count):
        base_descriptor_rva = struct.unpack("<I", pe.get_data(base_array_rva + index * 4, 4))[0]
        base_type_rva = struct.unpack("<I", pe.get_data(base_descriptor_rva, 4))[0]
        court_bases.append(pe.get_string_at_rva(base_type_rva + 16))
    _require_equal(court_bases, [b".?AVCCourtTypeSetting@@",
                                b".?AVCGameDatabaseObject@@", b".?AVCPersistent@@"], "court RTTI hierarchy")
    domicile = abi["r730_wrong_domicile_source"]
    _require_equal(rip_target(pe, 0xC8CEE4), rva(domicile["global_slot_rva"]), "excluded domicile global")
    _require_equal(call_target(pe, 0x1922305), rva(domicile["accessor_rva"]), "excluded domicile accessor 1")
    _require_equal(call_target(pe, 0x15ABC4B), rva(domicile["accessor_rva"]), "excluded domicile accessor 2")
    vtable_rva = rva(domicile["observed_first_vtable_rva"])
    col_va = struct.unpack("<Q", pe.get_data(vtable_rva - 8, 8))[0]
    _require_equal(col_va - pe.OPTIONAL_HEADER.ImageBase, rva(domicile["first_vtable_col_rva"]), "domicile COL address")
    col_rva = rva(domicile["first_vtable_col_rva"])
    signature, offset, _, peer_type_rva, hierarchy_rva, self_rva = struct.unpack(
        "<6I", pe.get_data(col_rva, 24))
    _require(signature == 1 and offset == 0 and self_rva == col_rva, "invalid domicile COL layout")
    _require_equal(peer_type_rva, rva(domicile["type_descriptor_rva"]), "domicile type descriptor")
    _require_equal(pe.get_string_at_rva(peer_type_rva + 16), b".?AVCDomicileBuildingType@@", "domicile RTTI name")
    _, _, base_count, base_array_rva = struct.unpack("<4I", pe.get_data(hierarchy_rva, 16))
    peer_bases = []
    for index in range(base_count):
        base_descriptor_rva = struct.unpack("<I", pe.get_data(base_array_rva + index * 4, 4))[0]
        base_type_rva = struct.unpack("<I", pe.get_data(base_descriptor_rva, 4))[0]
        peer_bases.append(pe.get_string_at_rva(base_type_rva + 16))
    _require_equal(peer_bases, [b".?AVCDomicileBuildingType@@",
                               b".?AVCGameDatabaseObject@@", b".?AVCPersistent@@"], "domicile RTTI hierarchy")
    _require_equal(rip_target(pe, 0x2C543F0), rva(world["primary_vtable_rva"]), "building constructor vtable")
    _require_equal(call_target(pe, 0x11A632E), rva(abi["stock_player_final_legality"]["native_predicate_rva"]), "player final-legality call")
    type_descriptor = rva(world["type_descriptor_rva"])
    _require_equal(pe.get_data(type_descriptor + 0x10, 19), b".?AVCBuildingType@@", "building RTTI name")
    for col_name in ("primary_col_rva", "secondary_col_rva"):
        col = rva(world[col_name])
        signature, _, _, type_rva, _, self_rva = struct.unpack("<6I", pe.get_data(col, 24))
        _require(signature == 1 and type_rva == type_descriptor and self_rva == col,
                 f"invalid building COL layout: {col_name}")
    print("GREEN exact CBuildingType manager vector/player final-legality source; CK3 not launched")
    print("EVIDENCE_SCOPE " + json.dumps({
        "evidence_scope": "exact-build-static-chain",
        "verified": ["executable-and-span-bytes", "direct-call-and-global-anchors", "RTTI-type-chain"],
        "not_verified": ["live-behavior", "complete-decision-semantics"],
        "game_process_started": False,
    }, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True, type=Path)
    verify(parser.parse_args().exe)
