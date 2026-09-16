"""Verify only the frozen stock1.19.0.6 faction metric getter chain.

Usage: py -3.13 faction_gift_metric_receivers_v1_source_contract.py --exe <ck3.exe>
This is read-only PE verification; it does not load or operate CK3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile


ABI = Path(__file__).with_name("faction_gift_metric_receivers_v1_abi.json")


def _target_of_lea_r8(pe: pefile.PE, rva: int) -> int:
    instruction = pe.get_data(rva, 7)
    if len(instruction) != 7 or instruction[:3] != b"\x4c\x8d\x05":
        raise AssertionError(f"missing frozen lea r8 callback at RVA {rva:#x}")
    return rva + 7 + struct.unpack("<i", instruction[3:])[0]


def _verify_span(pe: pefile.PE, rva: int, size: int, expected: str) -> None:
    body = pe.get_data(rva, size)
    if len(body) != size or hashlib.sha256(body).hexdigest().upper() != expected:
        raise AssertionError(f"frozen native span changed at RVA {rva:#x}")


def verify(exe: Path) -> dict[str, object]:
    contract = json.loads(ABI.read_text(encoding="utf-8"))
    if hashlib.sha256(exe.read_bytes()).hexdigest().upper() != contract["executable_sha256"]:
        raise AssertionError("CK3 EXE SHA does not match the frozen metric ABI")
    pe = pefile.PE(str(exe), fast_load=True)
    for name, getter in contract["getters"].items():
        target = _target_of_lea_r8(pe, getter["registration_callback_lea_rva"])
        if target != getter["callback_rva"]:
            raise AssertionError(f"{name} callback registration drift")
        _verify_span(pe, getter["leaf_rva"], getter["leaf_size"], getter["leaf_sha256"])
    for dependency in contract["power_dependencies"].values():
        _verify_span(pe, dependency["rva"], dependency["size"], dependency["sha256"])
    source = contract["direct_targeting_source"]
    _verify_span(pe, source["stock_refresh_rva"], source["stock_refresh_size"], source["stock_refresh_sha256"])
    return {
        "game_version": contract["game_version"],
        "executable_sha256": contract["executable_sha256"],
        "output_scale": contract["output_scale"],
        "getters": {name: getter["leaf_rva"] for name, getter in contract["getters"].items()},
        "direct_targeting_source_rva": source["stock_refresh_rva"],
        "evidence_stage": contract["evidence_stage"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.exe), sort_keys=True))


if __name__ == "__main__":
    main()
