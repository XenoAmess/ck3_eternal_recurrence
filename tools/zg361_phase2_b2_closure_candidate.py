#!/usr/bin/env python3
"""Materialize the exact no-stub B2 production-closure startup candidate.

The builder starts from the immutable 59-file B1 formal projection, copying
only the hash-bound manifest rows.  It then overlays the complete canonical
B2 product plus the exact currently required Workforce shards and fact
owners.  It performs static closure, file-boundary, BOM, brace, localization,
and replay checks, but deliberately never launches CK3.
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

from phase2_workforce_block_segments import find_blocks, scan_line
from zg361_phase2_product_projection import (
    ProductProjectionError,
    load_projection,
    materialize_projection,
    write_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
MOD_ROOT = ROOT / "mod_zhongguo_style"
MOD_TOOLS = MOD_ROOT / "tools"
CONTRACT_PATH = Path(__file__).with_name(
    "zg361_phase2_b2_production_closure.json"
)
BOM = b"\xef\xbb\xbf"

if str(MOD_TOOLS) not in sys.path:
    sys.path.insert(0, str(MOD_TOOLS))

import gen_361_b2_runtime as b2_generator
import gen_361_workforce_endgame_runtime as workforce_generator


EFFECT_CALL_RE = re.compile(r"\b(zg361_[A-Za-z0-9_]+_effect)\s*=")
CUSTOM_CALL_RE = re.compile(
    r"\b(zg361_[A-Za-z0-9_]+_(?:effect|trigger|value))\s*="
)
EVENT_REF_RE = re.compile(
    r"\b(?:id|EVENT)\s*=\s*((?:zg361[a-z0-9_]*|zg361)\.\d+)\b"
)
SCALAR_EVENT_REF_RE = re.compile(
    r"\b(?:trigger_event|character_event|event)\s*=\s*"
    r"((?:zg361[a-z0-9_]*|zg361)\.\d+)\b"
)
LOC_DEF_RE = re.compile(r'^\s+([A-Za-z0-9_.-]+):(?:\d+)?\s+"', re.MULTILINE)
LOC_EVENT_KEY_RE = re.compile(
    r"\b(?:zg361[a-z0-9_]*|zg361)\.\d+\.[A-Za-z0-9_.-]+\b"
)
SCRIPT_SUFFIXES = frozenset({".txt", ".gui", ".yml"})
CALLABLE_DIRS = (
    Path("common/scripted_effects"),
    Path("common/scripted_triggers"),
    Path("common/script_values"),
)


class B2ClosureError(ValueError):
    """The requested B2 closure is incomplete or not reproducible."""


@dataclass(frozen=True)
class ScriptBlock:
    name: str
    path: str
    data: bytes


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


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise B2ClosureError(f"cannot read B2 closure contract {path}: {error}") from error
    if not isinstance(payload, dict):
        raise B2ClosureError("B2 closure contract root must be an object")
    if payload.get("schema_version") != 1:
        raise B2ClosureError("B2 closure contract schema_version must be 1")
    if payload.get("kind") != "zg361_phase2_b2_production_closure":
        raise B2ClosureError("unexpected B2 closure contract kind")
    return payload


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise B2ClosureError(f"{label} must be an object")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise B2ClosureError(f"{label} must be a non-empty string")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise B2ClosureError(f"{label} must be a non-negative integer")
    return value


def _strings(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise B2ClosureError(f"{label} must be a list of non-empty strings")
    result = tuple(value)
    if len(result) != len(set(result)):
        raise B2ClosureError(f"{label} contains duplicate values")
    return result


def _relative(value: str, label: str) -> str:
    raw = value.replace("\\", "/")
    path = PurePosixPath(raw)
    if (
        path.is_absolute()
        or raw.startswith("//")
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise B2ClosureError(f"{label} must be a normalized relative path: {value!r}")
    return path.as_posix()


def _dependency(contract: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    dependencies = _mapping(contract.get("dependencies"), "dependencies")
    return _mapping(dependencies.get(name), f"dependencies.{name}")


def expected_closure(contract: Mapping[str, Any]) -> tuple[set[str], set[str]]:
    effects: list[str] = []
    events: list[str] = []
    for owner in ("b2_cycle", "case_kernel", "workforce_endgame", "normal_exit", "probation", "rehire"):
        row = _dependency(contract, owner)
        if "reachable_effects" in row:
            effects.extend(_strings(row["reachable_effects"], f"{owner}.reachable_effects"))
        if "reachable_events" in row:
            events.extend(_strings(row["reachable_events"], f"{owner}.reachable_events"))
    if len(effects) != len(set(effects)):
        raise B2ClosureError("declared reachable effect owners overlap")
    if len(events) != len(set(events)):
        raise B2ClosureError("declared reachable event owners overlap")
    candidate = _mapping(contract.get("candidate"), "candidate")
    expected_effect_count = _integer(
        candidate.get("expected_dependency_effect_closure_count"),
        "candidate.expected_dependency_effect_closure_count",
    )
    expected_event_count = _integer(
        candidate.get("expected_dependency_event_closure_count"),
        "candidate.expected_dependency_event_closure_count",
    )
    if len(effects) != expected_effect_count or len(events) != expected_event_count:
        raise B2ClosureError(
            "declared closure counts disagree with contract: "
            f"effects={len(effects)}/{expected_effect_count}, "
            f"events={len(events)}/{expected_event_count}"
        )
    return set(effects), set(events)


def overlay_paths(contract: Mapping[str, Any]) -> tuple[str, ...]:
    b2 = _mapping(contract.get("b2"), "b2")
    workforce = _dependency(contract, "workforce_endgame")
    paths: list[str] = [
        *_strings(b2.get("effect_shards"), "b2.effect_shards"),
        _string(b2.get("event_file"), "b2.event_file"),
        _string(b2.get("localization_file"), "b2.localization_file"),
        *_strings(workforce.get("effect_shards"), "workforce_endgame.effect_shards"),
        *_strings(workforce.get("event_shards"), "workforce_endgame.event_shards"),
        _string(workforce.get("localization_file"), "workforce_endgame.localization_file"),
    ]
    for owner in ("normal_exit", "probation", "rehire"):
        row = _dependency(contract, owner)
        effect_files = row.get("effect_files")
        paths.extend(
            _strings(effect_files, f"{owner}.effect_files")
            if effect_files is not None
            else (_string(row.get("effect_file"), f"{owner}.effect_file"),)
        )
        paths.extend(
            (
                _string(row.get("event_file"), f"{owner}.event_file"),
                _string(row.get("localization_file"), f"{owner}.localization_file"),
            )
        )
    normalized = tuple(_relative(path, "overlay path") for path in paths)
    if len(normalized) != len(set(normalized)):
        raise B2ClosureError("overlay file list contains duplicate paths")
    expected_count = _integer(
        _mapping(contract.get("candidate"), "candidate").get(
            "expected_overlay_file_count"
        ),
        "candidate.expected_overlay_file_count",
    )
    if len(normalized) != expected_count:
        raise B2ClosureError(
            f"overlay file count changed: {len(normalized)} != {expected_count}"
        )
    return normalized


def _generator_paths() -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    b2_effects = tuple(
        f"common/scripted_effects/{filename}"
        for filename, _names in b2_generator.EFFECT_GROUPS
    )
    closure_effects = set(workforce_generator.B2_EFFECT_CLOSURE_NAMES)
    workforce_effects = tuple(
        f"common/scripted_effects/{group.filename}"
        for group in workforce_generator.EFFECT_GROUPS
        if closure_effects.intersection(group.effect_names)
    )
    closure_event_ids = set(workforce_generator.B2_EVENT_CLOSURE_IDS)
    workforce_events = tuple(
        f"events/{group.filename}"
        for group in workforce_generator.EVENT_GROUPS
        if closure_event_ids.intersection(group.event_ids)
    )
    return b2_effects, workforce_effects, workforce_events


def validate_generator_selection(contract: Mapping[str, Any]) -> dict[str, object]:
    b2 = _mapping(contract.get("b2"), "b2")
    workforce = _dependency(contract, "workforce_endgame")
    declared = (
        _strings(b2.get("effect_shards"), "b2.effect_shards"),
        _strings(workforce.get("effect_shards"), "workforce_endgame.effect_shards"),
        _strings(workforce.get("event_shards"), "workforce_endgame.event_shards"),
    )
    generated = _generator_paths()
    labels = ("B2 effect shards", "Workforce effect closure shards", "Workforce event closure shards")
    for label, declared_paths, generated_paths in zip(labels, declared, generated, strict=True):
        if declared_paths != generated_paths:
            raise B2ClosureError(
                f"{label} drifted from generator: "
                f"missing={sorted(set(generated_paths) - set(declared_paths))}, "
                f"extra={sorted(set(declared_paths) - set(generated_paths))}"
            )
    if len(generated[0]) != 25 or len(generated[1]) != 16 or len(generated[2]) != 7:
        raise B2ClosureError(
            "generator selection cardinality changed: "
            f"B2={len(generated[0])}, Workforce effects={len(generated[1])}, "
            f"Workforce events={len(generated[2])}"
        )

    workforce_effect_closure = set(workforce_generator.B2_EFFECT_CLOSURE_NAMES)
    selected_effect_names = {
        name
        for group in workforce_generator.EFFECT_GROUPS
        if workforce_effect_closure.intersection(group.effect_names)
        for name in group.effect_names
    }
    workforce_event_closure = set(workforce_generator.B2_EVENT_CLOSURE_IDS)
    selected_event_ids = {
        event_id
        for group in workforce_generator.EVENT_GROUPS
        if workforce_event_closure.intersection(group.event_ids)
        for event_id in group.event_ids
    }
    declared_workforce_effects = set(
        _strings(
            workforce.get("reachable_effects"),
            "workforce_endgame.reachable_effects",
        )
    )
    declared_workforce_events = set(
        _strings(
            workforce.get("reachable_events"),
            "workforce_endgame.reachable_events",
        )
    )
    if (
        selected_effect_names != workforce_effect_closure
        or declared_workforce_effects != workforce_effect_closure
        or len(workforce_effect_closure) != 40
    ):
        raise B2ClosureError(
            "Workforce effect shard union is not the exact 40-effect B2 closure: "
            f"selected_extra={sorted(selected_effect_names - workforce_effect_closure)}, "
            f"selected_missing={sorted(workforce_effect_closure - selected_effect_names)}, "
            f"contract_extra={sorted(declared_workforce_effects - workforce_effect_closure)}, "
            f"contract_missing={sorted(workforce_effect_closure - declared_workforce_effects)}"
        )
    if (
        selected_event_ids != workforce_event_closure
        or declared_workforce_events
        != {f"zg361we.{event_id}" for event_id in workforce_event_closure}
        or len(workforce_event_closure) != 19
    ):
        raise B2ClosureError(
            "Workforce event shard union is not the exact 19-event B2 closure: "
            f"selected_extra={sorted(selected_event_ids - workforce_event_closure)}, "
            f"selected_missing={sorted(workforce_event_closure - selected_event_ids)}"
        )
    return {
        "status": "GREEN",
        "b2_effect_shards": len(generated[0]),
        "workforce_effect_shards": len(generated[1]),
        "workforce_effects": len(selected_effect_names),
        "workforce_event_shards": len(generated[2]),
        "workforce_events": len(selected_event_ids),
        "extra_effects": [],
        "missing_effects": [],
        "extra_events": [],
        "missing_events": [],
    }


def _blocks(path: Path, relative: str) -> tuple[bytes, tuple[ScriptBlock, ...]]:
    data = path.read_bytes()
    try:
        _header, rows = find_blocks(data)
    except (UnicodeError, ValueError) as error:
        raise B2ClosureError(f"cannot parse top-level blocks in {relative}: {error}") from error
    return data, tuple(
        ScriptBlock(
            name=str(row["name"]),
            path=relative,
            data=data[int(row["start_byte"]): int(row["end_byte"])],
        )
        for row in rows
    )


def _provider_map(
    root: Path, directories: Sequence[Path]
) -> tuple[dict[str, ScriptBlock], list[str]]:
    providers: dict[str, ScriptBlock] = {}
    duplicates: list[str] = []
    for directory in directories:
        base = root / directory
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*.txt")):
            relative = path.relative_to(root).as_posix()
            _data, blocks = _blocks(path, relative)
            for block in blocks:
                if block.name in providers:
                    duplicates.append(block.name)
                else:
                    providers[block.name] = block
    return providers, sorted(set(duplicates))


def _mask_comments_and_strings(text: str) -> str:
    output = list(text)
    in_comment = False
    in_quote = False
    escaped = False
    for index, char in enumerate(text):
        if in_comment:
            if char in "\r\n":
                in_comment = False
            else:
                output[index] = " "
            continue
        if in_quote:
            if char not in "\r\n":
                output[index] = " "
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_quote = False
            continue
        if char == "#":
            output[index] = " "
            in_comment = True
        elif char == '"':
            output[index] = " "
            in_quote = True
    return "".join(output)


def block_references(block: ScriptBlock) -> tuple[set[str], set[str], set[str]]:
    text = _mask_comments_and_strings(block.data.decode("utf-8-sig"))
    effects = set(EFFECT_CALL_RE.findall(text))
    callables = set(CUSTOM_CALL_RE.findall(text))
    events = set(EVENT_REF_RE.findall(text)) | set(SCALAR_EVENT_REF_RE.findall(text))
    effects.discard(block.name)
    callables.discard(block.name)
    return effects, events, callables


def dependency_fixed_point(
    effect_providers: Mapping[str, ScriptBlock],
    event_providers: Mapping[str, ScriptBlock],
    roots: Iterable[str],
) -> tuple[set[str], set[str], set[str], set[str]]:
    effects: set[str] = set()
    events: set[str] = set()
    missing_effects: set[str] = set()
    missing_events: set[str] = set()
    queue: deque[tuple[str, str]] = deque(("effect", name) for name in roots)
    while queue:
        kind, name = queue.popleft()
        if kind == "effect":
            if name in effects:
                continue
            block = effect_providers.get(name)
            if block is None:
                missing_effects.add(name)
                continue
            effects.add(name)
        else:
            if name in events:
                continue
            block = event_providers.get(name)
            if block is None:
                missing_events.add(name)
                continue
            events.add(name)
        effect_refs, event_refs, _callable_refs = block_references(block)
        queue.extend(("effect", reference) for reference in sorted(effect_refs))
        queue.extend(("event", reference) for reference in sorted(event_refs))
    return effects, events, missing_effects, missing_events


def validate_dependency_closure(
    root: Path, contract: Mapping[str, Any]
) -> dict[str, object]:
    effect_providers, effect_duplicates = _provider_map(
        root, (Path("common/scripted_effects"),)
    )
    event_providers, event_duplicates = _provider_map(root, (Path("events"),))
    if effect_duplicates or event_duplicates:
        raise B2ClosureError(
            f"duplicate providers: effects={effect_duplicates}, events={event_duplicates}"
        )
    roots = _strings(contract.get("root_effects"), "root_effects")
    actual_effects, actual_events, missing_effects, missing_events = dependency_fixed_point(
        effect_providers, event_providers, roots
    )
    expected_effects, expected_events = expected_closure(contract)
    if missing_effects or missing_events:
        raise B2ClosureError(
            f"dependency closure is unresolved: effects={sorted(missing_effects)}, "
            f"events={sorted(missing_events)}"
        )
    if actual_effects != expected_effects or actual_events != expected_events:
        raise B2ClosureError(
            "dependency fixed point drifted: "
            f"effect_missing={sorted(expected_effects - actual_effects)}, "
            f"effect_extra={sorted(actual_effects - expected_effects)}, "
            f"event_missing={sorted(expected_events - actual_events)}, "
            f"event_extra={sorted(actual_events - expected_events)}"
        )
    return {
        "status": "GREEN",
        "root_effects": list(roots),
        "effects": len(actual_effects),
        "events": len(actual_events),
        "effect_names": sorted(actual_effects),
        "event_ids": sorted(actual_events),
        "event_parameter_abi_ids": [
            event
            for event in ("zg361we.4606", "zg361we.4706", "zg361we.4801", "zg361we.4901")
            if event in actual_events
        ],
    }


def validate_whole_file_callable_closure(root: Path) -> dict[str, object]:
    callable_providers, callable_duplicates = _provider_map(root, CALLABLE_DIRS)
    event_providers, event_duplicates = _provider_map(root, (Path("events"),))
    if callable_duplicates or event_duplicates:
        raise B2ClosureError(
            "whole-file provider duplicates: "
            f"callables={callable_duplicates}, events={event_duplicates}"
        )
    referenced_callables: set[str] = set()
    referenced_events: set[str] = set()
    for block in (*callable_providers.values(), *event_providers.values()):
        _effects, events, callables = block_references(block)
        referenced_callables.update(callables)
        referenced_events.update(events)
    missing_callables = sorted(referenced_callables - set(callable_providers))
    missing_events = sorted(referenced_events - set(event_providers))
    if missing_callables or missing_events:
        raise B2ClosureError(
            "whole-file callable closure is unresolved: "
            f"callables={missing_callables}, events={missing_events}"
        )
    return {
        "status": "GREEN",
        "callable_providers": len(callable_providers),
        "event_providers": len(event_providers),
        "referenced_callables": len(referenced_callables),
        "referenced_events": len(referenced_events),
        "missing_callables": missing_callables,
        "missing_events": missing_events,
    }


def _group_counts(
    root: Path,
    groups: Sequence[tuple[str, Sequence[str]]],
    *,
    label: str,
    target: int,
    hard_max: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative, expected_names in groups:
        data, blocks = _blocks(root / PurePosixPath(relative), relative)
        names = tuple(block.name for block in blocks)
        if names != tuple(expected_names):
            raise B2ClosureError(
                f"{label} block inventory drifted in {relative}: "
                f"expected={list(expected_names)}, observed={list(names)}"
            )
        count = len(names)
        if count < 1 or count > hard_max:
            raise B2ClosureError(
                f"{label} shard violates 1-{hard_max} hard range: {relative} has {count}"
            )
        if count > target:
            raise B2ClosureError(
                f"{label} shard exceeds the current 1-{target} target: {relative} has {count}"
            )
        rows.append(
            {
                "path": relative,
                "definitions": count,
                "bytes": len(data),
                "sha256": sha256_bytes(data),
            }
        )
    return rows


def validate_file_boundaries(
    root: Path, contract: Mapping[str, Any]
) -> dict[str, object]:
    candidate = _mapping(contract.get("candidate"), "candidate")
    target = _integer(candidate.get("effect_target_per_file"), "effect target")
    hard_max = _integer(candidate.get("effect_hard_max_per_file"), "effect hard max")
    b2_groups = tuple(
        (
            f"common/scripted_effects/{filename}",
            tuple(names),
        )
        for filename, names in b2_generator.EFFECT_GROUPS
    )
    closure_effects = set(workforce_generator.B2_EFFECT_CLOSURE_NAMES)
    workforce_effect_groups = tuple(
        (
            f"common/scripted_effects/{group.filename}",
            tuple(group.effect_names),
        )
        for group in workforce_generator.EFFECT_GROUPS
        if closure_effects.intersection(group.effect_names)
    )
    closure_event_ids = set(workforce_generator.B2_EVENT_CLOSURE_IDS)
    workforce_event_groups = tuple(
        (
            f"events/{group.filename}",
            tuple(f"zg361we.{event_id}" for event_id in group.event_ids),
        )
        for group in workforce_generator.EVENT_GROUPS
        if closure_event_ids.intersection(group.event_ids)
    )
    b2_rows = _group_counts(
        root, b2_groups, label="B2 effect", target=target, hard_max=hard_max
    )
    workforce_effect_rows = _group_counts(
        root,
        workforce_effect_groups,
        label="Workforce effect",
        target=target,
        hard_max=hard_max,
    )
    workforce_event_rows = _group_counts(
        root,
        workforce_event_groups,
        label="Workforce event",
        target=target,
        hard_max=hard_max,
    )
    expected_b2_effects = _integer(
        candidate.get("expected_b2_effect_count"), "candidate.expected_b2_effect_count"
    )
    if sum(int(row["definitions"]) for row in b2_rows) != expected_b2_effects:
        raise B2ClosureError("B2 effect shard total changed")
    dependency_effect_rows: list[dict[str, object]] = []
    for owner in ("normal_exit", "probation", "rehire"):
        row = _dependency(contract, owner)
        effect_files = row.get("effect_files")
        relatives = (
            _strings(effect_files, f"{owner}.effect_files")
            if effect_files is not None
            else (_string(row.get("effect_file"), f"{owner}.effect_file"),)
        )
        for relative in relatives:
            data, blocks = _blocks(root / PurePosixPath(relative), relative)
            count = len(blocks)
            if count < 1 or count > hard_max:
                raise B2ClosureError(
                    f"{owner} effect owner violates the hard maximum {hard_max}: {count}"
                )
            dependency_effect_rows.append(
                {
                    "path": relative,
                    "definitions": count,
                    "target_1_to_10": count <= target,
                    "hard_max_20": count <= hard_max,
                    "bytes": len(data),
                    "sha256": sha256_bytes(data),
                }
            )
    return {
        "status": "GREEN",
        "target": target,
        "hard_max": hard_max,
        "b2": b2_rows,
        "workforce_effects": workforce_effect_rows,
        "workforce_events": workforce_event_rows,
        "other_dependency_effect_files": dependency_effect_rows,
        "over_hard_max": [],
    }


def brace_balance(path: Path) -> tuple[int, bool]:
    text = path.read_text(encoding="utf-8-sig")
    depth = 0
    quoted = False
    for line in text.splitlines(keepends=True):
        delta, quoted = scan_line(line, quoted)
        depth += delta
        if depth < 0:
            return depth, quoted
    return depth, quoted


def validate_bom_braces_and_stubs(
    root: Path, contract: Mapping[str, Any]
) -> dict[str, object]:
    text_files = sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in SCRIPT_SUFFIXES
    )
    bom_missing: list[str] = []
    unbalanced: list[dict[str, object]] = []
    marker_hits: list[dict[str, str]] = []
    markers = _strings(contract.get("stub_markers"), "stub_markers")
    for path in text_files:
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        if not data.startswith(BOM):
            bom_missing.append(relative)
        text = data.decode("utf-8-sig")
        for marker in markers:
            if marker in text:
                marker_hits.append({"path": relative, "marker": marker})
        if path.suffix.lower() != ".yml":
            depth, quoted = brace_balance(path)
            if depth != 0 or quoted:
                unbalanced.append(
                    {"path": relative, "depth": depth, "unterminated_quote": quoted}
                )
    effect_providers, duplicates = _provider_map(
        root, (Path("common/scripted_effects"),)
    )
    empty_effects: list[dict[str, str]] = []
    for block in effect_providers.values():
        text = _mask_comments_and_strings(block.data.decode("utf-8-sig"))
        left, right = text.find("{"), text.rfind("}")
        if left >= 0 and right > left and not text[left + 1:right].strip():
            empty_effects.append({"path": block.path, "effect": block.name})
    if bom_missing or unbalanced or marker_hits or empty_effects or duplicates:
        raise B2ClosureError(
            "BOM/brace/no-stub check failed: "
            f"bom={bom_missing}, braces={unbalanced}, markers={marker_hits}, "
            f"empty_effects={empty_effects}, duplicates={duplicates}"
        )
    return {
        "status": "GREEN",
        "text_files": len(text_files),
        "bom_missing": bom_missing,
        "brace_unbalanced": unbalanced,
        "stub_marker_hits": marker_hits,
        "empty_effect_definitions": empty_effects,
    }


def validate_localization(
    root: Path, contract: Mapping[str, Any]
) -> dict[str, object]:
    b2 = _mapping(contract.get("b2"), "b2")
    workforce = _dependency(contract, "workforce_endgame")
    event_paths = [
        _string(b2.get("event_file"), "b2.event_file"),
        *_strings(workforce.get("event_shards"), "workforce_endgame.event_shards"),
        *(
            _string(_dependency(contract, owner).get("event_file"), f"{owner}.event_file")
            for owner in ("normal_exit", "probation", "rehire")
        ),
    ]
    references: set[str] = set()
    event_count = 0
    for relative in event_paths:
        _data, blocks = _blocks(root / PurePosixPath(relative), relative)
        event_count += len(blocks)
        for block in blocks:
            text = _mask_comments_and_strings(block.data.decode("utf-8-sig"))
            references.update(LOC_EVENT_KEY_RE.findall(text))
    expected_events = _integer(
        _mapping(contract.get("candidate"), "candidate").get(
            "expected_selected_event_count"
        ),
        "candidate.expected_selected_event_count",
    )
    if event_count != expected_events:
        raise B2ClosureError(
            f"selected event definition count changed: {event_count} != {expected_events}"
        )

    definition_owners: dict[str, set[str]] = {}
    loc_root = root / "localization" / "simp_chinese"
    for path in sorted(loc_root.glob("*.yml")):
        relative = path.relative_to(root).as_posix()
        for key in LOC_DEF_RE.findall(path.read_text(encoding="utf-8-sig")):
            definition_owners.setdefault(key, set()).add(relative)
    missing = sorted(key for key in references if key not in definition_owners)
    duplicates = {
        key: sorted(owners)
        for key, owners in definition_owners.items()
        if key in references and len(owners) != 1
    }
    expected_loc_counts: dict[str, int] = {
        _string(b2.get("localization_file"), "b2.localization_file"): 35,
        _string(workforce.get("localization_file"), "workforce_endgame.localization_file"): _integer(
            workforce.get("referenced_localization_keys"),
            "workforce_endgame.referenced_localization_keys",
        ),
    }
    for owner in ("normal_exit", "probation", "rehire"):
        row = _dependency(contract, owner)
        expected_loc_counts[_string(row.get("localization_file"), f"{owner}.localization_file")] = _integer(
            row.get("referenced_localization_keys"),
            f"{owner}.referenced_localization_keys",
        )
    actual_loc_counts = {
        path: sum(
            1
            for key in references
            if definition_owners.get(key) == {path}
        )
        for path in expected_loc_counts
    }
    unexpected_owners = sorted(
        {
            owner
            for key in references
            for owner in definition_owners.get(key, set())
        }
        - set(expected_loc_counts)
    )
    if missing or duplicates or actual_loc_counts != expected_loc_counts or unexpected_owners:
        raise B2ClosureError(
            "Simplified Chinese localization closure drifted: "
            f"missing={missing}, duplicates={duplicates}, "
            f"counts={actual_loc_counts}/{expected_loc_counts}, "
            f"unexpected_owners={unexpected_owners}"
        )
    return {
        "status": "GREEN",
        "event_definitions": event_count,
        "referenced_keys": len(references),
        "owner_counts": actual_loc_counts,
        "missing": missing,
        "duplicate_owners": duplicates,
    }


def tree_rows(root: Path) -> list[dict[str, object]]:
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]


def verify_baseline_identity(
    contract: Mapping[str, Any], baseline_root: Path
) -> tuple[Path, Path, str, dict[str, object]]:
    baseline = _mapping(contract.get("baseline"), "baseline")
    source = baseline_root / "source"
    manifest = baseline_root / "projection.json"
    projection = _string(baseline.get("projection"), "baseline.projection")
    if not source.is_dir() or not manifest.is_file():
        raise B2ClosureError(
            f"frozen B1 baseline is missing: source={source}, manifest={manifest}"
        )
    expected_manifest_sha = _string(
        baseline.get("manifest_sha256"), "baseline.manifest_sha256"
    ).lower()
    observed_manifest_sha = sha256_file(manifest)
    if observed_manifest_sha != expected_manifest_sha:
        raise B2ClosureError(
            f"frozen B1 manifest SHA changed: {observed_manifest_sha} != {expected_manifest_sha}"
        )
    spec = load_projection(source, projection_name=projection, manifest_path=manifest)
    expected = {
        "source_tree_sha256": _string(
            baseline.get("source_tree_sha256"), "baseline.source_tree_sha256"
        ).lower(),
        "formal_overlay_tree_sha256": _string(
            baseline.get("formal_overlay_tree_sha256"),
            "baseline.formal_overlay_tree_sha256",
        ).lower(),
        "file_list_sha256": _string(
            baseline.get("file_list_sha256"), "baseline.file_list_sha256"
        ).lower(),
    }
    observed = {
        "source_tree_sha256": spec.source_tree_sha256,
        "formal_overlay_tree_sha256": spec.formal_overlay_tree_sha256,
        "file_list_sha256": spec.file_list_sha256,
    }
    if observed != expected:
        raise B2ClosureError(
            f"frozen B1 projection identity changed: observed={observed}, expected={expected}"
        )
    expected_count = _integer(baseline.get("file_count"), "baseline.file_count")
    if len(spec.entries) != expected_count:
        raise B2ClosureError(
            f"frozen B1 projection file count changed: {len(spec.entries)} != {expected_count}"
        )
    return source, manifest, projection, {
        "status": "GREEN",
        "manifest_sha256": observed_manifest_sha,
        "file_count": len(spec.entries),
        **observed,
    }


def validate_output_location(
    output: Path, canonical_source: Path, baseline_root: Path
) -> None:
    """Reject any output path that can overlap either authoritative input."""

    protected = (
        ("canonical mod source", canonical_source),
        ("frozen B1 baseline root", baseline_root),
    )
    for label, root in protected:
        if output == root or output in root.parents or root in output.parents:
            raise B2ClosureError(
                "output must be disjoint from the "
                f"{label} (not the same path or an ancestor/descendant): "
                f"output={output}, protected={root}"
            )


def copy_overlay(
    canonical_source: Path,
    candidate_source: Path,
    paths: Sequence[str],
    forbidden_paths: Sequence[str],
) -> list[dict[str, object]]:
    baseline_paths = {
        path.relative_to(candidate_source).as_posix()
        for path in candidate_source.rglob("*")
        if path.is_file()
    }
    overlap = sorted(baseline_paths.intersection(paths))
    if overlap:
        raise B2ClosureError(f"closure overlay collides with frozen B1 files: {overlap}")
    for relative in forbidden_paths:
        if (canonical_source / PurePosixPath(relative)).exists():
            raise B2ClosureError(f"canonical tree still contains forbidden legacy monolith: {relative}")
    rows: list[dict[str, object]] = []
    for relative in paths:
        source = canonical_source / PurePosixPath(relative)
        if not source.is_file() or source.is_symlink():
            raise B2ClosureError(f"canonical closure source is missing or symlinked: {source}")
        data = source.read_bytes()
        target = candidate_source / PurePosixPath(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        rows.append(
            {"path": relative, "bytes": len(data), "sha256": sha256_bytes(data)}
        )
    for relative in forbidden_paths:
        if (candidate_source / PurePosixPath(relative)).exists():
            raise B2ClosureError(f"candidate contains forbidden legacy monolith: {relative}")
    return rows


def materialize(
    *,
    output: Path,
    projection_name: str,
    contract_path: Path = CONTRACT_PATH,
    baseline_root: Path | None = None,
    canonical_source: Path = MOD_ROOT,
) -> dict[str, Any]:
    output = output.resolve()
    canonical_source = canonical_source.resolve()
    contract_path = contract_path.resolve()
    contract = load_contract(contract_path)
    baseline = _mapping(contract.get("baseline"), "baseline")
    if baseline_root is None:
        baseline_root = ROOT / _relative(
            _string(baseline.get("root"), "baseline.root"), "baseline.root"
        )
    baseline_root = baseline_root.resolve()
    # This must precede every existence check that could later lead to mkdir:
    # a fresh descendant of either authority would otherwise look safe.
    validate_output_location(output, canonical_source, baseline_root)
    if output.exists():
        raise B2ClosureError(f"output already exists; use a fresh attempt path: {output}")
    if not canonical_source.is_dir():
        raise B2ClosureError(f"canonical mod source is missing: {canonical_source}")
    if not projection_name.strip() or any(char in projection_name for char in "/\\\x00"):
        raise B2ClosureError(f"projection name is malformed: {projection_name!r}")

    selection_check = validate_generator_selection(contract)
    declared_overlay_paths = overlay_paths(contract)
    forbidden_paths = tuple(
        _relative(path, "forbidden path")
        for path in _strings(contract.get("forbidden_paths"), "forbidden_paths")
    )
    baseline_source, baseline_manifest, baseline_projection, baseline_identity = verify_baseline_identity(
        contract, baseline_root
    )

    output.mkdir(parents=True)
    candidate_source = output / "source"
    baseline_receipt = materialize_projection(
        baseline_source,
        candidate_source,
        projection_name=baseline_projection,
        manifest_path=baseline_manifest,
    )
    expected_baseline_bytes = _integer(baseline.get("bytes"), "baseline.bytes")
    if (
        baseline_receipt["file_count"] != baseline["file_count"]
        or baseline_receipt["bytes"] != expected_baseline_bytes
    ):
        raise B2ClosureError(
            "frozen B1 materialization size changed: "
            f"files={baseline_receipt['file_count']}, bytes={baseline_receipt['bytes']}"
        )
    write_json(output / "baseline-materialization.json", baseline_receipt)

    overlay_rows = copy_overlay(
        canonical_source, candidate_source, declared_overlay_paths, forbidden_paths
    )
    candidate_contract = _mapping(contract.get("candidate"), "candidate")
    expected_file_count = _integer(
        candidate_contract.get("expected_file_count"), "candidate.expected_file_count"
    )
    observed_source_rows = tree_rows(candidate_source)
    if len(observed_source_rows) != expected_file_count:
        raise B2ClosureError(
            f"candidate file count changed: {len(observed_source_rows)} != {expected_file_count}"
        )

    checks = {
        "generator_selection": selection_check,
        "baseline_identity": baseline_identity,
        "file_boundaries": validate_file_boundaries(candidate_source, contract),
        "dependency_fixed_point": validate_dependency_closure(candidate_source, contract),
        "whole_file_callable_closure": validate_whole_file_callable_closure(candidate_source),
        "simp_chinese_localization": validate_localization(candidate_source, contract),
        "bom_braces_no_stubs": validate_bom_braces_and_stubs(candidate_source, contract),
    }

    projection_path = output / "projection.json"
    manifest = write_manifest(
        candidate_source, projection_path, projection_name=projection_name
    )
    if len(manifest["files"]) != expected_file_count:
        raise B2ClosureError("candidate projection manifest file count changed")
    # Load before either final copy so all bytes/SHA rows and aggregate hashes
    # are proven before the launchable product directory is created.
    load_projection(
        candidate_source,
        projection_name=projection_name,
        manifest_path=projection_path,
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
    write_json(output / "materialization.json", receipt)
    write_json(output / "materialization-replay.json", replay_receipt)
    product_rows = tree_rows(product)
    replay_rows = tree_rows(replay)
    stable = observed_source_rows == product_rows == replay_rows
    if not stable:
        raise B2ClosureError("candidate source/product/replay byte rows are not identical")
    checks["deterministic_materialization"] = {
        "status": "GREEN",
        "source_equals_product": observed_source_rows == product_rows,
        "source_equals_replay": observed_source_rows == replay_rows,
        "file_count": len(product_rows),
    }

    contract_copy = output / "closure-contract.json"
    shutil.copy2(contract_path, contract_copy)
    preflight: dict[str, Any] = {
        "schema_version": 1,
        "kind": "zg361_phase2_b2_production_closure_preflight",
        "status": "GREEN_STATIC",
        "no_stubs": True,
        "production_candidate": True,
        "feature_or_runtime_certification": False,
        "canonical_source_modified": False,
        "projection": projection_name,
        "candidate": {
            "source": str(candidate_source),
            "product": str(product),
            "materialized_check": str(replay),
            "file_count": len(product_rows),
            "bytes": sum(int(row["bytes"]) for row in product_rows),
            "source_tree_sha256": manifest["source_tree_sha256"],
            "formal_overlay_tree_sha256": manifest["formal_overlay_tree_sha256"],
            "file_list_sha256": manifest["file_list_sha256"],
            "projection_manifest": str(projection_path),
            "projection_manifest_sha256": sha256_file(projection_path),
        },
        "baseline": {
            "root": str(baseline_root),
            **baseline_identity,
        },
        "overlay": {
            "canonical_source": str(canonical_source),
            "file_count": len(overlay_rows),
            "bytes": sum(int(row["bytes"]) for row in overlay_rows),
            "files": overlay_rows,
        },
        "contract": {
            "path": str(contract_copy),
            "sha256": sha256_file(contract_copy),
        },
        "checks": checks,
        "runtime": {
            "ck3_launch": "NOT_RUN",
            "live_status": "pending",
            "next_distinct_gate": "full-entry before seed",
        },
        "limits": [
            "This builder performs no CK3 launch and cannot create live evidence.",
            "GREEN_STATIC proves file identity and scripted closure, not gameplay semantics.",
            "The next authorized runtime action is one distinct full-entry run on this exact projection/hash; seed follows only after GREEN.",
        ],
    }
    write_json(output / "preflight.json", preflight)
    return preflight


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--projection-name",
        default="phase2-b2-production-closure-20260904-r1",
    )
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument(
        "--baseline-root",
        type=Path,
        help="override only the host location of the exact hash-bound B1 freeze",
    )
    parser.add_argument("--canonical-source", type=Path, default=MOD_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = materialize(
            output=args.output,
            projection_name=args.projection_name,
            contract_path=args.contract,
            baseline_root=args.baseline_root,
            canonical_source=args.canonical_source,
        )
    except (B2ClosureError, ProductProjectionError, OSError, UnicodeError, ValueError) as error:
        print(f"B2 production closure materialization failed: {error}")
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
