"""Verify the exact-build forced-subject-contract sources using files only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile

EXACT_SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"


def verify(executable: Path, manifest: Path, stock_game: Path | None = None) -> dict:
    abi = json.loads(manifest.read_text(encoding="utf-8"))
    raw = executable.read_bytes()
    assert abi["game_version"] == "1.20.0.2" and abi["exe_sha256"] == EXACT_SHA
    assert hashlib.sha256(raw).hexdigest().upper() == EXACT_SHA
    assert len(raw) == abi["exe_size"]
    image = pefile.PE(data=raw, fast_load=True)
    assert image.FILE_HEADER.Machine == 0x8664
    assert image.OPTIONAL_HEADER.ImageBase == 0x140000000
    assert image.OPTIONAL_HEADER.SizeOfImage == abi["image_size"]

    def at(rva: int, size: int) -> bytes:
        result = image.get_data(rva, size)
        assert len(result) == size, f"not file-backed: {rva:#x}"
        return result

    for span in abi["exact_spans"]:
        actual = at(int(span["start_rva"], 0), span["size"])
        assert hashlib.sha256(actual).hexdigest() == span["sha256"], span["name"]
    for check in abi["instruction_checks"]:
        expected = bytes.fromhex(check["bytes"])
        assert at(int(check["rva"], 0), len(expected)) == expected, check["name"]
    for edge in abi["direct_calls"]:
        site, target = int(edge["site_rva"], 0), int(edge["target_rva"], 0)
        instruction = at(site, 5)
        assert instruction[0] == 0xE8
        assert site + 5 + struct.unpack_from("<i", instruction, 1)[0] == target
    for binding in abi["rip_bindings"]:
        site, target = int(binding["site_rva"], 0), int(binding["target_rva"], 0)
        instruction = at(site, 7)
        assert instruction[0] in (0x48, 0x4C) and instruction[1] in (0x8B, 0x8D)
        assert instruction[2] & 0xC7 == 5
        assert site + 7 + struct.unpack_from("<i", instruction, 3)[0] == target
    for check in abi["literal_checks"]:
        expected = check["ascii"].encode("ascii") + b"\0"
        assert at(int(check["rva"], 0), len(expected)) == expected, check["name"]

    bindings = abi["bindings"]
    vtable = int(bindings["subject_contract_primary_vtable"], 0)
    col = int(bindings["subject_contract_col"], 0)
    type_descriptor = int(bindings["subject_contract_type_descriptor"], 0)
    assert struct.unpack("<Q", at(vtable - 8, 8))[0] == image.OPTIONAL_HEADER.ImageBase + col
    signature, offset, constructor_offset, type_rva, hierarchy, self_rva = struct.unpack("<6I", at(col, 24))
    assert (signature, offset, constructor_offset, type_rva, self_rva) == (1, 0, 0, type_descriptor, col)
    assert hierarchy != 0
    assert struct.unpack("<Q", at(vtable, 8))[0] == image.OPTIONAL_HEADER.ImageBase + 0x24C1BB0

    stock_count = 0
    if stock_game is not None:
        for source in abi["stock_sources"]:
            content = stock_game.joinpath(source["game_relative_path"]).read_bytes()
            assert hashlib.sha256(content).hexdigest() == source["sha256"]
            assert b"tributary_war_participation_obligation" in content
            assert b"code checks only for non-default" in content
            stock_count += 1
    return {"status": "GREEN_EXACT_BINDING", "game_version": "1.20.0.2",
            "exe_sha256": EXACT_SHA, "abi_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "exact_spans": len(abi["exact_spans"]), "instruction_checks": len(abi["instruction_checks"]),
            "direct_calls": len(abi["direct_calls"]), "rip_bindings": len(abi["rip_bindings"]),
            "literal_checks": len(abi["literal_checks"]), "rtti_verified": True,
            "stock_sources": stock_count, "readiness": "static-ready",
            "complete_initial_participants_ready": False,
            "game_process_touched": False, "live_verified": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--abi", type=Path, default=Path(__file__).with_name("ck3_12002_prewar_participants_abi.json"))
    parser.add_argument("--stock-game", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.exe, args.abi, args.stock_game)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
