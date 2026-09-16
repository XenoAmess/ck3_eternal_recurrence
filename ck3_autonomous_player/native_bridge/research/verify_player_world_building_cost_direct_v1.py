"""Verify direct stock player building cost source in frozen CK3 1.19.0.6.

This performs only PE byte/call checks; no game process is launched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile


ABI = Path(__file__).with_name("player_world_building_cost_direct_v1_abi.json")


def _call_target(pe: pefile.PE, source: int) -> int:
    data = pe.get_data(source, 5)
    assert data[0] == 0xE8, f"missing exact direct call {source:#x}"
    return source + 5 + struct.unpack_from("<i", data, 1)[0]


def verify(exe: Path, print_pins: bool = False) -> None:
    abi = json.loads(ABI.read_text(encoding="utf-8"))
    raw = exe.read_bytes()
    exe_hash = hashlib.sha256(raw).hexdigest().upper()
    assert exe_hash == abi["exact_build"]["exe_sha256"]
    pe = pefile.PE(data=raw, fast_load=True)
    assert pe.OPTIONAL_HEADER.SizeOfImage == 0x5C2D000
    assert _call_target(pe, 0x295DCC0) == 0x29190F0
    assert _call_target(pe, 0x18D184F) == 0x29190F0
    assert _call_target(pe, 0x11A632E) == 0x295CD60
    assert _call_target(pe, 0x295DCF4) == 0x2CDCFF0
    for region in abi["exact_spans"]:
        start = int(region["start_rva"], 16)
        end = int(region["end_rva_exclusive"], 16)
        digest = hashlib.sha256(pe.get_data(start, end - start)).hexdigest().upper()
        if print_pins:
            print(f'{region["name"]}: {digest}')
        else:
            assert digest == region["sha256"], region["name"]
    print("GREEN exact stock player cost source; CK3 not launched")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--print-pins", action="store_true")
    arguments = parser.parse_args()
    verify(arguments.exe, arguments.print_pins)
