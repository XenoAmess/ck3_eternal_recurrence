#!/usr/bin/env python3
"""Freeze the exact-build read-only CAddTruce preview observer seam.

This extractor reads only the pinned CK3 executable.  It does not start or
attach to CK3, install a detour, execute an effect, or mutate game state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
from typing import Any

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
import pefile


EXPECTED_EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_EXE_SIZE = 95_206_008
EXPECTED_IMAGE_BASE = 0x140000000

PREVIEW_RVA = 0x2E87140
PREVIEW_END_RVA = 0x2E8723B
PREVIEW_UNWIND_RVA = 0x4DF9914
PREVIEW_PROLOG_SIZE = 0x15
PATCH_RVA = PREVIEW_RVA + PREVIEW_PROLOG_SIZE
CONTINUE_RVA = 0x2E87165
ANCHOR_HEX = "488B024D8BF04C8BD2488BF966833804"
ANCHOR_SHA256 = "F5B206324844555C64D660A376350E28C0E9710717BA121E04B380415254FC63"
FUNCTION_SHA256 = "941E91BF0B43EB8029940BA378D75A7CF6B65DB1431B126B7265FAD84EDE7E1F"
EVALUATOR_RVA = 0x3373000

CADDTRUCE_TYPES = (
    {
        "template_parameter": 0,
        "vtable_rva": 0x4461CA8,
        "preview_slot_address_rva": 0x4461D60,
        "rtti_type_name": ".?AV?$CAddTruceEffect@$0A@@@",
    },
    {
        "template_parameter": 1,
        "vtable_rva": 0x4461D70,
        "preview_slot_address_rva": 0x4461E28,
        "rtti_type_name": ".?AV?$CAddTruceEffect@$00@@",
    },
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def bytes_at(data: bytes, image: pefile.PE, begin: int, end: int) -> bytes:
    offset = image.get_offset_from_rva(begin)
    value = data[offset : offset + end - begin]
    if len(value) != end - begin:
        raise ValueError(f"short read at 0x{begin:X}..0x{end:X}")
    return value


def u64(data: bytes, image: pefile.PE, rva: int) -> int:
    return struct.unpack_from("<Q", data, image.get_offset_from_rva(rva))[0]


def runtime_functions(image: pefile.PE) -> set[tuple[int, int, int]]:
    image.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]]
    )
    return {
        (int(row.struct.BeginAddress), int(row.struct.EndAddress), int(row.struct.UnwindData))
        for row in image.DIRECTORY_ENTRY_EXCEPTION
    }


def instruction_rows(decoder: Cs, blob: bytes, start_rva: int) -> list[dict[str, str]]:
    return [
        {
            "rva": f"0x{row.address - EXPECTED_IMAGE_BASE:X}",
            "bytes": row.bytes.hex().upper(),
            "mnemonic": row.mnemonic,
            "operands": row.op_str,
        }
        for row in decoder.disasm(blob, EXPECTED_IMAGE_BASE + start_rva)
    ]


def direct_relative_target(row: Any) -> int | None:
    if row.mnemonic not in {"call", "jmp"} or not row.op_str.startswith("0x"):
        return None
    return int(row.op_str, 16) - EXPECTED_IMAGE_BASE


def extract(exe: Path) -> dict[str, Any]:
    data = exe.read_bytes()
    digest = sha256(data)
    if len(data) != EXPECTED_EXE_SIZE or digest != EXPECTED_EXE_SHA256:
        raise ValueError(f"unexpected executable size/hash: {len(data)} {digest}")
    image = pefile.PE(data=data, fast_load=True)
    if int(image.OPTIONAL_HEADER.ImageBase) != EXPECTED_IMAGE_BASE:
        raise ValueError("unexpected image base")

    functions = runtime_functions(image)
    pdata = (PREVIEW_RVA, PREVIEW_END_RVA, PREVIEW_UNWIND_RVA)
    if pdata not in functions:
        raise ValueError("preview PDATA changed")

    function_blob = bytes_at(data, image, PREVIEW_RVA, PREVIEW_END_RVA)
    if sha256(function_blob) != FUNCTION_SHA256:
        raise ValueError("preview function changed")
    anchor = bytes_at(data, image, PATCH_RVA, CONTINUE_RVA)
    if anchor.hex().upper() != ANCHOR_HEX or sha256(anchor) != ANCHOR_SHA256:
        raise ValueError("preview observer anchor changed")

    unwind = bytes_at(data, image, PREVIEW_UNWIND_RVA, PREVIEW_UNWIND_RVA + 4)
    if unwind[1] != PREVIEW_PROLOG_SIZE:
        raise ValueError("preview unwind prolog size changed")

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    anchor_rows = instruction_rows(decoder, anchor, PATCH_RVA)
    expected_anchor_shape = ["mov", "mov", "mov", "mov", "cmp"]
    if [row["mnemonic"] for row in anchor_rows] != expected_anchor_shape:
        raise ValueError("preview observer anchor instruction shape changed")
    if anchor_rows != [
        {"rva": "0x2E87155", "bytes": "488B02", "mnemonic": "mov", "operands": "rax, qword ptr [rdx]"},
        {"rva": "0x2E87158", "bytes": "4D8BF0", "mnemonic": "mov", "operands": "r14, r8"},
        {"rva": "0x2E8715B", "bytes": "4C8BD2", "mnemonic": "mov", "operands": "r10, rdx"},
        {"rva": "0x2E8715E", "bytes": "488BF9", "mnemonic": "mov", "operands": "rdi, rcx"},
        {"rva": "0x2E87161", "bytes": "66833804", "mnemonic": "cmp", "operands": "word ptr [rax], 4"},
    ]:
        raise ValueError("preview observer anchor operands changed")

    full_rows = list(decoder.disasm(function_blob, EXPECTED_IMAGE_BASE + PREVIEW_RVA))
    if any(direct_relative_target(row) == EVALUATOR_RVA for row in full_rows):
        raise ValueError("preview unexpectedly calls or jumps to duration evaluator")
    if any("0x108" in row.op_str for row in full_rows):
        raise ValueError("preview unexpectedly consumes CAddTruce+0x108")

    preview_va = EXPECTED_IMAGE_BASE + PREVIEW_RVA
    preview_pointer = struct.pack("<Q", preview_va)
    references: list[int] = []
    for section in image.sections:
        raw = data[section.PointerToRawData : section.PointerToRawData + section.SizeOfRawData]
        cursor = 0
        while True:
            offset = raw.find(preview_pointer, cursor)
            if offset < 0:
                break
            references.append(int(section.VirtualAddress) + offset)
            cursor = offset + 1
    expected_references = [
        0x443F480,
        0x4446948,
        0x445D8A0,
        0x4461D60,
        0x4461E28,
        0x4462A48,
        0x4462CC0,
        0x4473150,
    ]
    if references != expected_references:
        raise ValueError("shared preview pointer references changed")

    caddtruce_rows: list[dict[str, Any]] = []
    for expected in CADDTRUCE_TYPES:
        slot_rva = expected["preview_slot_address_rva"]
        if u64(data, image, slot_rva) != preview_va:
            raise ValueError("CAddTruce preview vtable slot changed")
        caddtruce_rows.append(
            {
                **expected,
                "vtable_rva": f"0x{expected['vtable_rva']:X}",
                "preview_slot_address_rva": f"0x{slot_rva:X}",
                "preview_target_rva": f"0x{PREVIEW_RVA:X}",
            }
        )

    return {
        "schema": "xar.ck3.g2_truce_preview_entry_observer_seam.v1",
        "result": "STATIC_READ_ONLY_OBSERVER_SEAM_IDENTIFIED",
        "status": "static-ready-no-launch",
        "exact_build": {
            "version": "1.19.0.6",
            "sha256": digest,
            "file_size": len(data),
            "image_base": f"0x{EXPECTED_IMAGE_BASE:X}",
        },
        "preview_function": {
            "rva": f"0x{PREVIEW_RVA:X}",
            "pdata": [f"0x{value:X}" for value in pdata],
            "unwind_prolog_size": f"0x{PREVIEW_PROLOG_SIZE:X}",
            "function_sha256": sha256(function_blob),
            "shared_pointer_reference_count": len(references),
            "shared_pointer_reference_rvas": [f"0x{value:X}" for value in references],
            "calls_duration_evaluator": False,
            "consumes_duration_at_this_plus_0x108": False,
        },
        "observer_seam": {
            "patch_rva": f"0x{PATCH_RVA:X}",
            "continue_rva": f"0x{CONTINUE_RVA:X}",
            "patch_bytes": len(anchor),
            "anchor_hex": anchor.hex().upper(),
            "anchor_sha256": sha256(anchor),
            "after_unwind_prolog": True,
            "instructions": anchor_rows,
            "incoming_registers": {
                "RCX": "effect_this; preserved natively into RDI",
                "RDX": "preview source/context; preserved natively into R10 after [RDX] read",
                "R8": "preview output/collector; preserved natively into R14",
            },
            "caddtruce_filter": "read [RCX] and accept only exact vtable RVA 0x4461CA8 or 0x4461D70",
            "minimal_telemetry": [
                "hit_count",
                "RCX effect_this",
                "[RCX] exact vtable",
                "RDX preview source/context",
                "R8 preview output/collector",
                "derived address RCX+0x108 (identity only; never evaluate or dereference for days)",
            ],
        },
        "caddtruce_types": caddtruce_rows,
        "data_flow": {
            "this": "RCX -> RDI; native preview later reads this+0x10 and this+0x60",
            "preview_source_context": "RDX -> native [RDX] read -> R10",
            "preview_output_collector": "R8 -> R14 -> virtual call [R14]+0x8",
            "duration_script_value": "known execute layout is this+0x108, but preview does not read or evaluate it",
        },
        "observer_rules": {
            "default_enabled": False,
            "read_only_telemetry": True,
            "replay_exact_anchor": True,
            "preserve_registers_and_flags": True,
            "no_guard": True,
            "no_branch_or_return_change": True,
            "no_evaluator_call": True,
            "no_effect_execute": True,
            "no_action_or_mutation": True,
        },
        "evidence_limit": {
            "preview_hit_value": "proves a game-native read-only preview traversed an exact CAddTruce object",
            "preview_hit_is_evaluated_days": False,
            "can_close_evaluated_days_gap": False,
            "next_after_preview_hit": "none justified statically; require new native evidence before widening observation",
        },
        "boundaries": {
            "ck3_started": False,
            "process_attached": False,
            "effect_executed": False,
            "mutation_sent": False,
            "public_abi_changed": False,
            "public_readiness_changed": False,
            "evaluated_days_observable": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    payload = extract(arguments.exe.resolve())
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if arguments.output is None:
        print(rendered, end="")
    else:
        arguments.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
