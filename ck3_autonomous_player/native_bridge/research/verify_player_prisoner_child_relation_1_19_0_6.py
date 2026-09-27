#!/usr/bin/env python3
"""Verify the exact CK3 1.19.0.6 child-of registration and read-only ABI."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile


CONTRACT = Path(__file__).with_name("player_prisoner_child_relation_1_19_0_6.json")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--release-script", required=True, type=Path)
    args = parser.parse_args()
    expected = json.loads(CONTRACT.read_text(encoding="utf-8"))
    exact = expected["exact_build"]
    data = args.exe.read_bytes()
    image = pefile.PE(data=data, fast_load=True)
    require(len(data) == exact["executable_size"], "EXE size mismatch")
    require(hashlib.sha256(data).hexdigest().upper() == exact["executable_sha256"],
            "EXE SHA mismatch")
    require(image.OPTIONAL_HEADER.ImageBase == int(exact["image_base"], 16),
            "image base mismatch")
    stock = args.release_script.read_bytes()
    require(hashlib.sha256(stock).hexdigest().upper() == exact["release_script_sha256"],
            "release script SHA mismatch")
    require(b"is_child_of = scope:actor" in stock,
            "release AI child relation use missing")

    def read(rva: int, size: int) -> bytes:
        offset = image.get_offset_from_rva(rva)
        return data[offset:offset + size]

    def number(value: str) -> int:
        return int(value, 16)

    def check_function(entry: dict[str, str]) -> None:
        start = number(entry["start_rva"])
        end = number(entry["end_rva_exclusive"])
        require(start < end and hashlib.sha256(read(start, end - start)).hexdigest().upper()
                == entry["sha256"], f"function SHA mismatch at 0x{start:X}")

    def relative_target(rva: int, opcode: bytes) -> int:
        require(read(rva, len(opcode)) == opcode, f"opcode mismatch at 0x{rva:X}")
        displacement = struct.unpack("<i", read(rva + len(opcode), 4))[0]
        return rva + len(opcode) + 4 + displacement

    chain = expected["production_chain"]
    registration = chain["registration_function"]
    factory = chain["factory_method"]
    wrapper = chain["predicate_wrapper"]
    relation = chain["relation_function"]
    for entry in (registration, factory, wrapper, relation):
        check_function(entry)
    require(read(number(chain["trigger_name_rva"]), 12) == b"is_child_of\0",
            "trigger name mismatch")
    require(relative_target(number(registration["name_reference_instruction_rva"]),
                            bytes.fromhex("48 8D 05")) == number(chain["trigger_name_rva"]),
            "registration name edge mismatch")
    require(relative_target(number(registration["factory_vtable_assignment_rva"]),
                            bytes.fromhex("48 8D 0D")) == number(registration["factory_vtable_rva"]),
            "registration factory edge mismatch")
    require(relative_target(number(factory["predicate_vtable_assignment_rva"]),
                            bytes.fromhex("48 8D 05")) == number(factory["predicate_vtable_rva"]),
            "factory predicate edge mismatch")
    require(relative_target(number(wrapper["tail_jump_instruction_rva"]),
                            bytes.fromhex("E9")) == number(relation["start_rva"]),
            "predicate tail jump mismatch")
    base = image.OPTIONAL_HEADER.ImageBase
    factory_slot = number(registration["factory_vtable_rva"]) + number(
        chain["factory_vtable_method_offset"])
    predicate_slot = number(factory["predicate_vtable_rva"]) + number(
        chain["predicate_vtable_method_offset"])
    require(struct.unpack("<Q", read(factory_slot, 8))[0] == base +
            number(factory["start_rva"]), "factory virtual call mismatch")
    require(struct.unpack("<Q", read(predicate_slot, 8))[0] == base +
            number(wrapper["start_rva"]), "predicate virtual call mismatch")

    # Independent exact instructions identify both arguments and the result.
    for rva, opcode in (
        (0x26085EA, "48 8B 42 10"),  # validate parent character through RDX
        (0x26085F8, "FF 50 08"),
        (0x26085FF, "4C 8B 87 A0 01 00 00"),  # child +0x1A0
        (0x2608610, "41 8B 48 04"),  # second full parent ID
        (0x2608618, "8B 53 18"),  # parent's full CharacterID
        (0x260861B, "3B CA"),
        (0x2608624, "41 8B 00"),  # first full parent ID
        (0x260862B, "B0 01"),
        (0x260863D, "32 C0"),
    ):
        blob = bytes.fromhex(opcode)
        require(read(rva, len(blob)) == blob,
                f"child relation instruction mismatch at 0x{rva:X}")
    print("GREEN_STATIC exact child-of ABI; no paused prisoner readback or release action")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
