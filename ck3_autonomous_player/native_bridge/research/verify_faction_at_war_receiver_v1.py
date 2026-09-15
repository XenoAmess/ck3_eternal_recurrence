#!/usr/bin/env python3
"""Verify the exact 1.19.0.6 private faction-at-war receiver."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXPECTED_EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def pe_layout(image: bytes) -> tuple[int, list[tuple[int, int, int, int]]]:
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    require(image[pe : pe + 4] == b"PE\0\0", "PE signature drifted")
    count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    optional = pe + 24
    base = struct.unpack_from("<Q", image, optional + 24)[0]
    cursor = optional + optional_size
    sections = []
    for _ in range(count):
        virtual_size, rva, raw_size, raw = struct.unpack_from(
            "<IIII", image, cursor + 8
        )
        sections.append((rva, virtual_size, raw, raw_size))
        cursor += 40
    return base, sections


def at(image: bytes, sections: list[tuple[int, int, int, int]], rva: int, size: int) -> bytes:
    for start, virtual_size, raw, raw_size in sections:
        if start <= rva and rva + size <= start + max(virtual_size, raw_size):
            offset = raw + rva - start
            return image[offset : offset + size]
    raise AssertionError(f"RVA 0x{rva:X} is not file backed")


def rip_target(rva: int, instruction: bytes, displacement_offset: int = 3) -> int:
    return rva + len(instruction) + struct.unpack_from(
        "<i", instruction, displacement_offset
    )[0]


def direct_target(rva: int, instruction: bytes) -> int:
    return rva + 5 + struct.unpack_from("<i", instruction, 1)[0]


def verify_rtti(image: bytes, sections, base: int, binding: dict) -> None:
    type_rva = int(binding["type_descriptor_rva"], 0)
    name = (binding["name"] + "\0").encode("ascii")
    require(at(image, sections, type_rva + 0x10, len(name)) == name,
            f"RTTI name drifted: {binding['name']}")
    col_rva = int(binding["complete_object_locator_rva"], 0)
    col = struct.unpack("<6I", at(image, sections, col_rva, 24))
    require(col[0] == 1 and col[3] == type_rva and col[5] == col_rva,
            f"RTTI COL drifted: {binding['name']}")
    vtable = int(binding["vtable_rva"], 0)
    require(struct.unpack("<Q", at(image, sections, vtable - 8, 8))[0] == base + col_rva,
            f"RTTI vtable binding drifted: {binding['name']}")
    prefix = at(image, sections, vtable, binding["vtable_prefix_length"])
    require(hashlib.sha256(prefix).hexdigest().upper() == binding["vtable_prefix_sha256"],
            f"vtable prefix drifted: {binding['name']}")
    if "alive_slot_index" in binding:
        slot = struct.unpack_from("<Q", prefix, binding["alive_slot_index"] * 8)[0]
        require(slot == base + int(binding["alive_target_rva"], 0),
                f"alive slot drifted: {binding['name']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ck3-root", type=Path, required=True)
    args = parser.parse_args()
    abi = json.loads((HERE / "faction_at_war_receiver_v1_abi.json").read_text(encoding="utf-8"))
    root = args.ck3_root.resolve()
    stock = root / abi["stock_source"]["path"]
    stock_bytes = stock.read_bytes()
    require(hashlib.sha256(stock_bytes).hexdigest().upper() == abi["stock_source"]["sha256"],
            "stock faction GUI hash drifted")
    stock_text = stock_bytes.decode("utf-8-sig")
    for token in abi["stock_source"]["tokens"]:
        require(token in stock_text, f"stock token missing: {token}")

    image = (root / "binaries/ck3.exe").read_bytes()
    require(len(image) == abi["exact_build"]["executable_size"], "EXE size drifted")
    require(hashlib.sha256(image).hexdigest().upper() == EXPECTED_EXE_SHA,
            "EXE SHA drifted")
    base, sections = pe_layout(image)
    require(base == int(abi["exact_build"]["image_base"], 0), "image base drifted")
    for span in abi["native_spans"]:
        start = int(span["rva_start"], 0)
        body = at(image, sections, start, span["length"])
        require(start + len(body) == int(span["rva_end_exclusive"], 0),
                f"span length drifted: {span['name']}")
        require(hashlib.sha256(body).hexdigest().upper() == span["sha256"],
                f"span hash drifted: {span['name']}")

    registration = abi["registration"]
    method = (registration["method_string"] + "\0").encode("ascii")
    require(at(image, sections, int(registration["method_string_rva"], 0), len(method)) == method,
            "Faction.IsAtWar string drifted")
    lea_rva = int(registration["callback_lea_rva"], 0)
    lea = at(image, sections, lea_rva, 7)
    require(lea[:3] == bytes.fromhex("488D15") and
            rip_target(lea_rva, lea) == int(registration["callback_wrapper_rva"], 0),
            "Faction.IsAtWar registration callback drifted")
    wrapper_call = at(image, sections, 0x237A072, 5)
    require(wrapper_call[0] == 0xE8 and direct_target(0x237A072, wrapper_call) ==
            int(registration["callback_target_rva"], 0),
            "Faction.IsAtWar wrapper target drifted")

    layout = abi["layout"]
    resolver_store = at(image, sections, 0xE6F440, 7)
    resolver_fallback = at(image, sections, 0xE6F471, 7)
    require(rip_target(0xE6F440, resolver_store) == int(layout["faction_storage_slot_rva"], 0) and
            rip_target(0xE6F471, resolver_fallback) == int(layout["faction_fallback_slot_rva"], 0) and
            at(image, sections, 0xE6F46C, 5) == bytes.fromhex("3950107407"),
            "CFaction storage/identity chain drifted")
    war_store = at(image, sections, 0x2378200, 7)
    war_fallback = at(image, sections, 0x2378235, 7)
    require(rip_target(0x2378200, war_store) == int(layout["war_storage_slot_rva"], 0) and
            rip_target(0x2378235, war_fallback) == int(layout["war_fallback_slot_rva"], 0) and
            at(image, sections, 0x237820C, 6) == bytes.fromhex("8B918C000000") and
            at(image, sections, 0x2378230, 5) == bytes.fromhex("3951087407") and
            at(image, sections, 0x237823C, 7) == bytes.fromhex("488B0148FF6008"),
            "CWar receiver chain drifted")
    for binding in abi["rtti"].values():
        verify_rtti(image, sections, base, binding)

    header = (HERE.parent / "include/xar_bridge/faction_gift_receivers_v1.hpp").read_text(
        encoding="utf-8"
    )
    implementation = "\n".join(
        (header, (HERE.parent / "src/faction_gift_receivers_v1.cpp").read_text(encoding="utf-8"))
    )
    expected_constants = {
        "kFactionGiftFactionStorageSlotRvaV1": int(layout["faction_storage_slot_rva"], 0),
        "kFactionGiftFactionFallbackSlotRvaV1": int(layout["faction_fallback_slot_rva"], 0),
        "kFactionGiftWarStorageSlotRvaV1": int(layout["war_storage_slot_rva"], 0),
        "kFactionGiftWarFallbackSlotRvaV1": int(layout["war_fallback_slot_rva"], 0),
        "kFactionGiftFactionVtableRvaV1": int(abi["rtti"]["faction"]["vtable_rva"], 0),
        "kFactionGiftWarVtableRvaV1": int(abi["rtti"]["war"]["vtable_rva"], 0),
        "kFactionGiftNullWarVtableRvaV1": int(abi["rtti"]["null_war"]["vtable_rva"], 0),
        "kFactionGiftWarAliveLeafRvaV1": int(abi["rtti"]["war"]["alive_target_rva"], 0),
        "kFactionGiftNullWarAliveLeafRvaV1": int(abi["rtti"]["null_war"]["alive_target_rva"], 0),
    }
    for name, expected in expected_constants.items():
        match = re.search(rf"\b{name}\s*=\s*(0x[0-9A-Fa-f]+)", header)
        require(match is not None and int(match.group(1), 0) == expected,
                f"implementation RVA drifted: {name}")
    for token in (
        "kFactionGiftFactionStorageSlotRvaV1",
        "kFactionGiftWarStorageSlotRvaV1",
        "expected_faction_vtable",
        "expected_null_war_alive_leaf",
        "first != second",
        "SameFactionAtWarStoresV1",
        "sample.war_round_trip != 0xFFFFFFFFU",
    ):
        require(token in implementation, f"implementation gate missing: {token}")
    print("faction_at_war_receiver_v1_source_contract: GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
