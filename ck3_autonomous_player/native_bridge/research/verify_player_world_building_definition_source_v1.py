"""Focused CK3 1.19.0.6 stock source verifier for G2-M4-DEFINITION0.

It checks exact source bytes and the direct call/global/RTTI anchors used by
the default-OFF private world building-definition reader. It never starts CK3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile


ABI = Path(__file__).with_name("player_world_building_definition_source_v1_abi.json")


def rva(value: str) -> int:
    return int(value, 16)


def call_target(pe: pefile.PE, source: int) -> int:
    raw = pe.get_data(source, 5)
    assert raw[0] == 0xE8, f"not a direct stock call at {source:#x}"
    return source + 5 + struct.unpack_from("<i", raw, 1)[0]


def rip_target(pe: pefile.PE, source: int) -> int:
    raw = pe.get_data(source, 7)
    assert raw[:2] in (b"\x48\x8b", b"\x48\x8d"), source
    assert raw[2] & 0xC7 == 0x05, source
    return source + 7 + struct.unpack_from("<i", raw, 3)[0]


def verify(exe: Path) -> None:
    abi = json.loads(ABI.read_text(encoding="utf-8"))
    raw = exe.read_bytes()
    assert hashlib.sha256(raw).hexdigest().upper() == abi["exe_sha256"]
    pe = pefile.PE(data=raw, fast_load=True)
    for region in abi["exact_regions"]:
        start, end = rva(region["start_rva"]), rva(region["end_rva_exclusive"])
        assert hashlib.sha256(pe.get_data(start, end - start)).hexdigest().upper() == region["sha256"], region["name"]
    assert rip_target(pe, 0xC8CEE4) == rva(abi["world_source"]["global_slot_rva"])
    assert call_target(pe, 0x1922305) == rva(abi["world_source"]["accessor_rva"])
    assert call_target(pe, 0x15ABC4B) == rva(abi["world_source"]["accessor_rva"])
    assert rip_target(pe, 0x2C543F0) == rva(abi["world_source"]["primary_vtable_rva"])
    assert call_target(pe, 0x11A632E) == rva(abi["stock_player_final_legality"]["native_predicate_rva"])
    type_descriptor = rva(abi["world_source"]["type_descriptor_rva"])
    assert pe.get_data(type_descriptor + 0x10, 19) == b".?AVCBuildingType@@"
    for col_name in ("primary_col_rva", "secondary_col_rva"):
        col = rva(abi["world_source"][col_name])
        signature, _, _, type_rva, _, self_rva = struct.unpack("<6I", pe.get_data(col, 24))
        assert signature == 1 and type_rva == type_descriptor and self_rva == col
    print("GREEN exact world CBuildingType registry/player final-legality source; CK3 not launched")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True, type=Path)
    verify(parser.parse_args().exe)
