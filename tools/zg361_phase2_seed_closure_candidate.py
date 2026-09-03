#!/usr/bin/env python3
"""Build the exact callback-closed Phase-2 seed-entry product projection.

This builder never launches CK3.  It replays the immutable Incident-X r3
projection, discovers the production definitions required by the checked-in
seed fixture, and overlays only complete canonical purpose shards.  Court
position lifecycle callbacks are part of the dependency graph; omitting them
would produce a parser-clean but behaviorally incomplete Workforce closure.

Candidate hashes use an explicit two-stage contract.  ``--print-candidate-contract``
may be used while the contract contains no frozen overlay rows/fingerprints.
It prints the observed values but never edits the contract.  A normal build
requires those values to have been reviewed and copied into the contract.
"""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
from typing import Any, Iterable, Mapping, Sequence

import zg361_phase2_b2_closure_candidate as closure_utils
from zg361_phase2_product_projection import (
    ProductProjectionError,
    load_projection,
    materialize_projection,
    write_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
MOD_ROOT = ROOT / "mod_zhongguo_style"
CONTRACT_PATH = Path(__file__).with_name(
    "zg361_phase2_seed_production_closure.json"
)
BOM = b"\xef\xbb\xbf"
CALLABLE_DIRS = (
    Path("common/scripted_effects"),
    Path("common/scripted_triggers"),
    Path("common/script_values"),
)
EFFECT_DIRS = (Path("common/scripted_effects"),)
EVENT_DIRS = (Path("events"),)
COURT_POSITION_DIRS = (Path("common/court_positions/types"),)
SCRIPT_SUFFIXES = frozenset({".txt", ".gui", ".yml"})
COURT_POSITION_REF_RE = re.compile(
    r"\b(zg361_[A-Za-z0-9_]*_court_position)\b"
)
LOC_ASSIGN_RE = re.compile(
    r"\b(?:title|desc|name)\s*=\s*"
    r"((?:zg361[a-z0-9_]*|zg361)\.[A-Za-z0-9_.-]+)\b"
)


class SeedClosureError(ValueError):
    """The seed-entry product closure is incomplete or unreproducible."""


@dataclass(frozen=True)
class ProviderGraph:
    effects: Mapping[str, closure_utils.ScriptBlock]
    events: Mapping[str, closure_utils.ScriptBlock]
    triggers: Mapping[str, closure_utils.ScriptBlock]
    values: Mapping[str, closure_utils.ScriptBlock]
    court_positions: Mapping[str, closure_utils.ScriptBlock]


@dataclass(frozen=True)
class DependencyClosure:
    effects: frozenset[str]
    events: frozenset[str]
    triggers: frozenset[str]
    values: frozenset[str]
    court_positions: frozenset[str]
    missing_effects: frozenset[str]
    missing_events: frozenset[str]
    missing_triggers: frozenset[str]
    missing_values: frozenset[str]
    missing_court_positions: frozenset[str]

    @property
    def unresolved(self) -> bool:
        return any(
            (
                self.missing_effects,
                self.missing_events,
                self.missing_triggers,
                self.missing_values,
                self.missing_court_positions,
            )
        )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise SeedClosureError(f"{label} must be an object")
    return value


def _strings(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise SeedClosureError(f"{label} must be a list of non-empty strings")
    return tuple(value)


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise SeedClosureError(f"{label} must be a non-empty string")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SeedClosureError(f"{label} must be a non-negative integer")
    return value


def _digest(value: object, label: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-fA-F]{64}", value) is None:
        raise SeedClosureError(f"{label} must be a 64-character SHA-256")
    return value.lower()


def _relative(value: object, label: str) -> str:
    raw = _string(value, label).replace("\\", "/")
    path = PurePosixPath(raw)
    if path.is_absolute() or raw.startswith("//") or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise SeedClosureError(f"{label} must be a normalized relative path")
    return path.as_posix()


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SeedClosureError(f"cannot read seed closure contract {path}: {error}") from error
    if not isinstance(payload, dict):
        raise SeedClosureError("seed closure contract root must be an object")
    if payload.get("schema_version") != 1:
        raise SeedClosureError("seed closure contract schema_version must be 1")
    if payload.get("kind") != "zg361_phase2_seed_entry_production_closure":
        raise SeedClosureError("unexpected seed closure contract kind")
    return payload


def _provider_map(
    root: Path, directories: Sequence[Path]
) -> tuple[dict[str, closure_utils.ScriptBlock], list[str]]:
    try:
        return closure_utils._provider_map(root, directories)
    except closure_utils.B2ClosureError as error:
        raise SeedClosureError(str(error)) from error


def provider_graph(root: Path) -> tuple[ProviderGraph, dict[str, list[str]]]:
    effects, effect_duplicates = _provider_map(root, EFFECT_DIRS)
    events, event_duplicates = _provider_map(root, EVENT_DIRS)
    triggers, trigger_duplicates = _provider_map(
        root, (Path("common/scripted_triggers"),)
    )
    values, value_duplicates = _provider_map(root, (Path("common/script_values"),))
    court_positions, court_position_duplicates = _provider_map(
        root, COURT_POSITION_DIRS
    )
    duplicates = {
        "effects": effect_duplicates,
        "events": event_duplicates,
        "triggers": trigger_duplicates,
        "values": value_duplicates,
        "court_positions": court_position_duplicates,
    }
    if any(duplicates.values()):
        raise SeedClosureError(f"duplicate providers: {duplicates}")
    return (
        ProviderGraph(effects, events, triggers, values, court_positions),
        duplicates,
    )


def _block_references(
    block: closure_utils.ScriptBlock,
) -> tuple[set[str], set[str], set[str], set[str], set[str]]:
    effects, events, callables = closure_utils.block_references(block)
    text = closure_utils._mask_comments_and_strings(
        block.data.decode("utf-8-sig")
    )
    court_positions = set(COURT_POSITION_REF_RE.findall(text))
    court_positions.discard(block.name)
    triggers = {name for name in callables if name.endswith("_trigger")}
    values = {name for name in callables if name.endswith("_value")}
    return effects, events, triggers, values, court_positions


def dependency_fixed_point(
    graph: ProviderGraph, roots: Iterable[str]
) -> DependencyClosure:
    effects: set[str] = set()
    events: set[str] = set()
    triggers: set[str] = set()
    values: set[str] = set()
    court_positions: set[str] = set()
    missing_effects: set[str] = set()
    missing_events: set[str] = set()
    missing_triggers: set[str] = set()
    missing_values: set[str] = set()
    missing_court_positions: set[str] = set()
    queue: deque[tuple[str, str]] = deque(("effect", root) for root in roots)
    while queue:
        kind, name = queue.popleft()
        if kind == "effect":
            if name in effects:
                continue
            block = graph.effects.get(name)
            if block is None:
                missing_effects.add(name)
                continue
            effects.add(name)
        elif kind == "event":
            if name in events:
                continue
            block = graph.events.get(name)
            if block is None:
                missing_events.add(name)
                continue
            events.add(name)
        elif kind == "trigger":
            if name in triggers:
                continue
            block = graph.triggers.get(name)
            if block is None:
                missing_triggers.add(name)
                continue
            triggers.add(name)
        elif kind == "value":
            if name in values:
                continue
            block = graph.values.get(name)
            if block is None:
                missing_values.add(name)
                continue
            values.add(name)
        elif kind == "court_position":
            if name in court_positions:
                continue
            block = graph.court_positions.get(name)
            if block is None:
                missing_court_positions.add(name)
                continue
            court_positions.add(name)
        else:
            raise SeedClosureError(f"unknown dependency kind: {kind}")
        effect_refs, event_refs, trigger_refs, value_refs, position_refs = (
            _block_references(block)
        )
        queue.extend(("effect", item) for item in sorted(effect_refs))
        queue.extend(("event", item) for item in sorted(event_refs))
        queue.extend(("trigger", item) for item in sorted(trigger_refs))
        queue.extend(("value", item) for item in sorted(value_refs))
        queue.extend(("court_position", item) for item in sorted(position_refs))
    return DependencyClosure(
        frozenset(effects),
        frozenset(events),
        frozenset(triggers),
        frozenset(values),
        frozenset(court_positions),
        frozenset(missing_effects),
        frozenset(missing_events),
        frozenset(missing_triggers),
        frozenset(missing_values),
        frozenset(missing_court_positions),
    )


def _closure_counts(closure: DependencyClosure) -> dict[str, int]:
    return {
        "effects": len(closure.effects),
        "events": len(closure.events),
        "triggers": len(closure.triggers),
        "values": len(closure.values),
        "court_positions": len(closure.court_positions),
    }


def _assert_counts(
    observed: Mapping[str, int], expected: Mapping[str, Any], label: str
) -> None:
    differences = {
        key: {"expected": _integer(expected.get(key), f"{label}.{key}"), "observed": value}
        for key, value in observed.items()
        if value != _integer(expected.get(key), f"{label}.{key}")
    }
    if differences:
        raise SeedClosureError(f"{label} counts drifted: {differences}")


def validate_fixture(contract: Mapping[str, Any]) -> dict[str, object]:
    fixture = _mapping(contract.get("fixture"), "fixture")
    relative = _relative(fixture.get("event_file"), "fixture.event_file")
    path = ROOT / PurePosixPath(relative)
    if not path.is_file() or path.is_symlink():
        raise SeedClosureError(f"seed fixture event file is missing: {path}")
    data = path.read_bytes()
    expected_bytes = _integer(fixture.get("bytes"), "fixture.bytes")
    expected_sha = _digest(fixture.get("sha256"), "fixture.sha256")
    if len(data) != expected_bytes or sha256_bytes(data) != expected_sha:
        raise SeedClosureError(
            "seed fixture identity drifted: "
            f"bytes={len(data)}/{expected_bytes}, sha256={sha256_bytes(data)}/{expected_sha}"
        )
    text = closure_utils._mask_comments_and_strings(data.decode("utf-8-sig"))
    observed_roots = tuple(closure_utils.EFFECT_CALL_RE.findall(text))
    expected_roots = _strings(
        fixture.get("ordered_root_effects"), "fixture.ordered_root_effects"
    )
    if observed_roots != expected_roots:
        raise SeedClosureError(
            "seed fixture root order drifted: "
            f"observed={list(observed_roots)}, expected={list(expected_roots)}"
        )
    if len(set(observed_roots)) != len(observed_roots):
        raise SeedClosureError("seed fixture repeats a product root")
    return {
        "status": "GREEN",
        "path": relative,
        "bytes": len(data),
        "sha256": sha256_bytes(data),
        "ordered_root_effects": list(observed_roots),
    }


def verify_baseline_identity(
    contract: Mapping[str, Any], baseline_root: Path
) -> tuple[Path, Path, str, dict[str, object]]:
    baseline = _mapping(contract.get("baseline"), "baseline")
    source = baseline_root / _relative(baseline.get("source"), "baseline.source")
    product = baseline_root / _relative(baseline.get("product"), "baseline.product")
    replay = baseline_root / _relative(
        baseline.get("materialized_check"), "baseline.materialized_check"
    )
    manifest = baseline_root / _relative(
        baseline.get("manifest"), "baseline.manifest"
    )
    projection = _string(baseline.get("projection"), "baseline.projection")
    for label, path in (("source", source), ("product", product), ("replay", replay)):
        if not path.is_dir():
            raise SeedClosureError(f"baseline {label} tree is missing: {path}")
    if not manifest.is_file() or manifest.is_symlink():
        raise SeedClosureError(f"baseline manifest is missing or symlinked: {manifest}")
    expected_manifest_sha = _digest(
        baseline.get("manifest_sha256"), "baseline.manifest_sha256"
    )
    if sha256_file(manifest) != expected_manifest_sha:
        raise SeedClosureError("baseline projection manifest SHA-256 drifted")
    for field, filename in (
        ("preflight_sha256", "preflight.json"),
        ("closure_contract_sha256", "closure-contract.json"),
    ):
        expected = _digest(baseline.get(field), f"baseline.{field}")
        path = baseline_root / filename
        if not path.is_file() or sha256_file(path) != expected:
            raise SeedClosureError(f"baseline {filename} identity drifted")
    source_rows = closure_utils.tree_rows(source)
    product_rows = closure_utils.tree_rows(product)
    replay_rows = closure_utils.tree_rows(replay)
    if source_rows != product_rows or source_rows != replay_rows:
        raise SeedClosureError("baseline source/product/replay rows are not identical")
    expected_files = _integer(baseline.get("file_count"), "baseline.file_count")
    expected_bytes = _integer(baseline.get("bytes"), "baseline.bytes")
    observed_bytes = sum(int(row["bytes"]) for row in source_rows)
    if len(source_rows) != expected_files or observed_bytes != expected_bytes:
        raise SeedClosureError(
            "baseline size drifted: "
            f"files={len(source_rows)}/{expected_files}, bytes={observed_bytes}/{expected_bytes}"
        )
    try:
        spec = load_projection(
            source, projection_name=projection, manifest_path=manifest
        )
    except ProductProjectionError as error:
        raise SeedClosureError(str(error)) from error
    expected_identity = {
        "source_tree_sha256": _digest(
            baseline.get("source_tree_sha256"), "baseline.source_tree_sha256"
        ),
        "formal_overlay_tree_sha256": _digest(
            baseline.get("formal_overlay_tree_sha256"),
            "baseline.formal_overlay_tree_sha256",
        ),
        "file_list_sha256": _digest(
            baseline.get("file_list_sha256"), "baseline.file_list_sha256"
        ),
    }
    observed_identity = {
        "source_tree_sha256": spec.source_tree_sha256,
        "formal_overlay_tree_sha256": spec.formal_overlay_tree_sha256,
        "file_list_sha256": spec.file_list_sha256,
    }
    if observed_identity != expected_identity:
        raise SeedClosureError(
            f"baseline projection identity drifted: {observed_identity} != {expected_identity}"
        )
    return source, manifest, projection, {
        "status": "GREEN",
        "file_count": len(source_rows),
        "bytes": observed_bytes,
        "manifest_sha256": expected_manifest_sha,
        **expected_identity,
        "source_equals_product": True,
        "source_equals_replay": True,
    }


def _owner_rows(
    canonical_source: Path,
    providers: Mapping[str, closure_utils.ScriptBlock],
    selected: Iterable[str],
    *,
    kind: str,
) -> list[dict[str, object]]:
    selected_names = set(selected)
    by_path: dict[str, set[str]] = {}
    for name in selected_names:
        block = providers.get(name)
        if block is None:
            raise SeedClosureError(f"selected {kind} provider is missing: {name}")
        by_path.setdefault(block.path, set()).add(name)
    rows: list[dict[str, object]] = []
    mixed: list[dict[str, object]] = []
    for relative, names in sorted(by_path.items()):
        path = canonical_source / PurePosixPath(relative)
        data, blocks = closure_utils._blocks(path, relative)
        owner_names = tuple(block.name for block in blocks)
        if set(owner_names) != names:
            mixed.append(
                {
                    "path": relative,
                    "selected": sorted(names),
                    "extra": sorted(set(owner_names) - names),
                }
            )
            continue
        rows.append(
            {
                "path": relative,
                "kind": kind,
                "definitions": len(owner_names),
                "definition_names": list(owner_names),
                "bytes": len(data),
                "sha256": sha256_bytes(data),
            }
        )
    if mixed:
        raise SeedClosureError(
            "selected closure still shares canonical owner files; split by purpose first: "
            + json.dumps(mixed, ensure_ascii=False, sort_keys=True)
        )
    return rows


def _localization_provider_map(root: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    providers: dict[str, str] = {}
    duplicates: dict[str, list[str]] = {}
    loc_root = root / "localization" / "simp_chinese"
    if not loc_root.is_dir():
        return providers, duplicates
    owners: dict[str, list[str]] = {}
    for path in sorted(loc_root.glob("*.yml")):
        relative = path.relative_to(root).as_posix()
        for key in closure_utils.LOC_DEF_RE.findall(
            path.read_text(encoding="utf-8-sig")
        ):
            owners.setdefault(key, []).append(relative)
    for key, paths in owners.items():
        if len(paths) == 1:
            providers[key] = paths[0]
        else:
            duplicates[key] = sorted(paths)
    return providers, duplicates


def localization_requirements(
    canonical_source: Path,
    baseline_source: Path,
    canonical_graph: ProviderGraph,
    delta_events: Iterable[str],
    delta_court_positions: Iterable[str],
) -> tuple[set[str], list[dict[str, object]]]:
    explicit: set[str] = set()
    for event in delta_events:
        block = canonical_graph.events[event]
        text = closure_utils._mask_comments_and_strings(
            block.data.decode("utf-8-sig")
        )
        explicit.update(LOC_ASSIGN_RE.findall(text))
    conventional: set[str] = set()
    for name in delta_court_positions:
        conventional.update((name, f"{name}_desc"))
    required = explicit | conventional
    canonical_loc, canonical_duplicates = _localization_provider_map(canonical_source)
    baseline_loc, baseline_duplicates = _localization_provider_map(baseline_source)
    relevant_duplicates = {
        key: paths
        for key, paths in {**canonical_duplicates, **baseline_duplicates}.items()
        if key in required
    }
    if relevant_duplicates:
        raise SeedClosureError(
            f"required Simplified Chinese localization has duplicate owners: {relevant_duplicates}"
        )
    missing_canonical = sorted(required - set(canonical_loc))
    if missing_canonical:
        raise SeedClosureError(
            f"canonical Simplified Chinese localization is missing: {missing_canonical}"
        )
    delta_keys = required - set(baseline_loc)
    paths = sorted({canonical_loc[key] for key in delta_keys})
    rows: list[dict[str, object]] = []
    emitted_keys: set[str] = set()
    for relative in paths:
        path = canonical_source / PurePosixPath(relative)
        data = path.read_bytes()
        names = tuple(
            closure_utils.LOC_DEF_RE.findall(data.decode("utf-8-sig"))
        )
        emitted_keys.update(names)
        rows.append(
            {
                "path": relative,
                "kind": "localization",
                "definitions": len(names),
                "definition_names": list(names),
                "bytes": len(data),
                "sha256": sha256_bytes(data),
            }
        )
    if emitted_keys != delta_keys:
        raise SeedClosureError(
            "selected localization owner files are not the exact missing key set: "
            f"extra={sorted(emitted_keys - delta_keys)}, missing={sorted(delta_keys - emitted_keys)}"
        )
    return delta_keys, rows


def select_overlay(
    canonical_source: Path,
    baseline_source: Path,
    contract: Mapping[str, Any],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    canonical_graph, _ = provider_graph(canonical_source)
    baseline_graph, _ = provider_graph(baseline_source)
    expansion = _mapping(contract.get("expansion"), "expansion")
    root = _string(expansion.get("root_effect"), "expansion.root_effect")
    closure = dependency_fixed_point(canonical_graph, (root,))
    if closure.unresolved:
        raise SeedClosureError(f"canonical Workforce closure is unresolved: {closure}")
    _assert_counts(
        _closure_counts(closure),
        _mapping(expansion.get("expected_full"), "expansion.expected_full"),
        "expansion.expected_full",
    )
    expected_triggers = set(
        _strings(expansion.get("reachable_triggers"), "expansion.reachable_triggers")
    )
    if set(closure.triggers) != expected_triggers:
        raise SeedClosureError(
            "Workforce trigger closure drifted: "
            f"missing={sorted(expected_triggers - set(closure.triggers))}, "
            f"extra={sorted(set(closure.triggers) - expected_triggers)}"
        )
    delta_effects = set(closure.effects) - set(baseline_graph.effects)
    delta_events = set(closure.events) - set(baseline_graph.events)
    delta_positions = set(closure.court_positions) - set(
        baseline_graph.court_positions
    )
    delta_triggers = set(closure.triggers) - set(baseline_graph.triggers)
    delta_values = set(closure.values) - set(baseline_graph.values)
    delta_counts = {
        "effects": len(delta_effects),
        "events": len(delta_events),
        "triggers": len(delta_triggers),
        "values": len(delta_values),
        "court_positions": len(delta_positions),
    }
    _assert_counts(
        delta_counts,
        _mapping(expansion.get("expected_delta"), "expansion.expected_delta"),
        "expansion.expected_delta",
    )
    manager_effects = sorted(
        name for name in closure.effects if name.startswith("zg361_mg_")
    )
    manager_events = sorted(
        name for name in closure.events if name.startswith("zg361mg.")
    )
    manager_triggers = sorted(
        name for name in closure.triggers if name.startswith("zg361_mg_")
    )
    workforce_m360_effects = sorted(
        name
        for name in closure.effects
        if name.startswith("zg361_we_") and "_m360_" in name
    )
    workforce_m360_event_ids = {"zg361we.360", "zg361we.4804", "zg361we.4904", "zg361we.6360"}
    workforce_m360_events = sorted(set(closure.events) & workforce_m360_event_ids)
    if any(
        (
            manager_effects,
            manager_events,
            manager_triggers,
            workforce_m360_effects,
            workforce_m360_events,
        )
    ):
        raise SeedClosureError(
            "Manager/Workforce-M360 leaked into the seed closure: "
            f"manager_effects={manager_effects}, manager_events={manager_events}, "
            f"manager_triggers={manager_triggers}, "
            f"m360_effects={workforce_m360_effects}, "
            f"m360_events={workforce_m360_events}"
        )
    rows = [
        *_owner_rows(
            canonical_source,
            canonical_graph.effects,
            delta_effects,
            kind="effect",
        ),
        *_owner_rows(
            canonical_source,
            canonical_graph.events,
            delta_events,
            kind="event",
        ),
        *_owner_rows(
            canonical_source,
            canonical_graph.court_positions,
            delta_positions,
            kind="court_position",
        ),
    ]
    delta_loc_keys, loc_rows = localization_requirements(
        canonical_source,
        baseline_source,
        canonical_graph,
        delta_events,
        delta_positions,
    )
    rows.extend(loc_rows)
    rows.sort(key=lambda row: str(row["path"]))
    candidate = _mapping(contract.get("candidate"), "candidate")
    counts_by_kind = {
        kind: sum(1 for row in rows if row["kind"] == kind)
        for kind in ("effect", "event", "court_position", "localization")
    }
    expected_by_kind = {
        "effect": _integer(candidate.get("expected_effect_files"), "candidate.expected_effect_files"),
        "event": _integer(candidate.get("expected_event_files"), "candidate.expected_event_files"),
        "court_position": _integer(candidate.get("expected_court_position_files"), "candidate.expected_court_position_files"),
        "localization": _integer(candidate.get("expected_localization_files"), "candidate.expected_localization_files"),
    }
    if counts_by_kind != expected_by_kind:
        raise SeedClosureError(
            f"overlay file-kind counts drifted: {counts_by_kind} != {expected_by_kind}"
        )
    expected_overlay_count = _integer(
        candidate.get("expected_overlay_file_count"),
        "candidate.expected_overlay_file_count",
    )
    if len(rows) != expected_overlay_count:
        raise SeedClosureError(
            f"overlay file count drifted: {len(rows)} != {expected_overlay_count}"
        )
    expected_loc_keys = _integer(
        candidate.get("expected_new_localization_keys"),
        "candidate.expected_new_localization_keys",
    )
    if len(delta_loc_keys) != expected_loc_keys:
        raise SeedClosureError(
            f"new localization key count drifted: {len(delta_loc_keys)} != {expected_loc_keys}"
        )
    return rows, {
        "status": "GREEN",
        "root": root,
        "full": _closure_counts(closure),
        "delta": delta_counts,
        "delta_localization_keys": sorted(delta_loc_keys),
        "manager_effects": manager_effects,
        "manager_events": manager_events,
        "manager_triggers": manager_triggers,
        "workforce_m360_effects": workforce_m360_effects,
        "workforce_m360_events": workforce_m360_events,
        "effect_names": sorted(delta_effects),
        "event_ids": sorted(delta_events),
        "court_position_names": sorted(delta_positions),
        "reachable_triggers": sorted(closure.triggers),
    }


def _contract_overlay_rows(contract: Mapping[str, Any]) -> list[dict[str, object]]:
    overlay = _mapping(contract.get("overlay"), "overlay")
    value = overlay.get("files")
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise SeedClosureError("overlay.files must be a list of objects")
    return [dict(row) for row in value]


def overlay_inventory_sha256(rows: Sequence[Mapping[str, object]]) -> str:
    """Hash the reviewed overlay inventory independently of JSON whitespace."""
    payload = json.dumps(
        [dict(row) for row in rows],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(payload)


def validate_overlay_contract(
    observed: Sequence[Mapping[str, object]],
    contract: Mapping[str, Any],
    *,
    allow_unfrozen: bool,
) -> dict[str, object]:
    frozen = _contract_overlay_rows(contract)
    overlay = _mapping(contract.get("overlay"), "overlay")
    expected_inventory_sha = _digest(
        overlay.get("inventory_sha256"),
        "overlay.inventory_sha256",
        optional=True,
    )
    expected_bytes_raw = overlay.get("bytes")
    expected_bytes = (
        None
        if expected_bytes_raw is None
        else _integer(expected_bytes_raw, "overlay.bytes")
    )
    normalized = [dict(row) for row in observed]
    observed_inventory_sha = overlay_inventory_sha256(normalized)
    observed_bytes = sum(int(row["bytes"]) for row in normalized)
    if expected_bytes is not None and observed_bytes != expected_bytes:
        raise SeedClosureError(
            f"overlay bytes drifted: {observed_bytes} != {expected_bytes}"
        )
    if not frozen and (expected_inventory_sha is None or expected_bytes is None):
        if not allow_unfrozen:
            raise SeedClosureError(
                "overlay contract is not frozen; run --print-candidate-contract, "
                "review it, and update the contract"
            )
        return {
            "status": "PENDING_FREEZE",
            "files": len(normalized),
            "bytes": observed_bytes,
            "inventory_sha256": observed_inventory_sha,
        }
    if frozen and frozen != normalized:
        raise SeedClosureError("frozen overlay file inventory drifted")
    if expected_inventory_sha is not None and observed_inventory_sha != expected_inventory_sha:
        raise SeedClosureError(
            "frozen overlay inventory SHA-256 drifted: "
            f"{observed_inventory_sha} != {expected_inventory_sha}"
        )
    return {
        "status": "GREEN",
        "files": len(normalized),
        "bytes": observed_bytes,
        "inventory_sha256": observed_inventory_sha,
        "frozen_rows": bool(frozen),
    }


def validate_boundaries(
    candidate_source: Path,
    baseline_source: Path,
    overlay_rows: Sequence[Mapping[str, object]],
    contract: Mapping[str, Any],
) -> dict[str, object]:
    candidate = _mapping(contract.get("candidate"), "candidate")
    target = _integer(candidate.get("effect_target_per_file"), "candidate.effect_target_per_file")
    hard_max = _integer(candidate.get("effect_hard_max_per_file"), "candidate.effect_hard_max_per_file")
    exception_rows = candidate.get("effect_boundary_exceptions")
    if not isinstance(exception_rows, list) or not all(
        isinstance(row, dict) for row in exception_rows
    ):
        raise SeedClosureError(
            "candidate.effect_boundary_exceptions must be a list of objects"
        )
    exceptions: dict[str, dict[str, str]] = {}
    for index, raw_row in enumerate(exception_rows):
        row = _mapping(raw_row, f"candidate.effect_boundary_exceptions[{index}]")
        path = _relative(row.get("path"), f"effect exception {index}.path")
        reason = _string(row.get("reason"), f"effect exception {index}.reason")
        live_evidence = _string(
            row.get("live_evidence"), f"effect exception {index}.live_evidence"
        )
        if path in exceptions:
            raise SeedClosureError(f"duplicate effect boundary exception: {path}")
        exceptions[path] = {
            "path": path,
            "reason": reason,
            "live_evidence": live_evidence,
        }
    effect_rows = [dict(row) for row in overlay_rows if row["kind"] == "effect"]
    over_target = [row for row in effect_rows if int(row["definitions"]) > target]
    over_hard = [row for row in effect_rows if int(row["definitions"]) > hard_max]
    expected_over_target = _integer(
        candidate.get("expected_effect_files_over_target"),
        "candidate.expected_effect_files_over_target",
    )
    expected_over_hard = _integer(
        candidate.get("expected_effect_files_over_hard_max"),
        "candidate.expected_effect_files_over_hard_max",
    )
    over_hard_paths = {str(row["path"]) for row in over_hard}
    if (
        any(int(row["definitions"]) < 1 for row in effect_rows)
        or len(over_target) != expected_over_target
        or len(over_hard) != expected_over_hard
        or set(exceptions) != over_hard_paths
    ):
        raise SeedClosureError(
            "new effect shard boundary failed: "
            f"exceptions={list(exceptions.values())}, "
            f"over_target={over_target}, over_hard={over_hard}, "
            f"expected_over_target={expected_over_target}, "
            f"expected_over_hard={expected_over_hard}"
        )
    inherited_over_hard: list[dict[str, object]] = []
    base_effects = baseline_source / "common/scripted_effects"
    if base_effects.is_dir():
        for path in sorted(base_effects.glob("*.txt")):
            relative = path.relative_to(baseline_source).as_posix()
            _data, blocks = closure_utils._blocks(path, relative)
            if len(blocks) > hard_max:
                inherited_over_hard.append(
                    {"path": relative, "definitions": len(blocks)}
                )
    return {
        "status": "GREEN",
        "scope": "new-overlay-effects",
        "target": target,
        "hard_max": hard_max,
        "max_observed": max(int(row["definitions"]) for row in effect_rows),
        "over_target": over_target,
        "over_hard_max": over_hard,
        "exceptions": list(exceptions.values()),
        "inherited_r3_grandfathered": inherited_over_hard,
    }


def validate_whole_file_closure(root: Path) -> dict[str, object]:
    graph, _ = provider_graph(root)
    callable_providers = {
        **graph.effects,
        **graph.triggers,
        **graph.values,
    }
    referenced_callables: set[str] = set()
    referenced_events: set[str] = set()
    referenced_positions: set[str] = set()
    blocks = (
        *callable_providers.values(),
        *graph.events.values(),
        *graph.court_positions.values(),
    )
    for block in blocks:
        effects, events, triggers, values, positions = _block_references(block)
        referenced_callables.update(effects | triggers | values)
        referenced_events.update(events)
        referenced_positions.update(positions)
    missing_callables = sorted(referenced_callables - set(callable_providers))
    missing_events = sorted(referenced_events - set(graph.events))
    missing_positions = sorted(referenced_positions - set(graph.court_positions))
    if missing_callables or missing_events or missing_positions:
        raise SeedClosureError(
            "whole-file closure is unresolved: "
            f"callables={missing_callables}, events={missing_events}, court_positions={missing_positions}"
        )
    return {
        "status": "GREEN",
        "callable_providers": len(callable_providers),
        "event_providers": len(graph.events),
        "court_position_providers": len(graph.court_positions),
        "referenced_callables": len(referenced_callables),
        "referenced_events": len(referenced_events),
        "referenced_court_positions": len(referenced_positions),
        "missing_callables": [],
        "missing_events": [],
        "missing_court_positions": [],
    }


def validate_final_roots(
    root: Path, contract: Mapping[str, Any]
) -> dict[str, object]:
    graph, _ = provider_graph(root)
    roots = _strings(
        _mapping(contract.get("fixture"), "fixture").get("ordered_root_effects"),
        "fixture.ordered_root_effects",
    )
    closure = dependency_fixed_point(graph, roots)
    if closure.unresolved:
        raise SeedClosureError(f"materialized five-root closure is unresolved: {closure}")
    expected = _mapping(
        _mapping(contract.get("candidate"), "candidate").get("expected_five_root_closure"),
        "candidate.expected_five_root_closure",
    )
    # The frozen six-trigger figure is the Workforce expansion ABI.  B1 is
    # inherited from r3 and its already-proven root reaches three additional
    # baseline triggers; those are useful diagnostics, not seed-overlay
    # dependencies.  Keep both facts explicit instead of silently changing
    # the contract from six to nine.
    workforce_triggers = set(
        _strings(
            _mapping(contract.get("expansion"), "expansion").get(
                "reachable_triggers"
            ),
            "expansion.reachable_triggers",
        )
    )
    if not workforce_triggers <= set(closure.triggers):
        raise SeedClosureError("materialized five-root closure lost a Workforce trigger")
    expected_inherited_triggers = set(
        _strings(
            _mapping(contract.get("candidate"), "candidate").get(
                "expected_inherited_additional_triggers"
            ),
            "candidate.expected_inherited_additional_triggers",
        )
    )
    inherited_triggers = set(closure.triggers) - workforce_triggers
    if inherited_triggers != expected_inherited_triggers:
        raise SeedClosureError(
            "materialized inherited trigger closure drifted: "
            f"observed={sorted(inherited_triggers)}, "
            f"expected={sorted(expected_inherited_triggers)}"
        )
    counts = {
        **_closure_counts(closure),
        "triggers": len(workforce_triggers),
    }
    _assert_counts(counts, expected, "candidate.expected_five_root_closure")
    return {
        "status": "GREEN",
        "roots": list(roots),
        **counts,
        "all_reachable_triggers": sorted(closure.triggers),
        "inherited_additional_triggers": sorted(inherited_triggers),
    }


def validate_localization(
    root: Path, required_keys: Iterable[str]
) -> dict[str, object]:
    providers, duplicates = _localization_provider_map(root)
    keys = set(required_keys)
    relevant_duplicates = {key: value for key, value in duplicates.items() if key in keys}
    missing = sorted(keys - set(providers))
    if missing or relevant_duplicates:
        raise SeedClosureError(
            f"Simplified Chinese localization closure failed: missing={missing}, duplicates={relevant_duplicates}"
        )
    return {
        "status": "GREEN",
        "required_keys": len(keys),
        "missing": [],
        "duplicate_owners": {},
        "owners": {key: providers[key] for key in sorted(keys)},
    }


def validate_formatting_and_forbidden(
    root: Path, overlay_rows: Sequence[Mapping[str, object]], contract: Mapping[str, Any]
) -> dict[str, object]:
    markers = _strings(contract.get("stub_markers"), "stub_markers")
    forbidden = tuple(
        _relative(value, "forbidden path")
        for value in _strings(contract.get("forbidden_paths"), "forbidden_paths")
    )
    forbidden_present = [
        relative for relative in forbidden if (root / PurePosixPath(relative)).exists()
    ]
    bom_missing: list[str] = []
    unbalanced: list[dict[str, object]] = []
    marker_hits: list[dict[str, str]] = []
    for row in overlay_rows:
        relative = str(row["path"])
        path = root / PurePosixPath(relative)
        if path.suffix.lower() not in SCRIPT_SUFFIXES:
            continue
        data = path.read_bytes()
        if not data.startswith(BOM):
            bom_missing.append(relative)
        text = data.decode("utf-8-sig")
        for marker in markers:
            if marker in text:
                marker_hits.append({"path": relative, "marker": marker})
        if path.suffix.lower() != ".yml":
            depth, quoted = closure_utils.brace_balance(path)
            if depth != 0 or quoted:
                unbalanced.append(
                    {"path": relative, "depth": depth, "unterminated_quote": quoted}
                )
    if forbidden_present or bom_missing or unbalanced or marker_hits:
        raise SeedClosureError(
            "format/no-stub/forbidden gate failed: "
            f"forbidden={forbidden_present}, bom={bom_missing}, braces={unbalanced}, markers={marker_hits}"
        )
    return {
        "status": "GREEN",
        "forbidden_paths_present": [],
        "bom_missing": [],
        "brace_unbalanced": [],
        "stub_marker_hits": [],
    }


def validate_output_location(output: Path, *authorities: Path) -> None:
    resolved = output.resolve()
    for authority in authorities:
        authority = authority.resolve()
        try:
            resolved.relative_to(authority)
        except ValueError:
            continue
        raise SeedClosureError(f"output must not be inside immutable authority: {authority}")


def copy_overlay(
    canonical_source: Path,
    candidate_source: Path,
    rows: Sequence[Mapping[str, object]],
) -> None:
    baseline_paths = {
        path.relative_to(candidate_source).as_posix()
        for path in candidate_source.rglob("*")
        if path.is_file()
    }
    paths = {str(row["path"]) for row in rows}
    overlap = sorted(paths & baseline_paths)
    if overlap:
        raise SeedClosureError(f"seed overlay collides with frozen r3 paths: {overlap}")
    for row in rows:
        relative = str(row["path"])
        source = canonical_source / PurePosixPath(relative)
        if not source.is_file() or source.is_symlink():
            raise SeedClosureError(f"canonical purpose shard is missing or symlinked: {source}")
        data = source.read_bytes()
        if len(data) != int(row["bytes"]) or sha256_bytes(data) != row["sha256"]:
            raise SeedClosureError(f"canonical purpose shard changed during build: {relative}")
        target = candidate_source / PurePosixPath(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _fingerprint_candidate(
    manifest: Mapping[str, object], projection_path: Path, rows: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    return {
        "expected_file_count": len(rows),
        "expected_bytes": sum(int(row["bytes"]) for row in rows),
        "source_tree_sha256": manifest["source_tree_sha256"],
        "formal_overlay_tree_sha256": manifest["formal_overlay_tree_sha256"],
        "file_list_sha256": manifest["file_list_sha256"],
        "projection_manifest_sha256": sha256_file(projection_path),
    }


def validate_candidate_fingerprint(
    observed: Mapping[str, object],
    contract: Mapping[str, Any],
    *,
    allow_unfrozen: bool,
) -> dict[str, object]:
    candidate = _mapping(contract.get("candidate"), "candidate")
    expected = {
        "expected_file_count": _integer(
            candidate.get("expected_file_count"), "candidate.expected_file_count"
        ),
        "expected_bytes": candidate.get("expected_bytes"),
        "source_tree_sha256": candidate.get("source_tree_sha256"),
        "formal_overlay_tree_sha256": candidate.get("formal_overlay_tree_sha256"),
        "file_list_sha256": candidate.get("file_list_sha256"),
        "projection_manifest_sha256": candidate.get("projection_manifest_sha256"),
    }
    if int(observed["expected_file_count"]) != expected["expected_file_count"]:
        raise SeedClosureError("candidate file count drifted")
    pending = [key for key, value in expected.items() if key != "expected_file_count" and value is None]
    if pending:
        if not allow_unfrozen:
            raise SeedClosureError(
                "candidate fingerprint is not frozen; run --print-candidate-contract, review it, and update the contract"
            )
        return {"status": "PENDING_FREEZE", "pending": pending}
    normalized_expected = {
        "expected_file_count": expected["expected_file_count"],
        "expected_bytes": _integer(expected["expected_bytes"], "candidate.expected_bytes"),
        "source_tree_sha256": _digest(expected["source_tree_sha256"], "candidate.source_tree_sha256"),
        "formal_overlay_tree_sha256": _digest(expected["formal_overlay_tree_sha256"], "candidate.formal_overlay_tree_sha256"),
        "file_list_sha256": _digest(expected["file_list_sha256"], "candidate.file_list_sha256"),
        "projection_manifest_sha256": _digest(expected["projection_manifest_sha256"], "candidate.projection_manifest_sha256"),
    }
    if dict(observed) != normalized_expected:
        raise SeedClosureError(
            f"candidate fingerprint drifted: observed={dict(observed)}, expected={normalized_expected}"
        )
    return {"status": "GREEN"}


def materialize(
    *,
    output: Path,
    projection_name: str,
    contract_path: Path = CONTRACT_PATH,
    baseline_root: Path | None = None,
    canonical_source: Path = MOD_ROOT,
    print_candidate_contract: bool = False,
) -> dict[str, Any]:
    output = output.resolve()
    canonical_source = canonical_source.resolve()
    contract_path = contract_path.resolve()
    contract = load_contract(contract_path)
    baseline = _mapping(contract.get("baseline"), "baseline")
    candidate_contract = _mapping(contract.get("candidate"), "candidate")
    expected_projection_name = _string(
        candidate_contract.get("projection"), "candidate.projection"
    )
    if projection_name != expected_projection_name:
        raise SeedClosureError(
            "candidate projection name drifted: "
            f"{projection_name!r} != {expected_projection_name!r}"
        )
    if baseline_root is None:
        baseline_root = ROOT / _relative(baseline.get("root"), "baseline.root")
    baseline_root = baseline_root.resolve()
    validate_output_location(output, canonical_source, baseline_root)
    if output.exists():
        raise SeedClosureError(f"output already exists; use a fresh path: {output}")
    if not canonical_source.is_dir():
        raise SeedClosureError(f"canonical source is missing: {canonical_source}")
    if not projection_name or any(char in projection_name for char in "/\\\x00"):
        raise SeedClosureError(f"projection name is malformed: {projection_name!r}")

    fixture_check = validate_fixture(contract)
    baseline_source, baseline_manifest, baseline_projection, baseline_identity = (
        verify_baseline_identity(contract, baseline_root)
    )
    overlay_rows, selection_check = select_overlay(
        canonical_source, baseline_source, contract
    )
    overlay_contract_check = validate_overlay_contract(
        overlay_rows, contract, allow_unfrozen=print_candidate_contract
    )

    output.mkdir(parents=True)
    candidate_source = output / "source"
    try:
        baseline_receipt = materialize_projection(
            baseline_source,
            candidate_source,
            projection_name=baseline_projection,
            manifest_path=baseline_manifest,
        )
    except ProductProjectionError as error:
        raise SeedClosureError(str(error)) from error
    write_json(output / "baseline-materialization.json", baseline_receipt)
    copy_overlay(canonical_source, candidate_source, overlay_rows)

    expected_file_count = _integer(
        candidate_contract.get("expected_file_count"), "candidate.expected_file_count"
    )
    source_rows = closure_utils.tree_rows(candidate_source)
    if len(source_rows) != expected_file_count:
        raise SeedClosureError(
            f"candidate file count changed: {len(source_rows)} != {expected_file_count}"
        )

    delta_loc_keys = selection_check["delta_localization_keys"]
    checks: dict[str, object] = {
        "fixture": fixture_check,
        "baseline_identity": baseline_identity,
        "selection": selection_check,
        "overlay_contract": overlay_contract_check,
        "effect_boundaries": validate_boundaries(
            candidate_source, baseline_source, overlay_rows, contract
        ),
        "five_root_closure": validate_final_roots(candidate_source, contract),
        "whole_file_closure": validate_whole_file_closure(candidate_source),
        "localization": validate_localization(candidate_source, delta_loc_keys),
        "formatting": validate_formatting_and_forbidden(
            candidate_source, overlay_rows, contract
        ),
    }

    projection_path = output / "projection.json"
    try:
        manifest = write_manifest(
            candidate_source, projection_path, projection_name=projection_name
        )
        product = output / "product"
        replay = output / "materialized-check"
        receipt = materialize_projection(
            candidate_source,
            product,
            projection_name=projection_name,
            manifest_path=projection_path,
        )
        replay_receipt = materialize_projection(
            candidate_source,
            replay,
            projection_name=projection_name,
            manifest_path=projection_path,
        )
    except ProductProjectionError as error:
        raise SeedClosureError(str(error)) from error
    write_json(output / "materialization.json", receipt)
    write_json(output / "materialization-replay.json", replay_receipt)
    product_rows = closure_utils.tree_rows(product)
    replay_rows = closure_utils.tree_rows(replay)
    if source_rows != product_rows or source_rows != replay_rows:
        raise SeedClosureError("candidate source/product/replay rows are not identical")
    checks["deterministic_materialization"] = {
        "status": "GREEN",
        "source_equals_product": True,
        "source_equals_replay": True,
        "file_count": len(source_rows),
    }

    fingerprint = _fingerprint_candidate(manifest, projection_path, source_rows)
    checks["candidate_fingerprint"] = validate_candidate_fingerprint(
        fingerprint, contract, allow_unfrozen=print_candidate_contract
    )
    contract_candidate = {
        "overlay": {
            "bytes": sum(int(row["bytes"]) for row in overlay_rows),
            "inventory_sha256": overlay_inventory_sha256(overlay_rows),
            "files": overlay_rows,
        },
        "candidate": fingerprint,
    }
    shutil.copy2(contract_path, output / "closure-contract.json")
    preflight: dict[str, Any] = {
        "schema_version": 1,
        "kind": "zg361_phase2_seed_entry_production_closure_preflight",
        "status": (
            "PENDING_CONTRACT_FREEZE" if print_candidate_contract else "GREEN_STATIC"
        ),
        "no_stubs": True,
        "production_candidate": True,
        "feature_or_runtime_certification": False,
        "canonical_source_modified": False,
        "baseline_modified": False,
        "projection": projection_name,
        "candidate": {
            "source": str(candidate_source),
            "product": str(product),
            "materialized_check": str(replay),
            **fingerprint,
            "projection_manifest": str(projection_path),
        },
        "baseline": {"root": str(baseline_root), **baseline_identity},
        "overlay": {
            "canonical_source": str(canonical_source),
            "file_count": len(overlay_rows),
            "bytes": sum(int(row["bytes"]) for row in overlay_rows),
            "files": overlay_rows,
        },
        "contract": {
            "path": str(contract_path),
            "sha256": sha256_file(contract_path),
            "candidate_values": contract_candidate,
        },
        "checks": checks,
        "ck3_launch": "NOT_RUN_BY_BUILDER",
        "runtime": {"ck3_launch": "NOT_RUN", "live_status": "pending"},
        "next_action": (
            "Freeze the printed candidate contract and rebuild."
            if print_candidate_contract
            else "Run one separately authorized full-entry acceptance on this exact projection/hash before seed capture."
        ),
    }
    write_json(output / "preflight.json", preflight)
    return preflight


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "_runtime/phase2-seed-entry-production-closure-20260904-r4-final",
    )
    parser.add_argument(
        "--projection-name",
        default="phase2-seed-entry-production-closure-20260904-r4",
    )
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--baseline-root", type=Path)
    parser.add_argument("--canonical-source", type=Path, default=MOD_ROOT)
    parser.add_argument(
        "--print-candidate-contract",
        action="store_true",
        help="print candidate hash/inventory values without modifying the contract",
    )
    args = parser.parse_args(argv)
    try:
        report = materialize(
            output=args.output,
            projection_name=args.projection_name,
            contract_path=args.contract,
            baseline_root=args.baseline_root,
            canonical_source=args.canonical_source,
            print_candidate_contract=args.print_candidate_contract,
        )
    except SeedClosureError as error:
        print(f"RED: {error}")
        return 1
    if args.print_candidate_contract:
        print(
            json.dumps(
                report["contract"]["candidate_values"],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        candidate = report["candidate"]
        print(
            "GREEN_STATIC: seed-entry production closure "
            f"{candidate['expected_file_count']} files, "
            f"{candidate['expected_bytes']} bytes, "
            f"source SHA {candidate['source_tree_sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
