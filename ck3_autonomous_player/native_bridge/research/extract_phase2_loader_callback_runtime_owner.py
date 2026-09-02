#!/usr/bin/env python3
"""Bind the observed phase-two callback vptr to exact-build MSVC RTTI.

This extractor is read-only.  It verifies the pinned CK3 executable, follows
the x64 CompleteObjectLocator immediately before the observed vtable, checks
the class hierarchy, and decodes the observed slot-2 thunk.  It neither starts
CK3 nor changes the public bridge.
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
RUNTIME_VTABLE_RVA = 0x408A450
RUNTIME_SLOT_2_TARGET_RVA = 0x947BD0
EXPECTED_COL_RVA = 0x45BD3B0
EXPECTED_TYPE_DESCRIPTOR_RVA = 0x514FE60
EXPECTED_CLASS_HIERARCHY_RVA = 0x45B6270
EXPECTED_TYPE_NAME = ".?AV?$_Func_impl_no_alloc@P6AXXZX$$V@std@@"
EXPECTED_UNDECORATED_TYPE = (
    "class std::_Func_impl_no_alloc<void (__cdecl*)(void),void>"
)
EXPECTED_BASE_TYPES = (
    ".?AV?$_Func_impl_no_alloc@P6AXXZX$$V@std@@",
    ".?AV?$_Func_base@X$$V@std@@",
)
EXPECTED_SLOT_2_BYTES = bytes.fromhex("48 FF 61 08")


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


def u32(data: bytes, image: pefile.PE, rva: int) -> int:
    return struct.unpack("<I", bytes_at(data, image, rva, 4))[0]


def u64(data: bytes, image: pefile.PE, rva: int) -> int:
    return struct.unpack("<Q", bytes_at(data, image, rva, 8))[0]


def rtti_name(data: bytes, image: pefile.PE, type_rva: int) -> str:
    start = image.get_offset_from_rva(type_rva) + 16
    end = data.find(b"\0", start, start + 512)
    if end < 0:
        raise ValueError(f"unterminated RTTI name at RVA 0x{type_rva:X}")
    return data[start:end].decode("ascii")


def extract(exe: Path) -> dict[str, Any]:
    data = exe.read_bytes()
    if len(data) != EXPECTED_SIZE:
        raise ValueError(f"unexpected executable size: {len(data)}")
    digest = sha256(data)
    if digest != EXPECTED_SHA256:
        raise ValueError(f"unexpected executable SHA-256: {digest}")

    image = pefile.PE(data=data, fast_load=True)
    image_base = int(image.OPTIONAL_HEADER.ImageBase)
    if image_base != EXPECTED_IMAGE_BASE:
        raise ValueError(f"unexpected image base: 0x{image_base:X}")

    col_va = u64(data, image, RUNTIME_VTABLE_RVA - 8)
    col_rva = col_va - image_base
    if col_rva != EXPECTED_COL_RVA:
        raise ValueError(f"unexpected COL RVA: 0x{col_rva:X}")
    col = struct.unpack(
        "<IIIIII", bytes_at(data, image, col_rva, 24)
    )
    signature, object_offset, constructor_displacement, type_rva, hierarchy_rva, self_rva = col
    if signature != 1 or self_rva != col_rva:
        raise ValueError("invalid x64 self-relative CompleteObjectLocator")
    if type_rva != EXPECTED_TYPE_DESCRIPTOR_RVA:
        raise ValueError(f"unexpected type descriptor RVA: 0x{type_rva:X}")
    if hierarchy_rva != EXPECTED_CLASS_HIERARCHY_RVA:
        raise ValueError(f"unexpected class hierarchy RVA: 0x{hierarchy_rva:X}")
    type_name = rtti_name(data, image, type_rva)
    if type_name != EXPECTED_TYPE_NAME:
        raise ValueError(f"unexpected RTTI type name: {type_name}")

    hierarchy = struct.unpack(
        "<IIII", bytes_at(data, image, hierarchy_rva, 16)
    )
    hierarchy_signature, hierarchy_attributes, base_count, base_array_rva = hierarchy
    base_descriptor_rvas = [
        u32(data, image, base_array_rva + index * 4)
        for index in range(base_count)
    ]
    base_types: list[dict[str, Any]] = []
    for descriptor_rva in base_descriptor_rvas:
        descriptor = struct.unpack(
            "<IIiiiII", bytes_at(data, image, descriptor_rva, 28)
        )
        (
            base_type_rva,
            contained_bases,
            member_displacement,
            vbtable_displacement,
            displacement_inside_vbtable,
            attributes,
            base_hierarchy_rva,
        ) = descriptor
        base_types.append(
            {
                "base_class_descriptor_rva": f"0x{descriptor_rva:X}",
                "type_descriptor_rva": f"0x{base_type_rva:X}",
                "type_name": rtti_name(data, image, base_type_rva),
                "contained_bases": contained_bases,
                "pmd": {
                    "member_displacement": member_displacement,
                    "vbtable_displacement": vbtable_displacement,
                    "displacement_inside_vbtable": displacement_inside_vbtable,
                },
                "attributes": f"0x{attributes:X}",
                "class_hierarchy_rva": f"0x{base_hierarchy_rva:X}",
            }
        )
    names = tuple(row["type_name"] for row in base_types)
    if names != EXPECTED_BASE_TYPES:
        raise ValueError(f"unexpected RTTI base types: {names!r}")

    slots = [u64(data, image, RUNTIME_VTABLE_RVA + index * 8) for index in range(6)]
    slot_rvas = [value - image_base for value in slots]
    if slot_rvas[2] != RUNTIME_SLOT_2_TARGET_RVA:
        raise ValueError(f"unexpected slot-2 target RVA: 0x{slot_rvas[2]:X}")
    slot_2_bytes = bytes_at(data, image, slot_rvas[2], len(EXPECTED_SLOT_2_BYTES))
    if slot_2_bytes != EXPECTED_SLOT_2_BYTES:
        raise ValueError(
            f"unexpected slot-2 thunk bytes: {slot_2_bytes.hex().upper()}"
        )

    return {
        "schema": "xar.phase2.loader_callback_runtime_owner.extract.v1",
        "result": "GREEN",
        "read_only": True,
        "ck3_started": False,
        "executable": str(exe.resolve()),
        "exact_build": {
            "product_version": "1.19.0.6",
            "sha256": digest,
            "file_size": len(data),
            "image_base": f"0x{image_base:X}",
        },
        "observed_runtime_identity": {
            "vtable_rva": f"0x{RUNTIME_VTABLE_RVA:X}",
            "slot_2_target_rva": f"0x{RUNTIME_SLOT_2_TARGET_RVA:X}",
        },
        "complete_object_locator": {
            "rva": f"0x{col_rva:X}",
            "signature": signature,
            "object_offset": object_offset,
            "constructor_displacement": constructor_displacement,
            "type_descriptor_rva": f"0x{type_rva:X}",
            "class_hierarchy_rva": f"0x{hierarchy_rva:X}",
            "self_rva": f"0x{self_rva:X}",
        },
        "owner": {
            "rtti_type_name": type_name,
            "undecorated_type": EXPECTED_UNDECORATED_TYPE,
            "callback_storage": "receiver+0x08",
            "callback_signature": "void (__cdecl*)(void)",
            "invoke_return_kind": "void",
        },
        "class_hierarchy": {
            "signature": hierarchy_signature,
            "attributes": f"0x{hierarchy_attributes:X}",
            "base_count": base_count,
            "base_array_rva": f"0x{base_array_rva:X}",
            "base_types": base_types,
        },
        "vtable": {
            "first_six_slot_rvas": [f"0x{value:X}" for value in slot_rvas],
            "first_six_slots_sha256": sha256(
                bytes_at(data, image, RUNTIME_VTABLE_RVA, 6 * 8)
            ),
            "slot_2": {
                "target_rva": f"0x{slot_rvas[2]:X}",
                "bytes_hex": slot_2_bytes.hex().upper(),
                "decoded_shape": "jmp qword ptr [rcx+0x08]",
            },
        },
        "limits": [
            "RTTI binds the wrapper type, not the concrete function pointer stored at receiver+0x08",
            "static thunk bytes establish a void function-pointer call shape but do not prove one runtime invocation returned",
            "no source filename, callback object post-return lifetime, or loader readiness follows",
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
