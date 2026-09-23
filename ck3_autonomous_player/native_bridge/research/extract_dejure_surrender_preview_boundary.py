#!/usr/bin/env python3
"""Freeze the exact-build de-jure surrender effect dispatch without calling it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXE_SIZE = 95_206_008
IMAGE_BASE = 0x140000000
SETUP_RTTI_NAME = b".?AVCSetupDeJureCBChangeEffect@@\0"


def extract(exe: Path) -> dict[str, object]:
    data = exe.read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if len(data) != EXE_SIZE or digest != EXE_SHA256:
        raise ValueError("CK3 executable differs from frozen 1.19.0.6 build")
    image = pefile.PE(data=data, fast_load=True)
    if image.OPTIONAL_HEADER.ImageBase != IMAGE_BASE:
        raise ValueError("unexpected image base")

    def at(rva: int, size: int) -> bytes:
        offset = image.get_offset_from_rva(rva)
        value = data[offset : offset + size]
        if len(value) != size:
            raise ValueError(f"short read at RVA 0x{rva:X}")
        return value

    def pointer(rva: int) -> int:
        return struct.unpack("<Q", at(rva, 8))[0] - IMAGE_BASE

    def direct_call(source_rva: int, expected_target: int) -> str:
        instruction = at(source_rva, 5)
        if instruction[0] != 0xE8:
            raise ValueError(f"expected direct call at 0x{source_rva:X}")
        actual_target = source_rva + 5 + struct.unpack_from("<i", instruction, 1)[0]
        if actual_target != expected_target:
            raise ValueError(f"call at 0x{source_rva:X} changed target")
        return instruction.hex().upper()

    name_offset = data.find(SETUP_RTTI_NAME)
    if name_offset < 16 or data.find(SETUP_RTTI_NAME, name_offset + 1) >= 0:
        raise ValueError("setup-de-jure RTTI identity is absent or ambiguous")
    type_rva = image.get_rva_from_offset(name_offset) - 16
    type_references = struct.pack("<I", type_rva)
    complete_object_locators: list[int] = []
    scan = 0
    while (found := data.find(type_references, scan)) >= 0:
        scan = found + 1
        if found < 12:
            continue
        locator_offset = found - 12
        locator_rva = image.get_rva_from_offset(locator_offset)
        if struct.unpack_from("<6I", data, locator_offset) == (
            1, 0, 0, type_rva, 0x4AB3420, locator_rva
        ):
            complete_object_locators.append(locator_rva)
    if complete_object_locators != [0x4AB2FB8]:
        raise ValueError("setup-de-jure RTTI locator changed")

    locator_pointer = struct.pack("<Q", IMAGE_BASE + complete_object_locators[0])
    pointer_offset = data.find(locator_pointer)
    if pointer_offset < 0 or data.find(locator_pointer, pointer_offset + 1) >= 0:
        raise ValueError("setup-de-jure vtable identity is absent or ambiguous")
    vtable_rva = image.get_rva_from_offset(pointer_offset) + 8
    execute_rva = pointer(vtable_rva + 0xB0)
    preview_rva = pointer(vtable_rva + 0xB8)
    if (vtable_rva, execute_rva, preview_rva) != (
        0x444AFA0, 0x2E9F420, 0x2E9FA10
    ):
        raise ValueError("setup-de-jure execute/preview dispatch changed")
    if pointer(0x445CAD0 + 0xB8) != 0x7E9220 or at(0x7E9220, 3) != bytes.fromhex("B001C3"):
        raise ValueError("resolve-title preview boundary changed")

    return {
        "schema": "xar.ck3.dejure-defender-surrender-preview-boundary.v1",
        "status": "STATIC_PREVIEW_DISPATCH_ONLY",
        "exact_build": {"version": "1.19.0.6-steam23530548", "exe_sha256": digest},
        "setup_de_jure_cb_change_effect": {
            "rtti_type_descriptor_rva": f"0x{type_rva:X}",
            "rtti_col_rva": f"0x{complete_object_locators[0]:X}",
            "runtime_vtable_rva": f"0x{vtable_rva:X}",
            "execute_slot_22_rva": f"0x{execute_rva:X}",
            "preview_slot_23_rva": f"0x{preview_rva:X}",
            "preview_helper_call_rva": "0x2E9FBC8",
            "preview_helper_rva": "0x2E9FF30",
            "preview_helper_call_bytes": direct_call(0x2E9FBC8, 0x2E9FF30),
            "preview_output_helper_call_rva": "0x2E9FBE8",
            "preview_output_helper_rva": "0x2E9F190",
            "preview_output_helper_call_bytes": direct_call(0x2E9FBE8, 0x2E9F190),
            "execute_only_observed_call_rva": "0x2E9F60C",
            "execute_only_observed_target_rva": "0x8122E0",
            "execute_only_observed_call_bytes": direct_call(0x2E9F60C, 0x8122E0),
        },
        "resolve_title_and_vassal_change_effect": {
            "preview_slot_23_rva": "0x7E9220",
            "preview_bytes": "B0 01 C3",
            "preview_semantics": "returns true without producing resolved title/vassal operations",
        },
        "boundary": {
            "ck3_launched": False,
            "effect_called": False,
            "preview_safe_to_call": False,
            "final_title_holder_liege_vassal_operations_observed": False,
            "signed_resource_deltas_observed": False,
            "next_locator": "Prove ownership and effects of setup preview's +0x260 change object and shared helper 0x2E9FF30; then locate a non-mutating producer of complete resolved operations and signed resource deltas.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(extract(args.exe), indent=2, ensure_ascii=False) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
