#!/usr/bin/env python3
"""Inspect the exact CK3 build's defender surrender title preview path.

This reads the executable only. It never starts CK3 or calls an effect.
"""

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

    def verify_rtti(type_rva: int, col_rva: int, vtable_rva: int, name: str) -> None:
        if at(type_rva + 16, len(name) + 1) != name.encode() + b"\0":
            raise ValueError(f"RTTI name mismatch at 0x{type_rva:X}")
        signature, offset, cd_offset, type_pointer, _, self_pointer = struct.unpack(
            "<6I", at(col_rva, 24)
        )
        if (signature, offset, cd_offset, type_pointer, self_pointer) != (
            1, 0, 0, type_rva, col_rva
        ):
            raise ValueError(f"RTTI COL mismatch at 0x{col_rva:X}")
        if pointer(vtable_rva - 8) != col_rva:
            raise ValueError(f"vtable/COL mismatch at 0x{vtable_rva:X}")

    def verify_call(source_rva: int, target_rva: int) -> str:
        instruction = at(source_rva, 5)
        if instruction[0] != 0xE8:
            raise ValueError(f"expected direct call at 0x{source_rva:X}")
        displacement = struct.unpack_from("<i", instruction, 1)[0]
        if source_rva + 5 + displacement != target_rva:
            raise ValueError(f"call target mismatch at 0x{source_rva:X}")
        return instruction.hex().upper()

    verify_rtti(
        0x55D73A0, 0x4ABDAE0, 0x445CAD0,
        ".?AVCResolveTitleAndVassalChangeEffect@@",
    )
    verify_rtti(
        0x5210BE8, 0x467B030, 0x4108EE8,
        ".?AVCTitleAndVassalTransferVisitor@@",
    )
    verify_rtti(
        0x55D2F10, 0x4AB2E50, 0x444B548,
        ".?AV?$CSetupClaimCBEffect@$0A@@@",
    )

    resolve_execute = pointer(0x445CAD0 + 0xB0)
    resolve_preview = pointer(0x445CAD0 + 0xB8)
    setup_execute = pointer(0x444B548 + 0xB0)
    setup_preview = pointer(0x444B548 + 0xB8)
    if (resolve_execute, resolve_preview, setup_execute, setup_preview) != (
        0x2EC43F0, 0x7E9220, 0x2EA8200, 0x2EA7E90
    ):
        raise ValueError("title effect execute/preview dispatch changed")
    if at(resolve_preview, 3) != bytes.fromhex("B001C3"):
        raise ValueError("resolve-title preview is no longer the two-instruction stub")
    if at(0xF59722, 7) != bytes.fromhex("488B9000010000"):
        raise ValueError("WarOverview CB type load changed")
    if at(0xF59729, 7) != bytes.fromhex("4881C268090000"):
        raise ValueError("WarOverview victory root +0x968 changed")
    victory_call = verify_call(0xF59738, 0xF5BFD0)
    preview_call = verify_call(0xF5C09F, 0x3380170)
    if at(0xF5C038, 7) != bytes.fromhex("488D0DA9CE1A03"):
        raise ValueError("native title visitor construction changed")

    return {
        "schema": "xar.ck3.defender-surrender-title-preview-abi.v1",
        "status": "STATIC_RESOLVE_EFFECT_PREVIEW_NOOP",
        "exact_build": {"version": "1.19.0.6", "exe_sha256": digest},
        "absolute_outcome": "attacker_victory for played primary-defender surrender",
        "war_overview": {
            "victory_root_offset": "CB+0x968",
            "root_call_rva": "0xF59738",
            "root_call_bytes": victory_call,
            "title_visitor_ctor_rva": "0xF5C038",
            "preview_dispatch_call_rva": "0xF5C09F",
            "preview_dispatch_call_bytes": preview_call,
            "preview_dispatch_target_rva": "0x3380170",
        },
        "resolve_title_and_vassal_change": {
            "rtti_type_descriptor_rva": "0x55D73A0",
            "rtti_col_rva": "0x4ABDAE0",
            "runtime_vtable_rva": "0x445CAD0",
            "execute_slot_22_rva": f"0x{resolve_execute:X}",
            "preview_slot_23_rva": f"0x{resolve_preview:X}",
            "preview_bytes": "B0 01 C3",
            "preview_semantics": "returns true without visiting title/vassal operations",
        },
        "setup_claim_cb": {
            "runtime_vtable_rva": "0x444B548",
            "execute_slot_22_rva": f"0x{setup_execute:X}",
            "preview_slot_23_rva": f"0x{setup_preview:X}",
        },
        "title_transfer_visitor": {
            "rtti_type_descriptor_rva": "0x5210BE8",
            "rtti_col_rva": "0x467B030",
            "runtime_vtable_rva": "0x4108EE8",
            "method_slot_2_rva": f"0x{pointer(0x4108EE8 + 16):X}",
        },
        "boundary": {
            "effect_called": False,
            "ck3_launched": False,
            "material_title_liege_resource_terms_ready": False,
            "next_locator": "Trace the native WarOverview title visitor payload and independent CTitleAndVassalChange actual-move producer; the resolve effect's preview cannot supply resolved operations.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    value = extract(args.exe)
    result = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if args.output is None:
        print(result, end="")
    else:
        args.output.write_bytes(result.encode("utf-8"))
        print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
