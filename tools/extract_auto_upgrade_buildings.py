#!/usr/bin/env python3
"""Extract the frozen CK3 province-building upgrade graph used by AUB.

The parser is intentionally structural: top-level building definitions and
nested trigger/cost blocks are parsed as Clausewitz data rather than guessed
with line-oriented regular expressions.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GAME_ROOT = Path(
    r"C:\SteamLibrary\steamapps\common\Crusader Kings III\game"
)
OUTPUT = ROOT / "tools" / "auto_upgrade_buildings_1_19_0_6.json"
EXPECTED_GAME_VERSION = "1.19.0.6"
GATE_FIELDS = (
    "is_enabled",
    "can_construct_potential",
    "can_construct_showing_failures_only",
    "can_construct",
)
RESOURCE_FIELDS = {
    "cost_gold": "gold",
    "cost_prestige": "prestige",
    "cost_piety": "piety",
}
SUPPORTED_RESOURCES = ("gold", "prestige", "piety")
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


class ExtractionError(RuntimeError):
    """Raised when installed vanilla data does not satisfy the frozen contract."""


@dataclass(frozen=True)
class Entry:
    key: str
    operator: str | None = None
    value: str | "Block" | None = None


@dataclass(frozen=True)
class Block:
    entries: tuple[Entry, ...]


@dataclass(frozen=True)
class Building:
    name: str
    relative_path: str
    body: Block


def tokenize_clausewitz(value: str) -> list[str]:
    tokens: list[str] = []
    index = 0
    operators = ("?=", ">=", "<=", "!=", "==", "=", ">", "<")
    while index < len(value):
        char = value[index]
        if char.isspace():
            index += 1
            continue
        if char == "#":
            newline = value.find("\n", index)
            index = len(value) if newline == -1 else newline + 1
            continue
        if char in "{}":
            tokens.append(char)
            index += 1
            continue
        if char == '"':
            end = index + 1
            escaped = False
            while end < len(value):
                current = value[end]
                if current == '"' and not escaped:
                    end += 1
                    break
                if current == "\\" and not escaped:
                    escaped = True
                else:
                    escaped = False
                end += 1
            else:
                raise ExtractionError("unterminated quoted Clausewitz string")
            tokens.append(value[index:end])
            index = end
            continue
        operator = next(
            (candidate for candidate in operators if value.startswith(candidate, index)),
            None,
        )
        if operator is not None:
            tokens.append(operator)
            index += len(operator)
            continue
        end = index
        while end < len(value):
            if value[end].isspace() or value[end] in '{}#"=<>!':
                break
            if value.startswith("?=", end):
                break
            end += 1
        if end == index:
            raise ExtractionError(
                f"unsupported Clausewitz character {value[index]!r} at offset {index}"
            )
        tokens.append(value[index:end])
        index = end
    return tokens


def parse_clausewitz(value: str) -> Block:
    tokens = tokenize_clausewitz(value)
    index = 0
    operators = {"?=", ">=", "<=", "!=", "==", "=", ">", "<"}

    def parse_entries(stop_at_brace: bool) -> Block:
        nonlocal index
        entries: list[Entry] = []
        while index < len(tokens):
            if tokens[index] == "}":
                if not stop_at_brace:
                    raise ExtractionError("unexpected closing Clausewitz brace")
                index += 1
                return Block(tuple(entries))
            key = tokens[index]
            if key == "{":
                raise ExtractionError("unexpected opening Clausewitz brace")
            index += 1
            if index >= len(tokens) or tokens[index] not in operators:
                entries.append(Entry(key))
                continue
            operator = tokens[index]
            index += 1
            if index >= len(tokens) or tokens[index] == "}":
                raise ExtractionError(f"missing value after {key} {operator}")
            if tokens[index] == "{":
                index += 1
                nested: str | Block = parse_entries(True)
            else:
                nested = tokens[index]
                index += 1
            entries.append(Entry(key, operator, nested))
        if stop_at_brace:
            raise ExtractionError("unterminated Clausewitz block")
        return Block(tuple(entries))

    result = parse_entries(False)
    if index != len(tokens):
        raise ExtractionError("Clausewitz parser left trailing tokens")
    return result


def render_block_body(block: Block, indent: int = 0) -> str:
    lines: list[str] = []
    prefix = "\t" * indent
    for entry in block.entries:
        if entry.operator is None:
            lines.append(f"{prefix}{entry.key}")
        elif isinstance(entry.value, Block):
            lines.append(f"{prefix}{entry.key} {entry.operator} {{")
            lines.extend(render_block_body(entry.value, indent + 1).splitlines())
            lines.append(f"{prefix}}}")
        else:
            lines.append(f"{prefix}{entry.key} {entry.operator} {entry.value}")
    return "\n".join(lines)


def direct_entries(block: Block, key: str) -> list[Entry]:
    return [entry for entry in block.entries if entry.key == key]


def one_scalar(block: Block, key: str) -> str | None:
    matches = direct_entries(block, key)
    if not matches:
        return None
    if any(isinstance(match.value, Block) or match.value is None for match in matches):
        raise ExtractionError(f"{key} must be a unique scalar")
    values = {str(match.value) for match in matches}
    if len(values) != 1:
        raise ExtractionError(f"{key} has conflicting scalar values: {sorted(values)}")
    return str(matches[0].value)


def one_block(block: Block, key: str) -> Block | None:
    matches = direct_entries(block, key)
    if not matches:
        return None
    if len(matches) != 1 or not isinstance(matches[0].value, Block):
        raise ExtractionError(f"{key} must be a unique block")
    return matches[0].value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_buildings(game_root: Path) -> tuple[dict[str, Building], dict[str, str]]:
    directory = game_root / "common" / "buildings"
    paths = sorted(directory.glob("*.txt"))
    if not paths:
        raise ExtractionError(f"vanilla building directory is missing or empty: {directory}")
    result: dict[str, Building] = {}
    hashes: dict[str, str] = {}
    for path in paths:
        relative = path.relative_to(game_root).as_posix()
        hashes[relative] = sha256_file(path)
        parsed = parse_clausewitz(path.read_text(encoding="utf-8-sig", errors="strict"))
        for entry in parsed.entries:
            if (
                entry.operator != "="
                or not isinstance(entry.value, Block)
                or not IDENTIFIER.fullmatch(entry.key)
            ):
                continue
            if entry.key in result:
                raise ExtractionError(f"duplicate vanilla building definition: {entry.key}")
            result[entry.key] = Building(entry.key, relative, entry.value)
    return result, hashes


def read_primary_buildings(game_root: Path) -> tuple[dict[str, str], dict[str, str]]:
    directory = game_root / "common" / "holdings"
    paths = sorted(directory.glob("*.txt"))
    if not paths:
        raise ExtractionError(f"vanilla holding directory is missing or empty: {directory}")
    roots: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for path in paths:
        relative = path.relative_to(game_root).as_posix()
        hashes[relative] = sha256_file(path)
        parsed = parse_clausewitz(path.read_text(encoding="utf-8-sig", errors="strict"))
        for entry in parsed.entries:
            if entry.operator != "=" or not isinstance(entry.value, Block):
                continue
            primary = one_scalar(entry.value, "primary_building")
            if primary is not None:
                roots[primary] = entry.key
    return roots, hashes


def building_cost(building: Building) -> tuple[str, dict[str, str]]:
    scripted = one_block(building.body, "cost")
    direct = {
        resource: value
        for field, resource in RESOURCE_FIELDS.items()
        if (value := one_scalar(building.body, field)) is not None
    }
    if scripted is not None and direct:
        raise ExtractionError(f"mixed direct/scripted cost fields: {building.name}")
    if scripted is not None:
        resources: dict[str, str] = {}
        for entry in scripted.entries:
            if (
                entry.operator != "="
                or isinstance(entry.value, Block)
                or entry.value is None
                or entry.key not in SUPPORTED_RESOURCES
            ):
                raise ExtractionError(
                    f"unsupported scripted cost entry in {building.name}: {entry.key}"
                )
            if entry.key in resources:
                raise ExtractionError(f"duplicate scripted cost resource: {building.name}:{entry.key}")
            resources[entry.key] = entry.value
        kind = "scripted_cost"
    else:
        resources = direct
        kind = "+".join(f"cost_{key}" for key in SUPPORTED_RESOURCES if key in resources)
    if not resources or "gold" not in resources:
        raise ExtractionError(f"upgrade target lacks a supported gold cost: {building.name}")
    return kind, {key: resources[key] for key in SUPPORTED_RESOURCES if key in resources}


def gate_blocks(building: Building) -> dict[str, str]:
    result: dict[str, str] = {}
    for field in GATE_FIELDS:
        block = one_block(building.body, field)
        if block is not None:
            result[field] = render_block_body(block)
    return result


def graph_chains(edges: dict[str, str]) -> tuple[list[list[str]], dict[str, str]]:
    predecessors: dict[str, str] = {}
    for source, target in edges.items():
        if target in predecessors:
            raise ExtractionError(
                f"upgrade graph converges at {target}: {predecessors[target]}, {source}"
            )
        predecessors[target] = source
    roots = sorted(source for source in edges if source not in predecessors)
    chains: list[list[str]] = []
    root_for_source: dict[str, str] = {}
    visited: set[str] = set()
    for root in roots:
        chain: list[str] = []
        cursor = root
        while cursor in edges:
            if cursor in visited:
                raise ExtractionError(f"cycle or duplicate traversal at {cursor}")
            visited.add(cursor)
            root_for_source[cursor] = root
            chain.append(cursor)
            cursor = edges[cursor]
        chains.append(chain)
    if visited != set(edges):
        missing = sorted(set(edges) - visited)
        raise ExtractionError(f"upgrade graph contains a cycle: {missing[:5]}")
    return chains, root_for_source


def build_snapshot(game_root: Path, game_version: str = EXPECTED_GAME_VERSION) -> dict[str, object]:
    game_root = game_root.resolve()
    buildings, building_hashes = read_buildings(game_root)
    primary_roots, holding_hashes = read_primary_buildings(game_root)
    vanilla_edges: dict[str, str] = {}
    for building in buildings.values():
        target = one_scalar(building.body, "next_building")
        if target is None:
            continue
        if target not in buildings:
            raise ExtractionError(f"unknown next_building target: {building.name} -> {target}")
        vanilla_edges[building.name] = target
    all_chains, root_for_source = graph_chains(vanilla_edges)
    included: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    for source, target in sorted(vanilla_edges.items()):
        source_building = buildings[source]
        target_building = buildings[target]
        target_type = one_scalar(target_building.body, "type") or "regular"
        record: dict[str, object] = {
            "source": source,
            "target": target,
            "chain_root": root_for_source[source],
            "source_file": source_building.relative_path,
            "target_file": target_building.relative_path,
            "target_type": target_type,
        }
        if target_type == "great_building":
            record["reason"] = "great_project"
            excluded.append(record)
            continue
        cost_kind, resources = building_cost(target_building)
        record.update(
            {
                "cost_kind": cost_kind,
                "resources": resources,
                "gates": gate_blocks(target_building),
                "primary_building": root_for_source[source] in primary_roots,
                "primary_holding_type": primary_roots.get(root_for_source[source]),
            }
        )
        included.append(record)
    included_sources = {str(edge["source"]): str(edge["target"]) for edge in included}
    included_chains, _ = graph_chains(included_sources)
    schema_path = game_root / "common" / "buildings" / "_buildings.info"
    if not schema_path.is_file():
        raise ExtractionError(f"building schema is missing: {schema_path}")
    payload: dict[str, object] = {
        "schema_version": 1,
        "game_version": game_version,
        "source": "CK3 installed vanilla province-building definitions",
        "building_definition_count": len(buildings),
        "vanilla_edge_count": len(vanilla_edges),
        "included_edge_count": len(included),
        "excluded_edge_count": len(excluded),
        "chain_count": len(included_chains),
        "primary_building_roots": dict(sorted(primary_roots.items())),
        "input_sha256": {
            **dict(sorted(building_hashes.items())),
            **dict(sorted(holding_hashes.items())),
            schema_path.relative_to(game_root).as_posix(): sha256_file(schema_path),
        },
        "included_edges": included,
        "excluded_edges": excluded,
    }
    # Keep the full-graph chain walk live: it is part of cycle validation even
    # though only the included graph is serialized.
    if not all_chains:
        raise ExtractionError("vanilla building graph unexpectedly has no chains")
    return payload


def render_snapshot(payload: dict[str, object]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, default=DEFAULT_GAME_ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        expected = render_snapshot(build_snapshot(args.game_root))
    except (OSError, UnicodeError, ExtractionError) as error:
        print(f"AUTO UPGRADE BUILDINGS EXTRACTION FAILED: {error}", file=sys.stderr)
        return 1
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            print(f"STALE BUILDING SNAPSHOT: {OUTPUT}", file=sys.stderr)
            return 1
        print("AUTO UPGRADE BUILDINGS SNAPSHOT OK")
        return 0
    OUTPUT.write_bytes(expected)
    payload = json.loads(expected)
    print(
        f"Extracted {payload['building_definition_count']} buildings, "
        f"{payload['included_edge_count']} included edges, "
        f"{payload['excluded_edge_count']} excluded edges -> {OUTPUT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
