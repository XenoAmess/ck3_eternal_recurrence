#!/usr/bin/env python3
"""Verify the exact 1.19.0.6 gift opinion receiver ABI fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


HERE = Path(__file__).resolve().parent
ABI_PATH = HERE / "faction_gift_opinion_receivers_v1_abi.json"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def pe_layout(image: bytes) -> tuple[int, list[tuple[int, int, int, int]]]:
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    require(image[pe : pe + 4] == b"PE\0\0", "PE signature drifted")
    count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    optional = pe + 24
    require(struct.unpack_from("<H", image, optional)[0] == 0x20B,
            "expected PE32+ image")
    base = struct.unpack_from("<Q", image, optional + 24)[0]
    cursor = optional + optional_size
    sections: list[tuple[int, int, int, int]] = []
    for _ in range(count):
        virtual_size, rva, raw_size, raw = struct.unpack_from(
            "<IIII", image, cursor + 8
        )
        sections.append((rva, virtual_size, raw, raw_size))
        cursor += 40
    return base, sections


def at(image: bytes, sections: list[tuple[int, int, int, int]],
       rva: int, size: int) -> bytes:
    for start, virtual_size, raw, raw_size in sections:
        if start <= rva and rva + size <= start + max(virtual_size, raw_size):
            offset = raw + rva - start
            return image[offset : offset + size]
    raise AssertionError(f"RVA 0x{rva:X} is not file backed")


def direct_target(rva: int, instruction: bytes) -> int:
    require(len(instruction) == 5 and instruction[0] in (0xE8, 0xE9),
            f"expected rel32 call/jump at 0x{rva:X}")
    return rva + 5 + struct.unpack_from("<i", instruction, 1)[0]


def rip_target(rva: int, instruction: bytes, displacement_offset: int = 3) -> int:
    return rva + len(instruction) + struct.unpack_from(
        "<i", instruction, displacement_offset
    )[0]


def rotl32(value: int, count: int) -> int:
    return ((value << count) | (value >> (32 - count))) & 0xFFFFFFFF


def murmur3_x86_32_seed_zero(value: bytes) -> int:
    result = 0
    full = len(value) & ~3
    for index in range(0, full, 4):
        word = int.from_bytes(value[index : index + 4], "little")
        word = (word * 0xCC9E2D51) & 0xFFFFFFFF
        word = rotl32(word, 15)
        word = (word * 0x1B873593) & 0xFFFFFFFF
        result ^= word
        result = rotl32(result, 13)
        result = (result * 5 + 0xE6546B64) & 0xFFFFFFFF
    tail = value[full:]
    word = 0
    if len(tail) == 3:
        word ^= tail[2] << 16
    if len(tail) >= 2:
        word ^= tail[1] << 8
    if tail:
        word ^= tail[0]
        word = (word * 0xCC9E2D51) & 0xFFFFFFFF
        word = rotl32(word, 15)
        word = (word * 0x1B873593) & 0xFFFFFFFF
        result ^= word
    result ^= len(value)
    result ^= result >> 16
    result = (result * 0x85EBCA6B) & 0xFFFFFFFF
    result ^= result >> 13
    result = (result * 0xC2B2AE35) & 0xFFFFFFFF
    result ^= result >> 16
    return result & 0xFFFFFFFF


def verify_rtti(image: bytes, sections, base: int, binding: dict,
                prefix: str = "") -> None:
    name = (binding["name"] + "\0").encode("ascii")
    type_rva = int(binding["type_descriptor_rva"], 0)
    require(at(image, sections, type_rva + 0x10, len(name)) == name,
            f"{prefix} RTTI name drifted")
    primary_col = int(binding["primary_complete_object_locator_rva"], 0)
    col = struct.unpack("<6I", at(image, sections, primary_col, 24))
    require(col[0] == 1 and col[1] == 0 and col[3] == type_rva and
            col[5] == primary_col, f"{prefix} primary COL drifted")
    primary_vtable = int(binding["primary_vtable_rva"], 0)
    require(struct.unpack("<Q", at(image, sections, primary_vtable - 8, 8))[0]
            == base + primary_col, f"{prefix} primary vtable COL drifted")
    primary = at(image, sections, primary_vtable,
                 binding["primary_vtable_prefix_length"])
    require(hashlib.sha256(primary).hexdigest().upper() ==
            binding["primary_vtable_prefix_sha256"],
            f"{prefix} primary vtable prefix drifted")
    require(struct.unpack_from("<Q", primary)[0] == base + 0x7E9220,
            f"{prefix} slot-zero valid receiver drifted")

    secondary_col = int(binding["secondary_complete_object_locator_rva"], 0)
    secondary = struct.unpack("<6I", at(image, sections, secondary_col, 24))
    expected_offset = int(binding["secondary_complete_object_locator_offset"], 0)
    require(secondary[0] == 1 and secondary[1] == expected_offset and
            secondary[3] == type_rva and secondary[5] == secondary_col,
            f"{prefix} secondary COL drifted")
    if "secondary_complete_object_locator_cd_offset" in binding:
        require(secondary[2] == binding["secondary_complete_object_locator_cd_offset"],
                f"{prefix} secondary cdOffset drifted")
    secondary_vtable = int(binding["secondary_vtable_rva"], 0)
    require(struct.unpack("<Q", at(image, sections, secondary_vtable - 8, 8))[0]
            == base + secondary_col, f"{prefix} secondary vtable COL drifted")
    secondary_prefix = at(image, sections, secondary_vtable,
                          binding["secondary_vtable_prefix_length"])
    require(hashlib.sha256(secondary_prefix).hexdigest().upper() ==
            binding["secondary_vtable_prefix_sha256"],
            f"{prefix} secondary vtable prefix drifted")


def verify_source_contract(root: Path, abi: dict) -> None:
    contract_path = HERE / abi["stock_contract"]["fixture"]
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    require(contract["game_build"]["executable_sha256"] ==
            abi["build"]["executable_sha256"], "source ABI build drifted")
    for source in contract["stock_sources"]:
        path = root / source["relative_path"]
        body = path.read_bytes()
        require(hashlib.sha256(body).hexdigest().upper() == source["sha256"],
                f"stock source drifted: {source['relative_path']}")
    gift = (root / "game/common/character_interactions/00_gift.txt").read_text(
        encoding="utf-8-sig"
    )
    for token in ("gift_interaction = {", "modifier = gift_opinion",
                  "opinion = send_gift_opinion"):
        require(token in gift, f"gift source token missing: {token}")
    basic = (root / "game/common/script_values/00_basic_values.txt").read_text(
        encoding="utf-8-sig"
    )
    require("send_gift_opinion = {" in basic and "max = 100" in basic,
            "send_gift_opinion source contract drifted")
    modifiers = (root /
                 "game/common/opinion_modifiers/00_opinion_modifiers.txt").read_text(
                     encoding="utf-8-sig"
                 )
    require("gift_opinion = {" in modifiers and "decaying = yes" in modifiers,
            "gift_opinion modifier source contract drifted")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ck3-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.ck3_root.resolve()
    abi = json.loads(ABI_PATH.read_text(encoding="utf-8"))
    verify_source_contract(root, abi)

    image = (root / "binaries/ck3.exe").read_bytes()
    require(len(image) == abi["build"]["executable_size"], "EXE size drifted")
    require(hashlib.sha256(image).hexdigest().upper() ==
            abi["build"]["executable_sha256"], "EXE SHA drifted")
    base, sections = pe_layout(image)
    require(base == int(abi["build"]["image_base"], 0), "image base drifted")

    for span in abi["native_spans"]:
        start = int(span["rva_start"], 0)
        body = at(image, sections, start, span["length"])
        require(start + len(body) == int(span["rva_end_exclusive"], 0),
                f"span length drifted: {span['name']}")
        require(hashlib.sha256(body).hexdigest().upper() == span["sha256"],
                f"span hash drifted: {span['name']}")

    stock = abi["stock_contract"]
    require(murmur3_x86_32_seed_zero(b"gift_opinion") ==
            int(stock["gift_opinion_hash_murmur3_x86_32_seed_0"], 0),
            "gift_opinion stable hash drifted")
    require(murmur3_x86_32_seed_zero(b"send_gift_opinion") ==
            int(stock["send_gift_opinion_hash_murmur3_x86_32_seed_0"], 0),
            "send_gift_opinion stable hash drifted")
    require(murmur3_x86_32_seed_zero(b"favor_hook") == 0x4F5E02C2,
            "hash implementation control vector drifted")

    verify_rtti(image, sections, base, abi["gift_opinion_definition"]["rtti"],
                "COpinionModifier")
    verify_rtti(image, sections, base, abi["send_gift_opinion_definition"]["rtti"],
                "CJominiNamedValue")
    named_rtti = abi["send_gift_opinion_definition"]["rtti"]
    null_primary = int(named_rtti["null_primary_vtable_rva"], 0)
    null_secondary = int(named_rtti["null_secondary_vtable_rva"], 0)
    require(struct.unpack("<Q", at(image, sections, null_primary, 8))[0] ==
            base + 0x7E6590, "named-value null slot-zero drifted")
    require(null_primary != int(named_rtti["primary_vtable_rva"], 0) and
            null_secondary != int(named_rtti["secondary_vtable_rva"], 0),
            "named-value null identity collapsed")
    modifier_rtti = abi["gift_opinion_definition"]["rtti"]
    modifier_null_primary = int(modifier_rtti["null_primary_vtable_rva"], 0)
    require(struct.unpack("<Q", at(image, sections,
                                   modifier_null_primary, 8))[0] ==
            base + 0x7E6590, "opinion-modifier null slot-zero drifted")

    # Frozen native call edges for the three required receivers.
    edges = (
        (0x288C514, 0x2610A50, "COpinionTrigger -> total opinion"),
        (0x288BD2E, 0x2696D90, "has modifier -> active group"),
        (0x288BD92, 0x23101A0, "has modifier -> summed current value"),
        (0x23101DE, 0x230F280, "sum -> date/decay current value"),
        (0x2C44356, 0x3358E00, "stock gift preview -> scope clone"),
        (0x2309604, 0x3369820, "typed stock caller -> fixed receiver"),
        (0x2EDA026, 0x2EDC1B0, "add opinion -> integer helper"),
        (0x33696BA, 0x9A3740, "named integer -> fixed-tree integer"),
        (0x9A376A, 0x96EC00, "fixed-tree integer -> raw tree evaluator"),
        (0x28E2689, 0x3B8B000, "modifier parser -> stable hash"),
        (0x28E2693, 0x231D3E0, "modifier parser -> definition lookup"),
        (0x345E6E0, 0x3B8B000, "definition identity header -> stable hash"),
        (0x333A234, 0x345E690, "named value -> definition identity header"),
        (0x2B518CF, 0x345E690, "opinion modifier -> definition identity header"),
    )
    for call_rva, target, label in edges:
        require(direct_target(call_rva, at(image, sections, call_rva, 5)) == target,
                f"call edge drifted: {label}")
    require(direct_target(0x2EDC204, at(image, sections, 0x2EDC204, 5)) ==
            0x3373000, "add-opinion helper tail jump drifted")
    require(direct_target(0x3373079, at(image, sections, 0x3373079, 5)) ==
            0x3369600, "generic integer named call drifted")

    # The stock gift preview clone rewrites only the cloned root and keeps aliases.
    require(at(image, sections, 0x2C4434D, 9) == bytes.fromhex(
        "488D5108488D4C2420"
    ), "gift interaction clone arguments drifted")
    require(at(image, sections, 0x2C4435C, 21) == bytes.fromhex(
        "B80400000066894424208B87DC0200004889442428"
    ), "gift interaction recipient-root rewrite drifted")

    # The two database name displays prove the canonical MSVC string at +0x18,
    # with size/capacity at +0x28/+0x30, for the concrete returned definitions.
    require(at(image, sections, 0x23095AB, 14) == bytes.fromhex(
        "4883793010488D41188B50107203"
    ), "CJominiNamedValue canonical-name layout drifted")
    require(at(image, sections, 0x2EA145A, 18)[:8] == bytes.fromhex(
        "48837A3010488D42"
    ) and at(image, sections, 0x2EA1462, 1) == b"\x18",
            "COpinionModifier canonical-name layout drifted")
    require(at(image, sections, 0x345E6CD, 3) == bytes.fromhex("895610") and
            at(image, sections, 0x345E6E5, 3) == bytes.fromhex("894614") and
            at(image, sections, 0x345E6E8, 4) == bytes.fromhex("488D4E18"),
            "definition ordinal/hash/canonical-string header drifted")

    # DB singleton RIP target and exact modifier lookup argument chain.
    db_load = at(image, sections, 0x28E2634, 7)
    require(db_load[:3] == bytes.fromhex("488B3D") and
            rip_target(0x28E2634, db_load) ==
            int(abi["gift_opinion_definition"]["database_slot_rva"], 0),
            "opinion modifier database slot drifted")
    modifier_fallback = at(image, sections, 0x231D4EA, 7)
    require(modifier_fallback[:3] == bytes.fromhex("488B05") and
            rip_target(0x231D4EA, modifier_fallback) ==
            int(abi["gift_opinion_definition"]["null_fallback_slot_rva"], 0),
            "opinion modifier fallback slot drifted")
    named_database = at(image, sections, 0x999AF4, 7)
    require(named_database[:3] == bytes.fromhex("488B05") and
            rip_target(0x999AF4, named_database) ==
            int(abi["send_gift_opinion_definition"]["database_slot_rva"], 0),
            "named-value database slot drifted")
    named_fallback = at(image, sections, 0x999ABA, 7)
    require(named_fallback[:3] == bytes.fromhex("488B05") and
            rip_target(0x999ABA, named_fallback) ==
            int(abi["send_gift_opinion_definition"]["null_fallback_slot_rva"], 0),
            "named-value fallback slot drifted")
    require(at(image, sections, 0x288BD1B, 40).startswith(bytes.fromhex(
        "488B8DA80100004885C90F84"
    )), "recipient extension receiver drifted")
    require(at(image, sections, 0x288BD45, 7) == bytes.fromhex(
        "4C8B8718010000"
    ), "has-opinion trigger definition pointer offset drifted")
    require(at(image, sections, 0x288BD6C, 6) == bytes.fromhex(
        "4C394208740A"
    ), "active opinion exact modifier-pointer match drifted")

    # Exact five-argument fixed wrapper: stock writes a source pointer to the
    # fifth stack-argument home at caller rsp+0x20, then calls with R9=0.
    require(at(image, sections, 0x23095C1, 8) == bytes.fromhex(
        "4533C933C0895424"
    ), "stock fixed caller R9/source setup drifted")
    require(at(image, sections, 0x23095ED, 5) == bytes.fromhex(
        "4889442420"
    ), "stock fixed caller fifth argument drifted")
    require(at(image, sections, 0x33698D1, 5) == bytes.fromhex(
        "488B457F48"
    )[:5], "fixed receiver fifth-argument read drifted")

    # Exact integer rounding constants: range bias, +/-50000, magic /100000.
    conversion = at(image, sections, 0x9A3774, 178)
    for token in (
        (0xC35000000000).to_bytes(8, "little"),
        (0x1869FFFFE7960).to_bytes(8, "little"),
        (0x29F16B11C6D1E109).to_bytes(8, "little"),
        (50000).to_bytes(4, "little"),
    ):
        require(token in conversion, "integer rounding constant drifted")

    print("faction_gift_opinion_receivers_v1_abi: GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
