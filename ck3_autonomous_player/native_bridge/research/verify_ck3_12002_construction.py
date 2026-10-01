"""Verify the frozen 1.20 construction provider ABI without opening CK3."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile

EXACT_SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def verify(executable: Path, abi_path: Path) -> dict:
    raw = executable.read_bytes()
    abi = json.loads(abi_path.read_text(encoding="utf-8"))
    require(abi["game_version"] == "1.20.0.2" and abi["exe_sha256"] == EXACT_SHA,
            "ABI does not identify CK3 1.20.0.2")
    require(len(raw) == abi["exe_size"] and hashlib.sha256(raw).hexdigest().upper() == EXACT_SHA,
            "executable is not the frozen 1.20.0.2 build")
    pe = pefile.PE(data=raw, fast_load=True)
    require(pe.FILE_HEADER.Machine == 0x8664 and pe.OPTIONAL_HEADER.ImageBase == 0x140000000,
            "not the expected PE64 image")
    require(pe.OPTIONAL_HEADER.SizeOfImage == abi["image_size"], "image size differs")

    def at(rva: int, size: int) -> bytes:
        result = pe.get_data(rva, size)
        require(len(result) == size, f"RVA {rva:#x} is not file backed")
        return result

    for span in abi["exact_spans"]:
        start = int(span["start_rva"], 0)
        actual = at(start, int(span["end_rva_exclusive"], 0) - start)
        require(hashlib.sha256(actual).hexdigest() == span["sha256"], span["name"])

    edges = [(0x2982310, 0x8D1670), (0x298231B, 0x29860B0),
             (0x29823D9, 0x24677D0), (0x29823FC, 0x2C247C0),
             (0x298249A, 0x8D1670), (0x29824A5, 0x29860B0),
             (0x29824C1, 0x2C77D50)]
    for site, target in edges:
        call = at(site, 5)
        require(call[0] == 0xE8 and site + 5 + struct.unpack_from("<i", call, 1)[0] == target,
                f"direct call {site:#x} -> {target:#x} differs")

    # The manager pointer comes from a RIP-relative qword load in its getter.
    manager_getter = at(0x8D1670, 0x57)
    require(any(manager_getter[index:index + 3] == b"\x48\x8b\x05" and
                0x8D1670 + index + 7 + struct.unpack_from("<i", manager_getter, index + 3)[0] == 0x5C67540
                for index in range(len(manager_getter) - 6)), "building-manager global differs")
    vtable = int(abi["bindings"]["building_primary_vtable"], 0)
    col = struct.unpack("<Q", at(vtable - 8, 8))[0] - pe.OPTIONAL_HEADER.ImageBase
    signature, offset, cd_offset, type_rva, hierarchy, self_rva = struct.unpack("<6I", at(col, 24))
    require(signature == 1 and offset == 0 and cd_offset == 0 and hierarchy != 0 and self_rva == col,
            "building primary RTTI locator differs")
    require(type_rva == 0x5586BB8 and at(type_rva + 16, 128).split(b"\0", 1)[0] == b".?AVCBuildingType@@",
            "building definition RTTI differs")

    held_path = abi_path.with_name("ck3_12002_construction_held_layout.json")
    held = json.loads(held_path.read_text(encoding="utf-8"))
    require(held["exe_sha256"] == EXACT_SHA, "held-title layout build differs")
    for row in held["semantic_checks"]:
        expected = bytes.fromhex(row["bytes"])
        require(at(int(row["rva"], 0), len(expected)) == expected, row["name"])
    return {"status": "GREEN_EXACT_BINDING", "game_version": "1.20.0.2",
            "exe_sha256": EXACT_SHA, "abi_sha256": hashlib.sha256(abi_path.read_bytes()).hexdigest(),
            "exact_spans_verified": len(abi["exact_spans"]), "direct_calls_verified": len(edges),
            "held_semantic_checks_verified": len(held["semantic_checks"]),
            "definition_rtti_verified": True, "manager_global_verified": True,
            "game_process_touched": False, "live_verified": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ck3-executable", type=Path, required=True)
    parser.add_argument("--abi", type=Path, default=Path(__file__).with_name("ck3_12002_construction_abi.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.ck3_executable, args.abi)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
