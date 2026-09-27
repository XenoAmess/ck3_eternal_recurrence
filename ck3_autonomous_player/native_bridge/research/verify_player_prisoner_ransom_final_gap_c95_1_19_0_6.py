#!/usr/bin/env python3
"""Verify the C95 stock ransom path and native registration without launching CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile


CONTRACT = Path(__file__).with_name(
    "player_prisoner_ransom_final_gap_c95_1_19_0_6.json"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--game-root", type=Path, required=True)
    args = parser.parse_args()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    build = contract["exact_build"]
    for source in contract["stock_sources"]:
        path = args.game_root / source["path"].removeprefix("game/")
        require(path.is_file(), f"missing stock source: {path}")
        require(hashlib.sha256(path.read_bytes()).hexdigest().upper() == source["sha256"],
                f"stock source SHA mismatch: {path}")

    data = args.exe.read_bytes()
    require(len(data) == build["executable_size"], "EXE size mismatch")
    require(hashlib.sha256(data).hexdigest().upper() == build["executable_sha256"],
            "EXE SHA mismatch")
    pe = pefile.PE(data=data, fast_load=True)
    base = int(build["image_base"], 16)
    require(pe.OPTIONAL_HEADER.ImageBase == base, "image base mismatch")

    def read(rva: int, size: int) -> bytes:
        return data[pe.get_offset_from_rva(rva) : pe.get_offset_from_rva(rva) + size]

    def rel_target(rva: int, displacement_offset: int, instruction_size: int) -> int:
        displacement = struct.unpack("<i", read(rva + displacement_offset, 4))[0]
        return rva + instruction_size + displacement

    registration = contract["native_ransom_cost_registration"]
    start = int(registration["function_start_rva"], 16)
    end = int(registration["function_end_rva_exclusive"], 16)
    require(hashlib.sha256(read(start, end - start)).hexdigest().upper() ==
            registration["function_sha256"], "registration function SHA mismatch")
    name = int(registration["name_rva"], 16)
    require(read(name, 12) == b"ransom_cost\0", "script value name mismatch")
    require(rel_target(int(registration["name_lea_rva"], 16), 3, 7) == name,
            "name registration edge mismatch")
    require(rel_target(int(registration["registration_call_rva"], 16), 1, 5) ==
            int(registration["registration_call_target_rva"], 16),
            "script-value registration call mismatch")
    vtable = int(registration["node_vtable_rva"], 16)
    require(rel_target(int(registration["node_vtable_pointer_write_rva"], 16), 3, 7) ==
            vtable, "node vtable edge mismatch")
    thunk = int(registration["factory_thunk_rva"], 16)
    require(struct.unpack("<Q", read(vtable + 8, 8))[0] == base + thunk,
            "factory thunk vtable entry mismatch")
    require(read(thunk, 1) == b"\xe9" and
            rel_target(thunk, 1, 5) == int(registration["factory_body_rva"], 16),
            "factory thunk target mismatch")
    base_evaluator = contract["native_ransom_cost_base_evaluator_c210"]
    factory_start = int(base_evaluator["factory_body_rva"], 16)
    factory_end = int(base_evaluator["factory_body_end_rva_exclusive"], 16)
    require(hashlib.sha256(read(factory_start, factory_end - factory_start)).hexdigest().upper() ==
            base_evaluator["factory_body_sha256"], "base-cost node factory SHA mismatch")
    node_vtable = int(base_evaluator["constructed_node_vtable_rva"], 16)
    require(rel_target(int(base_evaluator["constructed_node_vtable_write_rva"], 16), 3, 7) ==
            node_vtable, "constructed ransom-cost node vtable mismatch")
    value_rva = int(base_evaluator["value_method_rva"], 16)
    require(struct.unpack("<Q", read(node_vtable +
                                  base_evaluator["value_method_vtable_slot"] * 8, 8))[0] ==
            base + value_rva, "base-cost value method vtable entry mismatch")
    value_end = int(base_evaluator["value_method_end_rva_exclusive"], 16)
    require(hashlib.sha256(read(value_rva, value_end - value_rva)).hexdigest().upper() ==
            base_evaluator["value_method_sha256"], "base-cost value method SHA mismatch")
    require(rel_target(int(base_evaluator["native_base_cost_call_rva"], 16), 1, 5) ==
            int(base_evaluator["native_base_cost_target_rva"], 16),
            "base-cost native call mismatch")
    reusable = contract["known_reusable_native_entries_c213"]
    for prefix in ("redirect_roles", "all_role_context_constructor",
                   "compiled_value_evaluator"):
        rva = int(reusable[f"{prefix}_rva"], 16)
        require(hashlib.sha256(read(rva, 64)).hexdigest().upper() ==
                reusable[f"{prefix}_first_64_sha256"],
                f"{prefix} exact-build entry SHA mismatch")
    print("GREEN_STATIC C95/C210/C213 native anchors; final payable amount/action not mapped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
