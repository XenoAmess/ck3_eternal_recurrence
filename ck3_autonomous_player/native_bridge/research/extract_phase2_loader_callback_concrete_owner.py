#!/usr/bin/env python3
"""Bind concrete loader callback RVA 0x2045330 to its direct owner path.

The scan is deliberately bounded to the concrete callback, its sole
RIP-relative construction reference, the containing registration function,
and the two RTTI vtables that directly contain that function.  It is
read-only, exact-build bound, and never starts CK3.
"""

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
CALLBACK_RVA = 0x2045330
CALLBACK_END_RVA = 0x204533E
CALLBACK_GLOBAL_RVA = 0x570C0F0
CONSTRUCTION_REF_RVA = 0x8235A5
OWNER_FUNCTION_RVA = 0x823570
OWNER_FUNCTION_END_RVA = 0x823647
OWNER_UNWIND_RVA = 0x4C3F330
REGISTRATION_CALL_RVA = 0x8235FD
REGISTRATION_TARGET_RVA = 0x2043D80
WRAPPER_VTABLE_RVA = 0x408A450
CALLBACK_BYTES = bytes.fromhex(
    "48 8B 0D B9 6D 6C 03 48 8B 01 48 FF 60 10"
)

OWNER_VTABLES = (
    {
        "col_pointer_rva": 0x4093150,
        "col_rva": 0x45C4FC0,
        "vtable_rva": 0x4093158,
        "slot_index": 23,
        "slot_rva": 0x4093210,
        "type_descriptor_rva": 0x51665E0,
        "type_name": ".?AVCInterfaceApplication@@",
    },
    {
        "col_pointer_rva": 0x428BC70,
        "col_rva": 0x48F22C8,
        "vtable_rva": 0x428BC78,
        "slot_index": 23,
        "slot_rva": 0x428BD30,
        "type_descriptor_rva": 0x5166560,
        "type_name": ".?AVCGameApplication@@",
    },
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def bytes_at(data: bytes, image: pefile.PE, rva: int, size: int) -> bytes:
    try:
        offset = image.get_offset_from_rva(rva)
    except pefile.PEFormatError as exc:
        raise ValueError(f"RVA 0x{rva:X} is outside the image") from exc
    value = data[offset : offset + size]
    if len(value) != size:
        raise ValueError(f"short read at RVA 0x{rva:X}")
    return value


def rtti_name(data: bytes, image: pefile.PE, type_rva: int) -> str:
    start = image.get_offset_from_rva(type_rva) + 16
    end = data.find(b"\0", start, start + 512)
    if end < 0:
        raise ValueError(f"unterminated RTTI name at RVA 0x{type_rva:X}")
    return data[start:end].decode("ascii")


def rel32_target(instruction_rva: int, raw: bytes) -> int:
    return instruction_rva + len(raw) + struct.unpack("<i", raw[-4:])[0]


def all_occurrences(data: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        offset = data.find(needle, start)
        if offset < 0:
            return offsets
        offsets.append(offset)
        start = offset + 1


def extract(exe: Path) -> dict[str, Any]:
    data = exe.read_bytes()
    if len(data) != EXPECTED_SIZE:
        raise ValueError(f"unexpected executable size: {len(data)}")
    digest = sha256(data)
    if digest != EXPECTED_SHA256:
        raise ValueError(f"unexpected executable SHA-256: {digest}")
    image = pefile.PE(data=data, fast_load=False)
    image_base = int(image.OPTIONAL_HEADER.ImageBase)
    if image_base != EXPECTED_IMAGE_BASE:
        raise ValueError(f"unexpected image base: 0x{image_base:X}")

    callback = bytes_at(data, image, CALLBACK_RVA, len(CALLBACK_BYTES))
    if callback != CALLBACK_BYTES:
        raise ValueError("concrete callback bytes changed")
    global_target = rel32_target(CALLBACK_RVA, callback[:7])
    if global_target != CALLBACK_GLOBAL_RVA:
        raise ValueError(f"unexpected callback global RVA: 0x{global_target:X}")

    construction_bytes = bytes_at(data, image, CONSTRUCTION_REF_RVA, 7)
    if construction_bytes[:3] != bytes.fromhex("48 8D 05"):
        raise ValueError("construction reference is not lea rax,[rip+rel32]")
    if rel32_target(CONSTRUCTION_REF_RVA, construction_bytes) != CALLBACK_RVA:
        raise ValueError("construction reference does not resolve to callback")

    callback_lea_refs: list[int] = []
    for offset in all_occurrences(data, bytes.fromhex("48 8D 05")):
        try:
            rva = image.get_rva_from_offset(offset)
        except pefile.PEFormatError:
            continue
        raw = data[offset : offset + 7]
        if len(raw) == 7 and rel32_target(rva, raw) == CALLBACK_RVA:
            callback_lea_refs.append(rva)
    if callback_lea_refs != [CONSTRUCTION_REF_RVA]:
        raise ValueError(f"callback construction refs changed: {callback_lea_refs!r}")

    registration_bytes = bytes_at(data, image, REGISTRATION_CALL_RVA, 5)
    if registration_bytes[0] != 0xE8 or rel32_target(
        REGISTRATION_CALL_RVA, registration_bytes
    ) != REGISTRATION_TARGET_RVA:
        raise ValueError("registration call target changed")

    wrapper_load = bytes_at(data, image, 0x82357E, 7)
    if wrapper_load[:3] != bytes.fromhex("48 8D 0D") or rel32_target(
        0x82357E, wrapper_load
    ) != WRAPPER_VTABLE_RVA:
        raise ValueError("owner no longer loads the observed wrapper vtable")

    pdata_rows = [
        entry
        for entry in image.DIRECTORY_ENTRY_EXCEPTION
        if entry.struct.BeginAddress <= OWNER_FUNCTION_RVA
        < entry.struct.EndAddress
    ]
    if len(pdata_rows) != 1:
        raise ValueError(f"owner PDATA match count changed: {len(pdata_rows)}")
    pdata = pdata_rows[0].struct
    if (
        pdata.BeginAddress != OWNER_FUNCTION_RVA
        or pdata.EndAddress != OWNER_FUNCTION_END_RVA
        or pdata.UnwindData != OWNER_UNWIND_RVA
    ):
        raise ValueError("owner PDATA boundary changed")

    owner_va = image_base + OWNER_FUNCTION_RVA
    absolute_owner_refs = [
        image.get_rva_from_offset(offset)
        for offset in all_occurrences(data, struct.pack("<Q", owner_va))
    ]
    expected_slots = [row["slot_rva"] for row in OWNER_VTABLES]
    if absolute_owner_refs != expected_slots:
        raise ValueError(f"owner absolute refs changed: {absolute_owner_refs!r}")

    owner_vtables: list[dict[str, Any]] = []
    for expected in OWNER_VTABLES:
        col_va = struct.unpack(
            "<Q", bytes_at(data, image, expected["col_pointer_rva"], 8)
        )[0]
        col_rva = col_va - image_base
        if col_rva != expected["col_rva"]:
            raise ValueError("owner COL pointer changed")
        col = struct.unpack("<IIIIII", bytes_at(data, image, col_rva, 24))
        signature, _, _, type_rva, hierarchy_rva, self_rva = col
        if signature != 1 or self_rva != col_rva:
            raise ValueError("invalid owner self-relative COL")
        if type_rva != expected["type_descriptor_rva"]:
            raise ValueError("owner type descriptor changed")
        name = rtti_name(data, image, type_rva)
        if name != expected["type_name"]:
            raise ValueError(f"owner RTTI name changed: {name}")
        slot_va = struct.unpack(
            "<Q", bytes_at(data, image, expected["slot_rva"], 8)
        )[0]
        if slot_va - image_base != OWNER_FUNCTION_RVA:
            raise ValueError("owner vtable slot target changed")
        if expected["vtable_rva"] + expected["slot_index"] * 8 != expected["slot_rva"]:
            raise ValueError("owner vtable slot arithmetic changed")
        owner_vtables.append(
            {
                "rtti_type_name": name,
                "complete_object_locator_rva": f"0x{col_rva:X}",
                "type_descriptor_rva": f"0x{type_rva:X}",
                "class_hierarchy_rva": f"0x{hierarchy_rva:X}",
                "vtable_rva": f"0x{expected['vtable_rva']:X}",
                "slot_index": expected["slot_index"],
                "slot_rva": f"0x{expected['slot_rva']:X}",
                "slot_target_rva": f"0x{OWNER_FUNCTION_RVA:X}",
            }
        )

    owner_bytes = bytes_at(
        data, image, OWNER_FUNCTION_RVA, OWNER_FUNCTION_END_RVA - OWNER_FUNCTION_RVA
    )
    return {
        "schema": "xar.phase2.loader_callback_concrete_owner.extract.v1",
        "result": "GREEN",
        "read_only": True,
        "ck3_started": False,
        "exact_build": {
            "product_version": "1.19.0.6",
            "sha256": digest,
            "file_size": len(data),
            "image_base": f"0x{image_base:X}",
        },
        "concrete_callback": {
            "rva": f"0x{CALLBACK_RVA:X}",
            "end_rva_exclusive": f"0x{CALLBACK_END_RVA:X}",
            "bytes_hex": callback.hex().upper(),
            "bytes_sha256": sha256(callback),
            "shape": "load global object pointer; load vptr; tail-jump vtable slot 2",
            "global_object_pointer_rva": f"0x{global_target:X}",
        },
        "direct_construction_path": {
            "construction_reference_rva": f"0x{CONSTRUCTION_REF_RVA:X}",
            "construction_reference_bytes": construction_bytes.hex().upper(),
            "all_rip_relative_construction_refs": [
                f"0x{rva:X}" for rva in callback_lea_refs
            ],
            "containing_function_rva": f"0x{OWNER_FUNCTION_RVA:X}",
            "containing_function_end_rva_exclusive": f"0x{OWNER_FUNCTION_END_RVA:X}",
            "containing_function_bytes_sha256": sha256(owner_bytes),
            "unwind_info_rva": f"0x{OWNER_UNWIND_RVA:X}",
            "wrapper_vtable_rva": f"0x{WRAPPER_VTABLE_RVA:X}",
            "registration_call_rva": f"0x{REGISTRATION_CALL_RVA:X}",
            "registration_target_rva": f"0x{REGISTRATION_TARGET_RVA:X}",
        },
        "source_owner": {
            "unique_code_owner_rva": f"0x{OWNER_FUNCTION_RVA:X}",
            "virtual_slot_index": 23,
            "rtti_vtables": owner_vtables,
            "bounded_identity": "shared CInterfaceApplication/CGameApplication virtual slot 23 registration body",
            "class_method_name": "unknown",
        },
        "limits": [
            "the code owner is unique, but the same inherited/overridden body appears in both CInterfaceApplication and CGameApplication vtables",
            "no method name is assigned without symbols",
            "the concrete callback tail-dispatches a global object's slot 2; that global runtime type is not inferred here",
            "no later stalled node, source filename, loader readiness, or production detour follows",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    payload = extract(arguments.exe.resolve())
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if arguments.output is None:
        print(text, end="")
    else:
        output = arguments.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
