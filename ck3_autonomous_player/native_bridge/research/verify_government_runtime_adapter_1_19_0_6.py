#!/usr/bin/env python3
"""Verify the CK3 1.19.0.6 government/runtime adapter research freeze.

The verifier is file-only.  It never starts or attaches to CK3.  Supply the
game root explicitly or through CK3_GAME_ROOT so the check is portable across
authorized operators and workstations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
from typing import Any


NONRELIGIOUS_AI_DEFAULTS = {
    "use_lifestyle": True,
    "arrange_marriage": True,
    "use_goals": True,
    "use_decisions": True,
    "use_scripted_guis": True,
    "use_legends": True,
    "use_great_projects": False,
}
AI_KEYS = tuple(NONRELIGIOUS_AI_DEFAULTS)
FEATURE_TRIGGER_MAP = {
    "has_ep3_dlc_trigger": "roads_to_power",
    "has_mpo_dlc_trigger": "khans_of_the_steppe",
    "has_tgp_dlc_trigger": "all_under_heaven",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def tokenize(text: str) -> list[str]:
    """Tokenize the Clausewitz subset needed by government definitions."""

    tokens: list[str] = []
    index = 0
    operator_chars = "=<>!?"
    delimiters = set("{}#\"") | set(operator_chars)
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char == "#":
            newline = text.find("\n", index)
            index = len(text) if newline == -1 else newline + 1
            continue
        if char in "{}":
            tokens.append(char)
            index += 1
            continue
        if char == '"':
            index += 1
            value: list[str] = []
            while index < len(text):
                char = text[index]
                if char == '"':
                    index += 1
                    break
                if char == "\\" and index + 1 < len(text):
                    value.append(text[index + 1])
                    index += 2
                    continue
                value.append(char)
                index += 1
            else:
                raise ValueError("unterminated quoted Clausewitz string")
            tokens.append("".join(value))
            continue
        if char in operator_chars:
            start = index
            while index < len(text) and text[index] in operator_chars:
                index += 1
            tokens.append(text[start:index])
            continue
        start = index
        while (
            index < len(text)
            and not text[index].isspace()
            and text[index] not in delimiters
        ):
            index += 1
        if index == start:
            raise ValueError(f"unsupported Clausewitz character at offset {index}")
        tokens.append(text[start:index])
    return tokens


def matching_brace(tokens: list[str], opening: int) -> int:
    if tokens[opening] != "{":
        raise ValueError("expected opening brace")
    depth = 0
    for index in range(opening, len(tokens)):
        if tokens[index] == "{":
            depth += 1
        elif tokens[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("unterminated Clausewitz block")


def top_level_blocks(tokens: list[str]) -> list[tuple[str, list[str]]]:
    blocks: list[tuple[str, list[str]]] = []
    index = 0
    while index < len(tokens):
        if index + 2 >= len(tokens) or tokens[index + 1] != "=":
            raise ValueError(f"expected top-level assignment near {tokens[index]!r}")
        if tokens[index + 2] != "{":
            index += 3
            continue
        closing = matching_brace(tokens, index + 2)
        blocks.append((tokens[index], tokens[index + 3 : closing]))
        index = closing + 1
    return blocks


def direct_fields(tokens: list[str]) -> dict[str, list[str | list[str]]]:
    fields: dict[str, list[str | list[str]]] = {}
    index = 0
    while index < len(tokens):
        if tokens[index] in {"{", "}"}:
            raise ValueError("unexpected brace in direct field scan")
        # Clausewitz permits function-style values such as ``color = hsv{...}``.
        # They are opaque to this extractor, but their body still has to be
        # skipped as one field value so inner assignments are not misclassified.
        if index + 1 < len(tokens) and tokens[index + 1] == "{":
            index = matching_brace(tokens, index + 1) + 1
            continue
        if index + 1 >= len(tokens) or tokens[index + 1] not in {
            "=", "?=", ">=", "<=", "!=", "==", ">", "<"
        }:
            index += 1
            continue
        key = tokens[index]
        if index + 2 >= len(tokens):
            raise ValueError(f"missing value for {key}")
        if tokens[index + 2] == "{":
            closing = matching_brace(tokens, index + 2)
            value: str | list[str] = tokens[index + 3 : closing]
            index = closing + 1
        elif index + 3 < len(tokens) and tokens[index + 3] == "{":
            # Function-style scalar followed by a body, for example hsv{...}.
            # Preserve the function name as the scalar and skip its opaque body.
            value = tokens[index + 2]
            index = matching_brace(tokens, index + 3) + 1
        else:
            value = tokens[index + 2]
            index += 3
        fields.setdefault(key, []).append(value)
    return fields


def one_scalar(
    fields: dict[str, list[str | list[str]]], key: str
) -> str | None:
    values = fields.get(key, [])
    if not values:
        return None
    if len(values) != 1 or not isinstance(values[0], str):
        raise ValueError(f"{key} is not one scalar")
    return values[0]


def one_block(
    fields: dict[str, list[str | list[str]]], key: str
) -> list[str] | None:
    values = fields.get(key, [])
    if not values:
        return None
    if len(values) != 1 or not isinstance(values[0], list):
        raise ValueError(f"{key} is not one block")
    return values[0]


def parse_bool(value: str, name: str) -> bool:
    if value == "yes":
        return True
    if value == "no":
        return False
    raise ValueError(f"{name} must be yes/no, got {value!r}")


def scalar_assignments(tokens: list[str]) -> dict[str, str]:
    fields = direct_fields(tokens)
    result: dict[str, str] = {}
    for key, values in fields.items():
        if len(values) == 1 and isinstance(values[0], str):
            result[key] = values[0]
    return result


def flag_values(tokens: list[str]) -> list[str]:
    if any(token in {"{", "}", "="} for token in tokens):
        raise ValueError("government flag block is not a flat value list")
    return list(tokens)


def recursive_feature_gates(tokens: list[str]) -> list[str]:
    gates: set[str] = set()
    for index in range(len(tokens) - 2):
        key, operator, value = tokens[index : index + 3]
        if operator != "=":
            continue
        if key in FEATURE_TRIGGER_MAP and value == "yes":
            gates.add(FEATURE_TRIGGER_MAP[key])
        elif key == "has_dlc_feature" and value not in {"yes", "no"}:
            gates.add(value)
    return sorted(gates, key=lambda item: item.encode("utf-8"))


def extract_registry(game_root: Path) -> list[dict[str, Any]]:
    registry: list[dict[str, Any]] = []
    for relative in (
        "game/common/governments/00_government_types.txt",
        "game/common/governments/01_japan_government_types.txt",
    ):
        path = game_root / relative
        text = path.read_text(encoding="utf-8-sig")
        for key, body in top_level_blocks(tokenize(text)):
            if not key.endswith("_government"):
                continue
            fields = direct_fields(body)
            raw_flags = one_block(fields, "flags")
            if raw_flags is None:
                raise ValueError(f"{key} lacks flags")
            ai_overrides: dict[str, bool] = {}
            ai_block = one_block(fields, "ai")
            if ai_block is not None:
                for ai_key, raw in scalar_assignments(ai_block).items():
                    if ai_key in AI_KEYS:
                        ai_overrides[ai_key] = parse_bool(raw, f"{key}.ai.{ai_key}")
            effective_ai = dict(NONRELIGIOUS_AI_DEFAULTS)
            effective_ai.update(ai_overrides)
            can_get = one_block(fields, "can_get_government")
            modifiers = scalar_assignments(one_block(fields, "character_modifier") or [])
            special_ai = {
                name: "scripted" if one_block(fields, name) is not None else (
                    one_scalar(fields, name) if one_scalar(fields, name) is not None else "default"
                )
                for name in (
                    "ai_ruler_desired_kingdom_titles",
                    "ai_ruler_desired_empire_titles",
                    "ai_can_reassign_council_positions",
                )
            }
            row: dict[str, Any] = {
                "key": key,
                "source": relative.removeprefix("game/"),
                "flags": flag_values(raw_flags),
                "mechanic_type": one_scalar(fields, "mechanic_type"),
                "mechanic_default": parse_bool(
                    one_scalar(fields, "is_mechanic_type_default") or "no",
                    f"{key}.is_mechanic_type_default",
                ),
                "fallback_priority": int(one_scalar(fields, "fallback") or "0"),
                "can_get_feature_gates": recursive_feature_gates(can_get or []),
                "nonreligious_ai_overrides": ai_overrides,
                "effective_nonreligious_ai_switches": effective_ai,
                "special_ai_scripts": special_ai,
                "ai_war_modifiers": {
                    name: modifiers[name]
                    for name in ("ai_war_chance", "ai_war_cooldown")
                    if name in modifiers
                },
            }
            registry.append(row)
    return registry


class PeImage:
    def __init__(self, path: Path) -> None:
        self.data = path.read_bytes()
        if self.data[:2] != b"MZ":
            raise ValueError("exact executable has no MZ header")
        pe_offset = struct.unpack_from("<I", self.data, 0x3C)[0]
        if self.data[pe_offset : pe_offset + 4] != b"PE\0\0":
            raise ValueError("exact executable has no PE signature")
        coff = pe_offset + 4
        section_count = struct.unpack_from("<H", self.data, coff + 2)[0]
        optional_size = struct.unpack_from("<H", self.data, coff + 16)[0]
        optional = coff + 20
        if struct.unpack_from("<H", self.data, optional)[0] != 0x20B:
            raise ValueError("exact executable is not PE32+")
        self.image_base = struct.unpack_from("<Q", self.data, optional + 24)[0]
        table = optional + optional_size
        self.sections: list[tuple[int, int, int, int]] = []
        for index in range(section_count):
            row = table + index * 40
            virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
                "<IIII", self.data, row + 8
            )
            self.sections.append(
                (virtual_address, max(virtual_size, raw_size), raw_offset, raw_size)
            )

    def read_rva(self, rva: int, size: int) -> bytes:
        for virtual, mapped, raw_offset, raw_size in self.sections:
            if virtual <= rva and rva + size <= virtual + mapped:
                delta = rva - virtual
                if delta + size > raw_size:
                    raise ValueError(f"RVA 0x{rva:X} reaches zero-filled data")
                return self.data[raw_offset + delta : raw_offset + delta + size]
        raise ValueError(f"RVA 0x{rva:X}+0x{size:X} is outside the image")

    def u32(self, rva: int) -> int:
        return struct.unpack("<I", self.read_rva(rva, 4))[0]

    def u64(self, rva: int) -> int:
        return struct.unpack("<Q", self.read_rva(rva, 8))[0]


def rva(value: str) -> int:
    return int(value, 0)


def verify_native(image: PeImage, native: dict[str, Any]) -> None:
    if image.image_base != rva(native["image_base"]):
        raise ValueError("PE image base changed")
    for name in (
        "government_resolver",
        "government_flag_evaluator",
        "government_flag_binary_search_helper",
        "government_link_leaf",
    ):
        item = native[name]
        start = rva(item["start_rva"])
        end = rva(item["end_rva_exclusive"])
        if sha256_bytes(image.read_rva(start, end - start)) != item["sha256"]:
            raise ValueError(f"{name} function body changed")
    for item in native["instruction_anchors"]:
        actual = image.read_rva(rva(item["rva"]), len(bytes.fromhex(item["hex"])))
        if actual.hex().upper() != item["hex"]:
            raise ValueError(f"instruction anchor changed at {item['rva']}")
    for item in native["rtti"]:
        type_rva = rva(item["type_descriptor_rva"])
        name = image.read_rva(type_rva + 16, 128).split(b"\0", 1)[0].decode("ascii")
        if name != item["name"]:
            raise ValueError(f"RTTI name changed: {item['name']}")
        col = image.u64(rva(item["vtable_rva"]) - 8) - image.image_base
        if col != rva(item["col_rva"]):
            raise ValueError(f"RTTI COL changed: {item['name']}")
    link = native["government_link_leaf"]
    target = image.u64(rva(link["vtable_rva"]) + int(link["vtable_slot"]) * 8)
    if target - image.image_base != rva(link["start_rva"]):
        raise ValueError("CGovernmentTypeLink leaf vtable slot changed")


def verify(game_root: Path, contract_path: Path, observer_path: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    observer = json.loads(observer_path.read_text(encoding="utf-8"))
    if contract.get("schema") != "xar.ck3.government_runtime_adapter_native_tree.v1":
        raise ValueError("unexpected government adapter research schema")
    if observer.get("contract") != "government-runtime-adapter-observer-v1":
        raise ValueError("unexpected observer contract")
    if contract["scope"]["religion_status"] != "owner-deferred":
        raise ValueError("religion deferral changed")
    if not contract["scope"]["religious_governments_identity_only"]:
        raise ValueError("religious-government identity boundary changed")
    for key in ("bridge_changed", "cmake_changed", "public_schema_changed", "planner_changed"):
        if contract["integration_impact"][key]:
            raise ValueError(f"research-only boundary changed: {key}")
    for relative, item in contract["repo_dependencies"].items():
        path = contract_path.parent / relative
        raw = path.read_bytes()
        if len(raw) != item["size"] or sha256_bytes(raw) != item["sha256"]:
            raise ValueError(f"repository dependency changed: {relative}")

    build = contract["exact_build"]
    exe = game_root / build["executable_relative_path"]
    if exe.stat().st_size != build["executable_size"]:
        raise ValueError("exact executable size changed")
    if sha256_file(exe) != build["executable_sha256"]:
        raise ValueError("exact executable hash changed")
    for relative, item in contract["source_files"].items():
        path = game_root / "game" / relative
        raw = path.read_bytes()
        if len(raw) != item["size"] or sha256_bytes(raw) != item["sha256"]:
            raise ValueError(f"source identity changed: {relative}")
        text = raw.decode("utf-8-sig")
        for token in item["required_tokens"]:
            if token not in text:
                raise ValueError(f"source token missing in {relative}: {token!r}")

    actual_registry = extract_registry(game_root)
    if actual_registry != contract["government_registry"]:
        raise ValueError("government registry/AI manifest changed")
    if len(actual_registry) != 18:
        raise ValueError("expected the complete 18-government stock registry")
    if sum(len(row["flags"]) for row in actual_registry) != 136:
        raise ValueError("expected 136 stock government flag declarations")
    stock_flag_manifest = json.dumps(
        [{"key": row["key"], "flags": row["flags"]} for row in actual_registry],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    if sha256_bytes(stock_flag_manifest) != contract["stock_key_flag_manifest_sha256"]:
        raise ValueError("stock government key/flag manifest changed")

    verify_native(PeImage(exe), contract["native_runtime_identity"])

    required_features = contract["adapter_feature_requirements"]
    if set(observer["feature_gate_vocabulary"]) != set(required_features["vocabulary"]):
        raise ValueError("observer and adapter feature vocabulary disagree")
    rows = {row["government_key"]: row for row in required_features["government_rows"]}
    if set(rows) != {row["key"] for row in actual_registry}:
        raise ValueError("adapter table does not cover the complete stock registry")
    for key in contract["scope"]["religious_government_keys"]:
        if rows[key]["adapter_status"] != "owner_deferred_religious":
            raise ValueError("religious government escaped the owner-deferred boundary")
    vocabulary = set(required_features["vocabulary"])
    registry_by_key = {row["key"]: row for row in actual_registry}
    for key, row in rows.items():
        if not set(row["required_effective_features"]).issubset(vocabulary):
            raise ValueError(f"adapter row uses an undeclared feature: {key}")
        if not set(registry_by_key[key]["can_get_feature_gates"]).issubset(
            set(row["required_effective_features"])
        ):
            raise ValueError(f"adapter row drops a direct source feature gate: {key}")
    if observer["implementation_status"] != "contract_only":
        raise ValueError("observer implementation status overclaims this work package")
    if not observer["read_only"] or not observer["application_main_only"]:
        raise ValueError("observer execution boundary changed")
    if observer["mutation_surface"] is not None:
        raise ValueError("observer contract gained a mutation surface")
    if observer["entitlement_semantics"]["ready"]:
        raise ValueError("observer invented entitlement provenance")

    return {
        "result": "GREEN",
        "schema": contract["schema"],
        "exact_build": build["game_version"],
        "government_rows": len(actual_registry),
        "flag_declarations": sum(len(row["flags"]) for row in actual_registry),
        "feature_vocabulary": required_features["vocabulary"],
        "observer_contract": observer["contract"],
        "ck3_started": False,
        "process_attached": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path)
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path(__file__).with_name("government_runtime_adapter_1_19_0_6.json"),
    )
    parser.add_argument(
        "--observer-contract",
        type=Path,
        default=Path(__file__).with_name("fixtures")
        / "government_runtime_adapter_observer_v1_contract.json",
    )
    parser.add_argument("--dump-government-registry", action="store_true")
    args = parser.parse_args()
    raw_root = args.game_root or (
        Path(os.environ["CK3_GAME_ROOT"]) if "CK3_GAME_ROOT" in os.environ else None
    )
    if raw_root is None:
        parser.error("--game-root or CK3_GAME_ROOT is required")
    game_root = raw_root.resolve()
    if args.dump_government_registry:
        print(json.dumps(extract_registry(game_root), ensure_ascii=False, indent=2))
        return 0
    result = verify(game_root, args.contract.resolve(), args.observer_contract.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
