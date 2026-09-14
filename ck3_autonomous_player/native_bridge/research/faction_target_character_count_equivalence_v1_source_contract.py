#!/usr/bin/env python3
"""Verify FACTION3's exact target-link and count-equivalence evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


EXPECTED_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_SIZE = 95_206_008
EXPECTED_IMAGE_BASE = 0x140000000


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _pe_layout(
    image: bytes,
) -> tuple[int, list[tuple[int, int, int, int]]]:
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    _require(image[pe : pe + 4] == b"PE\0\0", "PE signature drifted")
    section_count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    optional = pe + 24
    _require(
        struct.unpack_from("<H", image, optional)[0] == 0x20B,
        "expected a PE32+ image",
    )
    image_base = struct.unpack_from("<Q", image, optional + 24)[0]
    cursor = optional + optional_size
    sections: list[tuple[int, int, int, int]] = []
    for _ in range(section_count):
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
            "<IIII", image, cursor + 8
        )
        sections.append((virtual_address, virtual_size, raw_offset, raw_size))
        cursor += 40
    return image_base, sections


def _at(
    image: bytes,
    sections: list[tuple[int, int, int, int]],
    rva: int,
    size: int,
) -> bytes:
    for virtual_address, virtual_size, raw_offset, raw_size in sections:
        span = max(virtual_size, raw_size)
        if virtual_address <= rva and rva + size <= virtual_address + span:
            offset = raw_offset + rva - virtual_address
            return image[offset : offset + size]
    raise AssertionError(f"RVA 0x{rva:X} is not file-backed")


def _direct_target(rva: int, instruction: bytes) -> int:
    _require(
        len(instruction) == 5 and instruction[0] == 0xE8,
        f"RVA 0x{rva:X} is not a direct CALL",
    )
    return rva + 5 + struct.unpack_from("<i", instruction, 1)[0]


def _rip_target(rva: int, instruction: bytes, displacement_offset: int) -> int:
    return rva + len(instruction) + struct.unpack_from(
        "<i", instruction, displacement_offset
    )[0]


def check(root: Path, *, ck3_root: Path | None = None) -> None:
    native = root / "ck3_autonomous_player" / "native_bridge"
    abi = json.loads(
        (
            native
            / "research/faction_target_character_count_equivalence_v1_abi.json"
        ).read_text(encoding="utf-8")
    )
    contract = json.loads(
        (
            native
            / "research/fixtures/faction_target_character_count_equivalence_v1_source_contract.json"
        ).read_text(encoding="utf-8")
    )
    campaign_source = (native / "src/campaign_root_context_v1.cpp").read_text(
        encoding="utf-8"
    )
    private_header = (
        native / "include/xar_bridge/faction_targeting_row_observer_v1.hpp"
    ).read_text(encoding="utf-8")
    private_source = (
        native / "src/faction_targeting_row_observer_v1.cpp"
    ).read_text(encoding="utf-8")
    native_tree = (root / "docs/ck3-native-ai/factions-and-rebellions.md").read_text(
        encoding="utf-8"
    )

    _require(abi["schema_version"] == 1, "ABI schema drifted")
    _require(contract["schema_version"] == 1, "source contract schema drifted")
    _require(
        abi["status"] == contract["status"]
        == "static-confirmed-next-private-observer",
        "static evidence status drifted",
    )
    _require(
        abi["unique_next_implementation_entry"]
        == contract["unique_next_implementation_entry"],
        "next private observer seam drifted",
    )
    for key in (
        "target_character_getter_source_ready",
        "campaign_root_count_equivalence_source_ready",
        "same_frame_join_contract_ready",
    ):
        _require(abi["readiness"][key] is True, f"{key} was demoted")
        _require(contract["readiness"][key] is True, f"fixture {key} drifted")
    for key in (
        "private_target_and_count_observer_ready",
        "paused_live_equivalence_artifact_ready",
        "member_identity_ready",
        "public_targeting_rows_ready",
    ):
        _require(abi["readiness"][key] is False, f"{key} was over-promoted")
        _require(contract["readiness"][key] is False, f"fixture {key} drifted")
    _require(
        abi["scope"]["public_abi_changed"] is False
        and abi["scope"]["public_capability_changed"] is False
        and abi["scope"]["ck3_started"] is False,
        "evidence-only scope drifted",
    )
    for token in contract["campaign_root_source_tokens"]:
        _require(token in campaign_source, f"campaign-root source token missing: {token}")
    private_text = private_header + "\n" + private_source
    for token in contract["private_observer_source_tokens"]:
        _require(token in private_text, f"private observer source token missing: {token}")
    for token in (
        "FACTION3-EVIDENCE",
        "CFactionTargetLink",
        "0x1392CBC",
        contract["unique_next_implementation_entry"],
    ):
        _require(token in native_tree, f"native tree evidence missing: {token}")

    install = (ck3_root or root / "Crusader Kings III").resolve()
    executable = install / "binaries/ck3.exe"
    image = executable.read_bytes()
    _require(len(image) == EXPECTED_SIZE, "executable size drifted")
    _require(
        hashlib.sha256(image).hexdigest().upper() == EXPECTED_SHA256,
        "executable SHA-256 drifted",
    )
    image_base, sections = _pe_layout(image)
    _require(image_base == EXPECTED_IMAGE_BASE, "image base drifted")

    for span in contract["native_spans"]:
        start = int(span["rva_start"], 0)
        end = int(span["rva_end_exclusive"], 0)
        body = _at(image, sections, start, end - start)
        _require(len(body) == span["length"], f"{span['name']} length drifted")
        _require(
            hashlib.sha256(body).hexdigest().upper() == span["sha256"],
            f"{span['name']} body hash drifted",
        )

    # RTTI binds resolver slot 4 to CFactionTargetLink rather than a guessed
    # public FactionItem method.
    rtti = contract["rtti_binding"]
    type_descriptor = int(rtti["type_descriptor_rva"], 0)
    rtti_name = (rtti["name"] + "\0").encode("ascii")
    _require(
        _at(image, sections, type_descriptor + 0x10, len(rtti_name)) == rtti_name,
        "CFactionTargetLink RTTI name drifted",
    )
    col_rva = int(rtti["complete_object_locator_rva"], 0)
    col = struct.unpack("<6I", _at(image, sections, col_rva, 24))
    _require(
        col[0] == 1 and col[3] == type_descriptor and col[5] == col_rva,
        "CFactionTargetLink complete-object locator drifted",
    )
    vtable_rva = int(rtti["vtable_rva"], 0)
    _require(
        struct.unpack("<Q", _at(image, sections, vtable_rva - 8, 8))[0]
        == image_base + col_rva,
        "CFactionTargetLink vtable/COL binding drifted",
    )
    resolver_slot_rva = int(rtti["resolver_slot_rva"], 0)
    resolver_target_rva = int(rtti["resolver_target_rva"], 0)
    _require(
        resolver_slot_rva
        == vtable_rva + int(rtti["resolver_slot_index"]) * 8,
        "CFactionTargetLink resolver slot arithmetic drifted",
    )
    _require(
        struct.unpack("<Q", _at(image, sections, resolver_slot_rva, 8))[0]
        == image_base + resolver_target_rva,
        "CFactionTargetLink resolver target drifted",
    )

    _require(
        _at(image, sections, 0x19D8280, 7)
        == bytes.fromhex("498B0066833819"),
        "Faction scope-kind gate drifted",
    )
    faction_store = _at(image, sections, 0x19D8295, 7)
    _require(
        faction_store[:3] == bytes.fromhex("488B05")
        and _rip_target(0x19D8295, faction_store, 3) == 0x570C768,
        "Faction storage slot drifted",
    )
    faction_fallback = _at(image, sections, 0x19D82C6, 7)
    _require(
        faction_fallback[:3] == bytes.fromhex("488B05")
        and _rip_target(0x19D82C6, faction_fallback, 3) == 0x570C6F8,
        "Faction fallback slot drifted",
    )
    _require(
        _at(image, sections, 0x19D82C0, 6)
        == bytes.fromhex("443940107407")
        and _at(image, sections, 0x19D82CD, 16)
        == bytes.fromhex("8B404048894208488BC2C70204000000"),
        "CFaction identity/target Character scope projection drifted",
    )
    _require(
        _at(image, sections, 0x82B27C, 2) == bytes.fromhex("8B11")
        and _at(image, sections, 0x82B29C, 3) == bytes.fromhex("395018"),
        "Character full-generation identity reference resolver drifted",
    )

    # The refresh reads the same local player's land_state+0x12C count used
    # by campaign-root and appends exactly one inline row per uint32 source ID.
    _require(
        _at(image, sections, 0x1392CBC, 6)
        == bytes.fromhex("89A944010000"),
        "targeting destination count reset drifted",
    )
    character_store = _at(image, sections, 0x1392CC2, 7)
    _require(
        character_store[:3] == bytes.fromhex("4C8B05")
        and _rip_target(0x1392CC2, character_store, 3) == 0x570C130,
        "refresh Character storage slot drifted",
    )
    player_id = _at(image, sections, 0x1392CCE, 6)
    _require(
        player_id[:2] == bytes.fromhex("8B05")
        and _rip_target(0x1392CCE, player_id, 2) == 0x4FE7EE0,
        "refresh local-player identity source drifted",
    )
    character_fallback = _at(image, sections, 0x1392CFA, 7)
    _require(
        character_fallback[:3] == bytes.fromhex("488B0D")
        and _rip_target(0x1392CFA, character_fallback, 3) == 0x570C138,
        "refresh Character fallback slot drifted",
    )
    _require(
        _at(image, sections, 0x1392CF5, 4) == bytes.fromhex("39411874")
        and _at(image, sections, 0x1392D01, 7)
        == bytes.fromhex("488B81B8010000")
        and _at(image, sections, 0x1392D0D, 6)
        == bytes.fromhex("480520010000"),
        "refresh player round-trip/land-state path drifted",
    )
    null_land_state = _at(image, sections, 0x1392D15, 7)
    _require(
        null_land_state[:3] == bytes.fromhex("488D05")
        and _rip_target(0x1392D15, null_land_state, 3) == 0x4F66088,
        "refresh null-land-state fallback drifted",
    )
    _require(
        _at(image, sections, 0x1392D3A, 11)
        == bytes.fromhex("4C8B004863400C4D8D0C80"),
        "land-state targeting data/count span drifted",
    )
    _require(
        _direct_target(0x1392D4C, _at(image, sections, 0x1392D4C, 5))
        == 0x975ED0,
        "uint32 source copy target drifted",
    )
    _require(
        _at(image, sections, 0x975EF7, 15)
        == bytes.fromhex("482BEB4C897C242048C1FD02498BF1")
        and _at(image, sections, 0x975F90, 14)
        == bytes.fromhex("8B038904194883C304483BDE75F2"),
        "uint32 range length/copy loop drifted",
    )
    _require(
        _at(image, sections, 0x1392D80, 16)
        == bytes.fromhex("8B068944243848895C2440C644244800")
        and _at(image, sections, 0x1392D9E, 2) == bytes.fromhex("FFC5")
        and _at(image, sections, 0x1392E4F, 6)
        == bytes.fromhex("89AB44010000")
        and _at(image, sections, 0x1392E81, 6)
        == bytes.fromhex("FF8344010000")
        and _at(image, sections, 0x1392E8D, 7)
        == bytes.fromhex("4883C604493BF5"),
        "one-source-id/one-FactionItem projection drifted",
    )
    _require(
        _direct_target(0x1392EA3, _at(image, sections, 0x1392EA3, 5))
        == 0x1394540,
        "target-row sort target drifted",
    )
    _require(
        _at(image, sections, 0x139455D, 19)
        == bytes.fromhex("4863410C488D1440488D14D500000000488B31"),
        "sort's read-only data/count range construction drifted",
    )
    _require(
        _at(image, sections, 0xF6F790, 8)
        == bytes.fromhex("488D8138010000C3")
        and _at(image, sections, 0x1393C40, 11)
        == bytes.fromhex("83B944010000000F95C0C3"),
        "post-refresh targeting container/count consumer drifted",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    parser.add_argument("--ck3-root", type=Path)
    arguments = parser.parse_args()
    check(
        arguments.root.resolve(),
        ck3_root=arguments.ck3_root.resolve() if arguments.ck3_root else None,
    )
    print("faction-target-character-count-equivalence-source-contract: GREEN_STATIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
