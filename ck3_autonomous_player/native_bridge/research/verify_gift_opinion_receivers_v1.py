#!/usr/bin/env python3
"""Verify exact 1.19.0.6 gift opinion observation and preview receivers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

from verify_faction_at_war_receiver_v1 import at, pe_layout, require


HERE = Path(__file__).resolve().parent


def murmur3_x86_32(value: bytes) -> int:
    h = 0
    count = len(value) // 4
    for index in range(count):
        k = struct.unpack_from("<I", value, index * 4)[0]
        k = (k * 0xCC9E2D51) & 0xFFFFFFFF
        k = ((k << 15) | (k >> 17)) & 0xFFFFFFFF
        k = (k * 0x1B873593) & 0xFFFFFFFF
        h ^= k
        h = ((h << 13) | (h >> 19)) & 0xFFFFFFFF
        h = (h * 5 + 0xE6546B64) & 0xFFFFFFFF
    tail = value[count * 4 :]
    k = 0
    for index, byte in enumerate(tail):
        k |= byte << (index * 8)
    if tail:
        k = (k * 0xCC9E2D51) & 0xFFFFFFFF
        k = ((k << 15) | (k >> 17)) & 0xFFFFFFFF
        k = (k * 0x1B873593) & 0xFFFFFFFF
        h ^= k
    h ^= len(value)
    h ^= h >> 16
    h = (h * 0x85EBCA6B) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0xC2B2AE35) & 0xFFFFFFFF
    h ^= h >> 16
    return h


def verify_vtable(image: bytes, sections, base: int, row: dict, type_rva: int) -> None:
    col_rva = int(row["complete_object_locator_rva"], 0)
    col = struct.unpack("<6I", at(image, sections, col_rva, 24))
    require(col[0] == 1 and col[1] == row["object_offset"] and
            col[2] == row.get("cd_offset", 0) and col[3] == type_rva and
            col[5] == col_rva, "definition COL drifted")
    vtable = int(row["vtable_rva"], 0)
    require(struct.unpack("<Q", at(image, sections, vtable - 8, 8))[0] == base + col_rva,
            "definition vtable/COL binding drifted")
    prefix = at(image, sections, vtable, row["prefix_length"])
    require(hashlib.sha256(prefix).hexdigest().upper() == row["prefix_sha256"],
            "definition vtable prefix drifted")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ck3-root", type=Path, required=True)
    args = parser.parse_args()
    abi = json.loads((HERE / "gift_opinion_receivers_v1_abi.json").read_text(encoding="utf-8"))
    root = args.ck3_root.resolve()
    for source in abi["stock_sources"]:
        body = (root / source["path"]).read_bytes()
        require(hashlib.sha256(body).hexdigest().upper() == source["sha256"],
                f"stock hash drifted: {source['path']}")
        text = body.decode("utf-8-sig")
        for token in source["tokens"]:
            require(token in text, f"stock token missing: {token}")

    image = (root / "binaries/ck3.exe").read_bytes()
    require(len(image) == abi["exact_build"]["executable_size"], "EXE size drifted")
    require(hashlib.sha256(image).hexdigest().upper() == abi["exact_build"]["executable_sha256"],
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

    for key, expected in (("gift_opinion", 0xCA82155B),
                          ("send_gift_opinion", 0xF8A1F946)):
        require(murmur3_x86_32(key.encode("ascii")) == expected ==
                int(abi["keys"][key]["stable_hash"], 0), f"stable hash drifted: {key}")

    for definition in abi["definitions"].values():
        type_rva = int(definition["primary"]["type_descriptor_rva"], 0)
        verify_vtable(image, sections, base, definition["primary"], type_rva)
        verify_vtable(image, sections, base, definition["secondary"], type_rva)

    header = (HERE.parent / "include/xar_bridge/faction_gift_receivers_v1.hpp").read_text(
        encoding="utf-8"
    )
    implementation = "\n".join((
        header,
        (HERE.parent / "src/faction_gift_receivers_v1.cpp").read_text(encoding="utf-8"),
        (HERE.parent / "src/faction_gift_mitigation_async_glue_v1.cpp").read_text(encoding="utf-8"),
    ))
    expected_constants = {
        "kFactionGiftCharacterStorageSlotRvaV1": int(abi["layout"]["character_storage_slot_rva"], 0),
        "kFactionGiftCharacterFallbackSlotRvaV1": int(abi["layout"]["character_fallback_slot_rva"], 0),
        "kFactionGiftReadCharacterOpinionRvaV1": 0x2610A50,
        "kFactionGiftOpinionModifierDatabaseSlotRvaV1": int(abi["definitions"]["gift_opinion"]["database_slot_rva"], 0),
        "kFactionGiftStableHashRvaV1": 0x3B8B000,
        "kFactionGiftOpinionModifierLookupRvaV1": int(abi["definitions"]["gift_opinion"]["lookup_rva"], 0),
        "kFactionGiftFindActiveOpinionGroupRvaV1": 0x2696D90,
        "kFactionGiftSumOpinionModifierRvaV1": 0x23101A0,
        "kFactionGiftOpinionModifierVtableRvaV1": int(abi["definitions"]["gift_opinion"]["primary"]["vtable_rva"], 0),
        "kFactionGiftOpinionModifierSecondaryVtableRvaV1": int(abi["definitions"]["gift_opinion"]["secondary"]["vtable_rva"], 0),
        "kFactionGiftActiveOpinionVtableRvaV1": int(abi["layout"]["active_opinion_vtable_rva"], 0),
        "kFactionGiftTemporaryOpinionVtableRvaV1": int(abi["layout"]["temporary_opinion_vtable_rva"], 0),
        "kFactionGiftNamedValueDatabaseGetterRvaV1": int(abi["definitions"]["send_gift_opinion"]["getter_rva"], 0),
        "kFactionGiftNamedValueLookupRvaV1": int(abi["definitions"]["send_gift_opinion"]["lookup_rva"], 0),
        "kFactionGiftCloneEventTargetScopeRvaV1": 0x3358E00,
        "kFactionGiftSupport118ConstructorRvaV1": 0x3354330,
        "kFactionGiftSupport2A8ConstructorRvaV1": 0x3354280,
        "kFactionGiftEvaluateNamedFixedRvaV1": 0x3369820,
        "kFactionGiftNamedValueVtableRvaV1": int(abi["definitions"]["send_gift_opinion"]["primary"]["vtable_rva"], 0),
        "kFactionGiftNamedValueSecondaryVtableRvaV1": int(abi["definitions"]["send_gift_opinion"]["secondary"]["vtable_rva"], 0),
        "kFactionGiftEvaluationFlagRvaV1": int(abi["layout"]["evaluation_flag_rva"], 0),
    }
    for name, expected in expected_constants.items():
        match = re.search(rf"\b{name}\s*=\s*(0x[0-9A-Fa-f]+)", header)
        require(match is not None and int(match.group(1), 0) == expected,
                f"implementation RVA drifted: {name}")
    for token in (
        "kFactionGiftReadCharacterOpinionRvaV1",
        "kFactionGiftOpinionModifierSecondaryOffsetV1",
        "sample.modifier_present = true",
        "first != second",
        "kFactionGiftCloneEventTargetScopeRvaV1",
        "source_descriptor.data() + 0x24",
        "raw - kFixedPointScale / 2",
        "recipient_after != recipient_before",
        "gift_opinion_receiver_unavailable",
    ):
        require(token in implementation, f"implementation gate missing: {token}")
    require("gift_opinion_receiver_unclosed" not in implementation,
            "closed receiver is still serialized as unclosed")
    print("gift_opinion_receivers_v1_source_contract: GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
