#!/usr/bin/env python3
"""Freeze the exact CK3 identity and semantics of callback slot2 RVA 0x817C20."""

from __future__ import annotations

import argparse
from collections import Counter
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
    "109CB334D56B6A50F75F8AA8C4A9EBD349B2703A28ED71694E90E0262BE15471"
)
ENTRY_RVA = 0x817C20
END_RVA = 0x817C9C
FUNCTION_SHA256 = "3EFBF1BCD7A64FF8ACD10A7E6E954D9561DB8C77EE755171CB284F3E81F76C3C"
PDATA = (
    (0x817C20, 0x817C43, 0x4C3DF7C, 0),
    (0x817C43, 0x817C8E, 0x4C3DF8C, 4),
    (0x817C8E, 0x817C9C, 0x4C3DFA0, 4),
)
EXPECTED_RTTI_VTABLE_COUNT = 278
EXPECTED_RTTI_ROWS_SHA256 = (
    "BCE3AAEEA887157CC07FE219D6BDC545C1EB63883C993C4EC096530AE96C7222"
)
LOADER_CALLBACK_RVA = 0x88B480
TRUE_PRODUCER_TASK_RVA = 0x3B9CFD2
TRUE_PRODUCER_PUBLISH_RVA = 0x3B9CFD7


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def bytes_at(data: bytes, image: pefile.PE, rva: int, size: int) -> bytes:
    offset = image.get_offset_from_rva(rva)
    value = data[offset : offset + size]
    if len(value) != size:
        raise ValueError(f"short read at RVA 0x{rva:X}")
    return value


def c_string(data: bytes, image: pefile.PE, rva: int, maximum: int = 8192) -> str:
    raw = bytes_at(data, image, rva, maximum)
    end = raw.find(b"\0")
    if end < 0:
        raise ValueError(f"unterminated string at RVA 0x{rva:X}")
    return raw[:end].decode("ascii")


def enumerate_rtti_vtables(
    data: bytes, image: pefile.PE, target_rva: int
) -> list[dict[str, Any]]:
    image_base = int(image.OPTIONAL_HEADER.ImageBase)
    needle = struct.pack("<Q", image_base + target_rva)
    rows: list[dict[str, Any]] = []
    for section in image.sections:
        raw = section.get_data()
        offset = 0
        while True:
            found = raw.find(needle, offset)
            if found < 0:
                break
            slot_rva = int(section.VirtualAddress) + found
            vtable_rva = slot_rva - 16
            try:
                col_va = struct.unpack("<Q", bytes_at(data, image, vtable_rva - 8, 8))[0]
                col_rva = col_va - image_base
                signature, object_offset, cd_offset, type_rva, hierarchy_rva, self_rva = struct.unpack(
                    "<IIIIII", bytes_at(data, image, col_rva, 24)
                )
                type_name = c_string(data, image, type_rva + 16)
            except (ValueError, struct.error, UnicodeDecodeError, pefile.PEFormatError):
                offset = found + 1
                continue
            if signature == 1 and self_rva == col_rva and type_name.startswith(".?AV"):
                rows.append({
                    "vtable_rva": vtable_rva,
                    "slot2_rva": slot_rva,
                    "complete_object_locator_rva": col_rva,
                    "object_offset": object_offset,
                    "constructor_displacement_offset": cd_offset,
                    "type_descriptor_rva": type_rva,
                    "class_hierarchy_rva": hierarchy_rva,
                    "type_name": type_name,
                })
            offset = found + 1
    return sorted(rows, key=lambda row: row["vtable_rva"])


def extract(exe: Path, runner_report: Path, postprocess: Path) -> dict[str, Any]:
    exe_data = exe.resolve().read_bytes()
    if len(exe_data) != EXPECTED_EXE_SIZE or sha256(exe_data) != EXPECTED_EXE_SHA256:
        raise ValueError("source is not the pinned CK3 1.19.0.6 executable")
    runner_data = runner_report.resolve().read_bytes()
    if sha256(runner_data) != EXPECTED_RUNNER_SHA256:
        raise ValueError("runner report is not the frozen full list-identity live")
    postprocess_data = postprocess.resolve().read_bytes()
    typed = json.loads(postprocess_data.decode("utf-8"))
    expected_live = (
        typed.get("status") == "GREEN"
        and typed.get("decision") == "complete-list-excludes-loader-callback"
        and typed.get("observer", {}).get("scan_count") == 27
        and typed.get("identity", {}).get("slot2_rva_distribution")
        == [{"rva": "0x817C20", "count": 27}]
        and typed.get("identity", {}).get("owner_distribution")
        == [{"owner": "0x2686F59B440", "count": 27}]
        and typed.get("identity", {}).get("state_distribution")
        == [{"state": 0, "count": 2}, {"state": 1, "count": 25}]
    )
    if not expected_live:
        raise ValueError("typed list-identity tuple changed")

    image = pefile.PE(data=exe_data, fast_load=False)
    function = bytes_at(exe_data, image, ENTRY_RVA, END_RVA - ENTRY_RVA)
    if sha256(function) != FUNCTION_SHA256:
        raise ValueError("0x817C20 logical function bytes changed")
    pdata = {
        (int(entry.struct.BeginAddress), int(entry.struct.EndAddress), int(entry.struct.UnwindData))
        for entry in image.DIRECTORY_ENTRY_EXCEPTION
    }
    unwind_rows: list[dict[str, Any]] = []
    for begin, end, unwind, expected_flags in PDATA:
        if (begin, end, unwind) not in pdata:
            raise ValueError(f"PDATA fragment changed at RVA 0x{begin:X}")
        first = bytes_at(exe_data, image, unwind, 1)[0]
        version, flags = first & 7, first >> 3
        if version != 1 or flags != expected_flags:
            raise ValueError(f"unwind flags changed at RVA 0x{unwind:X}")
        unwind_rows.append({
            "begin_rva": f"0x{begin:X}", "end_rva_exclusive": f"0x{end:X}",
            "unwind_rva": f"0x{unwind:X}", "unwind_version": version,
            "unwind_flags": flags,
            "chain_info": flags == 4,
        })

    signatures = {
        0x817C2D: "488B7108448B761C418BDE8B6E14",
        0x817C3B: "F00FC11E3BDD7D4B",
        0x817C50: "428D04338BFD3BC50F4CF83BDF741B",
        0x817C60: "488B46284863D3488B08488B0CD1488B01FF5008",
        0x817C7E: "418BDEF00FC11E3BDD7CC7",
        0x817C8E: "488B5C24504883C420415E5E5DC3",
    }
    for rva, expected_hex in signatures.items():
        expected = bytes.fromhex(expected_hex)
        if bytes_at(exe_data, image, rva, len(expected)) != expected:
            raise ValueError(f"semantic signature changed at RVA 0x{rva:X}")

    rows = enumerate_rtti_vtables(exe_data, image, ENTRY_RVA)
    if len(rows) != EXPECTED_RTTI_VTABLE_COUNT:
        raise ValueError("shared 0x817C20 RTTI vtable count changed")
    expected_prefix = ".?AV?$_Func_impl_no_alloc@V?$reference_wrapper@U?$SPdxParallelFor@U?$SPdxParallelForOverArrayOperatorFromCallTraits@"
    if any(not row["type_name"].startswith(expected_prefix) for row in rows):
        raise ValueError("unexpected RTTI owner outside SPdxParallelForOverArray")
    canonical = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    if sha256(canonical) != EXPECTED_RTTI_ROWS_SHA256:
        raise ValueError("shared 0x817C20 RTTI identity rows changed")
    tokens = (
        "JominiCachedIcon", "PlayableDifficultyInfo", "GameRule",
        "JominiScriptedGui", "JominiScriptedEffectTemplate", "JominiLoadScreen",
        "JominiNotificationType", "Portrait", "Culture", "Activity",
    )
    token_counts = {
        token: sum(token in row["type_name"] for row in rows)
        for token in tokens
    }
    representative_indices = sorted({0, 1, len(rows) // 2, len(rows) - 1})

    return {
        "contract": "phase2-slot2-817c20-static-identity-v1",
        "status": "static-generic-task-domain-bound-owner-specialization-unresolved",
        "read_only": True,
        "source": {
            "path": str(exe.resolve()), "product_version": "1.19.0.6",
            "sha256": sha256(exe_data), "size_bytes": len(exe_data),
        },
        "live_evidence": {
            "runner_report": str(runner_report.resolve()),
            "runner_report_sha256": sha256(runner_data),
            "postprocess": str(postprocess.resolve()),
            "postprocess_sha256": sha256(postprocess_data),
            "list_count": 27, "slot2_rva": "0x817C20",
            "slot2_count": 27, "owner": "0x2686F59B440",
            "state_counts": {"0": 2, "1": 25},
            "task_equals_callback_count": 27,
            "task_and_descriptor_stride_bytes": 192,
            "loader_callback_0x88B480_count": 0,
        },
        "function": {
            "entry_rva": f"0x{ENTRY_RVA:X}",
            "end_rva_exclusive": f"0x{END_RVA:X}",
            "size_bytes": len(function), "bytes_sha256": sha256(function),
            "pdata_fragments": unwind_rows,
        },
        "bounded_cfg": {
            "shared_state": "[RCX+0x8]",
            "atomic_next_index_offset": "0x0",
            "total_bound_offset": "0x14",
            "batch_size_offset": "0x1C",
            "element_pointer_array_carrier_offset": "0x28",
            "claim_instruction_rvas": ["0x817C3B", "0x817C81"],
            "claim_operation": "lock xadd dword ptr [RSI], EBX",
            "batch_end": "min(claimed_index + batch_size, total_bound)",
            "element_load_rva": "0x817C6A",
            "element_dispatch_rva": "0x817C71",
            "element_dispatch": "call qword ptr [element_vptr+0x8] (virtual slot 1)",
            "terminal_condition": "claimed_index >= total_bound",
        },
        "rtti": {
            "valid_vtable_count": len(rows),
            "all_slot2_targets_rva": f"0x{ENTRY_RVA:X}",
            "canonical_rows_sha256": sha256(canonical),
            "common_type_prefix": expected_prefix,
            "token_counts": token_counts,
            "representatives": [rows[index] for index in representative_indices],
        },
        "identity": {
            "task_domain": "generic SPdxParallelForOverArray range-worker std::function callback",
            "owner_semantics": (
                "RCX is a std::function implementation wrapper; RCX+8 points to shared "
                "parallel-for range state and the callback invokes per-element virtual slot 1"
            ),
            "current_list_semantics": (
                "27 generic parallel-for worker task descriptors owned by one scheduler/list owner"
            ),
            "not_loader_completion_list": True,
            "reason": (
                "all 27 callbacks use the shared 0x817C20 parallel-for thunk and none uses "
                "the frozen loader completion callback RVA 0x88B480"
            ),
            "unique_runtime_rtti_owner_resolved": False,
            "unresolved_reason": (
                "278 RTTI vtables share this exact slot2 thunk and live v1 did not retain callback vptr"
            ),
        },
        "next_distinct_observation": {
            "primary_seam": {
                "rva": f"0x{TRUE_PRODUCER_PUBLISH_RVA:X}",
                "preceding_task_identity_rva": f"0x{TRUE_PRODUCER_TASK_RVA:X}",
                "capture": [
                    "RBX producer task identity", "[RBX+0x38] callback",
                    "[callback] callback vptr", "[callback vptr+0x10] slot2 target",
                    "[RBX+0x58] owner", "[RBX+0x60] state before/after publish",
                ],
                "purpose": (
                    "bind the actual task that publishes loader completion value 2, then carry "
                    "that exact identity outward instead of resampling the unrelated 0x3407D9C list"
                ),
            },
            "secondary_forensic_seam": {
                "location": "existing 0x3407DA1 bounded list capture",
                "additional_field": "[callback] vptr per descriptor",
                "purpose": "map this unrelated list to one of the 278 frozen RTTI specializations",
                "required_for_loader_progress": False,
            },
            "do_not_repeat": "the completed 0x3407DA1 slot2 histogram live",
        },
        "limits": [
            "RTTI establishes a generic parallel-for domain, not the concrete runtime specialization",
            "no thread wait or loader readiness is inferred",
            "no CK3 process was started and no public ABI/readiness changed",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--runner-report", type=Path, required=True)
    parser.add_argument("--postprocess", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = extract(args.exe, args.runner_report, args.postprocess)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
