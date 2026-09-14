#!/usr/bin/env python3
"""Validate the exact-build nonreligious law/contract/succession research freeze."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


CONTRACT_RELATIVE = Path(
    "ck3_autonomous_player/native_bridge/research/fixtures/"
    "g2_nonreligious_law_contract_succession_native_tree_v1.json"
)
DOC_RELATIVE = Path("docs/ck3-native-ai/laws-contracts-and-succession.md")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _parse_rva(value: str) -> int:
    return int(value, 16)


def _sections(image: bytes) -> list[tuple[int, int, int, int]]:
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    _require(image[pe : pe + 4] == b"PE\0\0", "PE signature drifted")
    count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    cursor = pe + 24 + optional_size
    result: list[tuple[int, int, int, int]] = []
    for _ in range(count):
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
            "<IIII", image, cursor + 8
        )
        result.append((virtual_address, virtual_size, raw_offset, raw_size))
        cursor += 40
    return result


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


def _cstring(
    image: bytes,
    sections: list[tuple[int, int, int, int]],
    rva: int,
    maximum: int = 256,
) -> str:
    raw = _at(image, sections, rva, maximum)
    end = raw.find(b"\0")
    _require(end >= 0, f"RVA 0x{rva:X} has no bounded NUL terminator")
    return raw[:end].decode("ascii")


def _rip_target(rva: int, instruction: bytes) -> int:
    _require(
        len(instruction) == 7 and instruction[:3] == bytes.fromhex("488D15"),
        f"RVA 0x{rva:X} is not the frozen LEA RDX,[RIP+disp32] anchor",
    )
    return rva + 7 + struct.unpack_from("<i", instruction, 3)[0]


def _read_stock_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def check(root: Path, executable: Path, game_root: Path) -> None:
    contract_path = root / CONTRACT_RELATIVE
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    _require(contract["schema_version"] == 1, "research schema version drifted")
    _require(contract["status"] == "static-ready", "research status overclaims live evidence")
    _require(contract["build"]["game_version"] == "1.19.0.6", "game version drifted")
    _require(contract["next_vertical_slice"]["priority"] == "P0", "P0 slice drifted")
    _require(
        contract["next_vertical_slice"]["observer"]["working_name"]
        == "realm_law_governance_snapshot_v1",
        "next read-only observer seam drifted",
    )
    impact = contract["integration_impact"]
    for key in ("public_schema_changed", "bridge_changed", "planner_changed", "cmake_changed"):
        _require(impact[key] is False, f"research-only boundary drifted: {key}")
    _require(impact["ck3_launched"] is False, "static freeze claims CK3 launch")

    for relative, source in contract["source_files"].items():
        path = game_root / relative
        _require(path.is_file(), f"missing exact-build stock file: {relative}")
        raw = path.read_bytes()
        _require(len(raw) == source["size"], f"stock file size drifted: {relative}")
        digest = hashlib.sha256(raw).hexdigest().upper()
        _require(digest == source["sha256"], f"stock file SHA-256 drifted: {relative}")
        text = _read_stock_text(path)
        for token in source["required_tokens"]:
            _require(token in text, f"stock semantic anchor missing from {relative}: {token}")

    image = executable.read_bytes()
    build = contract["build"]
    _require(len(image) == build["executable_size"], "executable size drifted")
    _require(
        hashlib.sha256(image).hexdigest().upper() == build["executable_sha256"],
        "executable SHA-256 drifted",
    )
    sections = _sections(image)

    for anchor in contract["native_reflection"]["registration_anchors"]:
        reference_rva = _parse_rva(anchor["registration_reference_rva"])
        string_rva = _parse_rva(anchor["string_rva"])
        expected = bytes.fromhex(anchor["anchor_hex"])
        actual = _at(image, sections, reference_rva, len(expected))
        _require(actual == expected, f"registration anchor drifted: {anchor['surface']}")
        _require(
            _rip_target(reference_rva, actual) == string_rva,
            f"registration string target drifted: {anchor['surface']}",
        )
        _require(
            _cstring(image, sections, string_rva) == anchor["surface"],
            f"registration surface string drifted: {anchor['surface']}",
        )

    for method, rva in contract["native_reflection"]["method_strings"].items():
        expected = method.rsplit(".", 1)[-1]
        _require(
            _cstring(image, sections, _parse_rva(rva)) == expected,
            f"method string drifted: {method}",
        )
    for name, rva in contract["native_reflection"]["rtti_strings"].items():
        _require(
            _cstring(image, sections, _parse_rva(rva)) == name,
            f"RTTI string drifted: {name}",
        )

    prewar = json.loads(
        (root / "ck3_autonomous_player/native_bridge/research/prewar_scope_v1_abi.json")
        .read_text(encoding="utf-8")
    )
    frozen_subject = contract["reusable_native_substrate"]["subject_contract"]
    live_contract = prewar["forced_tributary_contract_participants"]
    live_subject = live_contract["storage"]
    live_type = live_contract["subject_contract_type"]
    _require(live_subject["slot_rva"] == frozen_subject["storage_slot_rva"], "subject contract slot drifted")
    _require(live_subject["fallback_object_rva"] == frozen_subject["fallback_object_rva"], "subject contract fallback drifted")
    for key in ("type_descriptor_rva", "primary_vtable_rva", "secondary_vtable_rva", "object_size"):
        _require(live_type[key] == frozen_subject[key], f"subject contract type drifted: {key}")
    for offset, meaning in frozen_subject["layout"].items():
        _require(live_type["layout"][offset] == meaning, f"subject contract layout drifted: {offset}")

    campaign = json.loads(
        (root / "ck3_autonomous_player/native_bridge/research/campaign_root_context_v1_abi.json")
        .read_text(encoding="utf-8")
    )
    _require(campaign["held_title_partition"]["held_title_vector"]["data_offset"] == "0x1E0", "held-title data offset drifted")
    _require(campaign["held_title_partition"]["held_title_vector"]["count_offset"] == "0x1EC", "held-title count offset drifted")
    _require(campaign["primary_title_succession"]["title_layout"]["data_offset"] == "0x278", "successor data offset drifted")
    _require(campaign["primary_title_succession"]["title_layout"]["count_offset"] == "0x284", "successor count offset drifted")

    doc = (root / DOC_RELATIVE).read_text(encoding="utf-8")
    required_doc_tokens = (
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
        "RARE_TASK_TICK",
        "realm_law_governance_snapshot_v1",
        "enact_realm_law_v1",
        "subject_contract_governance_snapshot_v1",
        "0x570CCA0",
        "0xC444E6",
        "0x3DE0DF0",
        "未闭合",
        "宗教域排除",
        "static-ready",
    )
    for token in required_doc_tokens:
        _require(token in doc, f"law research document token missing: {token}")
    _require(doc.count("```mermaid") >= 3, "law research document needs three frozen trees")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--ck3-executable", type=Path)
    parser.add_argument("--game-root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    executable = (
        args.ck3_executable.resolve()
        if args.ck3_executable
        else root / "Crusader Kings III/binaries/ck3.exe"
    )
    game_root = (
        args.game_root.resolve()
        if args.game_root
        else root / "Crusader Kings III/game"
    )
    check(root, executable, game_root)
    print("nonreligious-law-contract-succession-native-tree: GREEN_STATIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
