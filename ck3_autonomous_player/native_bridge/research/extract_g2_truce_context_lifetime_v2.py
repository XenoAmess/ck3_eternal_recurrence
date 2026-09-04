#!/usr/bin/env python3
"""Freeze the exact-build CAddTruce leaf-context construction chain.

This extractor reads only the pinned executable and a committed live-RED
summary. It never starts or attaches to CK3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pefile


EXPECTED_EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_EXE_SIZE = 95_206_008
EXPECTED_IMAGE_BASE = 0x140000000

SLICES = {
    "root_preview_wrapper": (0x3380248, 0x3380289, "D386E4C4380A0DD51B1CE634CDF3223F97672678ACCD3F852C992CA0FA5E4C01"),
    "root_execute_wrapper": (0x3380357, 0x3380397, "E25A7F9C379AC423164DA80036024E762972212B34D66C3973CB4573DE72FABD"),
    "leaf_preview_wrapper": (0x338090F, 0x338094D, "FFB6BD82E8B81A6D8178EAE495574FF71A2E18C9F6E9BC654AA390EDE02BA2DD"),
    "leaf_execute_wrapper": (0x3380CBE, 0x3380D01, "6C471C3F62C598832AA22A84A15DBE05B0EB3007C38CADDE8E141D81F45D6788"),
    "crash_dereference": (0x334C665, 0x334C66D, "04E56C6B80D3FA658276F99F7861311B4F8866942582FDB1CE4223E206F788DD"),
    "evaluator_prefix": (0x3373000, 0x337307E, "2661AF2FBA9855AFC67AFE87262F4CD20B0F709DF72C4D1273BBA13829FC9988"),
    "evaluator_dispatch_prefix": (0x3369600, 0x33696BF, "0719A23D47B6EF1F405B246C11CCD26F7BD2F90972DAEA938958CD44AD10F7E5"),
}

FUNCTIONS = {
    "root_preview_dispatch": (0x3380170, 0x338030C, 0x4E61388, "8B50D40D412B827D7FAC2EE58B5446BE9B8F44A219EA60826C87E878D23D29AA"),
    "root_execute_dispatch": (0x3380310, 0x338040C, 0x4E613C8, "5BE57330A255468A844CCA0F44D8D3F198D8828D3439D15BD8719A482C885E9C"),
    "leaf_preview_dispatch": (0x3380840, 0x338097B, 0x4C89240, "A2BE88DECA174CE581585DE596D1F870227796928DEAB275F6E33F14750F8DFE"),
    "leaf_execute_dispatch": (0x3380A00, 0x3380EB1, 0x4E61464, "DE65DB5D7BF65D96B83F33C4D6F3F97094A080337B190BCAA23904B4D88EAA22"),
    "caddtruce_normal_execute": (0x2EDAD20, 0x2EDB27C, 0x4DFE04C, "0CC65B9CFAE1F080C333E4B219388B19AA231E11FDF69AA9470D6E6E5B9EF199"),
    "caddtruce_forced_execute": (0x2EDB3A0, 0x2EDB9A5, 0x4DFE0C4, "DED15DD333E2B6D037B31BBA5DF1DD521885C8F3715C3CB5C040087B657F92E0"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def bytes_at(data: bytes, image: pefile.PE, begin: int, end: int) -> bytes:
    offset = image.get_offset_from_rva(begin)
    value = data[offset : offset + end - begin]
    if len(value) != end - begin:
        raise ValueError(f"short file-backed range 0x{begin:X}..0x{end:X}")
    return value


def runtime_functions(image: pefile.PE) -> set[tuple[int, int, int]]:
    image.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]]
    )
    return {
        (
            int(row.struct.BeginAddress),
            int(row.struct.EndAddress),
            int(row.struct.UnwindData),
        )
        for row in image.DIRECTORY_ENTRY_EXCEPTION
    }


def range_row(
    data: bytes, image: pefile.PE, begin: int, end: int, *,
    include_bytes: bool = True,
) -> dict[str, Any]:
    value = bytes_at(data, image, begin, end)
    result = {
        "rva": f"0x{begin:X}..0x{end:X}",
        "size": len(value),
        "sha256": sha256(value),
    }
    if include_bytes:
        result["bytes"] = value.hex().upper()
    return result


def extract(exe: Path, live_red: Path) -> dict[str, Any]:
    data = exe.read_bytes()
    digest = sha256(data)
    if len(data) != EXPECTED_EXE_SIZE or digest != EXPECTED_EXE_SHA256:
        raise ValueError(f"unexpected executable: size={len(data)} sha256={digest}")
    image = pefile.PE(data=data, fast_load=True)
    if int(image.OPTIONAL_HEADER.ImageBase) != EXPECTED_IMAGE_BASE:
        raise ValueError("unexpected image base")
    pdata = runtime_functions(image)

    functions: dict[str, Any] = {}
    for name, (begin, end, unwind, expected_hash) in FUNCTIONS.items():
        if (begin, end, unwind) not in pdata:
            raise ValueError(f"{name} PDATA changed")
        row = range_row(data, image, begin, end, include_bytes=False)
        if row["sha256"] != expected_hash:
            raise ValueError(f"{name} bytes changed")
        row["pdata"] = [f"0x{begin:X}", f"0x{end:X}", f"0x{unwind:X}"]
        functions[name] = row

    slices: dict[str, Any] = {}
    for name, (begin, end, expected_hash) in SLICES.items():
        row = range_row(data, image, begin, end)
        if row["sha256"] != expected_hash:
            raise ValueError(f"{name} bytes changed")
        slices[name] = row

    live_data = live_red.read_bytes()
    live = json.loads(live_data.decode("utf-8"))
    crash = live["crash"]
    prefix = live["private_prefix"]
    if (
        live["status"] != "CAPABILITY_RED_FIRST_EVALUATOR_CALL"
        or crash["exception_rva"] != "0x334C668"
        or crash["access_address"] != "0x12"
        or crash["exception_context"]["R12"] != "0x12"
        or crash["effect_context_first_qword"] != "0x12"
        or prefix["completed_call_count"] != 0
    ):
        raise ValueError("unexpected live-RED boundary")

    return {
        "schema": "xar.ck3.g2_truce_context_lifetime.v2",
        "status": "STATIC_LEAF_CONTEXT_CHAIN_CLOSED",
        "read_only": True,
        "exact_build": {
            "version": "1.19.0.6",
            "sha256": digest,
            "file_size": len(data),
            "image_base": f"0x{EXPECTED_IMAGE_BASE:X}",
        },
        "functions": functions,
        "slices": slices,
        "execute_context_chain": {
            "generic_dispatcher": "0x3380A00",
            "incoming_parent_saved": "RDX -> R14 at 0x3380A25",
            "child_wrapper": "stack [RBP+0x00..0x2F]",
            "copied_fields": ["+0x00", "+0x08", "+0x10", "+0x18", "+0x20"],
            "child_evaluation_state": "[child+0x28] = &stack[RBP+0x288]",
            "virtual_call": "0x3380CFB call [vtable+0xB0]",
            "normal_receiver": "RDX -> R15 at 0x2EDAD3C",
            "forced_receiver": "RDX -> R12 at 0x2EDB3BC",
            "evaluator_arguments": "RCX=this+0x108, RDX=leaf wrapper, R8=[leaf wrapper+0x28]",
            "lifetime": "only through the synchronous slot+0xB0 call",
        },
        "preview_context_chain": {
            "root_wrapper": "0x3380170 constructs a root preview wrapper",
            "leaf_dispatcher": "0x3380840",
            "child_wrapper": "stack [RSP+0x20..0x4F]",
            "copied_fields": ["+0x00", "+0x08", "+0x10", "+0x18", "+0x20"],
            "child_evaluation_state": "[child+0x28] = &stack[RSP+0x70]",
            "virtual_call": "0x3380947 call [vtable+0xB8]",
            "caddtruce_entry": "0x2E87140; post-prolog seam 0x2E87155",
            "lifetime": "only through the synchronous slot+0xB8 call",
        },
        "live_red": {
            "summary_sha256": sha256(live_data),
            "effect_context": prefix["effect_context"],
            "evaluation_context": prefix["evaluation_context"],
            "first_qword": crash["effect_context_first_qword"],
            "fault_rva": crash["exception_rva"],
            "fault_register": crash["exception_context"]["R12"],
            "fault_read_address": crash["access_address"],
            "completed_call_count": prefix["completed_call_count"],
        },
        "diagnosis": {
            "raw_war_effect_context_is_valid_leaf_context": False,
            "root_preview_wrapper_is_valid_caddtruce_leaf_context": False,
            "root_slot58_proxy_can_supply_leaf_context": False,
            "rdx_and_r8_must_share_one_leaf_wrapper": True,
            "crash_chain": "0x334C665 loads [RDI] into R12; 0x334C668 reads word [R12]",
            "root_cause": "direct bridge call bypassed native leaf-context construction",
        },
        "candidate_boundary": {
            "supported_seam": "synchronous CAddTruce preview entry 0x2E87155",
            "context_source": "RDX from the active 0x3380840 leaf preview call",
            "evaluation_source": "pointer loaded from the same RDX+0x28",
            "wrapper_clone_allowed": False,
            "root_wrapper_substitution_allowed": False,
            "default_enabled": False,
            "private_only": True,
            "live_validated": False,
        },
        "boundaries": {
            "ck3_started": False,
            "process_attached": False,
            "mutation_sent": False,
            "public_wire_promoted": False,
            "public_readiness_promoted": False,
            "gen034_closed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--live-red", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    payload = extract(arguments.exe.resolve(), arguments.live_red.resolve())
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if arguments.output is None:
        print(rendered, end="")
    else:
        arguments.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
