#!/usr/bin/env python3
"""Freeze the bounded consumer of phase-two callback completion state."""

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
SLICE_BEGIN_RVA = 0x3B9A190
SLICE_END_RVA = 0x3B9E266
SLICE_SHA256 = "A96B0EDEFAE0770A756CA3AABECFD77FCA4BB9DB7A829264FAA169A6D7D08CCA"
CONSUMER_BEGIN_RVA = 0x3B9DD50
CONSUMER_END_RVA = 0x3B9E025
CONSUMER_UNWIND_RVA = 0x4F10198
CONSUMER_SHA256 = "084EEA10A407EA4A654FE02FB10E9435E3549EA4C3F48EDE29206CEE36480832"
WRAPPER_BEGIN_RVA = 0x3B9E030
WRAPPER_END_RVA = 0x3B9E266
WRAPPER_UNWIND_RVA = 0x4F101D4
WRAPPER_SHA256 = "C311284A4604FF68449A7C84CE8A607FA1175A2E6539F4F537FE28CF841CE249"
STATE_ZERO_READ_RVAS = (0x3B9A1EA, 0x3B9A241, 0x3B9B9A4, 0x3B9B9E0)
COMPLETION_READ_RVA = 0x3B9DEA7
COMPLETION_BRANCH_RVA = 0x3B9DEB0
RETIRE_BEGIN_RVA = 0x3B9DF63
FINAL_REF_BRANCH_RVA = 0x3B9DF70
RETIRED_PUBLISH_RVA = 0x3B9DF7B
CALLBACK_DESTROY_RVA = 0x3B9DF94
CALLBACK_CLEAR_RVA = 0x3B9DF97
OWNER_RELEASE_RVA = 0x3B9DFAA
CONSUMER_CALL_RVAS = (0x3B9E10B, 0x3B9E175)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def bytes_at(data: bytes, image: pefile.PE, rva: int, size: int) -> bytes:
    offset = image.get_offset_from_rva(rva)
    value = data[offset : offset + size]
    if len(value) != size:
        raise ValueError(f"short read at RVA 0x{rva:X}")
    return value


def direct_calls(raw: bytes, base_rva: int, target_rva: int) -> list[int]:
    result: list[int] = []
    for offset in range(len(raw) - 5):
        if raw[offset] != 0xE8:
            continue
        displacement = struct.unpack_from("<i", raw, offset + 1)[0]
        if base_rva + offset + 5 + displacement == target_rva:
            result.append(base_rva + offset)
    return result


def extract(exe: Path) -> dict[str, Any]:
    source = exe.resolve()
    data = source.read_bytes()
    digest = sha256(data)
    if len(data) != EXPECTED_SIZE or digest != EXPECTED_SHA256:
        raise ValueError("source is not the pinned CK3 1.19.0.6 executable")
    image = pefile.PE(str(source), fast_load=False)

    slice_bytes = bytes_at(
        data, image, SLICE_BEGIN_RVA, SLICE_END_RVA - SLICE_BEGIN_RVA
    )
    consumer_bytes = bytes_at(
        data, image, CONSUMER_BEGIN_RVA, CONSUMER_END_RVA - CONSUMER_BEGIN_RVA
    )
    wrapper_bytes = bytes_at(
        data, image, WRAPPER_BEGIN_RVA, WRAPPER_END_RVA - WRAPPER_BEGIN_RVA
    )
    if sha256(slice_bytes) != SLICE_SHA256:
        raise ValueError("bounded scheduler slice changed")
    if sha256(consumer_bytes) != CONSUMER_SHA256:
        raise ValueError("completion consumer bytes changed")
    if sha256(wrapper_bytes) != WRAPPER_SHA256:
        raise ValueError("completion wrapper bytes changed")

    pdata = {
        (
            int(entry.struct.BeginAddress),
            int(entry.struct.EndAddress),
            int(entry.struct.UnwindData),
        )
        for entry in image.DIRECTORY_ENTRY_EXCEPTION
    }
    expected_pdata = {
        (CONSUMER_BEGIN_RVA, CONSUMER_END_RVA, CONSUMER_UNWIND_RVA),
        (WRAPPER_BEGIN_RVA, WRAPPER_END_RVA, WRAPPER_UNWIND_RVA),
    }
    if not expected_pdata.issubset(pdata):
        raise ValueError("consumer/wrapper PDATA changed")

    signatures = {
        0x3B9A1EA: bytes.fromhex("8B416085C07525"),
        0x3B9A241: bytes.fromhex("8B4160488B572085C0"),
        0x3B9B9A4: bytes.fromhex("8B416085C0750C"),
        0x3B9B9E0: bytes.fromhex("8B416085C0750C"),
        COMPLETION_READ_RVA: bytes.fromhex("8B436083C0FE83F801"),
        COMPLETION_BRANCH_RVA: bytes.fromhex("0F86AD000000"),
        RETIRE_BEGIN_RVA: bytes.fromhex("B8FFFFFFFFF00FC14364"),
        FINAL_REF_BRANCH_RVA: bytes.fromhex("0F85EA FE FF FF".replace(" ", "")),
        RETIRED_PUBLISH_RVA: bytes.fromhex("874360"),
        CALLBACK_DESTROY_RVA: bytes.fromhex("FF5020"),
        CALLBACK_CLEAR_RVA: bytes.fromhex("4C897338"),
        OWNER_RELEASE_RVA: bytes.fromhex("FF5010"),
    }
    for rva, expected in signatures.items():
        if bytes_at(data, image, rva, len(expected)) != expected:
            raise ValueError(f"instruction signature changed at RVA 0x{rva:X}")

    bounded_state_zero_reads = [
        SLICE_BEGIN_RVA + offset
        for offset in range(len(slice_bytes) - 2)
        if slice_bytes[offset : offset + 3] == bytes.fromhex("8B4160")
    ]
    bounded_completion_reads = [
        SLICE_BEGIN_RVA + offset
        for offset in range(len(slice_bytes) - 2)
        if slice_bytes[offset : offset + 3] == bytes.fromhex("8B4360")
    ]
    if bounded_state_zero_reads != list(STATE_ZERO_READ_RVAS):
        raise ValueError("bounded state-zero reads changed")
    if bounded_completion_reads != [COMPLETION_READ_RVA]:
        raise ValueError("bounded completion consumer read changed")

    text = image.sections[0]
    calls = direct_calls(
        text.get_data(), int(text.VirtualAddress), CONSUMER_BEGIN_RVA
    )
    if calls != list(CONSUMER_CALL_RVAS):
        raise ValueError("completion consumer direct callers changed")

    return {
        "contract": "phase2-completion-consumer-extract-v1",
        "status": "static-completion-consumer-bound",
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
        "bounded_slice": {
            "begin_rva": f"0x{SLICE_BEGIN_RVA:X}",
            "end_rva_exclusive": f"0x{SLICE_END_RVA:X}",
            "bytes_sha256": sha256(slice_bytes),
            "state_zero_gate_read_rvas": [
                f"0x{rva:X}" for rva in bounded_state_zero_reads
            ],
            "completion_consumer_read_rvas": [
                f"0x{rva:X}" for rva in bounded_completion_reads
            ],
        },
        "consumer": {
            "function_rva": f"0x{CONSUMER_BEGIN_RVA:X}",
            "function_end_rva_exclusive": f"0x{CONSUMER_END_RVA:X}",
            "unwind_rva": f"0x{CONSUMER_UNWIND_RVA:X}",
            "bytes_sha256": sha256(consumer_bytes),
            "direct_call_rvas": [f"0x{rva:X}" for rva in calls],
            "state_read_rva": f"0x{COMPLETION_READ_RVA:X}",
            "complete_values": [2, 3],
            "completion_branch_rva": f"0x{COMPLETION_BRANCH_RVA:X}",
            "reference_count_offset": "0x64",
            "retired_value": 3,
            "retired_publish_rva": f"0x{RETIRED_PUBLISH_RVA:X}",
            "callback_offset": "0x38",
            "callback_destroy_rva": f"0x{CALLBACK_DESTROY_RVA:X}",
            "callback_clear_rva": f"0x{CALLBACK_CLEAR_RVA:X}",
            "owner_offset": "0x58",
            "owner_release_rva": f"0x{OWNER_RELEASE_RVA:X}",
        },
        "wrapper": {
            "function_rva": f"0x{WRAPPER_BEGIN_RVA:X}",
            "function_end_rva_exclusive": f"0x{WRAPPER_END_RVA:X}",
            "unwind_rva": f"0x{WRAPPER_UNWIND_RVA:X}",
            "bytes_sha256": sha256(wrapper_bytes),
            "consumer_call_rvas": [f"0x{rva:X}" for rva in calls],
        },
        "observation_entry": {
            "rva": f"0x{COMPLETION_READ_RVA:X}",
            "read": [
                "RBX task pointer",
                "dword [RBX+0x60] state",
                "qword [RBX+0x38] callback",
                "callback vtable slot 2 target",
            ],
            "selected_task_filter": "callback slot 2 target RVA equals 0x88B480",
            "mutation_required": False,
            "live_required_for_static_contract": False,
        },
        "conclusion": {
            "completion_release": "consumer poll classifies state 2/3, retires final reference, destroys callback, and releases task storage",
            "explicit_os_wait_or_signal_found": False,
            "next_distinct_stop_point_rva": f"0x{COMPLETION_READ_RVA:X}",
        },
        "limits": [
            "the bounded slice identifies polling consumption, not an OS wait primitive",
            "the generic executor's 1267 callers were not expanded",
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
