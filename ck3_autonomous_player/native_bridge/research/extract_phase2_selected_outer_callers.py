#!/usr/bin/env python3
"""Freeze the exact static caller boundary of callback RVA 0x88B480."""

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
EXPECTED_IMAGE_BASE = 0x140000000
FUNCTION_RVA = 0x88B480
FUNCTION_END_RVA = 0x88B649
FUNCTION_SHA256 = "0434F6BAD0F0DC15301E30408EAE2705CA65C4C5B54A422FB75EA4D643AE5F37"
FUNCTION_UNWIND_RVA = 0x4C42814
NORMAL_RETURN_RVA = 0x88B648
VTABLE_RVA = 0x408DBF0
VTABLE_SLOT_INDEX = 2
VTABLE_SLOT_RVA = 0x408DC00
COL_POINTER_RVA = 0x408DBE8
COL_RVA = 0x45BE710
TYPE_DESCRIPTOR_RVA = 0x5158290
TYPE_NAME = (
    ".?AV?$_Func_impl_no_alloc@V<lambda_68c316810e9676445097b6e1817a6010>"
    "@@X$$V@std@@"
)
VTABLE_CONSTRUCTION_REFS = (0x82193B, 0x88B650)


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
    offset = raw.find(b"\xE8")
    while offset >= 0:
        if offset + 5 <= len(raw):
            displacement = struct.unpack_from("<i", raw, offset + 1)[0]
            if base_rva + offset + 5 + displacement == target_rva:
                hits.append(base_rva + offset)
        offset = raw.find(b"\xE8", offset + 1)
    return hits


def scan_rip_lea_refs(raw: bytes, base_rva: int, target_rva: int) -> list[int]:
    hits: list[int] = []
    for offset in range(len(raw) - 7):
        if (
            raw[offset] in (0x48, 0x4C)
            and raw[offset + 1] == 0x8D
            and raw[offset + 2] & 0xC7 == 0x05
        ):
            displacement = struct.unpack_from("<i", raw, offset + 3)[0]
            if base_rva + offset + 7 + displacement == target_rva:
                hits.append(base_rva + offset)
    return hits


def all_file_refs(data: bytes, needle: bytes, image: pefile.PE) -> list[int]:
    hits: list[int] = []
    offset = data.find(needle)
    while offset >= 0:
        try:
            hits.append(image.get_rva_from_offset(offset))
        except pefile.PEFormatError:
            pass
        offset = data.find(needle, offset + 1)
    return hits


def extract(exe: Path) -> dict[str, Any]:
    source = exe.resolve()
    data = source.read_bytes()
    digest = sha256(data)
    if len(data) != EXPECTED_SIZE or digest != EXPECTED_SHA256:
        raise ValueError("source is not the pinned CK3 1.19.0.6 executable")
    image = pefile.PE(str(source), fast_load=False)
    image_base = int(image.OPTIONAL_HEADER.ImageBase)
    if image_base != EXPECTED_IMAGE_BASE:
        raise ValueError("unexpected image base")

    function = bytes_at(data, image, FUNCTION_RVA, FUNCTION_END_RVA - FUNCTION_RVA)
    if sha256(function) != FUNCTION_SHA256 or function[-1] != 0xC3:
        raise ValueError("selected outer function bytes changed")
    pdata = next(
        (
            entry.struct
            for entry in image.DIRECTORY_ENTRY_EXCEPTION
            if int(entry.struct.BeginAddress) == FUNCTION_RVA
        ),
        None,
    )
    if (
        pdata is None
        or int(pdata.EndAddress) != FUNCTION_END_RVA
        or int(pdata.UnwindData) != FUNCTION_UNWIND_RVA
    ):
        raise ValueError("selected outer function PDATA changed")

    text = next(
        section
        for section in image.sections
        if section.Name.rstrip(b"\0") == b".text"
    )
    text_raw = text.get_data()
    text_rva = int(text.VirtualAddress)
    direct_calls = scan_direct_calls(text_raw, text_rva, FUNCTION_RVA)
    if direct_calls:
        raise ValueError(f"unexpected direct callers: {direct_calls!r}")

    absolute_refs = all_file_refs(
        data, struct.pack("<Q", image_base + FUNCTION_RVA), image
    )
    if absolute_refs != [VTABLE_SLOT_RVA]:
        raise ValueError(f"absolute function refs changed: {absolute_refs!r}")

    col_pointer = struct.unpack(
        "<Q", bytes_at(data, image, COL_POINTER_RVA, 8)
    )[0]
    if col_pointer - image_base != COL_RVA:
        raise ValueError("vtable COL pointer changed")
    col = struct.unpack("<6I", bytes_at(data, image, COL_RVA, 24))
    if col[3] != TYPE_DESCRIPTOR_RVA or col[5] != COL_RVA:
        raise ValueError("COL identity changed")
    raw_name = bytes_at(data, image, TYPE_DESCRIPTOR_RVA + 16, len(TYPE_NAME) + 1)
    if raw_name != (TYPE_NAME + "\0").encode("ascii"):
        raise ValueError("RTTI type name changed")
    slot_target = struct.unpack(
        "<Q", bytes_at(data, image, VTABLE_SLOT_RVA, 8)
    )[0]
    if slot_target - image_base != FUNCTION_RVA:
        raise ValueError("vtable slot target changed")

    construction_refs = scan_rip_lea_refs(text_raw, text_rva, VTABLE_RVA)
    if construction_refs != list(VTABLE_CONSTRUCTION_REFS):
        raise ValueError(f"vtable construction refs changed: {construction_refs!r}")
    construction_owner = next(
        entry.struct
        for entry in image.DIRECTORY_ENTRY_EXCEPTION
        if int(entry.struct.BeginAddress) <= 0x82193B < int(entry.struct.EndAddress)
    )

    return {
        "contract": "phase2-selected-outer-callers-extract-v1",
        "status": "static-indirect-owner-bound",
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
        "function": {
            "rva": f"0x{FUNCTION_RVA:X}",
            "end_rva_exclusive": f"0x{FUNCTION_END_RVA:X}",
            "bytes_sha256": sha256(function),
            "unwind_rva": f"0x{FUNCTION_UNWIND_RVA:X}",
            "normal_return_rva": f"0x{NORMAL_RETURN_RVA:X}",
            "return_address_source": "[RSP] before RET",
        },
        "callers": {
            "direct_relative_call_count": 0,
            "direct_relative_calls": [],
            "absolute_function_pointer_ref_count": 1,
            "absolute_function_pointer_ref_rvas": [f"0x{VTABLE_SLOT_RVA:X}"],
            "static_continuations": [],
            "runtime_continuation_status": "requires normal-return observation",
        },
        "indirect_owner": {
            "rtti_type_name": TYPE_NAME,
            "type_descriptor_rva": f"0x{TYPE_DESCRIPTOR_RVA:X}",
            "complete_object_locator_rva": f"0x{COL_RVA:X}",
            "vtable_rva": f"0x{VTABLE_RVA:X}",
            "slot_index": VTABLE_SLOT_INDEX,
            "slot_rva": f"0x{VTABLE_SLOT_RVA:X}",
            "slot_target_rva": f"0x{FUNCTION_RVA:X}",
            "construction_reference_rvas": [
                f"0x{rva:X}" for rva in construction_refs
            ],
            "construction_owner": {
                "reference_rva": "0x82193B",
                "function_rva": f"0x{int(construction_owner.BeginAddress):X}",
                "function_end_rva_exclusive": f"0x{int(construction_owner.EndAddress):X}",
                "unwind_rva": f"0x{int(construction_owner.UnwindData):X}",
            },
            "assignment_stub_rva": "0x88B650",
        },
        "selection": {
            "result": "static-owner-unique-caller-continuation-unknown",
            "next_distinct_stop_point_rva": f"0x{NORMAL_RETURN_RVA:X}",
            "next_read": "[RSP] exact runtime continuation before RET",
            "live_authorized": False,
        },
        "limits": [
            "the unique vtable slot binds callable ownership, not its indirect callsite",
            "there is no direct static continuation to enumerate",
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
