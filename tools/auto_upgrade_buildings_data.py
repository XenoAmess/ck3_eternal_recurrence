"""Frozen CK3 1.19.0.6 province-building graph for Auto Upgrade Buildings."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "tools" / "auto_upgrade_buildings_1_19_0_6.json"
EXPECTED_GAME_VERSION = "1.19.0.6"
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
EXPECTED_TYPES = {"regular": 370, "special": 205, "duchy_capital": 30}
EXPECTED_COST_KINDS = {
    "cost_gold": 588,
    "cost_gold+cost_prestige": 5,
    "cost_gold+cost_piety": 3,
    "scripted_cost": 9,
}
EXPECTED_EXCLUSIONS = {
    ("mandala_capital_01", "mandala_capital_02"),
    ("mandala_capital_02", "mandala_capital_03"),
    ("mandala_capital_03", "mandala_capital_04"),
    ("mandala_capital_04", "mandala_capital_05"),
}


@dataclass(frozen=True)
class BuildingEdge:
    source: str
    target: str
    chain_root: str
    source_file: str
    target_file: str
    target_type: str
    cost_kind: str
    resources: tuple[tuple[str, str], ...]
    gates: tuple[tuple[str, str], ...]
    primary_building: bool
    primary_holding_type: str | None

    def resource(self, name: str) -> str | None:
        return dict(self.resources).get(name)


@dataclass(frozen=True)
class BuildingChain:
    root: str
    edges: tuple[BuildingEdge, ...]


@dataclass(frozen=True)
class ExcludedEdge:
    source: str
    target: str
    chain_root: str
    source_file: str
    target_file: str
    target_type: str
    reason: str


def _count(values: Iterable[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return result


def _load() -> tuple[dict[str, object], tuple[BuildingEdge, ...], tuple[ExcludedEdge, ...]]:
    try:
        payload = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot load frozen building snapshot: {error}") from error
    edges = tuple(
        BuildingEdge(
            source=item["source"],
            target=item["target"],
            chain_root=item["chain_root"],
            source_file=item["source_file"],
            target_file=item["target_file"],
            target_type=item["target_type"],
            cost_kind=item["cost_kind"],
            resources=tuple(item["resources"].items()),
            gates=tuple(item["gates"].items()),
            primary_building=item["primary_building"],
            primary_holding_type=item["primary_holding_type"],
        )
        for item in payload.get("included_edges", [])
    )
    excluded = tuple(
        ExcludedEdge(
            source=item["source"],
            target=item["target"],
            chain_root=item["chain_root"],
            source_file=item["source_file"],
            target_file=item["target_file"],
            target_type=item["target_type"],
            reason=item["reason"],
        )
        for item in payload.get("excluded_edges", [])
    )
    return payload, edges, excluded


def _chains(edges: tuple[BuildingEdge, ...]) -> tuple[BuildingChain, ...]:
    by_source = {edge.source: edge for edge in edges}
    roots = sorted({edge.chain_root for edge in edges})
    result: list[BuildingChain] = []
    visited: set[str] = set()
    for root in roots:
        chain: list[BuildingEdge] = []
        cursor = root
        while cursor in by_source:
            edge = by_source[cursor]
            if edge.chain_root != root or edge.source in visited:
                raise ValueError(f"invalid frozen chain traversal at {edge.source}")
            chain.append(edge)
            visited.add(edge.source)
            cursor = edge.target
        result.append(BuildingChain(root, tuple(chain)))
    if visited != set(by_source):
        raise ValueError("frozen included graph contains an unreachable edge")
    return tuple(result)


SNAPSHOT_DATA, EDGES, EXCLUDED_EDGES = _load()
CHAINS = _chains(EDGES)
INPUT_SHA256 = dict(SNAPSHOT_DATA.get("input_sha256", {}))
PRIMARY_BUILDING_ROOTS = dict(SNAPSHOT_DATA.get("primary_building_roots", {}))


def validate_data() -> None:
    if SNAPSHOT_DATA.get("schema_version") != 1:
        raise ValueError("unsupported building snapshot schema")
    if SNAPSHOT_DATA.get("game_version") != EXPECTED_GAME_VERSION:
        raise ValueError("building snapshot game version drifted")
    expected_counts = {
        "building_definition_count": 981,
        "vanilla_edge_count": 609,
        "included_edge_count": 605,
        "excluded_edge_count": 4,
        "chain_count": 165,
    }
    for key, expected in expected_counts.items():
        if SNAPSHOT_DATA.get(key) != expected:
            raise ValueError(f"building snapshot {key} drifted from {expected}")
    if len(EDGES) != 605 or len(CHAINS) != 165 or len(EXCLUDED_EDGES) != 4:
        raise ValueError("building graph object inventory drifted")
    if len({edge.source for edge in EDGES}) != len(EDGES):
        raise ValueError("included building sources must be unique")
    if len({edge.target for edge in EDGES}) != len(EDGES):
        raise ValueError("included building targets must be unique")
    for edge in EDGES:
        for identifier in (edge.source, edge.target, edge.chain_root):
            if IDENTIFIER.fullmatch(identifier) is None:
                raise ValueError(f"unsafe building identifier: {identifier}")
        if edge.target_type not in EXPECTED_TYPES:
            raise ValueError(f"unsupported building type: {edge.target_type}")
        if edge.cost_kind not in EXPECTED_COST_KINDS:
            raise ValueError(f"unsupported building cost kind: {edge.cost_kind}")
        resources = dict(edge.resources)
        if "gold" not in resources or not set(resources) <= {"gold", "prestige", "piety"}:
            raise ValueError(f"unsupported building resource set: {edge.target}")
        if any(not value or any(char.isspace() for char in value) for value in resources.values()):
            raise ValueError(f"unsafe building resource value: {edge.target}")
        if {name for name, _ in edge.gates} - {
            "is_enabled",
            "can_construct_potential",
            "can_construct_showing_failures_only",
            "can_construct",
        }:
            raise ValueError(f"unsupported building gate: {edge.target}")
    for expected, actual in (
        (EXPECTED_TYPES, _count(edge.target_type for edge in EDGES)),
        (EXPECTED_COST_KINDS, _count(edge.cost_kind for edge in EDGES)),
    ):
        if actual != expected:
            raise ValueError(f"building snapshot category drift: {actual} != {expected}")
    exclusions = {(edge.source, edge.target) for edge in EXCLUDED_EDGES}
    if exclusions != EXPECTED_EXCLUSIONS or any(
        edge.target_type != "great_building" or edge.reason != "great_project"
        for edge in EXCLUDED_EDGES
    ):
        raise ValueError("Great Project exclusion inventory drifted")
    if sum(edge.primary_building for edge in EDGES) != 13:
        raise ValueError("primary-building edge inventory drifted")
    if sum(bool(edge.gates) for edge in EDGES) != 601:
        raise ValueError("vanilla qualification-gate inventory drifted")
    temple_citadel_unique = sum(
        edge.target_file.endswith("/temple_citadel_buildings.txt")
        and not edge.primary_building
        for edge in EDGES
    )
    if temple_citadel_unique != 21:
        raise ValueError("temple-citadel unique edge inventory drifted")
    if set(PRIMARY_BUILDING_ROOTS) != {
        "castle_01",
        "city_01",
        "herder_camp_01",
        "nomadic_camp_01",
        "temple_01",
        "temple_citadel_01",
        "tribe_01",
    }:
        raise ValueError("primary-building root inventory drifted")


validate_data()
