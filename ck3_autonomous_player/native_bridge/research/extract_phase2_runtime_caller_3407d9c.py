#!/usr/bin/env python3
"""Freeze the exact runtime wrapper caller and its synchronous carrier lifetime."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
from typing import Any

import pefile


EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_EXE_SIZE = 95_206_008
EXPECTED_RUNNER_SHA256 = (
    "0556C55EF7D26535A8D9B5F0199BCA32CDB178323DE95F48678B2D38B4683BE7"
)
EXPECTED_POSTPROCESS_SHA256 = (
    "D74E8345B51E87F73B5DF6C65B7766B4618748FCE0FD8DFD9CD374D736B054F8"
)

CALLER_BEGIN_RVA = 0x3407C70
CALLER_END_RVA = 0x3407F80
CALLER_UNWIND_RVA = 0x4C3DD40
CALLER_SHA256 = "A262CC81AFD1235583E2AA6618D48106CA1557BB227AF6A0DAB63CBC60000F17"
WRAPPER_CALL_RVA = 0x3407D9C
WRAPPER_RVA = 0x3B9E030
CONTINUATION_RVA = 0x3407DA1
SCHEDULER_OWNER_GLOBAL_RVA = 0x5772E98
POST_RETURN_SEAM_RVA = 0x3407DA1
POST_RETURN_SEAM_CONTINUE_RVA = 0x3407DAF
POST_RETURN_SEAM_BYTES = 14
POST_RETURN_SEAM_SHA256 = (
    "65A4228B227424B730FA6F7A84DD15602E2063FD9227733901135CF00E4805A4"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def bytes_at(data: bytes, image: pefile.PE, rva: int, size: int) -> bytes:
    offset = image.get_offset_from_rva(rva)
    value = data[offset : offset + size]
    if len(value) != size:
        raise ValueError(f"short read at RVA 0x{rva:X}")
    return value


def require_bytes(
    data: bytes, image: pefile.PE, rva: int, expected_hex: str
) -> None:
    expected = bytes.fromhex(expected_hex)
    if bytes_at(data, image, rva, len(expected)) != expected:
        raise ValueError(f"instruction signature changed at RVA 0x{rva:X}")


def extract(
    exe: Path, runner_report: Path, postprocess: Path
) -> dict[str, Any]:
    exe_data = exe.resolve().read_bytes()
    if len(exe_data) != EXPECTED_EXE_SIZE or sha256(exe_data) != EXPECTED_EXE_SHA256:
        raise ValueError("source is not the pinned CK3 1.19.0.6 executable")
    runner_data = runner_report.resolve().read_bytes()
    postprocess_data = postprocess.resolve().read_bytes()
    if sha256(runner_data) != EXPECTED_RUNNER_SHA256:
        raise ValueError("wrapper-entry runner report identity changed")
    if sha256(postprocess_data) != EXPECTED_POSTPROCESS_SHA256:
        raise ValueError("wrapper-entry postprocess identity changed")
    live = json.loads(postprocess_data.decode("utf-8"))
    if live.get("status") != "GREEN" or live.get("decision") != (
        "entry-caller-owner-carrier-observed"
    ):
        raise ValueError("wrapper-entry postprocess is not the frozen GREEN result")
    heartbeat = live.get("heartbeat", {})
    caller_distribution = live.get("caller", {}).get(
        "sampled_last_value_distribution", []
    )
    owner_distribution = live.get("scheduler_owner", {}).get(
        "sampled_last_value_distribution", []
    )
    carrier_distribution = live.get("producer_list_carrier", {}).get(
        "sampled_last_value_distribution", []
    )
    thread_distribution = live.get("context", {}).get("thread_distribution", [])
    expected_live = (
        heartbeat.get("final_entry_count") == 1220
        and caller_distribution == [{"value": WRAPPER_CALL_RVA, "sample_count": 1}]
        and owner_distribution == [{"value": 0x22ED9921A00, "sample_count": 1}]
        and carrier_distribution == [{"value": 0xF282FFEE70, "sample_count": 1}]
        and thread_distribution == [{"value": 44900, "sample_count": 1}]
    )
    if not expected_live:
        raise ValueError("wrapper-entry live tuple changed")

    image = pefile.PE(str(exe.resolve()), fast_load=False)
    pdata = {
        (
            int(entry.struct.BeginAddress),
            int(entry.struct.EndAddress),
            int(entry.struct.UnwindData),
        )
        for entry in image.DIRECTORY_ENTRY_EXCEPTION
    }
    if (CALLER_BEGIN_RVA, CALLER_END_RVA, CALLER_UNWIND_RVA) not in pdata:
        raise ValueError("runtime caller PDATA changed")
    caller_bytes = bytes_at(
        exe_data, image, CALLER_BEGIN_RVA, CALLER_END_RVA - CALLER_BEGIN_RVA
    )
    if sha256(caller_bytes) != CALLER_SHA256:
        raise ValueError("runtime caller bytes changed")

    displacement = struct.unpack(
        "<i", bytes_at(exe_data, image, WRAPPER_CALL_RVA + 1, 4)
    )[0]
    if bytes_at(exe_data, image, WRAPPER_CALL_RVA, 1) != b"\xE8" or (
        WRAPPER_CALL_RVA + 5 + displacement != WRAPPER_RVA
    ):
        raise ValueError("runtime callsite no longer calls the wrapper")

    signatures = {
        0x3407C90: "4C8BF2488BF18B790C8B59083BFB0F84C5020000",
        0x3407CA4: "837918030F8497020000",
        0x3407CAE: "8B41142BC3FFC803C799F77914",
        0x3407CC1: "4883C110488D95580200003901480F4CD1448B3A",
        0x3407D37: "488D8DE0000000E82D0341FD90",
        0x3407D44: "418BD7488D8DE0000000E8ED0041FD",
        0x3407D53: "488D05C6510D014889442430488D85A00000004889442438",
        0x3407D75: "488B85600200004889442428488D85E00000004889442420",
        0x3407D8D: "458BCF488D542430488B0DFCB03602",
        0x3407DA1: "90488B4C24684885C97411488B01",
        0x3407DBD: "4533FF8B5584488D4C247885D27515",
        0x3407DCC: "488D95E0000000E8A8FD7500",
        0x3407DE1: "486385EC0000004C8B85E00000004D8D0CC0E8E8FF7500",
        0x3407E14: "488BB5E00000004885F67470",
        0x3407E90: "48635584488B7C2478488D1CD7483BDF7442",
        0x3407EB4: "488B03488B48184885C97417488B50208B416085C0750C",
        0x3407EF0: "488B1F488B4B184885C97420488B53208B416085C0750C",
        0x3407F13: "488B4B18E804017600",
        0x3407F2D: "488BCFE84B0041FD",
    }
    for rva, expected_hex in signatures.items():
        require_bytes(exe_data, image, rva, expected_hex)

    scheduler_load = bytes_at(exe_data, image, 0x3407D95, 7)
    scheduler_displacement = struct.unpack("<i", scheduler_load[3:7])[0]
    scheduler_global_rva = 0x3407D9C + scheduler_displacement
    if scheduler_global_rva != SCHEDULER_OWNER_GLOBAL_RVA:
        raise ValueError("scheduler-owner global changed")
    seam_bytes = bytes_at(
        exe_data, image, POST_RETURN_SEAM_RVA, POST_RETURN_SEAM_BYTES
    )
    if sha256(seam_bytes) != POST_RETURN_SEAM_SHA256:
        raise ValueError("post-return seam changed")

    return {
        "contract": "phase2-runtime-caller-3407d9c-static-extract-v1",
        "status": "runtime-caller-and-post-return-carrier-bound",
        "read_only": True,
        "source": {
            "path": str(exe.resolve()),
            "product_version": "1.19.0.6",
            "sha256": sha256(exe_data),
            "size_bytes": len(exe_data),
        },
        "live_evidence": {
            "runner_report": str(runner_report.resolve()),
            "runner_report_sha256": sha256(runner_data),
            "postprocess": str(postprocess.resolve()),
            "postprocess_sha256": sha256(postprocess_data),
            "entry_count": 1220,
            "sampling_boundary": "one final heartbeat; this is the last sampled caller, not a lossless 1220-entry distribution",
            "last_callsite_rva": f"0x{WRAPPER_CALL_RVA:X}",
            "last_scheduler_owner": "0x22ED9921A00",
            "last_producer_list": "0xF282FFEE70",
            "last_thread_id": 44900,
        },
        "caller": {
            "function_rva": f"0x{CALLER_BEGIN_RVA:X}",
            "function_end_rva_exclusive": f"0x{CALLER_END_RVA:X}",
            "unwind_rva": f"0x{CALLER_UNWIND_RVA:X}",
            "bytes_sha256": sha256(caller_bytes),
            "wrapper_call_rva": f"0x{WRAPPER_CALL_RVA:X}",
            "continuation_rva": f"0x{CONTINUATION_RVA:X}",
        },
        "call_arguments": {
            "rcx": "scheduler owner loaded from pointer global RVA 0x5772E98",
            "rdx": "address of caller-local object at [RSP+0x30]",
            "r8": "third argument passed through from caller entry",
            "r9d": "derived batch count r15d; path excludes empty range, mode 3, and count 1",
            "fifth": "address of caller-local producer-list object [RBP+0xE0]",
            "sixth": "caller fifth stack argument saved at [RBP+0x260]",
            "producer_list_layout": {
                "begin_pointer_offset": "0x0",
                "count_offset": "0xC",
                "element": "descriptor pointer",
                "descriptor_task_offset": "0x18",
                "descriptor_owner_offset": "0x20",
            },
        },
        "post_return_lifetime": {
            "continuation": "0x3407DA1",
            "temporary_argument_destroy": "0x3407DA2..0x3407DBA",
            "producer_to_destination_empty_path": "0x3407DCC call 0x3B67B80",
            "producer_to_destination_nonempty_path": "0x3407DE1..0x3407E0D via 0x3B67DE0 then 0x817F80",
            "producer_storage_release": "0x3407E14..0x3407E89",
            "destination_reverse_state0_retry": "0x3407E90..0x3407ED7",
            "destination_forward_state0_retry_and_release": "0x3407EE4..0x3407F23",
            "destination_storage_release": "0x3407F2D call 0x817F80",
            "normal_function_return": "0x3407F7F",
        },
        "next_observer": {
            "patch_rva": f"0x{POST_RETURN_SEAM_RVA:X}",
            "continue_rva": f"0x{POST_RETURN_SEAM_CONTINUE_RVA:X}",
            "patch_bytes": POST_RETURN_SEAM_BYTES,
            "anchor_hex": seam_bytes.hex().upper(),
            "anchor_sha256": sha256(seam_bytes),
            "read": [
                "producer-list carrier address RBP+0xE0",
                "[carrier+0x0] descriptor-array begin",
                "[carrier+0xC] descriptor count",
                "each descriptor +0x18 task and +0x20 owner",
                "task +0x38 callback, callback vslot2, task +0x60 state",
            ],
            "filter": "callback vslot2 target module+0x88B480",
            "purpose": "observe the selected synchronous task in its caller-local producer carrier immediately after wrapper return, before transfer/retry/release",
        },
        "limits": [
            "the final heartbeat identifies the last sampled callsite only",
            "no thread or OS-wait primitive is inferred",
            "no CK3 process, public ABI, readiness gate, or production loader changed",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--runner-report", type=Path, required=True)
    parser.add_argument("--postprocess", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(
        extract(args.exe, args.runner_report, args.postprocess),
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
