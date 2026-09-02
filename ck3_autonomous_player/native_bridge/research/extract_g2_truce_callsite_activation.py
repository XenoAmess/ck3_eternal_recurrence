#!/usr/bin/env python3
"""Extract the exact-build activation boundary for the G2 truce callsites.

This is a file-only extractor.  It reads the pinned executable and emits the
two CAddTruce specializations, their virtual execute/preview slots, and the
local branch that gates each evaluator call.  It never starts or attaches to
CK3.
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
EVALUATOR_RVA = 0x3373000
SPECIALIZATIONS = (
    {
        "template": 0,
        "vtable": 0x4461CA8,
        "col": 0x4AC06B8,
        "type_descriptor": 0x55D9598,
        "rtti": ".?AV?$CAddTruceEffect@$0A@@@",
        "execute": 0x2EDAD20,
        "execute_end": 0x2EDB27C,
        "unwind": 0x4DFE04C,
        "function_sha256": "0CC65B9CFAE1F080C333E4B219388B19AA231E11FDF69AA9470D6E6E5B9EF199",
        "predicate": (0x2EDAE3C, 0x2EDAE4C),
        "predicate_sha256": "9ED1F405367C3578FA62235471508C3D35731E7EF48C3A8D9212A4D587F3A190",
        "taken_target": 0x2EDAEDA,
        "call": 0x2EDAF0F,
    },
    {
        "template": 1,
        "vtable": 0x4461D70,
        "col": 0x4AC05C8,
        "type_descriptor": 0x55D8FD8,
        "rtti": ".?AV?$CAddTruceEffect@$00@@",
        "execute": 0x2EDB3A0,
        "execute_end": 0x2EDB9A5,
        "unwind": 0x4DFE0C4,
        "function_sha256": "DED15DD333E2B6D037B31BBA5DF1DD521885C8F3715C3CB5C040087B657F92E0",
        "predicate": (0x2EDB4CA, 0x2EDB4DA),
        "predicate_sha256": "2E053D5AC4C4E62B2B7505297535F7D7514C1DE1B449891462EBD735F02AF6F9",
        "taken_target": 0x2EDB56A,
        "call": 0x2EDB59E,
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


def u32(data: bytes, image: pefile.PE, rva: int) -> int:
    return struct.unpack_from("<I", data, image.get_offset_from_rva(rva))[0]


def u64(data: bytes, image: pefile.PE, rva: int) -> int:
    return struct.unpack_from("<Q", data, image.get_offset_from_rva(rva))[0]


def rtti_name(data: bytes, image: pefile.PE, type_rva: int) -> str:
    start = image.get_offset_from_rva(type_rva) + 16
    end = data.find(b"\0", start, start + 512)
    if end < 0:
        raise ValueError("unterminated RTTI name")
    return data[start:end].decode("ascii")


def instruction_rows(decoder: Cs, blob: bytes, start_rva: int) -> list[dict[str, Any]]:
    return [
        {
            "rva": f"0x{row.address - EXPECTED_IMAGE_BASE:X}",
            "bytes": row.bytes.hex().upper(),
            "mnemonic": row.mnemonic,
            "operands": row.op_str,
        }
        for row in decoder.disasm(blob, EXPECTED_IMAGE_BASE + start_rva)
    ]


def runtime_functions(image: pefile.PE) -> set[tuple[int, int, int]]:
    image.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]]
    )
    return {
        (int(row.struct.BeginAddress), int(row.struct.EndAddress), int(row.struct.UnwindData))
        for row in image.DIRECTORY_ENTRY_EXCEPTION
    }


def extract(exe: Path) -> dict[str, Any]:
    data = exe.read_bytes()
    digest = sha256(data)
    if len(data) != EXPECTED_EXE_SIZE or digest != EXPECTED_EXE_SHA256:
        raise ValueError(f"unexpected executable size/hash: {len(data)} {digest}")
    image = pefile.PE(data=data, fast_load=True)
    if int(image.OPTIONAL_HEADER.ImageBase) != EXPECTED_IMAGE_BASE:
        raise ValueError("unexpected image base")
    functions = runtime_functions(image)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)

    preview_function = next(
        row for row in functions if row[0] <= PREVIEW_RVA < row[1]
    )
    if preview_function != (0x2E87140, 0x2E8723B, 0x4DF9914):
        raise ValueError("preview PDATA changed")
    preview_blob = bytes_at(data, image, preview_function[0], preview_function[1])
    preview_rows = instruction_rows(decoder, preview_blob, preview_function[0])
    if any(row["operands"] == f"0x{EXPECTED_IMAGE_BASE + EVALUATOR_RVA:x}" for row in preview_rows):
        raise ValueError("preview unexpectedly calls the duration evaluator")

    output_specializations: list[dict[str, Any]] = []
    for expected in SPECIALIZATIONS:
        vtable = expected["vtable"]
        col_va = u64(data, image, vtable - 8)
        col = col_va - EXPECTED_IMAGE_BASE
        if col != expected["col"]:
            raise ValueError(f"COL changed for 0x{vtable:X}")
        type_descriptor = u32(data, image, col + 12)
        if type_descriptor != expected["type_descriptor"]:
            raise ValueError(f"type descriptor changed for 0x{vtable:X}")
        name = rtti_name(data, image, type_descriptor)
        if name != expected["rtti"]:
            raise ValueError(f"RTTI name changed for 0x{vtable:X}")
        slots = [u64(data, image, vtable + index * 8) - EXPECTED_IMAGE_BASE for index in range(24)]
        if slots[22] != expected["execute"] or slots[23] != PREVIEW_RVA:
            raise ValueError(f"execute/preview slots changed for 0x{vtable:X}")
        pdata = (expected["execute"], expected["execute_end"], expected["unwind"])
        if pdata not in functions:
            raise ValueError(f"execute PDATA changed for 0x{vtable:X}")
        function_blob = bytes_at(data, image, expected["execute"], expected["execute_end"])
        if sha256(function_blob) != expected["function_sha256"]:
            raise ValueError(f"execute body changed for 0x{vtable:X}")
        predicate_begin, predicate_end = expected["predicate"]
        predicate_blob = bytes_at(data, image, predicate_begin, predicate_end)
        if sha256(predicate_blob) != expected["predicate_sha256"]:
            raise ValueError(f"activation predicate changed for 0x{vtable:X}")
        predicate_rows = instruction_rows(decoder, predicate_blob, predicate_begin)
        if [row["mnemonic"] for row in predicate_rows] != ["mov", "mov", "cmp", "jne"]:
            raise ValueError(f"activation CFG changed for 0x{vtable:X}")
        if predicate_rows[-1]["operands"] != f"0x{EXPECTED_IMAGE_BASE + expected['taken_target']:x}":
            raise ValueError(f"activation target changed for 0x{vtable:X}")

        output_specializations.append(
            {
                "template_parameter": expected["template"],
                "vtable_rva": f"0x{vtable:X}",
                "col_rva": f"0x{col:X}",
                "type_descriptor_rva": f"0x{type_descriptor:X}",
                "rtti_type_name": name,
                "vtable_slots_sha256": sha256(bytes_at(data, image, vtable, vtable + 24 * 8)),
                "execute_slot": 22,
                "execute_rva": f"0x{expected['execute']:X}",
                "execute_pdata": [f"0x{value:X}" for value in pdata],
                "execute_sha256": sha256(function_blob),
                "preview_slot": 23,
                "preview_rva": f"0x{PREVIEW_RVA:X}",
                "evaluator_call_rva": f"0x{expected['call']:X}",
                "activation_predicate": {
                    "span": f"0x{predicate_begin:X}..0x{predicate_end:X}",
                    "sha256": sha256(predicate_blob),
                    "instructions": predicate_rows,
                    "taken_target_rva": f"0x{expected['taken_target']:X}",
                    "semantic": "resolved source CharacterID != resolved target CharacterID",
                },
            }
        )

    return {
        "schema": "xar.ck3.g2_truce_callsite_activation.v1",
        "result": "STATIC_ACTIVATION_BOUNDARY_IDENTIFIED",
        "read_only": True,
        "exact_build": {
            "version": "1.19.0.6",
            "sha256": digest,
            "file_size": len(data),
            "image_base": f"0x{EXPECTED_IMAGE_BASE:X}",
        },
        "specializations": output_specializations,
        "preview": {
            "shared_rva": f"0x{PREVIEW_RVA:X}",
            "pdata": [f"0x{value:X}" for value in preview_function],
            "sha256": sha256(preview_blob),
            "calls_duration_evaluator": False,
            "role": "read-only effect description/preview collector",
        },
        "current_loaded_path": {
            "observed_vtable_rva": "0x4461CA8",
            "observed_specialization": 0,
            "applicable_execute_rva": "0x2EDAD20",
            "applicable_evaluator_call_rva": "0x2EDAF0F",
            "second_callsite_structurally_applicable": False,
            "source_live_report_sha256": "24D9661AEC29E8247BF63E54082487BD6A2E296F4E2A0A965227BDB454A63706",
        },
        "activation_conclusion": {
            "required_native_dispatch": "CAddTruceEffect<0> virtual execute slot 22",
            "required_local_branch": "resolved source and target CharacterIDs differ",
            "frozen_state_character_ids": [29829, 36769],
            "frozen_state_character_ids_differ": True,
            "frozen_state_war_id": 50331699,
            "termination_or_context_effect_submitted": False,
            "why_no_hit": "the paused heartbeat-only run never dispatched the mutating execute slot",
        },
        "next_distinct_read_only_seam": {
            "preferred_rva": "0x2E87140",
            "kind": "shared virtual preview entry at slot 23",
            "trigger_condition": "game-native effect-description preview traversal, without confirming a war outcome",
            "value": "proves whether CAddTruce is traversed on a read-only UI/description path",
            "limitation": "preview does not call 0x3373000 and cannot produce evaluated_days",
            "execute_entry_rva": "0x2EDAD20",
            "execute_entry_limitation": "still requires mutating effect dispatch and is not a no-action duration seam",
        },
        "boundaries": {
            "ck3_started": False,
            "process_attached": False,
            "time_advanced": False,
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
    result = extract(arguments.exe.resolve())
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if arguments.output is None:
        print(rendered, end="")
    else:
        arguments.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
