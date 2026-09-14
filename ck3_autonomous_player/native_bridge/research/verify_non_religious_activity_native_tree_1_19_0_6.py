#!/usr/bin/env python3
"""Verify the CK3 1.19.0.6 non-religious activity research ledger.

This verifier is file-only. It never starts or attaches to CK3. The game root
must be supplied explicitly or through CK3_GAME_ROOT so the contract is not
bound to one workstation path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct

import pefile


EXPECTED_EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_EXE_SIZE = 95_206_008
EXPECTED_IMAGE_BASE = 0x140000000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def parse_rva(value: str) -> int:
    return int(value, 16)


def bytes_at(data: bytes, image: pefile.PE, rva: int, size: int) -> bytes:
    offset = image.get_offset_from_rva(rva)
    value = data[offset : offset + size]
    if len(value) != size:
        raise ValueError(f"short read at RVA 0x{rva:X}")
    return value


def u32(data: bytes, image: pefile.PE, rva: int) -> int:
    return struct.unpack("<I", bytes_at(data, image, rva, 4))[0]


def u64(data: bytes, image: pefile.PE, rva: int) -> int:
    return struct.unpack("<Q", bytes_at(data, image, rva, 8))[0]


def rel32_target(data: bytes, image: pefile.PE, instruction_rva: int) -> int:
    instruction = bytes_at(data, image, instruction_rva, 5)
    if instruction[0] not in (0xE8, 0xE9):
        raise ValueError(f"expected direct call/jump at RVA 0x{instruction_rva:X}")
    displacement = struct.unpack("<i", instruction[1:])[0]
    return instruction_rva + 5 + displacement


def rtti_name(data: bytes, image: pefile.PE, type_rva: int) -> str:
    raw = bytes_at(data, image, type_rva + 16, 160)
    return raw.split(b"\0", 1)[0].decode("ascii")


def assert_pdata(image: pefile.PE, expected: tuple[int, int, int]) -> None:
    if not hasattr(image, "DIRECTORY_ENTRY_EXCEPTION"):
        image.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]]
        )
    functions = {
        (int(row.struct.BeginAddress), int(row.struct.EndAddress), int(row.struct.UnwindData))
        for row in image.DIRECTORY_ENTRY_EXCEPTION
    }
    if expected not in functions:
        raise ValueError(f"PDATA row changed: {[hex(value) for value in expected]}")


def verify_source(game_root: Path, relative: str, expected_hash: str, anchors: list[str]) -> None:
    path = game_root / relative
    raw = path.read_bytes()
    if sha256(raw) != expected_hash:
        raise ValueError(f"source hash changed: {relative}")
    text = raw.decode("utf-8-sig").replace("\r\n", "\n")
    for anchor in anchors:
        if anchor not in text:
            raise ValueError(f"source anchor missing in {relative}: {anchor!r}")


def verify_vtable_rtti(
    data: bytes,
    image: pefile.PE,
    *,
    vtable_rva: int,
    expected_col_rva: int,
    expected_offset: int,
    expected_type_rva: int,
    expected_name: str,
) -> None:
    col_rva = u64(data, image, vtable_rva - 8) - EXPECTED_IMAGE_BASE
    if col_rva != expected_col_rva:
        raise ValueError(f"COL changed for vtable RVA 0x{vtable_rva:X}")
    if u32(data, image, col_rva + 4) != expected_offset:
        raise ValueError(f"COL object offset changed for vtable RVA 0x{vtable_rva:X}")
    if u32(data, image, col_rva + 12) != expected_type_rva:
        raise ValueError(f"type descriptor changed for vtable RVA 0x{vtable_rva:X}")
    if rtti_name(data, image, expected_type_rva) != expected_name:
        raise ValueError(f"RTTI name changed for vtable RVA 0x{vtable_rva:X}")


def verify(game_root: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract["schema"] != "xar.ck3.non_religious_activity_native_tree.v1":
        raise ValueError("unexpected contract schema")
    boundaries = contract["boundaries"]
    if not boundaries["religious_activities_excluded"] or boundaries["faith_details_exposed"]:
        raise ValueError("religion exclusion boundary changed")
    forbidden_true = (
        "ck3_started",
        "process_attached",
        "game_state_mutated",
        "observer_implemented",
        "action_implemented",
        "public_schema_changed",
        "public_mcp_changed",
        "planner_changed",
    )
    if any(boundaries[key] for key in forbidden_true):
        raise ValueError("research-only boundary changed")
    if contract["p0_slice"]["activity_type"] != "activity_feast":
        raise ValueError("P0 activity changed")

    exe = game_root / "binaries" / "ck3.exe"
    data = exe.read_bytes()
    if len(data) != EXPECTED_EXE_SIZE or sha256(data) != EXPECTED_EXE_SHA256:
        raise ValueError(f"unexpected executable size/hash: {len(data)} {sha256(data)}")
    image = pefile.PE(data=data, fast_load=True)
    if int(image.OPTIONAL_HEADER.ImageBase) != EXPECTED_IMAGE_BASE:
        raise ValueError("unexpected image base")

    anchors = {
        "game/common/activities/activity_types/_activity_type.info": [
            "must also exceed define ACTIVITY_SCORE_THRESHOLD to be eligible",
            "the highest scoring\n\t# activity will be selected as the hosting candidate",
            "this check will be taken from can_start_showing_failures_only instead",
            "Used to show a rough minimum or expected cost",
            "AI-only activities will not persist more than 1 day after this",
        ],
        "game/common/activities/activity_types/feast.txt": [
            "activity_feast = {",
            "is_single_location = yes",
            "ai_province_filter = capital",
            "value = 30",
            "multiply = -0.25",
            "multiply = 0.5",
            "max_guests = 40",
            "cooldown = { years = standard_feast_cooldown_time }",
        ],
        "game/common/activities/activity_types/hunt.txt": [
            "activity_hunt = {",
            "can_hunt_trigger = yes",
            "max_guests = 20",
            "progress_activity_phase_after = { weeks = 6 }",
            "days = 21",
            "days = 28",
            "days = 35",
        ],
        "game/common/activities/activity_types/tour.txt": [
            "activity_tour = {",
            "has_dlc_feature = tours_and_tournaments",
            "has_dlc_feature = advanced_activities",
            "is_single_location = no",
            "num_pickable_phases = 10",
            "max_guests = 100",
            "cooldown = { years = 10 }",
        ],
        "game/common/defines/ai/00_ai.txt": [
            "ACTIVITY_SCORE_THRESHOLD = 20",
            "OPEN_ACTIVITY_DISTANCE_DELAY = { 20 40 80 140 220 320 440 }",
        ],
    }
    for relative, expected_hash in contract["script_sources"].items():
        verify_source(game_root, relative, expected_hash, anchors[relative])

    ai = contract["native_ai_host_chain"]
    ai_pdata = tuple(parse_rva(value) for value in ai["function"]["pdata"])
    assert_pdata(image, ai_pdata)
    if sha256(bytes_at(data, image, ai_pdata[0], ai_pdata[1] - ai_pdata[0])) != ai["function"]["sha256"]:
        raise ValueError("AI host-selection body changed")
    for key in ("candidate_generator_call", "planning_rows_call", "queue_submit"):
        call = ai[key]
        if rel32_target(data, image, parse_rva(call["call_rva"])) != parse_rva(call["target_rva"]):
            raise ValueError(f"AI host call target changed: {key}")
    build = ai["command_build"]
    if rel32_target(data, image, parse_rva(build["call_rva"])) != parse_rva(build["target_rva"]):
        raise ValueError("AI activity command-build call changed")
    build_pdata = tuple(parse_rva(value) for value in build["target_pdata"])
    assert_pdata(image, build_pdata)
    if sha256(bytes_at(data, image, build_pdata[0], build_pdata[1] - build_pdata[0])) != build["target_sha256"]:
        raise ValueError("AI activity command-build body changed")
    if bytes_at(data, image, 0x18E0940, 0x12).hex().upper() != "8B014139014C0F4CC94883C110483BCA75EE":
        raise ValueError("highest-score selection loop changed")
    if bytes_at(data, image, 0x18E09A1, 0x17).hex().upper() != "B81F85EB5141F7E0C1EA056BC264442BC041FFC0453B01":
        raise ValueError("percent-roll reduction/compare changed")

    for rva_text, expected in (
        (ai["source_identity"]["diagnostic_rva"], ai["source_identity"]["diagnostic"]),
        (ai["source_identity"]["source_path_rva"], ai["source_identity"]["source_path"]),
        (contract["p0_slice"]["next_observer_seam"]["string_rvas"]["CanPlanActivity"], "CanPlanActivity"),
        (contract["p0_slice"]["next_observer_seam"]["string_rvas"]["GetCanPlanActivityTooltip"], "GetCanPlanActivityTooltip"),
    ):
        raw = bytes_at(data, image, parse_rva(rva_text), len(expected) + 1)
        if raw != expected.encode("ascii") + b"\0":
            raise ValueError(f"native string changed at {rva_text}")

    surfaces = contract["native_command_surfaces"]
    start = surfaces["start"]
    verify_vtable_rtti(
        data, image, vtable_rva=parse_rva(start["primary_vtable_rva"]),
        expected_col_rva=parse_rva(start["primary_col_rva"]), expected_offset=0,
        expected_type_rva=parse_rva(start["type_descriptor_rva"]), expected_name=start["rtti"],
    )
    verify_vtable_rtti(
        data, image, vtable_rva=parse_rva(start["secondary_vtable_rva"]),
        expected_col_rva=parse_rva(start["secondary_col_rva"]), expected_offset=24,
        expected_type_rva=parse_rva(start["type_descriptor_rva"]), expected_name=start["rtti"],
    )
    if u64(data, image, parse_rva(start["primary_vtable_rva"]) + 8 * 8) - EXPECTED_IMAGE_BASE != parse_rva(start["clone_rva"]):
        raise ValueError("start command clone slot changed")
    if u64(data, image, parse_rva(start["primary_vtable_rva"]) + 6 * 8) - EXPECTED_IMAGE_BASE != parse_rva(start["payload_validation_thunk_rva"]):
        raise ValueError("start command validation slot changed")
    if u64(data, image, parse_rva(start["secondary_vtable_rva"]) + 1 * 8) - EXPECTED_IMAGE_BASE != parse_rva(start["secondary_dispatch_rva"]):
        raise ValueError("start command dispatch slot changed")
    if rel32_target(data, image, parse_rva(start["payload_validation_thunk_rva"]) + 4) != parse_rva(start["payload_validator_rva"]):
        raise ValueError("start command payload-validator target changed")
    if rel32_target(data, image, parse_rva(start["secondary_dispatch_rva"]) + 0x19) != parse_rva(start["dispatch_target_rva"]):
        raise ValueError("start command dispatch target changed")
    for rva_key, sha_key, pdata in (
        ("clone_rva", "clone_sha256", (0x26CA920, 0x26CA9AC, 0x4DA4838)),
        ("payload_validator_rva", "payload_validator_sha256", (0x219A8B0, 0x219BA2C, 0x4D63588)),
    ):
        assert_pdata(image, pdata)
        if sha256(bytes_at(data, image, pdata[0], pdata[1] - pdata[0])) != start[sha_key]:
            raise ValueError(f"start command function changed: {rva_key}")

    join = surfaces["join"]
    verify_vtable_rtti(
        data, image, vtable_rva=parse_rva(join["primary_vtable_rva"]),
        expected_col_rva=parse_rva(join["primary_col_rva"]), expected_offset=0,
        expected_type_rva=parse_rva(join["type_descriptor_rva"]), expected_name=join["rtti"],
    )
    verify_vtable_rtti(
        data, image, vtable_rva=parse_rva(join["secondary_vtable_rva"]),
        expected_col_rva=parse_rva(join["secondary_col_rva"]), expected_offset=24,
        expected_type_rva=parse_rva(join["type_descriptor_rva"]), expected_name=join["rtti"],
    )
    if u64(data, image, parse_rva(join["primary_vtable_rva"]) + 8 * 8) - EXPECTED_IMAGE_BASE != parse_rva(join["clone_rva"]):
        raise ValueError("join command clone slot changed")
    if u64(data, image, parse_rva(join["primary_vtable_rva"]) + 6 * 8) - EXPECTED_IMAGE_BASE != parse_rva(join["validator_rva"]):
        raise ValueError("join command validator slot changed")
    if u64(data, image, parse_rva(join["secondary_vtable_rva"]) + 1 * 8) - EXPECTED_IMAGE_BASE != parse_rva(join["execute_rva"]):
        raise ValueError("join command execute slot changed")
    for rva_key, sha_key, pdata in (
        ("validator_rva", "validator_sha256", (0x26C8550, 0x26C8789, 0x4DA46B0)),
        ("execute_rva", "execute_sha256", (0x26C8480, 0x26C854B, 0x4DA46A0)),
    ):
        assert_pdata(image, pdata)
        if sha256(bytes_at(data, image, pdata[0], pdata[1] - pdata[0])) != join[sha_key]:
            raise ValueError(f"join command function changed: {rva_key}")

    force = surfaces["ai_force_host_effect"]
    verify_vtable_rtti(
        data, image, vtable_rva=parse_rva(force["vtable_rva"]),
        expected_col_rva=parse_rva(force["col_rva"]), expected_offset=0,
        expected_type_rva=parse_rva(force["type_descriptor_rva"]), expected_name=force["rtti"],
    )
    if u64(data, image, parse_rva(force["vtable_rva"]) + force["execute_slot"] * 8) - EXPECTED_IMAGE_BASE != parse_rva(force["execute_rva"]):
        raise ValueError("AI force-host effect execute slot changed")
    force_pdata = (0x2E60180, 0x2E603BA, 0x4DF7928)
    assert_pdata(image, force_pdata)
    if sha256(bytes_at(data, image, force_pdata[0], force_pdata[1] - force_pdata[0])) != force["execute_sha256"]:
        raise ValueError("AI force-host effect changed")
    if rel32_target(data, image, parse_rva(force["ai_manager_call_rva"])) != parse_rva(force["ai_manager_target_rva"]):
        raise ValueError("AI force-host manager call changed")
    force_diagnostic = force["non_ai_diagnostic"]
    if bytes_at(data, image, parse_rva(force["non_ai_diagnostic_rva"]), len(force_diagnostic) + 1) != force_diagnostic.encode("ascii") + b"\0":
        raise ValueError("AI force-host non-AI diagnostic changed")

    return {
        "result": "GREEN",
        "schema": contract["schema"],
        "exact_build": contract["exact_build"]["product_version"],
        "executable_sha256": EXPECTED_EXE_SHA256,
        "script_sources": len(contract["script_sources"]),
        "activity_types": list(contract["activity_slices"]),
        "p0": contract["p0_slice"]["activity_type"],
        "ck3_started": False,
        "process_attached": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path)
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path(__file__).with_name("non_religious_activity_native_tree_1_19_0_6.json"),
    )
    args = parser.parse_args()
    raw_root = args.game_root or (Path(os.environ["CK3_GAME_ROOT"]) if "CK3_GAME_ROOT" in os.environ else None)
    if raw_root is None:
        parser.error("--game-root or CK3_GAME_ROOT is required")
    result = verify(raw_root.resolve(), args.contract.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
