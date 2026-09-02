#!/usr/bin/env python3
"""Resolve the bounded G2 truce next-layer vtables through exact-build RTTI.

This extractor is read-only.  It parses the MSVC x64 CompleteObjectLocator,
type descriptor, class hierarchy, vtable slots, and scalar deleting
destructor size for the seven positions captured by the prior paused live
probe.  It does not start CK3, inspect a process, or change the public bridge.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
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
MULTIPLE_TARGET_BASE = ".?AVCMultipleTargetEffect@@"


@dataclass(frozen=True)
class RttiContract:
    vtable_rva: int
    col_rva: int
    type_descriptor_rva: int
    class_hierarchy_rva: int
    type_name: str
    base_names: tuple[str, ...]
    deleting_destructor_rva: int
    delete_size_instruction_rva: int
    object_size: int
    live_positions: tuple[str, ...]


CONTRACTS = (
    RttiContract(
        0x4446EF0,
        0x4AB0FC0,
        0x55D1758,
        0x4AB02B8,
        ".?AVCTargetingFactionsDiscontentEffect@@",
        (
            ".?AVCTargetingFactionsDiscontentEffect@@",
            ".?AV?$CJominiValueEffect@VCFixedPoint@@@@",
            ".?AVCJominiEffect@@",
        ),
        0x2DA4530,
        0x2DA4555,
        0x168,
        ("index9.context_child0.child0",),
    ),
    RttiContract(
        0x44D2138,
        0x4B4FD60,
        0x5656100,
        0x4B4F650,
        ".?AV?$CSaveEventTargetAsEffect@$00@@",
        (
            ".?AV?$CSaveEventTargetAsEffect@$00@@",
            ".?AVCSimpleAssignEffect@@",
            ".?AVCJominiEffect@@",
        ),
        0x1978C30,
        0x1978C49,
        0x68,
        (
            "index10.context_child0.child0",
            "index10.context_child0.child1",
        ),
    ),
    RttiContract(
        0x44786C8,
        0x4ACE7D0,
        0x55DFE68,
        0x4ACDF10,
        ".?AV?$CSaveScopeValueAsEffect@$00@@",
        (
            ".?AV?$CSaveScopeValueAsEffect@$00@@",
            ".?AVCJominiEffect@@",
        ),
        0x2F0D180,
        0x2F0D1B1,
        0x278,
        ("index10.context_child0.child2",),
    ),
    RttiContract(
        0x41B1E90,
        0x479C520,
        0x5320BB0,
        0x479C0B8,
        ".?AV?$CScriptedListEffect@VCEveryInScriptedListEffect@@VCCharacterActiveTaskContractList@@@@",
        (
            ".?AV?$CScriptedListEffect@VCEveryInScriptedListEffect@@VCCharacterActiveTaskContractList@@@@",
            ".?AV?$CScriptedListEffectBase@VCCharacterActiveTaskContractList@@VCEveryInScriptedListEffect@@$0A@@@",
            ".?AVCEveryInScriptedListEffect@@",
            ".?AVCTargetInScriptedListEffect@@",
            ".?AVCTargetInListEffect@@",
            ".?AVCMultipleTargetEffect@@",
            ".?AVCJominiEffect@@",
        ),
        0x19280D0,
        0x19280E9,
        0x270,
        ("index10.context_child0.child3",),
    ),
    RttiContract(
        0x44D1E18,
        0x4B50288,
        0x56570B8,
        0x4B50580,
        ".?AVCIfEffect@@",
        (
            ".?AVCIfEffect@@",
            ".?AVCMultipleTargetEffect@@",
            ".?AVCJominiEffect@@",
        ),
        0x338C2D0,
        0x338C303,
        0x260,
        (
            "index9.context_child0",
            "index10.context_child0.child4",
            "index10.context_child0.child5",
        ),
    ),
)

TARGET = RttiContract(
    0x4461CA8,
    0x4AC06B8,
    0x55D9598,
    0x4ABFE98,
    ".?AV?$CAddTruceEffect@$0A@@@",
    (
        ".?AV?$CAddTruceEffect@$0A@@@",
        ".?AVCJominiEffect@@",
    ),
    0x2EDC0B0,
    0x2EDC180,
    0x1F8,
    (),
)

CIF_OPTIONAL_EFFECT_POINTER_RVA = 0x338C2DF
CIF_OPTIONAL_EFFECT_POINTER_BYTES = bytes.fromhex(
    "48 8B 89 58 02 00 00 48 85 C9 74 0A 48 8B 01 BA 01 00 00 00 FF 10"
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


def u32(data: bytes, image: pefile.PE, rva: int) -> int:
    return struct.unpack("<I", bytes_at(data, image, rva, 4))[0]


def u64(data: bytes, image: pefile.PE, rva: int) -> int:
    return struct.unpack("<Q", bytes_at(data, image, rva, 8))[0]


def rtti_name(data: bytes, image: pefile.PE, type_rva: int) -> str:
    start = image.get_offset_from_rva(type_rva) + 16
    end = data.find(b"\0", start, start + 1024)
    if end < 0:
        raise ValueError(f"unterminated RTTI name at RVA 0x{type_rva:X}")
    return data[start:end].decode("ascii")


def extract_contract(
    data: bytes,
    image: pefile.PE,
    image_base: int,
    contract: RttiContract,
) -> dict[str, Any]:
    col_va = u64(data, image, contract.vtable_rva - 8)
    col_rva = col_va - image_base
    if col_rva != contract.col_rva:
        raise ValueError(
            f"vtable 0x{contract.vtable_rva:X} COL changed: 0x{col_rva:X}"
        )
    col = struct.unpack("<6I", bytes_at(data, image, col_rva, 24))
    signature, object_offset, constructor_displacement, type_rva, hierarchy_rva, self_rva = col
    if signature != 1 or self_rva != col_rva:
        raise ValueError(f"invalid x64 COL at RVA 0x{col_rva:X}")
    if object_offset != 0 or constructor_displacement != 0:
        raise ValueError(f"non-primary vtable at RVA 0x{contract.vtable_rva:X}")
    if type_rva != contract.type_descriptor_rva:
        raise ValueError(f"type descriptor changed at RVA 0x{contract.vtable_rva:X}")
    if hierarchy_rva != contract.class_hierarchy_rva:
        raise ValueError(f"class hierarchy changed at RVA 0x{contract.vtable_rva:X}")
    type_name = rtti_name(data, image, type_rva)
    if type_name != contract.type_name:
        raise ValueError(f"RTTI name changed at RVA 0x{contract.vtable_rva:X}")

    hierarchy = struct.unpack("<4I", bytes_at(data, image, hierarchy_rva, 16))
    hierarchy_signature, hierarchy_attributes, base_count, base_array_rva = hierarchy
    base_descriptor_rvas = [
        u32(data, image, base_array_rva + index * 4)
        for index in range(base_count)
    ]
    base_names = tuple(
        rtti_name(data, image, u32(data, image, descriptor_rva))
        for descriptor_rva in base_descriptor_rvas
    )
    if base_names != contract.base_names:
        raise ValueError(
            f"base hierarchy changed at RVA 0x{contract.vtable_rva:X}: {base_names!r}"
        )

    slots = [u64(data, image, contract.vtable_rva + index * 8) for index in range(12)]
    slot_rvas = [value - image_base for value in slots]
    if slot_rvas[0] != contract.deleting_destructor_rva:
        raise ValueError(f"deleting destructor changed at RVA 0x{contract.vtable_rva:X}")
    delete_size = bytes_at(data, image, contract.delete_size_instruction_rva, 5)
    if delete_size[0] != 0xBA or struct.unpack("<I", delete_size[1:])[0] != contract.object_size:
        raise ValueError(f"object size changed at RVA 0x{contract.vtable_rva:X}")

    multiple_target = MULTIPLE_TARGET_BASE in base_names
    return {
        "vtable_rva": f"0x{contract.vtable_rva:X}",
        "complete_object_locator": {
            "rva": f"0x{col_rva:X}",
            "signature": signature,
            "object_offset": object_offset,
            "constructor_displacement": constructor_displacement,
            "self_rva": f"0x{self_rva:X}",
        },
        "type_descriptor_rva": f"0x{type_rva:X}",
        "class_hierarchy_rva": f"0x{hierarchy_rva:X}",
        "rtti_type_name": type_name,
        "base_types": list(base_names),
        "hierarchy_signature": hierarchy_signature,
        "hierarchy_attributes": f"0x{hierarchy_attributes:X}",
        "primary_vtable": True,
        "deleting_destructor_rva": f"0x{slot_rvas[0]:X}",
        "object_size": f"0x{contract.object_size:X}",
        "first_twelve_slot_rvas": [f"0x{value:X}" for value in slot_rvas],
        "first_twelve_slots_sha256": sha256(
            bytes_at(data, image, contract.vtable_rva, 12 * 8)
        ),
        "multiple_target_effect_base": multiple_target,
        "bounded_container_classification": (
            "multiple_target_composite"
            if multiple_target
            else "no_multiple_target_base"
        ),
        "live_positions": list(contract.live_positions),
    }


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

    candidates = [
        extract_contract(data, image, image_base, contract)
        for contract in CONTRACTS
    ]
    target = extract_contract(data, image, image_base, TARGET)
    cif_span = bytes_at(
        data,
        image,
        CIF_OPTIONAL_EFFECT_POINTER_RVA,
        len(CIF_OPTIONAL_EFFECT_POINTER_BYTES),
    )
    if cif_span != CIF_OPTIONAL_EFFECT_POINTER_BYTES:
        raise ValueError("CIfEffect +0x258 owned optional-effect pointer span changed")

    remaining_positions = [
        position
        for candidate in candidates
        if candidate["multiple_target_effect_base"]
        for position in candidate["live_positions"]
    ]
    excluded_positions = [
        position
        for candidate in candidates
        if not candidate["multiple_target_effect_base"]
        for position in candidate["live_positions"]
    ]
    return {
        "schema": "xar.ck3.g2_truce_next_layer_rtti.extract.v1",
        "result": "GREEN",
        "read_only": True,
        "ck3_started": False,
        "exact_build": {
            "product_version": "1.19.0.6",
            "sha256": digest,
            "file_size": len(data),
            "image_base": f"0x{image_base:X}",
        },
        "observed_next_layer_candidates": candidates,
        "target_truce_effect": target,
        "cif_optional_effect_storage": {
            "owner_vtable_rva": "0x44D1E18",
            "field_offset": "0x258",
            "destructor_span_rva": f"0x{CIF_OPTIONAL_EFFECT_POINTER_RVA:X}",
            "destructor_span_hex": cif_span.hex().upper(),
            "decoded_shape": (
                "load this+0x258; if non-null call pointee vtable slot 0 with delete flag 1"
            ),
        },
        "bounded_path_classification": {
            "direct_truce_matches": 0,
            "remaining_multiple_target_positions": remaining_positions,
            "excluded_from_common_multiple_target_walk": excluded_positions,
            "unique_path_identified": False,
            "next_read_only_entry": (
                "inspect index9 CIfEffect +0x258; index10 child3 common effect vector; "
                "and index10 child4/child5 common vectors plus +0x258"
            ),
        },
        "boundaries": {
            "public_abi_changed": False,
            "readiness_changed": False,
            "production_shape_contract_changed": False,
            "mutation_sent": False,
        },
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
