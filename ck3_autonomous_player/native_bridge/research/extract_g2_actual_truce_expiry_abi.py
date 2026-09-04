#!/usr/bin/env python3
"""Freeze the exact-build post-application truce-expiry read chain.

This tool only reads ck3.exe and repository sources. It never starts, injects
into, or attaches to CK3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86_const import X86_INS_CALL, X86_OP_IMM
import pefile


EXPECTED_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_SIZE = 95_206_008
EXPECTED_IMAGE_BASE = 0x140000000
EXPECTED_IMAGE_SIZE = 0x5C2D000
EXPECTED_TIMESTAMP = 0x6A1EEE6D

RANGES = {
    "relation_lookup_read_only": (0x2610840, 0x26108F0),
    "relation_get_or_create": (0x26108F0, 0x2610A4C),
    "has_truce": (0x26631E0, 0x2663244),
    "get_truce_end_date": (0x2663250, 0x26632E6),
    "script_has_truce_evaluator": (0x28852E0, 0x2885426),
    "script_has_truce_registration": (0x550520, 0x5505B8),
    "caddtruce_normal": (0x2EDAD20, 0x2EDB27C),
    "caddtruce_forced": (0x2EDB3A0, 0x2EDB9A5),
}

EXPECTED_RANGE_HASHES = {
    "relation_lookup_read_only": "F8775B263CF77288E58D1B97AFA4FB900327EC072D0AA4CFB0CB4EA94256A8B9",
    "relation_get_or_create": "F5344D8A6D2A5864B6A5A5B02C31AE52EFA918A5EB8A6ED634AC3340B109A3AB",
    "has_truce": "017CC5018D7F0E5DC1DF6ADCC912A90D235F39ADE1E2D6FD8B284C34DE0BDCD9",
    "get_truce_end_date": "4914D12A0E256891B3A73550F30DB05CB006E9969F417E464948BC5B7E46F103",
    "script_has_truce_evaluator": "64B70965E505B34B6EF18509E9FB589721B9CF29141BC20A1576170CF341A149",
    "script_has_truce_registration": "D01CF38467B57C7D579765C202CF9FC95895F741A0D09FFCE0C398B742552F47",
    "caddtruce_normal": "0CC65B9CFAE1F080C333E4B219388B19AA231E11FDF69AA9470D6E6E5B9EF199",
    "caddtruce_forced": "DED15DD333E2B6D037B31BBA5DF1DD521885C8F3715C3CB5C040087B657F92E0",
}

REQUIRED_CALLS = {
    "has_truce": {0x26631ED: 0x2610840},
    "get_truce_end_date": {0x266325D: 0x2610840},
    "script_has_truce_evaluator": {0x2885404: 0x26631E0},
    "caddtruce_normal": {
        0x2EDAEDD: 0x26108F0,
        0x2EDAF0F: 0x3373000,
        0x2EDB223: 0x2367C00,
    },
    "caddtruce_forced": {
        0x2EDB56D: 0x26108F0,
        0x2EDB59E: 0x3373000,
        0x2EDB94C: 0x2367C00,
    },
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def file_bytes(data: bytes, image: pefile.PE, begin: int, end: int) -> bytes:
    offset = image.get_offset_from_rva(begin)
    value = data[offset : offset + end - begin]
    if len(value) != end - begin:
        raise ValueError(f"short range 0x{begin:X}..0x{end:X}")
    return value


def decode(decoder: Cs, data: bytes, image: pefile.PE, begin: int, end: int):
    return list(
        decoder.disasm(
            file_bytes(data, image, begin, end), EXPECTED_IMAGE_BASE + begin
        )
    )


def validate_call(instructions, call_rva: int, target_rva: int) -> None:
    address = EXPECTED_IMAGE_BASE + call_rva
    target = EXPECTED_IMAGE_BASE + target_rva
    row = next((item for item in instructions if item.address == address), None)
    if (
        row is None
        or row.id != X86_INS_CALL
        or not row.operands
        or row.operands[0].type != X86_OP_IMM
        or row.operands[0].imm != target
    ):
        raise ValueError(
            f"call binding changed at 0x{call_rva:X}; expected 0x{target_rva:X}"
        )


def source_hashes(root: Path) -> dict[str, str]:
    relative = (
        "include/xar_bridge/raiktor_actual_truce_expiry_v1.hpp",
        "include/xar_bridge/ck3_11906.hpp",
        "include/xar_bridge/game_adapter.hpp",
        "src/raiktor_actual_truce_expiry_v1.cpp",
        "src/ck3_11906.cpp",
        "src/ck3_11906_adapter.cpp",
        "src/game_adapter.cpp",
        "src/bridge.cpp",
        "CMakeLists.txt",
    )
    return {name: digest((root / name).read_bytes()) for name in relative}


def extract(exe: Path, native_root: Path) -> dict[str, Any]:
    data = exe.read_bytes()
    exe_hash = digest(data)
    if len(data) != EXPECTED_SIZE or exe_hash != EXPECTED_SHA256:
        raise ValueError(f"unexpected ck3.exe: size={len(data)} sha256={exe_hash}")
    image = pefile.PE(data=data, fast_load=False)
    if (
        int(image.OPTIONAL_HEADER.ImageBase) != EXPECTED_IMAGE_BASE
        or int(image.OPTIONAL_HEADER.SizeOfImage) != EXPECTED_IMAGE_SIZE
        or int(image.FILE_HEADER.TimeDateStamp) != EXPECTED_TIMESTAMP
    ):
        raise ValueError("exact-build PE metadata changed")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    rows: dict[str, Any] = {}
    decoded: dict[str, Any] = {}
    for name, (begin, end) in RANGES.items():
        blob = file_bytes(data, image, begin, end)
        observed_hash = digest(blob)
        if observed_hash != EXPECTED_RANGE_HASHES[name]:
            raise ValueError(f"{name} hash changed: {observed_hash}")
        decoded[name] = decode(decoder, data, image, begin, end)
        rows[name] = {
            "begin_rva": f"0x{begin:X}",
            "end_rva_exclusive": f"0x{end:X}",
            "size": end - begin,
            "sha256": observed_hash,
        }
    for name, calls in REQUIRED_CALLS.items():
        for call_rva, target_rva in calls.items():
            validate_call(decoded[name], call_rva, target_rva)

    has_text = "\n".join(row.op_str.lower() for row in decoded["has_truce"])
    getter_text = "\n".join(
        row.op_str.lower() for row in decoded["get_truce_end_date"]
    )
    normal_text = "\n".join(
        row.op_str.lower() for row in decoded["caddtruce_normal"]
    )
    for offset in ("+ 0x28", "+ 0x58"):
        if offset not in has_text or offset not in getter_text:
            raise ValueError(f"directional truce slot {offset} is no longer shared")
    if "eax, 0x28" not in normal_text or "eax, 0x58" not in normal_text:
        raise ValueError("CAddTruce directional slot selection changed")
    key = file_bytes(data, image, 0x43AC098, 0x43AC098 + 10)
    if key != b"has_truce\0":
        raise ValueError("has_truce script key moved")

    return {
        "schema": "xar.ck3.g2_actual_truce_expiry_abi.v1",
        "schema_version": 1,
        "status": "static-ready_live-pending",
        "read_only": True,
        "default_enabled": False,
        "build": {
            "product_version": "1.19.0.6",
            "executable_sha256": exe_hash,
            "file_size": len(data),
            "image_base": f"0x{EXPECTED_IMAGE_BASE:X}",
            "size_of_image": f"0x{EXPECTED_IMAGE_SIZE:X}",
            "pe_timestamp": f"0x{EXPECTED_TIMESTAMP:X}",
            "architecture": "x86_64-msvc",
        },
        "native_ranges": rows,
        "bindings": {
            "read_only_relation_lookup_rva": "0x2610840",
            "get_or_create_relation_rva": "0x26108F0",
            "has_truce_rva": "0x26631E0",
            "get_truce_end_date_rva": "0x2663250",
            "script_has_truce_evaluator_rva": "0x28852E0",
            "has_truce_key_rva": "0x43AC098",
            "caddtruce_duration_evaluator_rva": "0x3373000",
            "expired_slot_cleanup_rva": "0x2367C00",
            "directional_slot_offsets": ["0x28", "0x58"],
        },
        "temporal_split": {
            "before_application": (
                "CAddTruce evaluates a duration and computes a target date; "
                "that is a prediction, not persisted-state observation."
            ),
            "after_application": (
                "has_truce and get_truce_end_date lookup the existing pair "
                "relation and return the persisted owner-direction date."
            ),
        },
        "candidate": {
            "capability": "game.command.query-raiktor-actual-truce-expiry-v1-N",
            "owner_binding": "living current played character",
            "toward_binding": "caller-supplied full-generation CharacterID",
            "green_requires": [
                "native_has_truce=true",
                "two native getter reads agree",
                "same paused Snapshot before/after",
                "expiry_date_raw > current_date_raw",
            ],
            "ack_can_make_ready": False,
            "arbitrary_variable_lookup": False,
            "owner_arbitrary_selection": False,
            "toward_is_explicit_generation_safe_identity": True,
        },
        "source_sha256": source_hashes(native_root),
        "evidence_limits": [
            "No CK3 process was started or attached.",
            "The compiled provider is a default-off candidate, not production-live.",
            "A retained paused post-result frame is still required before promotion.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("g2_actual_truce_expiry_v1_abi.json"),
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    rendered = json.dumps(
        extract(args.exe.resolve(), root), ensure_ascii=False, indent=2
    ) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit("g2 actual truce-expiry ABI artifact is stale")
        print(f"OK: {args.output}")
        return 0
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
