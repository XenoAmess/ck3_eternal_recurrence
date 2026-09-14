#!/usr/bin/env python3
"""Verify FACTION5's exact leader and character-member source contract."""

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


def _pe_layout(image: bytes) -> tuple[int, list[tuple[int, int, int, int]]]:
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    _require(image[pe : pe + 4] == b"PE\0\0", "PE signature drifted")
    section_count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    optional = pe + 24
    _require(struct.unpack_from("<H", image, optional)[0] == 0x20B, "expected PE32+")
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


def _rip_target(rva: int, instruction: bytes, displacement_offset: int = 3) -> int:
    return rva + len(instruction) + struct.unpack_from(
        "<i", instruction, displacement_offset
    )[0]


def _direct_target(rva: int, instruction: bytes) -> int:
    _require(len(instruction) == 5, f"RVA 0x{rva:X} direct instruction length drifted")
    return rva + 5 + struct.unpack_from("<i", instruction, 1)[0]


def _verify_rtti(
    image: bytes,
    sections: list[tuple[int, int, int, int]],
    image_base: int,
    binding: dict[str, object],
) -> None:
    type_descriptor = int(str(binding["type_descriptor_rva"]), 0)
    encoded_name = (str(binding["name"]) + "\0").encode("ascii")
    _require(
        _at(image, sections, type_descriptor + 0x10, len(encoded_name)) == encoded_name,
        f"RTTI name drifted: {binding['name']}",
    )
    col_rva = int(str(binding["complete_object_locator_rva"]), 0)
    col = struct.unpack("<6I", _at(image, sections, col_rva, 24))
    _require(
        col[0] == 1 and col[3] == type_descriptor and col[5] == col_rva,
        f"RTTI complete-object locator drifted: {binding['name']}",
    )
    vtable = int(str(binding["vtable_rva"]), 0)
    _require(
        struct.unpack("<Q", _at(image, sections, vtable - 8, 8))[0]
        == image_base + col_rva,
        f"RTTI vtable binding drifted: {binding['name']}",
    )


def check(root: Path, *, ck3_root: Path | None = None) -> None:
    native = root / "ck3_autonomous_player" / "native_bridge"
    abi = json.loads(
        (native / "research/faction_leader_character_members_v1_abi.json").read_text(
            encoding="utf-8"
        )
    )
    contract = json.loads(
        (
            native
            / "research/fixtures/faction_leader_character_members_v1_source_contract.json"
        ).read_text(encoding="utf-8")
    )
    upstream = json.loads(
        (native / "research/faction_targeting_row_observer_v1_abi.json").read_text(
            encoding="utf-8"
        )
    )
    observer_text = "\n".join(
        (
            (native / "include/xar_bridge/faction_targeting_row_observer_v1.hpp").read_text(
                encoding="utf-8"
            ),
            (native / "src/faction_targeting_row_observer_v1.cpp").read_text(
                encoding="utf-8"
            ),
        )
    )
    native_tree = (root / "docs/ck3-native-ai/factions-and-rebellions.md").read_text(
        encoding="utf-8"
    )

    _require(abi["schema_version"] == contract["schema_version"] == 1, "schema drifted")
    _require(
        abi["status"] == contract["status"] == "static-confirmed-next-private-reader",
        "evidence status drifted",
    )
    _require(
        abi["unique_next_implementation_entry"]
        == contract["unique_next_implementation_entry"],
        "unique next implementation seam drifted",
    )
    for key in (
        "leader_identity_source_ready",
        "member_vector_layout_source_ready",
        "member_identity_source_ready",
        "borrowed_ownership_source_ready",
        "same_admission_reader_contract_ready",
        "canonical_leader_nullable_semantics_ready",
    ):
        _require(abi["readiness"][key] is True, f"{key} was demoted")
        _require(contract["readiness"][key] is True, f"fixture {key} was demoted")
    for key in (
        "private_feasibility_reader_ready",
        "paused_live_leader_member_artifact_ready",
        "public_faction_feasibility_ready",
    ):
        _require(abi["readiness"][key] is False, f"{key} was over-promoted")
        _require(contract["readiness"][key] is False, f"fixture {key} was over-promoted")
    _require(
        abi["scope"]["runtime_observer_changed"] is False
        and abi["scope"]["public_abi_changed"] is False
        and abi["scope"]["public_schema_changed"] is False
        and abi["scope"]["ck3_started"] is False,
        "research-only scope drifted",
    )
    _require(
        upstream["status"] == "static-ready-private-target-count-pending-paused-live"
        and upstream["readiness"]["private_target_and_count_observer_ready"] is True
        and upstream["unique_next_reverse_engineering_entry"]
        == "faction_leader_and_character_member_vector_semantics",
        "FACTION4 prerequisite drifted",
    )
    for token in contract["upstream_private_observer_tokens"]:
        _require(token in observer_text, f"upstream observer token missing: {token}")
    for token in (
        "FACTION5-EVIDENCE",
        "CFaction+0x44",
        "CFaction+0x48",
        contract["unique_next_implementation_entry"],
    ):
        _require(token in native_tree, f"native tree evidence missing: {token}")

    install = (ck3_root or root / "Crusader Kings III").resolve()
    for source in contract["stock_sources"]:
        source_path = install / str(source["path"])
        payload = source_path.read_bytes()
        _require(
            hashlib.sha256(payload).hexdigest().upper() == source["sha256"],
            f"stock source hash drifted: {source['path']}",
        )
        text = payload.decode("utf-8-sig")
        for token in source["tokens"]:
            _require(token in text, f"stock token missing in {source['path']}: {token}")

    image = (install / "binaries/ck3.exe").read_bytes()
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
            f"{span['name']} hash drifted",
        )

    leader_rtti = contract["leader_link_rtti_binding"]
    _verify_rtti(image, sections, image_base, leader_rtti)
    leader_vtable = int(leader_rtti["vtable_rva"], 0)
    leader_vtable_body = _at(image, sections, leader_vtable, leader_rtti["vtable_length"])
    _require(
        hashlib.sha256(leader_vtable_body).hexdigest().upper()
        == leader_rtti["vtable_sha256"],
        "CFactionLeaderLink vtable hash drifted",
    )
    leader_slot = int(leader_rtti["resolver_slot_rva"], 0)
    _require(
        leader_slot == leader_vtable + int(leader_rtti["resolver_slot_index"]) * 8
        and struct.unpack("<Q", _at(image, sections, leader_slot, 8))[0]
        == image_base + int(leader_rtti["resolver_target_rva"], 0),
        "CFactionLeaderLink resolver slot drifted",
    )
    _require(
        _at(image, sections, 0x19D8320, 7) == bytes.fromhex("498B0066833819"),
        "leader Faction scope-kind gate drifted",
    )
    faction_store = _at(image, sections, 0x19D8335, 7)
    faction_fallback = _at(image, sections, 0x19D8366, 7)
    _require(
        faction_store[:3] == bytes.fromhex("488B05")
        and _rip_target(0x19D8335, faction_store) == 0x570C768
        and faction_fallback[:3] == bytes.fromhex("488B05")
        and _rip_target(0x19D8366, faction_fallback) == 0x570C6F8,
        "leader faction storage/fallback drifted",
    )
    _require(
        _at(image, sections, 0x19D8360, 6) == bytes.fromhex("443940107407")
        and _at(image, sections, 0x19D836D, 17)
        == bytes.fromhex("8B404448894208488BC2C70204000000C3"),
        "leader identity projection drifted",
    )

    bindings = contract["registration_bindings"]
    for name, binding in bindings.items():
        if "method_string" in binding:
            method = (binding["method_string"] + "\0").encode("ascii")
            _require(
                _at(image, sections, int(binding["method_string_rva"], 0), len(method))
                == method,
                f"{name} method string drifted",
            )
        if "class_string" in binding:
            class_name = (binding["class_string"] + "\0").encode("ascii")
            _require(
                _at(image, sections, int(binding["class_string_rva"], 0), len(class_name))
                == class_name,
                f"{name} class string drifted",
            )
        callback_lea = int(binding["callback_lea_rva"], 0)
        callback = _at(image, sections, callback_lea, 7)
        _require(
            callback[:3] == bytes.fromhex("488D15")
            and _rip_target(callback_lea, callback) == int(
                binding.get("callback_rva", binding.get("callback_thunk_rva")), 0
            ),
            f"{name} callback registration drifted",
        )
    leader_binding = bindings["get_leader"]
    leader_thunk = int(leader_binding["callback_thunk_rva"], 0)
    _require(
        _direct_target(leader_thunk, _at(image, sections, leader_thunk, 5))
        == int(leader_binding["callback_target_rva"], 0),
        "GetLeader callback thunk drifted",
    )

    # GetCharacterMembers resolves the FactionItem identity and passes a borrowed
    # pointer to the CFaction-embedded collection at +0x48 into the data model.
    member_store = _at(image, sections, 0x1394C7C, 7)
    member_fallback = _at(image, sections, 0x1394CAD, 7)
    _require(
        member_store[:3] == bytes.fromhex("488B05")
        and _rip_target(0x1394C7C, member_store) == 0x570C768
        and member_fallback[:3] == bytes.fromhex("488B05")
        and _rip_target(0x1394CAD, member_fallback) == 0x570C6F8,
        "member collection faction storage/fallback drifted",
    )
    _require(
        _at(image, sections, 0x1394C88, 4) == bytes.fromhex("8B118BCA")
        and _at(image, sections, 0x1394CA8, 5) == bytes.fromhex("3950107407")
        and _at(image, sections, 0x1394CB4, 4) == bytes.fromhex("4883C048")
        and _at(image, sections, 0x1395059, 4) == bytes.fromhex("83785400"),
        "CFaction member container/count offsets drifted",
    )
    wrapper = _at(image, sections, 0x1394CCA, 7)
    wrapper_rva = _rip_target(0x1394CCA, wrapper)
    collection_rtti = contract["container_rtti_binding"]
    _require(
        wrapper[:3] == bytes.fromhex("488D05")
        and wrapper_rva == int(collection_rtti["wrapper_descriptor_rva"], 0),
        "character-member collection wrapper drifted",
    )
    functions_vtable = int(collection_rtti["functions_vtable_rva"], 0)
    _require(
        struct.unpack("<Q", _at(image, sections, wrapper_rva, 8))[0]
        == image_base + functions_vtable,
        "character-member wrapper/functions table drifted",
    )
    _verify_rtti(image, sections, image_base, collection_rtti)
    for index, key in enumerate(
        ("count_adapter", "collection_builder", "slice_adapter", "element_adapter")
    ):
        _require(
            struct.unpack("<Q", _at(image, sections, functions_vtable + index * 8, 8))[0]
            == image_base + int(collection_rtti["vtable_entries"][key], 0),
            f"character-member collection {key} binding drifted",
        )
    _require(
        _at(image, sections, 0x13A3AC2, 8) == bytes.fromhex("8B480C4C8B002BCB")
        and _at(image, sections, 0x13A3AD8, 10)
        == bytes.fromhex("0F44D148C1E0054903C0"),
        "member collection data/count/stride adapter drifted",
    )

    _require(
        _at(image, sections, 0x1A60416, 15)
        == bytes.fromhex("488B78484863685448C1E5054803EF")
        and _at(image, sections, 0x1A60460, 19)
        == bytes.fromhex("8B470848894424288B4308C744242004000000"),
        "member scope enumerator layout drifted",
    )
    row_rtti = contract["character_member_row_rtti_binding"]
    _verify_rtti(image, sections, image_base, row_rtti)
    row_vtable = int(row_rtti["vtable_rva"], 0)
    row_prefix = _at(image, sections, row_vtable, row_rtti["vtable_prefix_length"])
    _require(
        hashlib.sha256(row_prefix).hexdigest().upper()
        == row_rtti["vtable_prefix_sha256"],
        "CFactionCharacterMember vtable prefix drifted",
    )
    _require(
        _at(image, sections, 0x23782C5, 43)
        == bytes.fromhex(
            "498D5F48488B0B4C63430C49C1E0054C03C1493BC874120F1F40003979087409"
            "4883C120493BC875F233F6"
        )
        and _at(image, sections, 0x2378582, 30)
        == bytes.fromhex(
            "4489430C48634C245848C1E10548030B418B471089410C418B4518894108"
        ),
        "member row ownership/write layout drifted",
    )

    member_resolver = int(bindings["get_character_member"]["callback_rva"], 0)
    character_store = _at(image, sections, member_resolver, 7)
    character_fallback = _at(image, sections, member_resolver + 0x32, 7)
    _require(
        character_store[:3] == bytes.fromhex("488B05")
        and _rip_target(member_resolver, character_store) == 0x570C130
        and _at(image, sections, member_resolver + 0x0C, 3) == bytes.fromhex("8B5108")
        and _at(image, sections, member_resolver + 0x2D, 3) == bytes.fromhex("395018")
        and character_fallback[:3] == bytes.fromhex("488B05")
        and _rip_target(member_resolver + 0x32, character_fallback) == 0x570C138,
        "member Character identity resolver drifted",
    )
    _require(
        _at(image, sections, 0x23741AF, 4) == bytes.fromhex("448B410C")
        and _at(image, sections, 0x23741D3, 4) == bytes.fromhex("44394210")
        and _at(image, sections, 0x23741FD, 4) == bytes.fromhex("458B5908")
        and _at(image, sections, 0x237422B, 4) == bytes.fromhex("44395E18")
        and _at(image, sections, 0x2374234, 4) == bytes.fromhex("448B4A40")
        and _at(image, sections, 0x2374257, 4) == bytes.fromhex("45394E18"),
        "member owner/member/target resolver relation drifted",
    )
    _require(
        _at(image, sections, 0x23794B9, 6) == bytes.fromhex("8B9190000000")
        and _at(image, sections, 0x23794C6, 3) == bytes.fromhex("8B5144"),
        "special-character/leader portrait branch drifted",
    )
    _require(
        _at(image, sections, 0x1390AED, 4) == bytes.fromhex("41035854"),
        "display total member-count addition drifted",
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
    print("faction-leader-character-members-source-contract: GREEN_STATIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
