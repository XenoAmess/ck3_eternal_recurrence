"""Pin the stock CK3 1.19.0.6 construction submit and material-result chain.

This verifies only the frozen PE bytes/calls. It never starts CK3 or issues a
game command; a static GREEN cannot close the paused action gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile


ABI = Path(__file__).with_name("player_world_building_action_private_v1_abi.json")


def _call_target(pe: pefile.PE, source: int) -> int:
    data = pe.get_data(source, 5)
    assert data[0] == 0xE8, f"missing exact direct call at {source:#x}"
    return source + 5 + struct.unpack_from("<i", data, 1)[0]


def verify(exe: Path) -> None:
    abi = json.loads(ABI.read_text(encoding="utf-8"))
    raw = exe.read_bytes()
    assert hashlib.sha256(raw).hexdigest().upper() == abi["exact_build"]["exe_sha256"]
    pe = pefile.PE(data=raw, fast_load=True)
    assert pe.OPTIONAL_HEADER.ImageBase == 0x140000000
    assert pe.OPTIONAL_HEADER.SizeOfImage == 0x5C2D000
    calls = {
        0x26CD475: 0x864750,
        0x26CD480: 0x26D0F50,
        0x26CD49C: 0x295CD60,
        0x26CD3A9: 0x21F6860,
        0x26CD3C7: 0x29190F0,
        0x26CD3E9: 0x2CDBEA0,
    }
    for source, target in calls.items():
        assert _call_target(pe, source) == target, f"changed stock call {source:#x}"
    exact_bytes = {
        0x26CD485: bytes.fromhex("44 8B 4B 28"),  # command selector -> stock slot
        0x26CD48C: bytes.fromhex("8B 53 24"),  # command province
        0x26CD48F: bytes.fromhex("8B 4B 20"),  # command actor
        0x26CD47A: bytes.fromhex("8B 53 2C"),  # command BuildingTypeID
        0x21F699B: bytes.fromhex("44 89 77 78"),  # active slot
        0x21F699F: bytes.fromhex("48 89 77 70"),  # active CBuildingType*
        0x21F69C4: bytes.fromhex("89 9F E0 00 00 00"),  # initiator
        0x2CDD0A6: bytes.fromhex("4D 03 45 38"),  # conditional raw[7] extra
    }
    for rva, expected in exact_bytes.items():
        assert pe.get_data(rva, len(expected)) == expected, f"changed stock field {rva:#x}"
    for region in abi["exact_spans"]:
        start = int(region["start_rva"], 16)
        end = int(region["end_rva_exclusive"], 16)
        assert hashlib.sha256(pe.get_data(start, end - start)).hexdigest().upper() == region["sha256"], region["name"]
    print("GREEN exact stock world-building submit/material source; CK3 not launched")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True, type=Path)
    arguments = parser.parse_args()
    verify(arguments.exe)
