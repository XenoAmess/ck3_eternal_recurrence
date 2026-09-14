#!/usr/bin/env python3
"""Verify the frozen CK3 1.19.0.6 found-kingdom source evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any


EXPECTED_INTERVALS = {
    "barony": 0,
    "county": 0,
    "duchy": 60,
    "kingdom": 0,
    "empire": 0,
    "hegemony": 0,
}

EXPECTED_COST_MATRIX = [
    {"has_treasury": False, "is_nomadic": False, "gold": 300, "treasury": 0, "prestige": 500, "piety": 200},
    {"has_treasury": True, "is_nomadic": False, "gold": 0, "treasury": 300, "prestige": 500, "piety": 200},
    {"has_treasury": False, "is_nomadic": True, "gold": 0, "treasury": 0, "prestige": 500, "piety": 0},
    {"has_treasury": True, "is_nomadic": True, "gold": 0, "treasury": 300, "prestige": 500, "piety": 0},
]

EXPECTED_RUNTIME_FIELDS = {
    "snapshot_id",
    "frame",
    "played_character_id",
    "decision_id",
    "definition_revision",
    "top_title_tier",
    "is_shown",
    "is_valid",
    "is_valid_showing_failures_only",
    "is_affordable",
    "can_take",
    "evaluated_cost.gold",
    "evaluated_cost.treasury",
    "evaluated_cost.prestige",
    "evaluated_cost.piety",
}

DECISION_FRAGMENTS = [
    "decision_group_type = major",
    "ai_check_interval_by_tier = {",
    "barony = 0",
    "county = 0",
    "duchy = 60",
    "kingdom = 0",
    "empire = 0",
    "hegemony = 0",
    "highest_held_title_tier = tier_duchy",
    "has_game_rule = off_custom_kingdoms",
    "is_landed_or_landless_administrative = yes",
    "is_confederation_member = no",
    "prestige_level >= 3",
    "top_liege = this",
    "count > 2",
    "title_tier = duchy",
    "sub_realm_size >= 30",
    "has_realm_law = nomadic_authority_5",
    "has_realm_law = nomadic_authority_4",
    "has_realm_law = nomadic_authority_3",
    "is_available_adult = yes",
    "is_at_war = no",
    "prestige = 500",
    "create_custom_kingdom_effect = yes",
    "name = found_kingdom_decision",
    "name = found_kingdom_decision_kingdom",
    "always = yes",
    "base = 100",
]

EFFECT_FRAGMENTS = [
    "create_dynamic_title = {",
    "tier = kingdom",
    "create_title_and_vassal_change = {",
    "change_title_holder = {",
    "resolve_title_and_vassal_change = scope:change",
    "set_de_jure_liege_title = scope:old_empire",
    "set_de_jure_liege_title = scope:new_title",
    "set_coa = scope:old_title",
    "set_color_from_title = scope:old_title",
    "set_capital_county = scope:old_title.title_capital_county",
    "set_primary_title_to = scope:new_title",
    "trigger_event = major_decisions.1101",
    "trigger_event = major_decisions.1102",
    "trigger_event = major_decisions.1105",
]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def canonical_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def extract_top_level_block(text: str, key: str) -> str:
    lines = text.splitlines(keepends=True)
    prefix = f"{key} = {{"
    start_offset: int | None = None
    cursor = 0
    for line in lines:
        if line.rstrip("\n") == prefix:
            start_offset = cursor
            break
        cursor += len(line)
    if start_offset is None:
        raise ValueError(f"top-level block not found: {key}")

    depth = 0
    in_string = False
    escaped = False
    in_comment = False
    saw_open = False
    for index in range(start_offset, len(text)):
        char = text[index]
        if in_comment:
            if char == "\n":
                in_comment = False
            continue
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == "#":
            in_comment = True
        elif char == '"':
            in_string = True
        elif char == "{":
            depth += 1
            saw_open = True
        elif char == "}":
            depth -= 1
            if saw_open and depth == 0:
                return text[start_offset : index + 1]
            if depth < 0:
                break
    raise ValueError(f"unterminated top-level block: {key}")


def verify_pe_image_base(path: Path, expected: str) -> str | None:
    data = path.read_bytes()
    if data[:2] != b"MZ":
        return "exact-build executable is missing MZ header"
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_offset : pe_offset + 4] != b"PE\0\0":
        return "exact-build executable is missing PE signature"
    optional = pe_offset + 24
    if struct.unpack_from("<H", data, optional)[0] != 0x20B:
        return "exact-build executable is not PE32+"
    image_base = struct.unpack_from("<Q", data, optional + 24)[0]
    if image_base != int(expected, 0):
        return f"image base mismatch: 0x{image_base:X}"
    return None


def verify_sources(contract: dict[str, Any], game_root: Path, errors: list[str]) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for source in contract.get("sources", []):
        relative = source.get("relative_path")
        if not isinstance(relative, str):
            fail(errors, "source relative_path is missing")
            continue
        path = game_root / relative
        if not path.is_file():
            fail(errors, f"missing source: {path}")
            continue
        actual_size = path.stat().st_size
        if actual_size != source.get("size"):
            fail(errors, f"source size mismatch: {relative} {actual_size}")
        actual_sha = sha256_file(path)
        if actual_sha != source.get("sha256"):
            fail(errors, f"source SHA-256 mismatch: {relative} {actual_sha}")

        text = canonical_text(path)
        lines = text.splitlines()
        for anchor in source.get("line_anchors", []):
            line_number = anchor.get("line")
            expected_text = anchor.get("text")
            if not isinstance(line_number, int) or not (1 <= line_number <= len(lines)):
                fail(errors, f"line anchor out of range: {relative}:{line_number}")
            elif lines[line_number - 1] != expected_text:
                fail(errors, f"line anchor mismatch: {relative}:{line_number}")

        for block_contract in source.get("blocks", []):
            key = block_contract.get("key")
            if not isinstance(key, str):
                fail(errors, f"block key is missing: {relative}")
                continue
            try:
                block = extract_top_level_block(text, key)
            except ValueError as exc:
                fail(errors, f"{relative}: {exc}")
                continue
            blocks[key] = block
            actual_block_sha = sha256_bytes(block.encode("utf-8"))
            if actual_block_sha != block_contract.get("canonical_sha256"):
                fail(errors, f"block SHA-256 mismatch: {key} {actual_block_sha}")
            first_line = text[: text.index(block)].count("\n") + 1
            last_line = first_line + block.count("\n")
            if first_line != block_contract.get("first_line"):
                fail(errors, f"block first line mismatch: {key} {first_line}")
            if last_line != block_contract.get("last_line"):
                fail(errors, f"block last line mismatch: {key} {last_line}")
    return blocks


def require_fragments(block: str, fragments: list[str], label: str, errors: list[str]) -> None:
    for fragment in fragments:
        if fragment not in block:
            fail(errors, f"{label} is missing authored fragment: {fragment}")


def verify_semantics(
    contract: dict[str, Any], observer: dict[str, Any], blocks: dict[str, str], errors: list[str]
) -> None:
    if contract.get("scope") != "nonreligious major decision P0 slice: found_kingdom_decision":
        fail(errors, "source contract scope drifted from the nonreligious P0 slice")
    religion = contract.get("religion_scope", {})
    if religion.get("status") != "owner-deferred":
        fail(errors, "religion scope must remain owner-deferred")

    tree = contract.get("decision_tree", {})
    if tree.get("decision_id") != "found_kingdom_decision":
        fail(errors, "unexpected decision ID")
    if tree.get("group") != "major" or tree.get("ai_goal") is not False:
        fail(errors, "major group or interval-driven AI contract drifted")
    candidate = tree.get("candidate", {})
    if candidate.get("interval_months_by_top_title_tier") != EXPECTED_INTERVALS:
        fail(errors, "AI interval matrix drifted")
    if candidate.get("ai_potential") != "always = yes":
        fail(errors, "AI potential drifted")
    if tree.get("cost_matrix") != EXPECTED_COST_MATRIX:
        fail(errors, "dynamic cost matrix drifted")
    score = tree.get("score", {})
    if score.get("ai_will_do_base_percent") != 100 or score.get("modifiers") != []:
        fail(errors, "AI will-do score drifted")

    decision = blocks.get("found_kingdom_decision", "")
    effect = blocks.get("create_custom_kingdom_effect", "")
    landed = blocks.get("is_landed_or_landless_administrative", "")
    game_rule = blocks.get("custom_kingdoms", "")
    require_fragments(decision, DECISION_FRAGMENTS, "decision block", errors)
    require_fragments(effect, EFFECT_FRAGMENTS, "scripted effect block", errors)
    require_fragments(
        landed,
        ["is_landed = yes", "is_landless_administrative = yes"],
        "landed/admin trigger block",
        errors,
    )
    require_fragments(
        game_rule,
        ["default = on_custom_kingdoms", "off_custom_kingdoms = {"],
        "custom kingdoms game-rule block",
        errors,
    )

    if observer.get("contract") != "major-decision-found-kingdom-observer-v1-source-contract":
        fail(errors, "observer contract identity drifted")
    if observer.get("read_only") is not True or observer.get("requires_paused") is not True:
        fail(errors, "observer must remain read-only and paused-only")
    if observer.get("actor_scope") != "played_character_only":
        fail(errors, "observer actor scope must remain played-character-only")
    if observer.get("decision_allowlist") != ["found_kingdom_decision"]:
        fail(errors, "observer decision allowlist drifted")
    fields = observer.get("same_frame_fields", [])
    if len(fields) != len(set(fields)) or set(fields) != EXPECTED_RUNTIME_FIELDS:
        fail(errors, "observer same-frame field set drifted or contains duplicates")
    boundary = observer.get("effect_boundary", {})
    if boundary.get("mode") != "source_fingerprint_only":
        fail(errors, "observer effect boundary must remain source-fingerprint-only")
    if boundary.get("must_not_execute_effect") is not True:
        fail(errors, "observer must forbid effect execution")
    forbidden = set(observer.get("forbidden", []))
    if "execute decision" not in forbidden or "deduct cost" not in forbidden:
        fail(errors, "observer forbidden-operation list is incomplete")

    source_binding = observer.get("definition_binding", {})
    source_blocks = {
        block["key"]: block["canonical_sha256"]
        for source in contract.get("sources", [])
        for block in source.get("blocks", [])
    }
    if source_binding.get("decision_block_sha256") != source_blocks.get("found_kingdom_decision"):
        fail(errors, "observer decision fingerprint does not bind the source contract")
    if source_binding.get("effect_block_sha256") != source_blocks.get("create_custom_kingdom_effect"):
        fail(errors, "observer effect fingerprint does not bind the source contract")


def verify_contract(contract: dict[str, Any], observer: dict[str, Any], game_root: Path) -> list[str]:
    errors: list[str] = []
    build = contract.get("build", {})
    exe_path = game_root / str(build.get("exe_relative_path", ""))
    if not exe_path.is_file():
        return [f"missing exact-build executable: {exe_path}"]
    actual_size = exe_path.stat().st_size
    if actual_size != build.get("exe_size"):
        fail(errors, f"EXE size mismatch: {actual_size}")
    actual_sha = sha256_file(exe_path)
    if actual_sha != build.get("exe_sha256"):
        fail(errors, f"EXE SHA-256 mismatch: {actual_sha}")
    pe_error = verify_pe_image_base(exe_path, str(build.get("image_base", "0")))
    if pe_error is not None:
        fail(errors, pe_error)
    blocks = verify_sources(contract, game_root, errors)
    verify_semantics(contract, observer, blocks, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game-root",
        type=Path,
        required=True,
        help="Exact CK3 root containing binaries/ck3.exe and game/",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path(__file__).with_name("major_decision_found_kingdom_1_19_0_6_source.json"),
    )
    parser.add_argument(
        "--observer-contract",
        type=Path,
        default=Path(__file__).parent
        / "fixtures"
        / "major_decision_found_kingdom_observer_v1_source_contract.json",
    )
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8-sig"))
    observer = json.loads(args.observer_contract.read_text(encoding="utf-8-sig"))
    errors = verify_contract(contract, observer, args.game_root)
    if errors:
        for error in errors:
            print(f"RED: {error}", file=sys.stderr)
        return 1
    print(
        "GREEN: CK3 1.19.0.6 found_kingdom_decision candidate, eligibility, "
        "cost, score, effect source tree, and read-only observer contract match"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
