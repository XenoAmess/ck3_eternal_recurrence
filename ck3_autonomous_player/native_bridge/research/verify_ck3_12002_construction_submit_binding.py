"""Verify frozen building-command RTTI/callsites without touching CK3."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

EXACT_SHA256 = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
EXACT_SIZE = 101039736


def check(executable: Path, contract: Path) -> dict:
    image = executable.read_bytes()
    if len(image) != EXACT_SIZE or hashlib.sha256(image).hexdigest().upper() != EXACT_SHA256:
        raise AssertionError("not the frozen CK3 1.20.0.2 executable")
    abi = json.loads(contract.read_text(encoding="utf-8"))
    assert abi["exact_build"]["product_version"] == "1.20.0.2"
    assert abi["exact_build"]["executable_sha256"] == EXACT_SHA256
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    assert image[pe:pe + 4] == b"PE\0\0"
    count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_bytes = struct.unpack_from("<H", image, pe + 20)[0]
    optional = pe + 24
    image_base = struct.unpack_from("<Q", image, optional + 24)[0]
    assert image_base == 0x140000000
    section_table = optional + optional_bytes
    sections = [struct.unpack_from("<IIII", image, section_table + index * 40 + 8)
                for index in range(count)]

    def at(rva: int, size: int) -> bytes:
        for virtual_size, virtual_address, raw_size, raw_offset in sections:
            if virtual_address <= rva and rva + size <= virtual_address + raw_size:
                offset = raw_offset + rva - virtual_address
                return image[offset:offset + size]
        raise AssertionError(f"RVA {rva:#x} is not file backed")

    for span in abi["exact_spans"]:
        actual = at(int(span["rva"], 0), span["size"])
        assert actual == bytes.fromhex(span["hex"]), span["name"]
        assert hashlib.sha256(actual).hexdigest() == span["sha256"], span["name"]
    for edge in abi["direct_call_targets"]:
        site = int(edge["call_rva"], 0)
        encoded = at(site, 5)
        assert encoded[0] == 0xE8, edge["meaning"]
        target = site + 5 + struct.unpack_from("<i", encoded, 1)[0]
        assert target == int(edge["target_rva"], 0), edge["meaning"]
    for entry in abi["rtti"]:
        col_rva = int(entry["col_rva"], 0)
        signature, offset, cd_offset, type_rva, hierarchy, self_rva = struct.unpack(
            "<6I", at(col_rva, 24))
        assert signature == 1 and cd_offset == 0 and hierarchy != 0
        assert offset == entry["object_offset"]
        assert self_rva == col_rva
        assert type_rva == int(entry["type_rva"], 0)
        assert at(type_rva + 16, 128).split(b"\0", 1)[0].decode("ascii") == entry["name"]
        vtable = int(entry["vtable_rva"], 0)
        assert struct.unpack("<Q", at(vtable - 8, 8))[0] == image_base + col_rva
    primary = int(abi["building_command"]["primary_vtable_rva"], 0)
    secondary = int(abi["building_command"]["secondary_vtable_rva"], 0)
    assert struct.unpack("<Q", at(primary + 0x30, 8))[0] == image_base + 0x2982440
    assert struct.unpack("<Q", at(primary + 0x40, 8))[0] == image_base + 0x2985DC0
    assert struct.unpack("<Q", at(secondary + 8, 8))[0] == image_base + 0x29822C0
    assert not abi["legacy_misclassification"]["validate_holding_bound"]
    assert not abi["readiness"]["live_verified"]
    return {"status": "GREEN_EXACT_BINDING", "game_process_touched": False,
            "executable_sha256": EXACT_SHA256,
            "contract_sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
            "exact_spans_verified": len(abi["exact_spans"]),
            "direct_calls_verified": len(abi["direct_call_targets"]),
            "rtti_objects_verified": len(abi["rtti"]),
            "building_command_bytes": abi["building_command"]["native_size"],
            "holding_backend_bound": False, "live_verified": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ck3-executable", type=Path, required=True)
    parser.add_argument("--abi", type=Path, default=Path(__file__).with_name(
        "ck3_12002_construction_submit_binding_abi.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = check(args.ck3_executable, args.abi)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
