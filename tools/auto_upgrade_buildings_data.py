"""Reviewed CK3 1.21.0 building graph for Auto Upgrade Buildings."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable

from extract_auto_upgrade_buildings import BlockScriptValue, ScalarScriptValue


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "tools" / "auto_upgrade_buildings_1_21_0.json"
EXPECTED_GAME_VERSION = "1.21.0"
# Independently reviewed contracts; extracting/generating never refreshes these.
# Policy hashes every edge field except vanilla gates, the primary roots and
# Great Project exclusions, including scalar/block district level requirements.
EXPECTED_POLICY_SHA256 = "9e0a7edf046155a3223c22f6058126476c6835fcd75c8dc71cc0bbb88c13292f"
EXPECTED_GATES_SHA256 = "7dfba98380212dfe16dea4441b2860863485ac10af9be6308e797e0bafa53084"
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
EXPECTED_TYPES = {"regular": 2583}
EXPECTED_COST_KINDS = {
    "cost_gold": 2382,
    "cost_gold+cost_prestige": 108,
    "cost_gold+cost_piety": 3,
    "scripted_cost": 90,
}
EXPECTED_EXCLUDED_CHAIN_ROOTS = {
    "great_project_cathedral_01", "mandala_capital_01", "patron_saint_sanctuary_1",
    "pb_republic_city_hall_01", "republic_basilica_01", "republic_civic_hospital_01",
    "republic_civic_ward_01", "republic_clock_tower_01", "republic_council_chamber_01",
    "republic_debt_office_01", "republic_fountain_01", "republic_league_chapter_house_01",
    "republic_loggia_01", "republic_podesta_residence_01", "republic_statute_hall_01",
    "republic_weigh_house_01",
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
    district_level_requirement: ScalarScriptValue | BlockScriptValue | None

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


def _semantic_sha256(value: object) -> str:
    data = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(f"{label} keys must be strings")
        result[key] = item
    return result


def _objects(value: object, label: str) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return [_object(item, label) for item in value]


def _string(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    return value


def _strings(value: object, label: str) -> dict[str, str]:
    return {key: _string(item, f"{label}.{key}") for key, item in _object(value, label).items()}


def _boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean")
    return value


def _requirement(value: object) -> ScalarScriptValue | BlockScriptValue | None:
    if value is None:
        return None
    item = _object(value, "district_level_requirement")
    if item.get("kind") == "scalar" and set(item) == {"kind", "value"}:
        return ScalarScriptValue(kind="scalar", value=_string(item["value"], "requirement.value"))
    if item.get("kind") == "block" and set(item) == {"kind", "body"}:
        return BlockScriptValue(kind="block", body=_string(item["body"], "requirement.body"))
    raise ValueError("invalid district_level_requirement")


def validate_snapshot_contract(payload: dict[str, object]) -> None:
    edges = _objects(payload["included_edges"], "included_edges")
    policy = {
        "primary_building_roots": payload["primary_building_roots"],
        "excluded_edges": payload["excluded_edges"],
        "included_edges": [
            {key: value for key, value in edge.items() if key != "gates"}
            for edge in edges
        ],
    }
    gates = [
        {key: edge[key] for key in ("source", "target", "gates")}
        for edge in edges
    ]
    if _semantic_sha256(policy) != EXPECTED_POLICY_SHA256:
        raise ValueError("reviewed building upgrade policy contract drifted")
    if _semantic_sha256(gates) != EXPECTED_GATES_SHA256:
        raise ValueError("reviewed CK3 1.21.0 building gate contract drifted")


def _load() -> tuple[dict[str, object], tuple[BuildingEdge, ...], tuple[ExcludedEdge, ...]]:
    try:
        raw: object = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        payload = _object(raw, "snapshot")
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot load frozen building snapshot: {error}") from error
    edges = tuple(
        BuildingEdge(
            source=_string(item["source"], "source"),
            target=_string(item["target"], "target"),
            chain_root=_string(item["chain_root"], "chain_root"),
            source_file=_string(item["source_file"], "source_file"),
            target_file=_string(item["target_file"], "target_file"),
            target_type=_string(item["target_type"], "target_type"),
            cost_kind=_string(item["cost_kind"], "cost_kind"),
            resources=tuple(_strings(item["resources"], "resources").items()),
            gates=tuple(_strings(item["gates"], "gates").items()),
            primary_building=_boolean(item["primary_building"], "primary_building"),
            primary_holding_type=None if item["primary_holding_type"] is None else _string(item["primary_holding_type"], "primary_holding_type"),
            district_level_requirement=_requirement(item["district_level_requirement"]),
        )
        for item in _objects(payload["included_edges"], "included_edges")
    )
    excluded = tuple(
        ExcludedEdge(
            source=_string(item["source"], "source"),
            target=_string(item["target"], "target"),
            chain_root=_string(item["chain_root"], "chain_root"),
            source_file=_string(item["source_file"], "source_file"),
            target_file=_string(item["target_file"], "target_file"),
            target_type=_string(item["target_type"], "target_type"),
            reason=_string(item["reason"], "reason"),
        )
        for item in _objects(payload["excluded_edges"], "excluded_edges")
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
INPUT_SHA256 = _strings(SNAPSHOT_DATA["input_sha256"], "input_sha256")
PRIMARY_BUILDING_ROOTS = _strings(SNAPSHOT_DATA["primary_building_roots"], "primary_building_roots")


def validate_data() -> None:
    if type(SNAPSHOT_DATA.get("schema_version")) is not int or SNAPSHOT_DATA["schema_version"] != 2:
        raise ValueError("unsupported building snapshot schema")
    if SNAPSHOT_DATA.get("game_version") != EXPECTED_GAME_VERSION:
        raise ValueError("building snapshot game version drifted")
    expected_counts = {
        "building_definition_count": 3548,
        "vanilla_edge_count": 2644,
        "included_edge_count": 2583,
        "excluded_edge_count": 61,
        "chain_count": 677,
    }
    for key, expected in expected_counts.items():
        if type(SNAPSHOT_DATA.get(key)) is not int or SNAPSHOT_DATA[key] != expected:
            raise ValueError(f"building snapshot {key} drifted from {expected}")
    if len(EDGES) != 2583 or len(CHAINS) != 677 or len(EXCLUDED_EDGES) != 61:
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
    for expected_distribution, actual in (
        (EXPECTED_TYPES, _count(edge.target_type for edge in EDGES)),
        (EXPECTED_COST_KINDS, _count(edge.cost_kind for edge in EDGES)),
    ):
        if actual != expected_distribution:
            raise ValueError(f"building snapshot category drift: {actual} != {expected_distribution}")
    exclusions = {edge.chain_root for edge in EXCLUDED_EDGES}
    if exclusions != EXPECTED_EXCLUDED_CHAIN_ROOTS or any(
        edge.target_type != "great_building" or edge.reason != "great_project"
        for edge in EXCLUDED_EDGES
    ):
        raise ValueError("Great Project exclusion inventory drifted")
    if sum(edge.primary_building for edge in EDGES) != 13:
        raise ValueError("primary-building edge inventory drifted")
    if sum(bool(edge.gates) for edge in EDGES) != 2571:
        raise ValueError("vanilla qualification-gate inventory drifted")
    temple_citadel_unique = sum(
        edge.target_file.endswith("/temple_citadel_buildings.txt")
        and not edge.primary_building
        for edge in EDGES
    )
    if temple_citadel_unique != 0:
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
    validate_snapshot_contract(SNAPSHOT_DATA)


validate_data()
