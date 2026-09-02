#!/usr/bin/env python3
"""Freeze the exact direct callers and local reschedule boundary of the completion wrapper."""

from __future__ import annotations

import argparse
import bisect
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
from typing import Any

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_INS_CALL, X86_OP_IMM
import pefile


EXPECTED_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_SIZE = 95_206_008
WRAPPER_BEGIN_RVA = 0x3B9E030
WRAPPER_END_RVA = 0x3B9E266
WRAPPER_UNWIND_RVA = 0x4F101D4
WRAPPER_SHA256 = "C311284A4604FF68449A7C84CE8A607FA1175A2E6539F4F537FE28CF841CE249"
EXPECTED_DIRECT_CALL_COUNT = 618
EXPECTED_CALL_LIST_SHA256 = (
    "32B88FEACB2D43E2284C116C53A448D8C1F14FDBD4B2BFB97C0725622E861A8C"
)
EXPECTED_CALLER_FUNCTION_COUNT = 525
EXPECTED_OWNER_LIST_SHA256 = (
    "DFEF530E330DEEEC2154A5A8D826605A46EC46C8E670249162FC0586938715C5"
)
EXPECTED_DUAL_CALLER_FUNCTION_COUNT = 93
TASK_BUILDER_BEGIN_RVA = 0x3B9DBB0
TASK_BUILDER_END_RVA = 0x3B9DD4E
TASK_BUILDER_UNWIND_RVA = 0x4F10158
TASK_BUILDER_SHA256 = "3EC3E5D8366717B979C04125CBF8EAD0D2AF6D42DB9930E0CA48D8DB89FCF05A"
CONSUMER_ENQUEUE_BEGIN_RVA = 0x3B9EBD0
CONSUMER_ENQUEUE_END_RVA = 0x3B9ED27
CONSUMER_ENQUEUE_UNWIND_RVA = 0x4F1037C
CONSUMER_ENQUEUE_SHA256 = "2B217C2378A435E6BB34EECE8FB9C1E47EF16A209E940EC3E09B51F3FD616E25"

LOCAL_CALLERS = (
    (0x3B8A9C0, 0x3B8AC01, 0x4DA2E1C, 0x3B8AB00,
     "1C347CC97B68C148C2EAE2C1B60337499EC99B9529773FEC5465CC12FE4BC695"),
    (0x3B9B750, 0x3B9BA5F, 0x4CD5CF4, 0x3B9B87C,
     "A45E45B5638573AF4F2D93204FA0D4B898D4C0C28F7C70F67801C22A7111FF17"),
    (0x3B9DA60, 0x3B9DBAD, 0x4F10128, 0x3B9DB04,
     "E24EB11B82DABEBC05EC6B6493D8F1D10A70246A1CD3BE47FF05BCA9FFDF1BF3"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def bytes_at(data: bytes, image: pefile.PE, rva: int, size: int) -> bytes:
    offset = image.get_offset_from_rva(rva)
    value = data[offset : offset + size]
    if len(value) != size:
        raise ValueError(f"short read at RVA 0x{rva:X}")
    return value


def canonical_rva_digest(rvas: list[int]) -> str:
    value = json.dumps(
        [f"0x{rva:X}" for rva in rvas], separators=(",", ":")
    ).encode("ascii")
    return sha256(value)


def direct_relative_calls(raw: bytes, base_rva: int, target_rva: int) -> list[int]:
    result: list[int] = []
    offset = raw.find(b"\xE8")
    while offset >= 0 and offset + 5 <= len(raw):
        displacement = struct.unpack_from("<i", raw, offset + 1)[0]
        if base_rva + offset + 5 + displacement == target_rva:
            result.append(base_rva + offset)
        offset = raw.find(b"\xE8", offset + 1)
    return result


def extract(exe: Path) -> dict[str, Any]:
    source = exe.resolve()
    data = source.read_bytes()
    digest = sha256(data)
    if len(data) != EXPECTED_SIZE or digest != EXPECTED_SHA256:
        raise ValueError("source is not the pinned CK3 1.19.0.6 executable")
    image = pefile.PE(str(source), fast_load=False)
    text = image.sections[0]
    text_rva = int(text.VirtualAddress)
    call_rvas = direct_relative_calls(text.get_data(), text_rva, WRAPPER_BEGIN_RVA)
    if len(call_rvas) != EXPECTED_DIRECT_CALL_COUNT:
        raise ValueError("completion wrapper direct-call count changed")
    if canonical_rva_digest(call_rvas) != EXPECTED_CALL_LIST_SHA256:
        raise ValueError("completion wrapper direct-call list changed")

    pdata = sorted(
        (
            int(entry.struct.BeginAddress),
            int(entry.struct.EndAddress),
            int(entry.struct.UnwindData),
        )
        for entry in image.DIRECTORY_ENTRY_EXCEPTION
    )
    pdata_set = set(pdata)
    if (WRAPPER_BEGIN_RVA, WRAPPER_END_RVA, WRAPPER_UNWIND_RVA) not in pdata_set:
        raise ValueError("completion wrapper PDATA changed")
    wrapper_bytes = bytes_at(
        data, image, WRAPPER_BEGIN_RVA, WRAPPER_END_RVA - WRAPPER_BEGIN_RVA
    )
    if sha256(wrapper_bytes) != WRAPPER_SHA256:
        raise ValueError("completion wrapper bytes changed")
    frozen_functions = (
        (
            TASK_BUILDER_BEGIN_RVA,
            TASK_BUILDER_END_RVA,
            TASK_BUILDER_UNWIND_RVA,
            TASK_BUILDER_SHA256,
            "task builder",
        ),
        (
            CONSUMER_ENQUEUE_BEGIN_RVA,
            CONSUMER_ENQUEUE_END_RVA,
            CONSUMER_ENQUEUE_UNWIND_RVA,
            CONSUMER_ENQUEUE_SHA256,
            "consumer enqueue",
        ),
    )
    frozen_function_results: dict[str, dict[str, str]] = {}
    for begin, end, unwind, expected_hash, name in frozen_functions:
        if (begin, end, unwind) not in pdata_set:
            raise ValueError(f"{name} PDATA changed")
        function_bytes = bytes_at(data, image, begin, end - begin)
        if sha256(function_bytes) != expected_hash:
            raise ValueError(f"{name} bytes changed")
        frozen_function_results[name.replace(" ", "_")] = {
            "function_rva": f"0x{begin:X}",
            "function_end_rva_exclusive": f"0x{end:X}",
            "unwind_rva": f"0x{unwind:X}",
            "bytes_sha256": sha256(function_bytes),
        }

    starts = [entry[0] for entry in pdata]
    owners: list[tuple[int, int, int]] = []
    for call_rva in call_rvas:
        index = bisect.bisect_right(starts, call_rva) - 1
        if index < 0 or not (pdata[index][0] <= call_rva < pdata[index][1]):
            raise ValueError(f"call RVA 0x{call_rva:X} has no PDATA owner")
        owners.append(pdata[index])
    unique_owners = sorted(set(owners))
    owner_payload = [
        [f"0x{begin:X}", f"0x{end:X}", f"0x{unwind:X}"]
        for begin, end, unwind in unique_owners
    ]
    owner_digest = sha256(
        json.dumps(owner_payload, separators=(",", ":")).encode("ascii")
    )
    owner_counts = Counter(owners)
    dual_owners = sum(1 for count in owner_counts.values() if count == 2)
    if len(unique_owners) != EXPECTED_CALLER_FUNCTION_COUNT:
        raise ValueError("completion wrapper caller-function count changed")
    if owner_digest != EXPECTED_OWNER_LIST_SHA256:
        raise ValueError("completion wrapper caller-function list changed")
    if dual_owners != EXPECTED_DUAL_CALLER_FUNCTION_COUNT or any(
        count not in (1, 2) for count in owner_counts.values()
    ):
        raise ValueError("completion wrapper call multiplicity changed")

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    decoded_call_rvas: list[int] = []
    for begin, end, _ in unique_owners:
        owner_bytes = bytes_at(data, image, begin, end - begin)
        for instruction in decoder.disasm(owner_bytes, begin):
            if (
                instruction.id == X86_INS_CALL
                and len(instruction.operands) == 1
                and instruction.operands[0].type == X86_OP_IMM
                and instruction.operands[0].imm == WRAPPER_BEGIN_RVA
            ):
                decoded_call_rvas.append(instruction.address)
    if sorted(decoded_call_rvas) != call_rvas:
        raise ValueError("raw and instruction-bound direct-call lists disagree")

    local_results: list[dict[str, Any]] = []
    for begin, end, unwind, call_rva, expected_hash in LOCAL_CALLERS:
        if (begin, end, unwind) not in pdata_set or call_rva not in call_rvas:
            raise ValueError(f"local caller contract changed at 0x{call_rva:X}")
        owner_bytes = bytes_at(data, image, begin, end - begin)
        if sha256(owner_bytes) != expected_hash:
            raise ValueError(f"local caller bytes changed at 0x{begin:X}")
        local_results.append(
            {
                "function_rva": f"0x{begin:X}",
                "function_end_rva_exclusive": f"0x{end:X}",
                "unwind_rva": f"0x{unwind:X}",
                "bytes_sha256": sha256(owner_bytes),
                "call_rva": f"0x{call_rva:X}",
                "continuation_rva": f"0x{call_rva + 5:X}",
            }
        )

    signatures = {
        0x3B8A9ED: bytes.fromhex("8B520C448B4F08413BD1750C"),
        0x3B9B776: bytes.fromhex("8B790C8B59083BFB0F84C4020000"),
        0x3B9B784: bytes.fromhex("837918030F8497020000"),
        0x3B9B7B5: bytes.fromhex("4183FF010F8466020000"),
        0x3B9DAF6: bytes.fromhex("BD01000000448BCD488BD7488BCB"),
        0x3B9DBD7: bytes.fromhex("803D74F7390100740E83B9AC000000007E0541B401EB034532E4"),
        0x3B9DC74: bytes.fromhex("4889735833C0894360C74364010000004889436848894370"),
        0x3B9DCB3: bytes.fromhex("488958184C896820"),
        0x3B9DCCA: bytes.fromhex("4584E4740FF0FF4364488BD3498BCFE8F20E0000"),
        0x3B9DCDE: bytes.fromhex("488D542478498BCEE855214CFF"),
        0x3B9E0A6: bytes.fromhex("443805A5F23901740E443987AC0000007E0540B501EB034032ED"),
        0x3B9E214: bytes.fromhex("4084ED752F"),
        0x3B9E219: bytes.fromhex("498B1E4963460C488D3CC3483BDF741F"),
        0x3B9E230: bytes.fromhex("488B0B488BD6488B4918E811EDFFFF"),
        0x3B9E23F: bytes.fromhex("4883C308483BDF75E8"),
        0x3B9E248: bytes.fromhex("4C8D5C2460"),
        0x3B9E265: bytes.fromhex("C3"),
        0x3B9ECFA: bytes.fromhex("488B4E084923CE488B46104C892CC890498D460148894708"),
    }
    for rva, expected in signatures.items():
        if bytes_at(data, image, rva, len(expected)) != expected:
            raise ValueError(f"instruction signature changed at RVA 0x{rva:X}")

    return {
        "contract": "phase2-completion-wrapper-callers-extract-v1",
        "status": "static-synchronous-carrier-bound-runtime-owner-unresolved",
        "read_only": True,
        "source": {
            "path": str(source),
            "product_version": "1.19.0.6",
            "sha256": digest,
            "size_bytes": len(data),
        },
        "wrapper": {
            "function_rva": f"0x{WRAPPER_BEGIN_RVA:X}",
            "function_end_rva_exclusive": f"0x{WRAPPER_END_RVA:X}",
            "unwind_rva": f"0x{WRAPPER_UNWIND_RVA:X}",
            "bytes_sha256": sha256(wrapper_bytes),
            "entry_anchor_hex": bytes_at(data, image, WRAPPER_BEGIN_RVA, 15).hex().upper(),
            "return_rva": "0x3B9E265",
        },
        "direct_callers": {
            "callsite_count": len(call_rvas),
            "callsite_list_sha256": canonical_rva_digest(call_rvas),
            "call_rvas": [f"0x{rva:X}" for rva in call_rvas],
            "caller_function_count": len(unique_owners),
            "caller_function_list_sha256": owner_digest,
            "single_call_function_count": sum(
                1 for count in owner_counts.values() if count == 1
            ),
            "dual_call_function_count": dual_owners,
            "instruction_boundary_verified": True,
        },
        "local_callers": local_results,
        "local_conditions": {
            "0x3B8AB00": "call is skipped only by the empty-range equality at 0x3B8A9F4; surviving path reaches one call",
            "0x3B9B87C": "call requires nonempty range, mode != 3, and derived batch count != 1",
            "0x3B9DB04": "one unconditional wrapper call per 0x3B9DA60 invocation",
        },
        "task_carrier_routing": {
            "functions": frozen_function_results,
            "task_layout": {
                "callback_offset": "0x38",
                "owner_offset": "0x58",
                "state_offset": "0x60",
                "reference_count_offset": "0x64",
                "initial_state": 0,
                "initial_reference_count": 1,
            },
            "descriptor_task_pointer_offset": "0x18",
            "producer_list_append_call_rva": "0x3B9DCE6",
            "consumer_ring_enqueue_call_rva": "0x3B9DCD9",
            "consumer_ring_pointer_write_rva": "0x3B9ED05",
            "mode_matrix": [
                {
                    "mode": "synchronous",
                    "wrapper_bpl": 0,
                    "producer_list_appended": True,
                    "consumer_ring_enqueued": False,
                    "wrapper_producer_loop_runs": True,
                },
                {
                    "mode": "queued",
                    "wrapper_bpl": 1,
                    "producer_list_appended": True,
                    "consumer_ring_enqueued": True,
                    "wrapper_producer_loop_runs": False,
                },
            ],
            "conclusion": "the synchronous task published by the wrapper producer loop is carried by descriptor+0x18 in the fifth-argument producer list and is never enqueued into the consumer ring scanned at 0x3B9DEA7",
        },
        "prior_raw_live": {
            "runner_report_sha256": "DD6F61C871AD371F3BCE843BDA864E7D6317267AE839CB7A65EC399CCD4098A8",
            "terminal_evidence_index_sha256": "7E6B405A03C0E3F4A799F5836C6FACC4E6261E6C3E997886D0D01FFB32876487",
            "observer_installed": True,
            "observer_failure_code": 0,
            "raw_hit_count": 1908,
            "raw_state2_count": 0,
            "raw_state3_count": 0,
            "raw_last_callback": 0,
            "raw_last_callback_slot2_target": 0,
            "selected_event_count": 0,
            "database_completion_publish_observed": True,
            "database_completion_publish_rva": "0x3B9CFD7",
            "interpretation": "the consumer hook executed, but the synchronously published task was not a member of its consumer ring",
        },
        "post_publish_cfg": {
            "consumer_calls": ["0x3B9E10B", "0x3B9E175"],
            "producer_loop_begin_rva": "0x3B9E230",
            "producer_call_rva": "0x3B9E23A",
            "producer_loop_back_edge_rva": "0x3B9E246",
            "teardown_begin_rva": "0x3B9E248",
            "return_rva": "0x3B9E265",
            "consumer_reentry_after_producer": False,
            "wrapper_self_call": False,
            "external_reinvocation_required": True,
        },
        "next_observation": {
            "entry_rva": "0x3B9E030",
            "read": [
                "[RSP] return address before the 15-byte prologue anchor",
                "RCX scheduler owner",
                "[RSP+0x28] fifth-argument producer-list carrier",
            ],
            "mapping": "return_rva - 5 maps exactly to the frozen direct callsite list",
            "purpose": "bind the runtime caller and synchronous producer-list carrier without expanding 525 caller CFGs or observing the unrelated consumer ring again",
        },
        "limits": [
            "618 callsites across 525 functions do not statically identify the selected runtime caller",
            "no thread, OS wait, or wake primitive is inferred",
            "no CK3 process, public bridge, readiness gate, or production loader changed",
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
