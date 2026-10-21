"""Closed, machine-independent specifications for the 63 acceptance requirements.

The catalog contains inputs and assertions, never execution results.  A consumer
must bind real actors, source observations and supported routes independently.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Literal, TypedDict

from living_artifacts_model import AFFIX_IDS, CURSE_IDS

Domain = Literal["static", "prototype", "load", "growth", "feeding", "suppression", "ai", "lifecycle", "ui", "affix", "curse", "combo"]
Route = Literal["offline", "existing_mcp", "root_gui", "missing"]
NativeSlot = Literal["helmet", "regalia", "armor", "primary_armament", "brooch", "miscellaneous", "journal"]
ActionKind = Literal[
    "offline_check", "native_equip", "native_unequip", "calendar_advance", "native_battle", "native_duel",
    "native_feast", "native_sway", "native_build", "native_secret_discovery", "native_transfer",
    "native_scheme_discovery", "native_travel", "native_perk", "native_mental_break", "native_repair",
    "native_ai", "native_feed", "native_suppression", "native_soothe", "save_reload", "native_inheritance",
    "native_new_artifact", "native_destroy", "native_rename", "native_view", "normal_campaign",
    "compatibility_load", "multiplayer", "reobserve",
]
SAFE_INTEGER = 2**53 - 1
REQUIREMENT_IDS = tuple(
    f"LW-{prefix}{number:02}"
    for prefix, count in (("S", 6), ("P", 3), ("L", 1), ("G", 7), ("F", 5), ("T", 4),
                          ("I", 4), ("R", 6), ("U", 3), ("A", 12), ("C", 8), ("X", 4))
    for number in range(1, count + 1)
)


class ContentSlotJson(TypedDict):
    slot: int
    id: int
    rank: int


class ArtifactSeedJson(TypedDict):
    alias: str
    owner_alias: str
    slot: NativeSlot
    level: int
    xp: int
    resonance: int
    equipped: bool
    affixes: list[ContentSlotJson]
    curses: list[ContentSlotJson]


class ProductionActionJson(TypedDict):
    id: str
    kind: ActionKind
    route: Route
    description: str
    required_tools: list[str]


class IndependentAssertionJson(TypedDict):
    id: str
    metric: str
    expected_decimal: str | None
    description: str
    evidence_required: list[str]


class SourceRefJson(TypedDict):
    path: str
    sha256: str
    anchor: str


class RequirementJson(TypedDict):
    id: str
    domain: Domain
    cell_ids: list[str]


class AcceptanceCellJson(TypedDict):
    id: str
    requirement_ids: list[str]
    status: Literal["NOT_RUN"]
    artifact_seeds: list[ArtifactSeedJson]
    fixture_conditions: list[str]
    production_actions: list[ProductionActionJson]
    independent_assertions: list[IndependentAssertionJson]
    source_refs: list[SourceRefJson]


class AcceptanceCatalogJson(TypedDict):
    schema: Literal["living-artifacts-acceptance-catalog-v1"]
    schema_version: Literal[1]
    requirements: list[RequirementJson]
    cells: list[AcceptanceCellJson]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _object(value: object, keys: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label}: object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError(f"{label}: string keys required")
        result[key] = item
    _require(set(result) == keys, f"{label}: missing or unknown fields")
    return result


def _array(value: object, label: str) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{label}: JSON array required")
    return list(value)


def _text(value: object, label: str) -> str:
    if type(value) is not str or not value or "\0" in value:
        raise ValueError(f"{label}: nonempty string required")
    return value


def _integer(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label}: strict bounded integer required; bool/float rejected")
    return value


def _strings(value: object, label: str, *, nonempty: bool = True) -> tuple[str, ...]:
    values = tuple(_text(item, label) for item in _array(value, label))
    _require((not nonempty or bool(values)) and len(set(values)) == len(values), f"{label}: unique nonempty list required")
    return values


def _alias(value: object) -> str:
    result = _text(value, "alias")
    _require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", result) is not None,
             "Seed aliases are labels, never numeric native actor/artifact IDs")
    return result


def _domain(value: object) -> Domain:
    match value:
        case "static" | "prototype" | "load" | "growth" | "feeding" | "suppression" | "ai" | "lifecycle" | "ui" | "affix" | "curse" | "combo":
            return value
    raise ValueError("Unknown requirement domain")


def _route(value: object) -> Route:
    match value:
        case "offline" | "existing_mcp" | "root_gui" | "missing":
            return value
    raise ValueError("Unknown production route")


def _slot(value: object) -> NativeSlot:
    match value:
        case "helmet" | "regalia" | "armor" | "primary_armament" | "brooch" | "miscellaneous" | "journal":
            return value
    raise ValueError("Unknown native personal slot")


def _kind(value: object) -> ActionKind:
    match value:
        case ("offline_check" | "native_equip" | "native_unequip" | "calendar_advance" | "native_battle" | "native_duel"
              | "native_feast" | "native_sway" | "native_build" | "native_secret_discovery" | "native_transfer"
              | "native_scheme_discovery" | "native_travel" | "native_perk" | "native_mental_break" | "native_repair"
              | "native_ai" | "native_feed" | "native_suppression" | "native_soothe" | "save_reload" | "native_inheritance"
              | "native_new_artifact" | "native_destroy" | "native_rename" | "native_view" | "normal_campaign"
              | "compatibility_load" | "multiplayer" | "reobserve"):
            return value
    raise ValueError("Unknown production action kind")


@dataclass(frozen=True)
class ContentSlot:
    slot: int
    id: int
    rank: int

    @classmethod
    def parse(cls, value: object, kind: Literal["affix", "curse"]) -> ContentSlot:
        row = _object(value, {"slot", "id", "rank"}, "content slot")
        identifiers = AFFIX_IDS if kind == "affix" else CURSE_IDS
        identifier = _integer(row["id"], min(identifiers), max(identifiers), "enabled content ID")
        _require(identifier in identifiers, "Content ID is outside the enabled registry")
        return cls(_integer(row["slot"], 1, 6 if kind == "affix" else 2, "content slot"),
                   identifier,
                   _integer(row["rank"], 1, 3, "rank"))

    def to_json(self) -> ContentSlotJson:
        return {"slot": self.slot, "id": self.id, "rank": self.rank}


@dataclass(frozen=True)
class ArtifactSeed:
    alias: str
    owner_alias: str
    slot: NativeSlot
    level: int
    xp: int
    resonance: int
    equipped: bool
    affixes: tuple[ContentSlot, ...]
    curses: tuple[ContentSlot, ...]

    @classmethod
    def parse(cls, value: object) -> ArtifactSeed:
        row = _object(value, {"alias", "owner_alias", "slot", "level", "xp", "resonance", "equipped", "affixes", "curses"}, "artifact seed")
        if type(row["equipped"]) is not bool:
            raise ValueError("equipped: strict bool required")
        affixes = tuple(ContentSlot.parse(item, "affix") for item in _array(row["affixes"], "affixes"))
        curses = tuple(ContentSlot.parse(item, "curse") for item in _array(row["curses"], "curses"))
        for slots in (affixes, curses):
            _require(len({item.slot for item in slots}) == len(slots) and len({item.id for item in slots}) == len(slots),
                     "A seed cannot duplicate a content ID or slot")
        level = _integer(row["level"], 1, SAFE_INTEGER, "level")
        xp = _integer(row["xp"], 0, SAFE_INTEGER, "xp")
        _require(xp < 100 * level, "Seed XP must be a settled below-threshold input")
        alias, owner_alias = _alias(row["alias"]), _alias(row["owner_alias"])
        _require(alias != owner_alias, "Character and artifact aliases must differ")
        return cls(alias, owner_alias, _slot(row["slot"]), level, xp,
                   _integer(row["resonance"], 0, 100, "resonance"), row["equipped"], affixes, curses)

    def to_json(self) -> ArtifactSeedJson:
        return {"alias": self.alias, "owner_alias": self.owner_alias, "slot": self.slot, "level": self.level,
                "xp": self.xp, "resonance": self.resonance, "equipped": self.equipped,
                "affixes": [item.to_json() for item in self.affixes], "curses": [item.to_json() for item in self.curses]}


@dataclass(frozen=True)
class ProductionAction:
    id: str
    kind: ActionKind
    route: Route
    description: str
    required_tools: tuple[str, ...]

    @classmethod
    def parse(cls, value: object) -> ProductionAction:
        row = _object(value, {"id", "kind", "route", "description", "required_tools"}, "production action")
        route = _route(row["route"])
        kind = _kind(row["kind"])
        tools = _strings(row["required_tools"], "required_tools", nonempty=False)
        _require((route == "offline") == (kind == "offline_check"), "offline route/kind must be paired")
        _require(route != "existing_mcp" or bool(tools), "existing_mcp must name actual tools")
        return cls(_text(row["id"], "action ID"), kind, route, _text(row["description"], "action description"), tools)

    def to_json(self) -> ProductionActionJson:
        return {"id": self.id, "kind": self.kind, "route": self.route, "description": self.description,
                "required_tools": list(self.required_tools)}


@dataclass(frozen=True)
class IndependentAssertion:
    id: str
    metric: str
    expected_decimal: str | None
    description: str
    evidence_required: tuple[str, ...]

    @classmethod
    def parse(cls, value: object) -> IndependentAssertion:
        row = _object(value, {"id", "metric", "expected_decimal", "description", "evidence_required"}, "independent assertion")
        expected = row["expected_decimal"]
        if expected is not None:
            expected = _text(expected, "expected_decimal")
            _require(re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?", expected) is not None and expected != "-0",
                     "expected_decimal must be a canonical decimal string; no float/exponent/trailing zero")
        return cls(_text(row["id"], "assertion ID"), _text(row["metric"], "metric"), expected,
                   _text(row["description"], "assertion description"), _strings(row["evidence_required"], "evidence_required"))

    def to_json(self) -> IndependentAssertionJson:
        return {"id": self.id, "metric": self.metric, "expected_decimal": self.expected_decimal,
                "description": self.description, "evidence_required": list(self.evidence_required)}


@dataclass(frozen=True)
class SourceRef:
    path: str
    sha256: str
    anchor: str

    @classmethod
    def parse(cls, value: object) -> SourceRef:
        row = _object(value, {"path", "sha256", "anchor"}, "source ref")
        path, sha = _text(row["path"], "source path"), _text(row["sha256"], "source sha256")
        parts = PurePosixPath(path)
        _require(not parts.is_absolute() and "\\" not in path and ":" not in path and
                 all(part not in {"", ".", ".."} for part in path.split("/")) and parts.as_posix() == path,
                 "Source refs require canonical repository-relative POSIX paths")
        _require(re.fullmatch(r"[0-9a-f]{64}", sha) is not None, "Source SHA256 must be 64 lowercase hex")
        return cls(path, sha, _text(row["anchor"], "source anchor"))

    def to_json(self) -> SourceRefJson:
        return {"path": self.path, "sha256": self.sha256, "anchor": self.anchor}


@dataclass(frozen=True)
class Requirement:
    id: str
    domain: Domain
    cell_ids: tuple[str, ...]

    @classmethod
    def parse(cls, value: object) -> Requirement:
        row = _object(value, {"id", "domain", "cell_ids"}, "requirement")
        identifier = _text(row["id"], "requirement ID")
        _require(identifier in REQUIREMENT_IDS, "Requirement ID is outside the agreed 63-item version")
        domain = _domain(row["domain"])
        expected: dict[str, Domain] = {"S": "static", "P": "prototype", "L": "load", "G": "growth", "F": "feeding",
                                      "T": "suppression", "I": "ai", "R": "lifecycle", "U": "ui", "A": "affix", "C": "curse", "X": "combo"}
        _require(domain == expected[identifier[3]], "Requirement prefix/domain disagree")
        return cls(identifier, domain, _strings(row["cell_ids"], "requirement cells"))

    def to_json(self) -> RequirementJson:
        return {"id": self.id, "domain": self.domain, "cell_ids": list(self.cell_ids)}


@dataclass(frozen=True)
class AcceptanceCell:
    id: str
    requirement_ids: tuple[str, ...]
    status: Literal["NOT_RUN"]
    artifact_seeds: tuple[ArtifactSeed, ...]
    fixture_conditions: tuple[str, ...]
    production_actions: tuple[ProductionAction, ...]
    independent_assertions: tuple[IndependentAssertion, ...]
    source_refs: tuple[SourceRef, ...]

    @classmethod
    def parse(cls, value: object) -> AcceptanceCell:
        row = _object(value, {"id", "requirement_ids", "status", "artifact_seeds", "fixture_conditions",
                              "production_actions", "independent_assertions", "source_refs"}, "acceptance cell")
        _require(row["status"] == "NOT_RUN" and type(row["status"]) is str,
                 "The input catalog can only declare NOT_RUN; results belong in independent receipts")
        seeds = tuple(ArtifactSeed.parse(item) for item in _array(row["artifact_seeds"], "artifact seeds"))
        actions = tuple(ProductionAction.parse(item) for item in _array(row["production_actions"], "production actions"))
        assertions = tuple(IndependentAssertion.parse(item) for item in _array(row["independent_assertions"], "independent assertions"))
        sources = tuple(SourceRef.parse(item) for item in _array(row["source_refs"], "source refs"))
        _require(bool(actions) and bool(assertions) and bool(sources), "Each cell needs actions, independent assertions and source refs")
        for identifiers in (tuple(item.alias for item in seeds), tuple(item.id for item in actions), tuple(item.id for item in assertions)):
            _require(len(set(identifiers)) == len(identifiers), "Duplicate cell-local artifact/action/assertion ID")
        return cls(_text(row["id"], "cell ID"), _strings(row["requirement_ids"], "cell requirements"), "NOT_RUN", seeds,
                   _strings(row["fixture_conditions"], "fixture conditions"), actions, assertions, sources)

    def to_json(self) -> AcceptanceCellJson:
        return {"id": self.id, "requirement_ids": list(self.requirement_ids), "status": self.status,
                "artifact_seeds": [item.to_json() for item in self.artifact_seeds], "fixture_conditions": list(self.fixture_conditions),
                "production_actions": [item.to_json() for item in self.production_actions],
                "independent_assertions": [item.to_json() for item in self.independent_assertions],
                "source_refs": [item.to_json() for item in self.source_refs]}


@dataclass(frozen=True)
class AcceptanceCatalog:
    requirements: tuple[Requirement, ...]
    cells: tuple[AcceptanceCell, ...]

    @classmethod
    def parse(cls, value: object) -> AcceptanceCatalog:
        row = _object(value, {"schema", "schema_version", "requirements", "cells"}, "acceptance catalog")
        _require(row["schema"] == "living-artifacts-acceptance-catalog-v1", "Unknown catalog schema")
        _integer(row["schema_version"], 1, 1, "schema_version")
        requirements = tuple(Requirement.parse(item) for item in _array(row["requirements"], "requirements"))
        cells = tuple(AcceptanceCell.parse(item) for item in _array(row["cells"], "cells"))
        _require(len(requirements) == 63 and len({item.id for item in requirements}) == 63 and
                 {item.id for item in requirements} == set(REQUIREMENT_IDS), "Exactly the 63 agreed requirements are required")
        by_cell = {item.id: item for item in cells}
        _require(bool(cells) and len(by_cell) == len(cells), "Unique nonempty cell list required")
        by_requirement = {item.id: item for item in requirements}
        for requirement in requirements:
            for identifier in requirement.cell_ids:
                _require(identifier in by_cell and requirement.id in by_cell[identifier].requirement_ids,
                         "Requirement/cell references must be reciprocal")
        for cell in cells:
            for identifier in cell.requirement_ids:
                _require(identifier in by_requirement and cell.id in by_requirement[identifier].cell_ids,
                         "Cell/requirement references must be reciprocal")
        return cls(requirements, cells)

    def to_json(self) -> AcceptanceCatalogJson:
        return {"schema": "living-artifacts-acceptance-catalog-v1", "schema_version": 1,
                "requirements": [item.to_json() for item in self.requirements], "cells": [item.to_json() for item in self.cells]}


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        _require(key not in result, f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def read_catalog(path: Path) -> AcceptanceCatalog:
    value: object = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_unique)
    return AcceptanceCatalog.parse(value)


def verify_catalog_sources(catalog: AcceptanceCatalog, repository: Path) -> None:
    """Reject drift before execution without interpreting any descriptive text."""
    root = repository.resolve()
    observed: dict[str, tuple[str, str]] = {}
    for cell in catalog.cells:
        for source in cell.source_refs:
            if source.path not in observed:
                path = (root / source.path).resolve()
                _require(path.is_relative_to(root) and path.is_file(), "Catalog source escaped or is missing")
                raw = path.read_bytes()
                observed[source.path] = hashlib.sha256(raw).hexdigest(), raw.decode("utf-8-sig")
            sha, text = observed[source.path]
            _require(sha == source.sha256 and source.anchor in text, f"Catalog source changed: {source.path}")
