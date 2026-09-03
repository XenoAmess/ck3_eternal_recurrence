#!/usr/bin/env python3
"""Materialize the no-stub production X-incident closure over frozen B2 r2.

The builder copies only the 119 hash-bound baseline rows, then overlays eleven
purpose-oriented incident effect shards, four X-only event shards, and the
Simplified Chinese localization owner.  It performs static checks and two
deterministic materializations; it never launches CK3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
from typing import Any, Mapping, Sequence

import zg361_phase2_b2_closure_candidate as closure_utils
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
    "zg361_phase2_incident_x_production_closure.json"
)
BOM = b"\xef\xbb\xbf"
EVENT_ABI_RE = re.compile(
    r"\bEVENT\s*=\s*((?:zg361[a-z0-9_]*|zg361)\.\d+)\b"
)
INCIDENT_LOC_REF_RE = re.compile(
    r"\b(?:title|desc|name)\s*=\s*(zg361ip\.[A-Za-z0-9_.-]+)\b"
)

if str(MOD_TOOLS) not in sys.path:
    sys.path.insert(0, str(MOD_TOOLS))

import gen_361_incident_platform_runtime as incident_generator


class IncidentXClosureError(ValueError):
    """The incident-X closure is incomplete, stale, or non-reproducible."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
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
        raise IncidentXClosureError(f"{label} must be an object")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IncidentXClosureError(f"{label} must be a non-empty string")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise IncidentXClosureError(f"{label} must be a non-negative integer")
    return value


def _strings(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise IncidentXClosureError(f"{label} must be a list of non-empty strings")
    rows = tuple(value)
    if len(rows) != len(set(rows)):
        raise IncidentXClosureError(f"{label} contains duplicate values")
    return rows


def _relative(value: str, label: str) -> str:
    raw = value.replace("\\", "/")
    path = PurePosixPath(raw)
    if (
        path.is_absolute()
        or raw.startswith("//")
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise IncidentXClosureError(
            f"{label} must be a normalized relative path: {value!r}"
        )
    return path.as_posix()


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise IncidentXClosureError(
            f"cannot read incident-X closure contract {path}: {error}"
        ) from error
    if not isinstance(payload, dict):
        raise IncidentXClosureError("incident-X closure contract root must be an object")
    if payload.get("schema_version") != 1:
        raise IncidentXClosureError("incident-X closure contract schema_version must be 1")
    if payload.get("kind") != "zg361_phase2_incident_x_production_closure":
        raise IncidentXClosureError("unexpected incident-X closure contract kind")
    return payload


def _incident(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(contract.get("incident"), "incident")


def _case_kernel(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    dependencies = _mapping(contract.get("dependencies"), "dependencies")
    return _mapping(dependencies.get("case_kernel"), "dependencies.case_kernel")


def overlay_paths(contract: Mapping[str, Any]) -> tuple[str, ...]:
    incident = _incident(contract)
    paths = (
        *_strings(incident.get("effect_shards"), "incident.effect_shards"),
        *_strings(incident.get("event_shards"), "incident.event_shards"),
        _string(incident.get("localization_file"), "incident.localization_file"),
    )
    normalized = tuple(_relative(path, "overlay path") for path in paths)
    if len(normalized) != len(set(normalized)):
        raise IncidentXClosureError("incident overlay contains duplicate paths")
    expected = _integer(
        _mapping(contract.get("candidate"), "candidate").get(
            "expected_overlay_file_count"
        ),
        "candidate.expected_overlay_file_count",
    )
    if len(normalized) != expected:
        raise IncidentXClosureError(
            f"incident overlay file count changed: {len(normalized)} != {expected}"
        )
    return normalized


def _selected_generator_groups() -> tuple[
    tuple[incident_generator.EffectGroup, ...],
    tuple[incident_generator.EventGroup, ...],
]:
    production_names = set(incident_generator.X_EFFECT_CLOSURE_NAMES) | {
        "zg361_ip_consume_due_kpi_inputs_effect"
    }
    effect_groups = tuple(
        group
        for group in incident_generator.EFFECT_GROUPS
        if production_names.intersection(group.effect_names)
    )
    event_ids = set(incident_generator.X_EVENT_CLOSURE_IDS)
    event_groups = tuple(
        group
        for group in incident_generator.EVENT_GROUPS
        if event_ids.intersection(group.event_ids)
    )
    return effect_groups, event_groups


def validate_generator_selection(
    contract: Mapping[str, Any], canonical_source: Path = MOD_ROOT
) -> dict[str, object]:
    incident = _incident(contract)
    candidate = _mapping(contract.get("candidate"), "candidate")

    # These calls independently enforce the generator's 124/124 and 54/54
    # purpose maps and byte-identical block reconstruction.
    effect_parts = incident_generator.render_effect_parts()
    event_parts = incident_generator.render_event_parts()
    historical_effects = dict(
        incident_generator.top_level_blocks(incident_generator.render_effects())
    )
    emitted_effects = {
        name: body
        for payload in effect_parts.values()
        for name, body in incident_generator.top_level_blocks(payload)
    }
    historical_events = dict(
        incident_generator.top_level_blocks(incident_generator.render_events())
    )
    emitted_events = {
        name: body
        for payload in event_parts.values()
        for name, body in incident_generator.top_level_blocks(payload)
    }
    if emitted_effects != historical_effects or len(historical_effects) != 124:
        raise IncidentXClosureError("incident effect purpose map lost block-byte parity")
    if emitted_events != historical_events or len(historical_events) != 54:
        raise IncidentXClosureError("incident event purpose map lost block-byte parity")

    effect_groups, event_groups = _selected_generator_groups()
    generated_effect_paths = tuple(
        f"common/scripted_effects/{group.filename}" for group in effect_groups
    )
    generated_event_paths = tuple(
        f"events/{group.filename}" for group in event_groups
    )
    declared_effect_paths = _strings(
        incident.get("effect_shards"), "incident.effect_shards"
    )
    declared_event_paths = _strings(
        incident.get("event_shards"), "incident.event_shards"
    )
    if generated_effect_paths != declared_effect_paths:
        raise IncidentXClosureError(
            "incident effect shard selection drifted from generator: "
            f"missing={sorted(set(generated_effect_paths) - set(declared_effect_paths))}, "
            f"extra={sorted(set(declared_effect_paths) - set(generated_effect_paths))}"
        )
    if generated_event_paths != declared_event_paths:
        raise IncidentXClosureError(
            "incident event shard selection drifted from generator: "
            f"missing={sorted(set(generated_event_paths) - set(declared_event_paths))}, "
            f"extra={sorted(set(declared_event_paths) - set(generated_event_paths))}"
        )

    fixture_expected = set(
        _strings(
            incident.get("fixture_reachable_effects"),
            "incident.fixture_reachable_effects",
        )
    )
    production_expected = fixture_expected | set(
        _strings(
            incident.get("production_only_effects"),
            "incident.production_only_effects",
        )
    )
    selected_names = {
        name for group in effect_groups for name in group.effect_names
    }
    selected_event_ids = {
        event_id for group in event_groups for event_id in group.event_ids
    }
    expected_event_ids = {
        int(event.removeprefix("zg361ip."))
        for event in _strings(incident.get("reachable_events"), "incident.reachable_events")
    }
    if fixture_expected != set(incident_generator.X_EFFECT_CLOSURE_NAMES):
        raise IncidentXClosureError("contract fixture effect closure drifted from generator")
    if selected_names != production_expected:
        raise IncidentXClosureError(
            "selected incident effect shards are not the exact production closure: "
            f"missing={sorted(production_expected - selected_names)}, "
            f"extra={sorted(selected_names - production_expected)}"
        )
    if selected_event_ids != expected_event_ids or expected_event_ids != set(
        incident_generator.X_EVENT_CLOSURE_IDS
    ):
        raise IncidentXClosureError(
            "selected incident event shards are not the exact X closure: "
            f"missing={sorted(expected_event_ids - selected_event_ids)}, "
            f"extra={sorted(selected_event_ids - expected_event_ids)}"
        )

    expected_counts = {
        "effect_shards": _integer(
            candidate.get("expected_incident_effect_shards"),
            "candidate.expected_incident_effect_shards",
        ),
        "event_shards": _integer(
            candidate.get("expected_incident_event_shards"),
            "candidate.expected_incident_event_shards",
        ),
        "effects": _integer(
            candidate.get("expected_incident_effect_definitions"),
            "candidate.expected_incident_effect_definitions",
        ),
        "events": _integer(
            candidate.get("expected_incident_event_definitions"),
            "candidate.expected_incident_event_definitions",
        ),
    }
    observed_counts = {
        "effect_shards": len(effect_groups),
        "event_shards": len(event_groups),
        "effects": len(selected_names),
        "events": len(selected_event_ids),
    }
    if observed_counts != expected_counts:
        raise IncidentXClosureError(
            f"incident generator selection counts drifted: {observed_counts} != {expected_counts}"
        )

    expected_payloads = {
        **{
            f"common/scripted_effects/{name}": payload
            for name, payload in effect_parts.items()
            if f"common/scripted_effects/{name}" in generated_effect_paths
        },
        **{
            f"events/{name}": payload
            for name, payload in event_parts.items()
            if f"events/{name}" in generated_event_paths
        },
        _string(incident.get("localization_file"), "incident.localization_file"):
            incident_generator.render_localization("simp_chinese"),
    }
    stale = []
    for relative, payload in expected_payloads.items():
        path = canonical_source / PurePosixPath(relative)
        if not path.is_file() or path.read_bytes() != payload:
            stale.append(relative)
    if stale:
        raise IncidentXClosureError(
            f"canonical incident generator outputs are stale: {sorted(stale)}"
        )

    return {
        "status": "GREEN",
        "historical_effect_blocks": len(historical_effects),
        "historical_event_blocks": len(historical_events),
        "incident_effect_shards": len(effect_groups),
        "fixture_incident_effects": len(fixture_expected),
        "production_incident_effects": len(selected_names),
        "incident_event_shards": len(event_groups),
        "incident_events": len(selected_event_ids),
        "extra_effects": [],
        "missing_effects": [],
        "extra_events": [],
        "missing_events": [],
    }


def verify_baseline_identity(
    contract: Mapping[str, Any], baseline_root: Path
) -> tuple[Path, Path, str, dict[str, object]]:
    baseline = _mapping(contract.get("baseline"), "baseline")
    source = baseline_root / "source"
    manifest_path = baseline_root / "projection.json"
    projection = _string(baseline.get("projection"), "baseline.projection")
    if not source.is_dir() or not manifest_path.is_file():
        raise IncidentXClosureError(
            f"frozen B2 r2 baseline is missing: source={source}, manifest={manifest_path}"
        )
    expected_manifest_sha = _string(
        baseline.get("manifest_sha256"), "baseline.manifest_sha256"
    ).lower()
    observed_manifest_sha = sha256_file(manifest_path)
    if observed_manifest_sha != expected_manifest_sha:
        raise IncidentXClosureError(
            f"frozen B2 r2 manifest SHA changed: {observed_manifest_sha} != {expected_manifest_sha}"
        )
    try:
        spec = load_projection(
            source, projection_name=projection, manifest_path=manifest_path
        )
    except ProductProjectionError as error:
        raise IncidentXClosureError(str(error)) from error
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
    expected_count = _integer(baseline.get("file_count"), "baseline.file_count")
    if observed != expected or len(spec.entries) != expected_count:
        raise IncidentXClosureError(
            "frozen B2 r2 projection identity changed: "
            f"observed={observed}, expected={expected}, "
            f"files={len(spec.entries)}/{expected_count}"
        )
    return source, manifest_path, projection, {
        "status": "GREEN",
        "manifest_sha256": observed_manifest_sha,
        "file_count": len(spec.entries),
        **observed,
    }


def validate_output_location(
    output: Path, canonical_source: Path, baseline_root: Path
) -> None:
    for label, protected in (
        ("canonical mod source", canonical_source),
        ("frozen B2 baseline root", baseline_root),
    ):
        if output == protected or output in protected.parents or protected in output.parents:
            raise IncidentXClosureError(
                "output must be disjoint from the "
                f"{label} (not the same path or an ancestor/descendant): "
                f"output={output}, protected={protected}"
            )


def _wrap_closure_error(callback: Any, *args: object) -> Any:
    try:
        return callback(*args)
    except (closure_utils.B2ClosureError, ProductProjectionError) as error:
        raise IncidentXClosureError(str(error)) from error


def validate_file_boundaries(
    root: Path, contract: Mapping[str, Any]
) -> dict[str, object]:
    candidate = _mapping(contract.get("candidate"), "candidate")
    target = _integer(candidate.get("effect_target_per_file"), "effect target")
    hard_max = _integer(candidate.get("effect_hard_max_per_file"), "effect hard max")
    effect_groups, event_groups = _selected_generator_groups()
    effect_rows: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []
    over_target: list[str] = []
    over_hard: list[str] = []
    for group in effect_groups:
        relative = f"common/scripted_effects/{group.filename}"
        data, blocks = _wrap_closure_error(
            closure_utils._blocks, root / PurePosixPath(relative), relative
        )
        names = tuple(block.name for block in blocks)
        if names != group.effect_names:
            raise IncidentXClosureError(
                f"incident effect shard inventory drifted in {relative}"
            )
        if not names:
            raise IncidentXClosureError(f"empty incident effect shard: {relative}")
        if len(names) > target:
            over_target.append(relative)
        if len(names) > hard_max:
            over_hard.append(relative)
        effect_rows.append(
            {
                "path": relative,
                "definitions": len(names),
                "target_1_to_10": len(names) <= target,
                "hard_max_20": len(names) <= hard_max,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    for group in event_groups:
        relative = f"events/{group.filename}"
        data, blocks = _wrap_closure_error(
            closure_utils._blocks, root / PurePosixPath(relative), relative
        )
        names = tuple(block.name for block in blocks)
        expected_names = tuple(f"zg361ip.{event_id}" for event_id in group.event_ids)
        if names != expected_names:
            raise IncidentXClosureError(
                f"incident event shard inventory drifted in {relative}"
            )
        if not names or len(names) > hard_max:
            raise IncidentXClosureError(
                f"incident event shard violates 1-{hard_max}: {relative}"
            )
        event_rows.append(
            {
                "path": relative,
                "definitions": len(names),
                "target_1_to_10": len(names) <= target,
                "hard_max_20": len(names) <= hard_max,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    if over_hard:
        raise IncidentXClosureError(
            f"candidate incident effect shards exceed hard maximum {hard_max}: {over_hard}"
        )
    if incident_generator.EFFECT_HARD_LIMIT_EXCEPTIONS:
        raise IncidentXClosureError("incident effect hard-limit exceptions must remain empty")
    expected_effects = _integer(
        candidate.get("expected_incident_effect_definitions"),
        "candidate.expected_incident_effect_definitions",
    )
    expected_events = _integer(
        candidate.get("expected_incident_event_definitions"),
        "candidate.expected_incident_event_definitions",
    )
    if sum(int(row["definitions"]) for row in effect_rows) != expected_effects:
        raise IncidentXClosureError("candidate incident effect definition count drifted")
    if sum(int(row["definitions"]) for row in event_rows) != expected_events:
        raise IncidentXClosureError("candidate incident event definition count drifted")
    return {
        "status": "GREEN",
        "target": target,
        "hard_max": hard_max,
        "incident_effects": effect_rows,
        "incident_events": event_rows,
        "target_exceptions": [],
        "over_target": over_target,
        "over_hard_max": over_hard,
    }


def _expected_effects(
    contract: Mapping[str, Any], *, production: bool
) -> set[str]:
    incident = _incident(contract)
    result = set(
        _strings(
            incident.get("fixture_reachable_effects"),
            "incident.fixture_reachable_effects",
        )
    )
    result.update(
        _strings(
            _case_kernel(contract).get("reachable_effects"),
            "case_kernel.reachable_effects",
        )
    )
    if production:
        result.update(
            _strings(
                incident.get("production_only_effects"),
                "incident.production_only_effects",
            )
        )
    return result


def validate_dependency_closures(
    root: Path, contract: Mapping[str, Any]
) -> dict[str, object]:
    effect_providers, effect_duplicates = _wrap_closure_error(
        closure_utils._provider_map, root, (Path("common/scripted_effects"),)
    )
    event_providers, event_duplicates = _wrap_closure_error(
        closure_utils._provider_map, root, (Path("events"),)
    )
    callable_providers, callable_duplicates = _wrap_closure_error(
        closure_utils._provider_map, root, closure_utils.CALLABLE_DIRS
    )
    if effect_duplicates or event_duplicates or callable_duplicates:
        raise IncidentXClosureError(
            "duplicate providers: "
            f"effects={effect_duplicates}, events={event_duplicates}, "
            f"callables={callable_duplicates}"
        )

    candidate = _mapping(contract.get("candidate"), "candidate")
    expected_events = set(
        _strings(_incident(contract).get("reachable_events"), "incident.reachable_events")
    )
    rows: dict[str, dict[str, object]] = {}
    closures: dict[str, tuple[set[str], set[str]]] = {}
    for label, roots_key, production, count_key in (
        ("fixture", "fixture_root_effects", False, "expected_fixture_effect_closure_count"),
        ("production", "production_root_effects", True, "expected_production_effect_closure_count"),
    ):
        roots = _strings(contract.get(roots_key), roots_key)
        effects, events, missing_effects, missing_events = _wrap_closure_error(
            closure_utils.dependency_fixed_point,
            effect_providers,
            event_providers,
            roots,
        )
        expected_effects = _expected_effects(contract, production=production)
        expected_count = _integer(candidate.get(count_key), f"candidate.{count_key}")
        expected_event_count = _integer(
            candidate.get("expected_event_closure_count"),
            "candidate.expected_event_closure_count",
        )
        if missing_effects or missing_events:
            raise IncidentXClosureError(
                f"{label} dependency closure unresolved: "
                f"effects={sorted(missing_effects)}, events={sorted(missing_events)}"
            )
        if (
            effects != expected_effects
            or events != expected_events
            or len(effects) != expected_count
            or len(events) != expected_event_count
        ):
            raise IncidentXClosureError(
                f"{label} dependency fixed point drifted: "
                f"effect_missing={sorted(expected_effects - effects)}, "
                f"effect_extra={sorted(effects - expected_effects)}, "
                f"event_missing={sorted(expected_events - events)}, "
                f"event_extra={sorted(events - expected_events)}"
            )
        closures[label] = (effects, events)
        rows[label] = {
            "root_effects": list(roots),
            "effects": len(effects),
            "events": len(events),
            "effect_names": sorted(effects),
            "event_ids": sorted(events),
        }

    production_effects, production_events = closures["production"]
    referenced_triggers: set[str] = set()
    for name in sorted(production_effects):
        _effects, _events, callables = closure_utils.block_references(
            effect_providers[name]
        )
        referenced_triggers.update(
            callable_name
            for callable_name in callables
            if callable_name.endswith("_trigger")
        )
    for name in sorted(production_events):
        _effects, _events, callables = closure_utils.block_references(
            event_providers[name]
        )
        referenced_triggers.update(
            callable_name
            for callable_name in callables
            if callable_name.endswith("_trigger")
        )
    expected_triggers = set(
        _strings(
            _case_kernel(contract).get("reachable_triggers"),
            "case_kernel.reachable_triggers",
        )
    )
    missing_trigger_providers = sorted(referenced_triggers - set(callable_providers))
    expected_trigger_count = _integer(
        candidate.get("expected_trigger_closure_count"),
        "candidate.expected_trigger_closure_count",
    )
    if (
        referenced_triggers != expected_triggers
        or missing_trigger_providers
        or len(referenced_triggers) != expected_trigger_count
    ):
        raise IncidentXClosureError(
            "incident trigger closure drifted: "
            f"missing={sorted(expected_triggers - referenced_triggers)}, "
            f"extra={sorted(referenced_triggers - expected_triggers)}, "
            f"missing_providers={missing_trigger_providers}"
        )
    return {
        "status": "GREEN",
        "fixture": rows["fixture"],
        "production": rows["production"],
        "triggers": {
            "count": len(referenced_triggers),
            "names": sorted(referenced_triggers),
            "missing_providers": [],
        },
    }


def validate_whole_file_callable_closure(root: Path) -> dict[str, object]:
    result = _wrap_closure_error(
        closure_utils.validate_whole_file_callable_closure, root
    )
    incident_abi_ids: set[str] = set()
    effect_groups, _event_groups = _selected_generator_groups()
    for group in effect_groups:
        path = root / "common" / "scripted_effects" / group.filename
        text = closure_utils._mask_comments_and_strings(
            path.read_text(encoding="utf-8-sig")
        )
        incident_abi_ids.update(EVENT_ABI_RE.findall(text))
    expected = {f"zg361ip.{event_id}" for event_id in range(102, 108)}
    if incident_abi_ids != expected:
        raise IncidentXClosureError(
            "incident EVENT parameter ABI drifted: "
            f"missing={sorted(expected - incident_abi_ids)}, "
            f"extra={sorted(incident_abi_ids - expected)}"
        )
    return {
        **result,
        "incident_event_parameter_abi_ids": sorted(incident_abi_ids),
    }


def validate_localization(
    root: Path, contract: Mapping[str, Any]
) -> dict[str, object]:
    incident = _incident(contract)
    references: set[str] = set()
    event_count = 0
    for relative in _strings(incident.get("event_shards"), "incident.event_shards"):
        _data, blocks = _wrap_closure_error(
            closure_utils._blocks, root / PurePosixPath(relative), relative
        )
        event_count += len(blocks)
        for block in blocks:
            text = closure_utils._mask_comments_and_strings(
                block.data.decode("utf-8-sig")
            )
            references.update(INCIDENT_LOC_REF_RE.findall(text))
    expected_references = set(
        _strings(
            incident.get("referenced_localization_keys"),
            "incident.referenced_localization_keys",
        )
    )
    if references != expected_references:
        raise IncidentXClosureError(
            "incident Simplified Chinese localization references drifted: "
            f"missing={sorted(expected_references - references)}, "
            f"extra={sorted(references - expected_references)}"
        )
    owners: dict[str, set[str]] = {}
    for path in sorted((root / "localization" / "simp_chinese").glob("*.yml")):
        relative = path.relative_to(root).as_posix()
        for key in closure_utils.LOC_DEF_RE.findall(
            path.read_text(encoding="utf-8-sig")
        ):
            owners.setdefault(key, set()).add(relative)
    expected_owner = _string(
        incident.get("localization_file"), "incident.localization_file"
    )
    missing = sorted(key for key in references if key not in owners)
    duplicate_owners = {
        key: sorted(owners[key])
        for key in references
        if len(owners.get(key, set())) > 1
    }
    wrong_owners = {
        key: sorted(owners.get(key, set()))
        for key in references
        if owners.get(key) != {expected_owner}
    }
    expected_events = _integer(
        _mapping(contract.get("candidate"), "candidate").get(
            "expected_incident_event_definitions"
        ),
        "candidate.expected_incident_event_definitions",
    )
    if missing or duplicate_owners or wrong_owners or event_count != expected_events:
        raise IncidentXClosureError(
            "incident Simplified Chinese localization closure failed: "
            f"missing={missing}, duplicates={duplicate_owners}, "
            f"wrong_owners={wrong_owners}, events={event_count}/{expected_events}"
        )
    return {
        "status": "GREEN",
        "event_definitions": event_count,
        "referenced_keys": len(references),
        "keys": sorted(references),
        "owner": expected_owner,
        "owner_counts": {expected_owner: len(references)},
        "missing": [],
        "duplicate_owners": {},
    }


def validate_bom_braces_and_stubs(
    root: Path, contract: Mapping[str, Any]
) -> dict[str, object]:
    result = _wrap_closure_error(
        closure_utils.validate_bom_braces_and_stubs, root, contract
    )
    forbidden_present = [
        relative
        for relative in _strings(contract.get("forbidden_paths"), "forbidden_paths")
        if (root / PurePosixPath(relative)).exists()
    ]
    if forbidden_present:
        raise IncidentXClosureError(
            f"candidate contains forbidden legacy monoliths: {forbidden_present}"
        )
    return {**result, "forbidden_paths_present": []}


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
        raise IncidentXClosureError(
            f"incident overlay collides with frozen B2 r2 files: {overlap}"
        )
    for relative in forbidden_paths:
        if (canonical_source / PurePosixPath(relative)).exists():
            raise IncidentXClosureError(
                f"canonical tree still contains forbidden legacy monolith: {relative}"
            )
    rows: list[dict[str, object]] = []
    for relative in paths:
        source = canonical_source / PurePosixPath(relative)
        if not source.is_file() or source.is_symlink():
            raise IncidentXClosureError(
                f"canonical incident closure source is missing or symlinked: {source}"
            )
        data = source.read_bytes()
        target = candidate_source / PurePosixPath(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        rows.append(
            {
                "path": relative,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
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
    # This gate precedes every mkdir and protects both immutable authorities.
    validate_output_location(output, canonical_source, baseline_root)
    if output.exists():
        raise IncidentXClosureError(
            f"output already exists; use a fresh named attempt path: {output}"
        )
    if not canonical_source.is_dir():
        raise IncidentXClosureError(
            f"canonical mod source is missing: {canonical_source}"
        )
    if not projection_name.strip() or any(char in projection_name for char in "/\\\x00"):
        raise IncidentXClosureError(
            f"projection name is malformed: {projection_name!r}"
        )

    selection_check = validate_generator_selection(contract, canonical_source)
    declared_overlay_paths = overlay_paths(contract)
    forbidden_paths = tuple(
        _relative(path, "forbidden path")
        for path in _strings(contract.get("forbidden_paths"), "forbidden_paths")
    )
    baseline_source, baseline_manifest, baseline_projection, baseline_identity = (
        verify_baseline_identity(contract, baseline_root)
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
        raise IncidentXClosureError(str(error)) from error
    if (
        baseline_receipt["file_count"]
        != _integer(baseline.get("file_count"), "baseline.file_count")
        or baseline_receipt["bytes"]
        != _integer(baseline.get("bytes"), "baseline.bytes")
    ):
        raise IncidentXClosureError("frozen B2 r2 materialization size changed")
    write_json(output / "baseline-materialization.json", baseline_receipt)

    overlay_rows = copy_overlay(
        canonical_source,
        candidate_source,
        declared_overlay_paths,
        forbidden_paths,
    )
    candidate_contract = _mapping(contract.get("candidate"), "candidate")
    expected_file_count = _integer(
        candidate_contract.get("expected_file_count"),
        "candidate.expected_file_count",
    )
    observed_source_rows = closure_utils.tree_rows(candidate_source)
    if len(observed_source_rows) != expected_file_count:
        raise IncidentXClosureError(
            f"candidate file count changed: {len(observed_source_rows)} != {expected_file_count}"
        )

    checks = {
        "generator_selection": selection_check,
        "baseline_identity": baseline_identity,
        "file_boundaries": validate_file_boundaries(candidate_source, contract),
        "dependency_closures": validate_dependency_closures(candidate_source, contract),
        "whole_file_callable_closure": validate_whole_file_callable_closure(candidate_source),
        "simp_chinese_localization": validate_localization(candidate_source, contract),
        "bom_braces_no_stubs": validate_bom_braces_and_stubs(candidate_source, contract),
    }

    projection_path = output / "projection.json"
    try:
        manifest = write_manifest(
            candidate_source, projection_path, projection_name=projection_name
        )
        if len(manifest["files"]) != expected_file_count:
            raise IncidentXClosureError(
                "incident-X candidate projection manifest file count changed"
            )
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
    except ProductProjectionError as error:
        raise IncidentXClosureError(str(error)) from error
    write_json(output / "materialization.json", receipt)
    write_json(output / "materialization-replay.json", replay_receipt)
    product_rows = closure_utils.tree_rows(product)
    replay_rows = closure_utils.tree_rows(replay)
    if observed_source_rows != product_rows or observed_source_rows != replay_rows:
        raise IncidentXClosureError(
            "incident-X candidate source/product/replay byte rows are not identical"
        )
    checks["deterministic_materialization"] = {
        "status": "GREEN",
        "source_equals_product": True,
        "source_equals_replay": True,
        "file_count": len(product_rows),
    }

    contract_copy = output / "closure-contract.json"
    shutil.copy2(contract_path, contract_copy)
    preflight: dict[str, Any] = {
        "schema_version": 1,
        "kind": "zg361_phase2_incident_x_production_closure_preflight",
        "status": "GREEN_STATIC",
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
            "file_count": len(product_rows),
            "bytes": sum(int(row["bytes"]) for row in product_rows),
            "source_tree_sha256": manifest["source_tree_sha256"],
            "formal_overlay_tree_sha256": manifest["formal_overlay_tree_sha256"],
            "file_list_sha256": manifest["file_list_sha256"],
            "projection_manifest": str(projection_path),
            "projection_manifest_sha256": sha256_file(projection_path),
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
        },
        "checks": checks,
        "ck3_launch": "NOT_RUN_BY_BUILDER",
        "runtime": {
            "ck3_launch": "NOT_RUN",
            "live_status": "pending",
        },
        "next_action": (
            "Run one separately authorized CK3 full-entry acceptance on this exact named projection/hash."
        ),
    }
    write_json(output / "preflight.json", preflight)
    return preflight


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "_runtime/phase2-incident-x-production-closure-20260904-r3",
    )
    parser.add_argument(
        "--projection-name",
        default="phase2-incident-x-production-closure-20260904-r3",
    )
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--baseline-root", type=Path)
    parser.add_argument("--canonical-source", type=Path, default=MOD_ROOT)
    args = parser.parse_args()
    try:
        preflight = materialize(
            output=args.output,
            projection_name=args.projection_name,
            contract_path=args.contract,
            baseline_root=args.baseline_root,
            canonical_source=args.canonical_source,
        )
    except IncidentXClosureError as error:
        print(f"RED: {error}")
        return 1
    candidate = preflight["candidate"]
    print(
        "GREEN_STATIC: incident-X production closure "
        f"{candidate['file_count']} files, {candidate['bytes']} bytes, "
        f"source SHA {candidate['source_tree_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
