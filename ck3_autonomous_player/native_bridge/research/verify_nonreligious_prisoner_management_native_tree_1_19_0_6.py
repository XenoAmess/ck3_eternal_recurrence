#!/usr/bin/env python3
"""Verify the exact-build nonreligious prisoner-management research tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
CONTRACT_RELATIVE = Path(
    "ck3_autonomous_player/native_bridge/research/"
    "nonreligious_prisoner_management_native_tree_1_19_0_6.json"
)
DOC_RELATIVE = Path("docs/ck3-native-ai/prisoner-crime-ransom-ai.md")
CORE_CONTRACT_RELATIVE = Path(
    "ck3_autonomous_player/native_bridge/research/"
    "core_diplomatic_proposals_v1_contract.json"
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _parse_rva(value: str) -> int:
    return int(value, 16)


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
    _require(depth == 0, "unbalanced scripted definition")
    return text[opening_end : cursor - 1], cursor


def _top_level_body(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}[ \t]*=[ \t]*\{{", text)
    _require(match is not None, f"missing top-level definition: {name}")
    body, _ = _balanced_body(text, match.end())
    return body


def _direct_blocks(body: str, key: str) -> list[str]:
    result: list[str] = []
    pattern = re.compile(rf"(?m)^[ \t]*{re.escape(key)}[ \t]*=[ \t]*\{{")
    for match in pattern.finditer(body):
        depth = body[: match.start()].count("{") - body[: match.start()].count("}")
        if depth == 0:
            value, _ = _balanced_body(body, match.end())
            result.append(value)
    return result


def _direct_block(body: str, key: str) -> str | None:
    values = _direct_blocks(body, key)
    _require(len(values) <= 1, f"multiple direct {key} blocks")
    return values[0] if values else None


def _direct_scalars(body: str, key: str) -> list[str]:
    result: list[str] = []
    pattern = re.compile(
        rf"(?m)^[ \t]*{re.escape(key)}[ \t]*=[ \t]*([^\s{{}}]+)"
    )
    for match in pattern.finditer(body):
        depth = body[: match.start()].count("{") - body[: match.start()].count("}")
        if depth == 0:
            result.append(match.group(1))
    return result


def _direct_scalar(body: str | None, key: str) -> str | None:
    if body is None:
        return None
    values = _direct_scalars(body, key)
    _require(len(values) <= 1, f"multiple direct scalar values for {key}")
    return values[0] if values else None


def _optional_int(value: str | None) -> int | None:
    return None if value is None else int(value)


def _direct_modifier_stats(body: str | None) -> tuple[int, int]:
    if body is None:
        return 0, 0
    modifiers = _direct_blocks(body, "modifier")
    factor_zero = sum(_direct_scalar(modifier, "factor") == "0" for modifier in modifiers)
    return len(modifiers), factor_zero


def _frequency_by_tier(body: str) -> dict[str, int]:
    block = _direct_block(body, "ai_frequency_by_tier")
    if block is None:
        return {}
    result: dict[str, int] = {}
    for key in ("barony", "county", "duchy", "kingdom", "empire", "hegemony"):
        value = _direct_scalar(block, key)
        if value is not None:
            result[key] = int(value)
    return result


def _ai_recipients(body: str) -> list[str]:
    result: list[str] = []
    for targets in _direct_blocks(body, "ai_targets"):
        result.extend(_direct_scalars(targets, "ai_recipients"))
    return result


def _send_option_flags(body: str) -> list[str]:
    result: list[str] = []
    for option in _direct_blocks(body, "send_option"):
        flag = _direct_scalar(option, "flag")
        _require(flag is not None, "send_option lost flag")
        result.append(flag)
    return result


def _definition_line_spans(text: str) -> dict[str, tuple[int, int]]:
    starts: list[tuple[str, int]] = []
    for match in re.finditer(r"(?m)^([A-Za-z0-9_]+)[ \t]*=[ \t]*\{", text):
        starts.append((match.group(1), text.count("\n", 0, match.start()) + 1))
    line_count = len(text.splitlines())
    return {
        name: (line, starts[index + 1][1] - 1 if index + 1 < len(starts) else line_count)
        for index, (name, line) in enumerate(starts)
    }


def _verify_sources(ck3_root: Path, contract: dict[str, Any]) -> None:
    for source in contract["stock_sources"]:
        path = ck3_root / source["path"]
        data = path.read_bytes()
        _require(len(data) == source["size"], f"stock source size drifted: {source['path']}")
        _require(
            _sha256(data) == str(source["sha256"]).upper(),
            f"stock source hash drifted: {source['path']}",
        )
        text = data.decode("utf-8-sig")
        for token in source["required_tokens"]:
            _require(token in text, f"stock token missing in {source['path']}: {token}")


def _verify_interaction_tree(ck3_root: Path, contract: dict[str, Any]) -> None:
    path = ck3_root / "game/common/character_interactions/00_prison_interactions.txt"
    text = path.read_text(encoding="utf-8-sig")
    clean = _without_comments(text)
    spans = _definition_line_spans(clean)
    for name, expected in contract["interaction_definitions"].items():
        body = _top_level_body(clean, name)
        accept = _direct_block(body, "ai_accept")
        will_do = _direct_block(body, "ai_will_do")
        accept_count, accept_factor_zero = _direct_modifier_stats(accept)
        will_count, will_factor_zero = _direct_modifier_stats(will_do)
        _require(accept_factor_zero == 0, f"unexpected ai_accept factor zero in {name}")
        _require(
            list(spans[name]) == expected["definition_lines"],
            f"definition line span drifted: {name}",
        )
        _require(
            _ai_recipients(body) == expected["ai_recipients"],
            f"AI recipient inventory drifted: {name}",
        )
        _require(
            _frequency_by_tier(body) == expected["ai_frequency_by_tier"],
            f"AI tier frequency drifted: {name}",
        )
        _require(
            _optional_int(_direct_scalar(body, "ai_frequency"))
            == expected.get("ai_frequency"),
            f"AI scalar frequency drifted: {name}",
        )
        _require(
            _optional_int(_direct_scalar(accept, "base")) == expected["ai_accept_base"],
            f"ai_accept base drifted: {name}",
        )
        _require(
            accept_count == expected["ai_accept_direct_modifier_count"],
            f"ai_accept modifier count drifted: {name}",
        )
        _require(
            _optional_int(_direct_scalar(will_do, "base")) == expected["ai_will_do_base"],
            f"ai_will_do base drifted: {name}",
        )
        _require(
            will_count == expected["ai_will_do_direct_modifier_count"],
            f"ai_will_do modifier count drifted: {name}",
        )
        _require(
            will_factor_zero == expected["ai_will_do_factor_zero_count"],
            f"ai_will_do factor-zero count drifted: {name}",
        )
        _require(
            _send_option_flags(body) == expected["send_option_flags"],
            f"send-option inventory drifted: {name}",
        )

    _require(
        "debug_imprison_simple_interaction" not in contract["interaction_definitions"],
        "debug interaction entered the frozen product tree",
    )
    _require(
        "prison_break_contract_interaction" not in contract["interaction_definitions"],
        "scheme interaction entered the prisoner-management slice",
    )


def _verify_native_substrate(
    root: Path,
    image: bytes,
    sections: list[tuple[int, int, int, int]],
    contract: dict[str, Any],
) -> None:
    core = json.loads((root / CORE_CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    core_spans = {row["name"]: row for row in core["native_pipeline"]["spans"]}
    for name, expected in contract["generic_interaction_native_substrate"]["spans"].items():
        reference = core_spans[name]
        for key in ("rva_start", "rva_end_exclusive", "sha256"):
            _require(reference[key] == expected[key], f"generic native substrate drifted: {name}.{key}")
        start = _parse_rva(expected["rva_start"])
        end = _parse_rva(expected["rva_end_exclusive"])
        _require(
            _sha256(_at(image, sections, start, end - start)) == expected["sha256"],
            f"exact-build native span drifted: {name}",
        )

    for name, rva_text in contract["exact_build_reflection_anchors"].items():
        if name == "boundary":
            continue
        expected = name.encode("ascii") + b"\0"
        _require(
            _at(image, sections, _parse_rva(rva_text), len(expected)) == expected,
            f"exact-build reflection string drifted: {name}",
        )


def _verify_research_contract(root: Path, contract: dict[str, Any]) -> None:
    _require(contract["schema_version"] == 1, "schema version drifted")
    _require(contract["status"] == "static-confirmed-research-only", "status drifted")
    scope = contract["scope"]
    for forbidden in (
        "faith",
        "doctrine",
        "tenet",
        "conversion",
        "holy orders",
        "bridge",
        "CMake",
        "CK3 launch",
    ):
        _require(
            forbidden.lower() in json.dumps(scope, ensure_ascii=False).lower(),
            f"scope boundary missing: {forbidden}",
        )
    boundary = contract["boundaries"]
    _require(not any(boundary.values()), "research-only boundary was widened")
    readiness = contract["readiness_at_research_close"]
    _require(readiness["stock_tree_frozen"], "stock tree is not frozen")
    _require(readiness["exact_build_sources_reproducible"], "exact-build sources are not reproducible")
    for key in (
        "prisoner_enumerator_mapped",
        "ransom_special_role_payload_mapped",
        "observer_implemented",
        "paused_live_validated",
        "action_designed",
        "public_mcp_ready",
        "planner_ready",
    ):
        _require(not readiness[key], f"research overstated readiness: {key}")

    observer = contract["p0_observer_contract"]
    _require(observer["name"] == "player_prisoner_management_snapshot_v1", "observer name drifted")
    _require(observer["status"] == "research-only; not implemented or public", "observer status drifted")
    _require(observer["read_only"], "P0 observer is not read-only")
    _require(
        observer["inputs"]
        == ["none; bind actor to the current played character in one paused application-main snapshot"],
        "P0 observer accepted caller identities",
    )
    _require(
        observer["collection_contract"]["source"]
        == "complete engine-owned prisoner collection for the played character",
        "P0 observer lost complete native collection requirement",
    )
    _require("cap" in observer["collection_contract"]["prohibition"].lower(), "truncation boundary missing")
    _require(
        observer["implementation_entry"]
        == "implement_private_exact_build_player_prisoner_management_snapshot_v1_reader",
        "next implementation entry drifted",
    )
    preview_keys = [row["interaction"] for row in observer["allowlisted_preview_rows"]]
    _require(
        preview_keys[:5]
        == [
            "ransom_interaction",
            "release_from_prison_interaction",
            "execute_prisoner_interaction",
            "move_to_dungeon_interaction",
            "move_to_house_arrest_interaction",
        ],
        "P0 preview order drifted",
    )
    _require(
        "demand_conversion and take_vows are omitted"
        in observer["allowlisted_preview_rows"][1]["required"],
        "religious release options entered the P0 observer",
    )

    doc = (root / DOC_RELATIVE).read_text(encoding="utf-8")
    for token in (
        "G2-M6-PRISONER1-NATIVE-TREE",
        "1.19.0.6",
        "3E05C94C",
        "player_prisoner_management_snapshot_v1",
        "implement_private_exact_build_player_prisoner_management_snapshot_v1_reader",
        "GetPrisoners",
        "0x4107BA8",
        "Can Send",
        "宗教域排除",
        "static-ready",
        "research-only",
    ):
        _require(token in doc, f"research document token missing: {token}")
    _require(doc.count("~~~mermaid") >= 4, "research document needs four frozen trees")


def check(root: Path, ck3_root: Path) -> None:
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    _verify_sources(ck3_root, contract)
    _verify_interaction_tree(ck3_root, contract)

    executable = ck3_root / contract["exact_build"]["executable_relative_path"]
    image = executable.read_bytes()
    _require(len(image) == contract["exact_build"]["executable_size"], "ck3.exe size drifted")
    _require(_sha256(image) == contract["exact_build"]["executable_sha256"], "ck3.exe hash drifted")
    image_base, sections = _pe_layout(image)
    _require(
        image_base == _parse_rva(contract["exact_build"]["image_base"]),
        "ck3.exe image base drifted",
    )
    _verify_native_substrate(root, image, sections, contract)
    _verify_research_contract(root, contract)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--ck3-root",
        type=Path,
        default=REPO_ROOT / "Crusader Kings III",
        help="CK3 install root containing binaries/ck3.exe and game/",
    )
    args = parser.parse_args()
    check(args.root.resolve(), args.ck3_root.resolve())
    print("nonreligious-prisoner-management-native-tree: GREEN_STATIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
