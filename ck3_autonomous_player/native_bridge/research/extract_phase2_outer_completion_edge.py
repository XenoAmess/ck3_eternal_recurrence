#!/usr/bin/env python3
"""Freeze the bounded completion-state edge reached after RVA 0x88B648."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
from typing import Any

import pefile


EXPECTED_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_SIZE = 95_206_008
LOGICAL_ENTRY_RVA = 0x3B9CF50
LOGICAL_END_RVA = 0x3B9D04D
LOGICAL_BYTES_SHA256 = (
    "63B6E134E77569D6E261BD9B99091BCEF5D41F531F5F67592C64BC890EDAEA83"
)
CONTINUATION_RVA = 0x3B9CFD2
COMPLETION_PUBLISH_RVA = 0x3B9CFD7
TRUE_RETURN_RVA = 0x3B9D039
BUSY_RETURN_RVA = 0x3B9D046
NULL_CALLBACK_TRAP_RVA = 0x3B9D047
CHAINED_RANGES = (
    (0x3B9CF50, 0x3B9CF72, 0x4C3AB8C),
    (0x3B9CF72, 0x3B9CFCC, 0x4F1003C),
    (0x3B9CFCC, 0x3B9D04D, 0x4F10050),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def bytes_at(data: bytes, image: pefile.PE, rva: int, size: int) -> bytes:
    offset = image.get_offset_from_rva(rva)
    value = data[offset : offset + size]
    if len(value) != size:
        raise ValueError(f"short read at RVA 0x{rva:X}")
    return value


def scan_direct_calls(raw: bytes, base_rva: int, target_rva: int) -> list[int]:
    hits: list[int] = []
    for offset in range(len(raw) - 5):
        if raw[offset] != 0xE8:
            continue
        displacement = struct.unpack_from("<i", raw, offset + 1)[0]
        if base_rva + offset + 5 + displacement == target_rva:
            hits.append(base_rva + offset)
    return hits


def extract(exe: Path) -> dict[str, Any]:
    source = exe.resolve()
    data = source.read_bytes()
    digest = sha256(data)
    if len(data) != EXPECTED_SIZE or digest != EXPECTED_SHA256:
        raise ValueError("source is not the pinned CK3 1.19.0.6 executable")
    image = pefile.PE(str(source), fast_load=False)

    logical_bytes = bytes_at(
        data, image, LOGICAL_ENTRY_RVA, LOGICAL_END_RVA - LOGICAL_ENTRY_RVA
    )
    if sha256(logical_bytes) != LOGICAL_BYTES_SHA256:
        raise ValueError("logical owner bytes changed")
    pdata = {
        (
            int(entry.struct.BeginAddress),
            int(entry.struct.EndAddress),
            int(entry.struct.UnwindData),
        )
        for entry in image.DIRECTORY_ENTRY_EXCEPTION
    }
    if not all(row in pdata for row in CHAINED_RANGES):
        raise ValueError("chained PDATA ranges changed")

    signatures = {
        0x3B9CFBE: bytes.fromhex("488B4B38488B7424384885C9747B"),
        0x3B9CFCC: bytes.fromhex("488B01FF5010"),
        CONTINUATION_RVA: bytes.fromhex("B802000000"),
        COMPLETION_PUBLISH_RVA: bytes.fromhex("874360"),
        0x3B9CFDA: bytes.fromhex("E861702800488BF8E8F9401300"),
        0x3B9D014: bytes.fromhex("482B4370"),
        0x3B9D02A: bytes.fromhex("F20F114368"),
        TRUE_RETURN_RVA: bytes.fromhex("C3"),
        BUSY_RETURN_RVA: bytes.fromhex("C3"),
        NULL_CALLBACK_TRAP_RVA: bytes.fromhex("E83C5A2800CC"),
    }
    for rva, expected in signatures.items():
        if bytes_at(data, image, rva, len(expected)) != expected:
            raise ValueError(f"instruction signature changed at RVA 0x{rva:X}")

    text = image.sections[0]
    direct_calls = scan_direct_calls(
        text.get_data(), int(text.VirtualAddress), LOGICAL_ENTRY_RVA
    )
    if len(direct_calls) != 1267:
        raise ValueError("generic logical owner direct-call count changed")

    return {
        "contract": "phase2-outer-completion-edge-extract-v1",
        "status": "static-post-init-edge-bound",
        "read_only": True,
        "production_installed": False,
        "production_abi_changed": False,
        "readiness_promotion": False,
        "source": {
            "path": str(source),
            "product_version": "1.19.0.6",
            "sha256": digest,
            "size_bytes": len(data),
        },
        "runtime_entry": {
            "prior_selected_outer_return_rva": "0x88B648",
            "continuation_rva": f"0x{CONTINUATION_RVA:X}",
        },
        "logical_owner": {
            "entry_rva": f"0x{LOGICAL_ENTRY_RVA:X}",
            "end_rva_exclusive": f"0x{LOGICAL_END_RVA:X}",
            "bytes_sha256": sha256(logical_bytes),
            "chained_pdata": [
                {
                    "begin_rva": f"0x{begin:X}",
                    "end_rva_exclusive": f"0x{end:X}",
                    "unwind_rva": f"0x{unwind:X}",
                }
                for begin, end, unwind in CHAINED_RANGES
            ],
            "direct_relative_caller_count": len(direct_calls),
            "caller_scope": "generic helper; callers deliberately not expanded",
        },
        "bounded_cfg": {
            "callback_receiver": "[RBX+0x38]",
            "callback_dispatch_rva": "0x3B9CFCF",
            "callback_slot": 2,
            "callback_return_continuation_rva": f"0x{CONTINUATION_RVA:X}",
            "state_offset": "0x60",
            "completion_value": 2,
            "completion_publish_rva": f"0x{COMPLETION_PUBLISH_RVA:X}",
            "completion_instruction": "xchg dword ptr [rbx+0x60], eax",
            "start_time_offset": "0x70",
            "elapsed_time_offset": "0x68",
            "elapsed_store_rva": "0x3B9D02A",
            "true_return_rva": f"0x{TRUE_RETURN_RVA:X}",
            "busy_return_rva": f"0x{BUSY_RETURN_RVA:X}",
            "null_callback_trap_rva": f"0x{NULL_CALLBACK_TRAP_RVA:X}",
        },
        "conclusion": {
            "closed": "direct post-init completion-state publication",
            "next_distinct_stop_point_rva": f"0x{COMPLETION_PUBLISH_RVA:X}",
            "additional_live_required": False,
        },
        "limits": [
            "state value 2 is bound as callback-complete within this helper only",
            "the 1267 generic callers are not a unique loader owner and were not expanded",
            "no CK3 process was started and no public bridge or readiness changed",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(extract(args.exe), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
