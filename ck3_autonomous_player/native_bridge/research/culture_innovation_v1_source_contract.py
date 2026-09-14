#!/usr/bin/env python3
"""Verify the exact-build CULTURE1 innovation research contract."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import struct
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]


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


def _without_comments(text: str) -> str:
    return re.sub(r"#.*", "", text)


def _balanced_body(text: str, opening_end: int) -> tuple[str, int]:
    depth = 1
    cursor = opening_end
    while cursor < len(text) and depth:
        depth += (text[cursor] == "{") - (text[cursor] == "}")
        cursor += 1
    _require(depth == 0, "unbalanced innovation definition")
    return text[opening_end : cursor - 1], cursor


def _definitions(text: str) -> list[tuple[str, str]]:
    clean = _without_comments(text)
    result: list[tuple[str, str]] = []
    for match in re.finditer(r"(?m)^([A-Za-z0-9_]+)\s*=\s*\{", clean):
        body, _ = _balanced_body(clean, match.end())
        result.append((match.group(1), body))
    return result


def _depth_at(text: str, position: int) -> int:
    return text[:position].count("{") - text[:position].count("}")


def _direct_scalar(body: str, key: str) -> str | None:
    pattern = re.compile(rf"(?m)^\s*{re.escape(key)}\s*=\s*([^\s{{}}]+)")
    for match in pattern.finditer(body):
        if _depth_at(body, match.start()) == 0:
            return match.group(1)
    return None


def _direct_block(body: str, key: str) -> str | None:
    pattern = re.compile(rf"(?m)^\s*{re.escape(key)}\s*=\s*\{{")
    for match in pattern.finditer(body):
        if _depth_at(body, match.start()) == 0:
            value, _ = _balanced_body(body, match.end())
            return value
    return None


def _normalized(block: str) -> str:
    return re.sub(r"\s+", " ", block).strip()


def _verify_innovation_inventory(game_root: Path, expected: dict[str, object]) -> None:
    source_dir = game_root / "common/culture/innovations"
    definitions: list[tuple[str, str]] = []
    for source in sorted(source_dir.glob("*.txt")):
        definitions.extend(_definitions(source.read_text(encoding="utf-8-sig")))

    _require(
        len(definitions) == expected["definition_count"],
        f"innovation definition count drifted: {len(definitions)}",
    )
    era_counts = collections.Counter(
        _direct_scalar(body, "culture_era") for _, body in definitions
    )
    group_counts = collections.Counter(_direct_scalar(body, "group") for _, body in definitions)
    skill_counts = collections.Counter(_direct_scalar(body, "skill") for _, body in definitions)
    _require(dict(era_counts) == expected["era_counts"], f"era counts drifted: {era_counts}")
    _require(
        dict(group_counts) == expected["group_counts"],
        f"innovation group counts drifted: {group_counts}",
    )
    _require(
        dict(skill_counts) == expected["skill_counts"],
        f"innovation skill counts drifted: {skill_counts}",
    )

    fascination = {
        name: _direct_block(body, "ai_weight_for_fascination")
        for name, body in definitions
    }
    spread = {
        name: _direct_block(body, "ai_weight_for_spread") for name, body in definitions
    }
    potential = {name: _direct_block(body, "potential") for name, body in definitions}
    can_progress = {
        name: _direct_block(body, "can_progress") for name, body in definitions
    }
    _require(
        sum(value is not None for value in fascination.values())
        == expected["with_ai_weight_for_fascination"],
        "fascination weight coverage drifted",
    )
    _require(
        sum(value is not None for value in spread.values())
        == expected["with_ai_weight_for_spread"],
        "spread weight coverage drifted",
    )
    _require(
        sum(value is not None for value in potential.values()) == expected["with_potential"],
        "potential gate coverage drifted",
    )
    _require(
        sum(value is not None for value in can_progress.values())
        == expected["with_can_progress"],
        "can_progress gate coverage drifted",
    )
    _require(
        sorted(name for name, value in can_progress.items() if value is not None)
        == sorted(expected["can_progress_keys"]),
        "can_progress innovation keys drifted",
    )

    template_counts = collections.Counter(_normalized(value or "") for value in fascination.values())
    templates = {
        "plain_100": "value = 100",
        "early_100_else_0": (
            "value = 100 if = { limit = { NOT = { has_cultural_era_or_later = "
            "culture_era_early_medieval } } multiply = 0 }"
        ),
        "high_100_else_0": (
            "value = 100 if = { limit = { NOT = { has_cultural_era_or_later = "
            "culture_era_high_medieval } } multiply = 0 }"
        ),
        "late_100_else_0": (
            "value = 100 if = { limit = { NOT = { has_cultural_era_or_later = "
            "culture_era_late_medieval } } multiply = 0 }"
        ),
    }
    actual_templates = {name: template_counts[value] for name, value in templates.items()}
    _require(
        actual_templates == expected["fascination_weight_templates"],
        f"fascination templates drifted: {actual_templates}",
    )
    _require(len(template_counts) == len(templates), "unexpected fascination weight template")

    exception = expected["cross_era_exception"]
    by_name = {name: body for name, body in definitions}
    exception_body = by_name[str(exception["key"])]
    _require(
        _direct_scalar(exception_body, "culture_era") == exception["declared_era"]
        and str(exception["fascination_gate"])
        in (_direct_block(exception_body, "ai_weight_for_fascination") or ""),
        "cross-era fascination exception drifted",
    )


def check(repo_root: Path, ck3_root: Path) -> None:
    contract_path = (
        repo_root
        / "ck3_autonomous_player/native_bridge/research/culture_innovation_v1_abi.json"
    )
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    _require(contract["schema_version"] == 1, "schema version drifted")
    _require(contract["status"] == "static-confirmed-research-only", "status drifted")
    scope = contract["scope"]
    _require(not any(scope.values()), "research-only scope was widened")

    for source in contract["stock_sources"]:
        source_path = ck3_root / str(source["path"])
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest().upper()
        _require(digest == source["sha256"], f"stock source hash drifted: {source['path']}")

    game_root = ck3_root / "game"
    _verify_innovation_inventory(game_root, contract["innovation_inventory"])

    schema_text = (
        game_root / "common/culture/innovations/_culture_innovations.info"
    ).read_text(encoding="utf-8-sig")
    for token in (
        "ai_weight_for_spread",
        "ai_weight_for_fascination",
        "potential = {}",
        "can_progress = {}",
        "scope:character",
    ):
        _require(token in schema_text, f"innovation schema token missing: {token}")

    era_text = (game_root / "common/culture/eras/00_culture_eras.txt").read_text(
        encoding="utf-8-sig"
    )
    for token in (
        "culture_era_tribal = {",
        "culture_era_early_medieval = {",
        "year = 900",
        "culture_era_high_medieval = {",
        "year = 1050",
        "culture_era_late_medieval = {",
        "year = 1200",
    ):
        _require(token in era_text, f"culture era token missing: {token}")

    defines_text = (game_root / "common/defines/00_defines.txt").read_text(
        encoding="utf-8-sig"
    )
    for token in (
        "MINIMUM_INNOVATIONS_TO_NEXT_ERA = 8",
        "ERA_PROGRESS_GAIN_BASE_MONTHLY = 0.1",
        "INNOVATION_PROGRESS_CHANCE_BASE = 5",
        "INNOVATION_PROGRESS_CHANCE_FROM_SPREAD = 40",
        "INNOVATION_PROGRESS_CHANCE_FROM_FASCINATION_BASE = 10",
        "INNOVATION_PROGRESS_CHANCE_FROM_FASCINATION_SKILL_CAP = 45",
        "INNOVATION_PROGRESS_GAIN_BASE = 0.3",
        "INNOVATION_PROGRESS_GAIN_PER_AVERAGE_DEVELOPMENT_LEVEL = 0.02",
    ):
        _require(token in defines_text, f"culture define token missing: {token}")

    gui_text = (game_root / "gui/window_culture.gui").read_text(encoding="utf-8-sig")
    for token in (
        "[CultureWindow.GetCultureEras]",
        "[GuiCultureEraGroup.GetInnovations]",
        "[And(CultureInnovation.GetCulture.IsPlayerCultureHead, Not(CultureInnovation.IsActive))]",
        "[CultureInnovation.CanBeFascination]",
        "[CultureInnovation.SelectAsFascination]",
        "[CultureInnovation.IsFascination]",
        "[CultureInnovation.HasSpreadMarker]",
        "[FixedPointToFloat(CultureInnovation.GetProgress)]",
    ):
        _require(token in gui_text, f"culture GUI token missing: {token}")

    doc_text = (repo_root / "docs/ck3-native-ai/culture-innovation-ai.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "G2-M6-CULTURE1-NATIVE-TREE",
        "implement_private_exact_build_culture_innovation_snapshot_v1_reader",
        "0x22C4FC0",
        "0xC02860",
        "```mermaid",
        "unknown",
    ):
        _require(token in doc_text, f"native-tree evidence missing: {token}")

    executable = contract["executable"]
    image = (ck3_root / str(executable["path"])).read_bytes()
    _require(len(image) == executable["size"], "executable size drifted")
    _require(
        hashlib.sha256(image).hexdigest().upper() == executable["sha256"],
        "executable SHA-256 drifted",
    )
    image_base, sections = _pe_layout(image)
    _require(image_base == int(executable["image_base"], 0), "image base drifted")
    for binding in contract["native_strings"]:
        payload = (str(binding["value"]) + "\0").encode("ascii")
        _require(
            _at(image, sections, int(binding["rva"], 0), len(payload)) == payload,
            f"native string drifted: {binding['name']}",
        )
    for anchor in contract["native_anchors"]:
        payload = bytes.fromhex(anchor["bytes_hex"])
        _require(
            _at(image, sections, int(anchor["rva"], 0), len(payload)) == payload,
            f"native anchor drifted: {anchor['name']}",
        )

    p0 = contract["p0_read_only_slice"]
    _require(
        p0["unique_next_implementation_entry"]
        == "implement_private_exact_build_culture_innovation_snapshot_v1_reader",
        "P0 implementation seam drifted",
    )
    _require(contract["action_seam"]["ack_is_success"] is False, "ACK boundary drifted")
    _require(len(contract["unknowns"]) >= 4, "unknown ledger was silently narrowed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--ck3-root", type=Path)
    arguments = parser.parse_args()
    repo_root = arguments.repo_root.resolve()
    ck3_root = (arguments.ck3_root or repo_root / "Crusader Kings III").resolve()
    check(repo_root, ck3_root)
    print(
        "[culture_innovation_v1_source_contract] GREEN_STATIC "
        "build=1.19.0.6 definitions=108 p0=read-only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
