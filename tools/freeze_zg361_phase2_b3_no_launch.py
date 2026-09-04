#!/usr/bin/env python3
"""Freeze one cumulative B3 product/native candidate without launching CK3."""

from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
NATIVE_ROOT = ROOT / "ck3_autonomous_player" / "native_bridge"
MOD_ROOT = ROOT / "mod_zhongguo_style"
EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_GAME_VERSION = "1.19.0.6"
EXPECTED_NATIVE_TESTS = 92
TARGET_EFFECT_MAX = 10
HARD_EFFECT_MAX = 20
EXPECTED_CASE_KERNEL_SHARDS = 39
CASE_KERNEL_SHARD_PATTERN = re.compile(
    r"^zg361_case_kernel_[0-9]{3}_.+_effects\.txt$"
)
REQUIRED_PROBATION_SHARDS = frozenset(
    {
        "zg361_workforce_probation_fact_consumption_effects.txt",
        "zg361_workforce_probation_fact_ledger_arm_effects.txt",
        "zg361_workforce_probation_fact_outcome_publish_effects.txt",
    }
)
FORBIDDEN_SPLIT_MONOLITHS = frozenset(
    {
        "zg361_case_kernel_effects.txt",
        "zg361_workforce_probation_fact_effects.txt",
    }
)
CENTRAL_ROOT_EFFECTS = ("zg361_p2c_stage_10_manager_governance_effect",)
REQUIRED_CENTRAL_EFFECT_PROVIDER_FILES = frozenset(
    {"zg361_phase2_central_003_dispatch_control_effects.txt"}
)
REQUIRED_CENTRAL_EVENT_PROVIDER_FILES = frozenset(
    {"zg361_phase2_central_001_serial_dispatch_events.txt"}
)
CUSTOM_EFFECT_CALL_RE = re.compile(r"\b(zg361_[A-Za-z0-9_]+_effect)\s*=")
CUSTOM_TRIGGER_CALL_RE = re.compile(r"\b(zg361_[A-Za-z0-9_]+_trigger)\s*=")
CUSTOM_TRIGGER_ARGUMENT_RE = re.compile(
    r"\b(?:TRIGGER|[A-Z][A-Z0-9_]*_TRIGGER)\s*=\s*"
    r"(zg361_[A-Za-z0-9_]+_trigger)\b"
)
CUSTOM_EVENT_ID_RE = re.compile(
    r"\b(?:id|EVENT)\s*=\s*(zg361[A-Za-z0-9_]*\.[0-9]+)\b"
)
CUSTOM_EVENT_DIRECT_CALL_RE = re.compile(
    r"\b(?:trigger_event|character_event|event)\s*=\s*"
    r"(zg361[A-Za-z0-9_]*\.[0-9]+)\b"
)
EXPECTED_PREDECESSOR_UNKNOWN_EFFECTS = frozenset(
    {"zg361_p2c_record_red_effect", "zg361_p2c_record_stage_effect"}
)
PREDECESSOR_CALLER_FILE = (
    "common/scripted_effects/"
    "zg361_phase2_central_008_stage10_manager_governance_effects.txt"
)
EXPECTED_EVENT_PREDECESSOR_MISSING_EVENTS = frozenset(
    {"zg361p2c.1", "zg361p2c.2"}
)
EVENT_PREDECESSOR_CALLER_FILE = (
    "common/scripted_effects/"
    "zg361_phase2_central_003_dispatch_control_effects.txt"
)
EXPECTED_PARAMETERIZED_EVENT_PREDECESSOR_MISSING_EVENTS = frozenset(
    {
        "zg361we.4804",
        "zg361cl.100",
        "zg361cl.101",
        "zg361cl.102",
        "zg361cl.103",
        "zg361cl.104",
        "zg361cl.105",
        "zg361cl.200",
        "zg361cl.201",
        "zg361cl.202",
        "zg361cl.203",
        "zg361cl.204",
        "zg361ip.202",
        "zg361ip.302",
    }
)
PARAMETERIZED_EVENT_PREDECESSOR_CALLER_FILE = (
    "common/scripted_effects/"
    "zg361_case_kernel_001_shared_helpers_effects.txt"
)
EXPECTED_TRIGGER_PREDECESSOR_MISSING_TRIGGERS = frozenset(
    {
        "zg361_p2c_m360_candidate_ready_trigger",
        "zg361_p2c_m360_frozen_manager_exact_trigger",
    }
)
EXPECTED_TRIGGER_PREDECESSOR_COUNTS = {
    "zg361_p2c_m360_candidate_ready_trigger": 3,
    "zg361_p2c_m360_frozen_manager_exact_trigger": 3,
}
TRIGGER_PREDECESSOR_CALLER_FILE = (
    "common/scripted_effects/"
    "zg361_phase2_central_001_m360_source_effects.txt"
)

B3_EFFECT_SHARDS = (
    "zg361_manager_governance_core_adapters_effects.txt",
    "zg361_manager_governance_dispatch_effects.txt",
    "zg361_manager_review_effects.txt",
    "zg361_policy_intake_effects.txt",
    "zg361_policy_audit_effects.txt",
    "zg361_policy_history_effects.txt",
    "zg361_policy_fairness_effects.txt",
)

# These five Python cells were present at the freeze point, but they are not
# CK3 product files and must not inherit a production-live claim from B3.
ACTION_CELL_ONLY = (
    "ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_incident_action_cell.py",
    "tools/zg361_phase2_promotion_compensation_action_cell.py",
    "tools/zg361_phase2_hc_workforce_b6_action_cell.py",
    "tools/zg361_phase2_cross_cycle_endgame_action_cell.py",
    "tools/zg361_phase2_projects_metrics_action_cell.py",
)

INHERITED_OVERSIZE = {
    "common/scripted_effects/zg361_b1_runtime_effects.txt": (
        "historical B1 provider; not created or enlarged by the B3 projection"
    ),
    "common/scripted_effects/zg361_b1_runtime_effects_part2.txt": (
        "historical B1 provider; not created or enlarged by the B3 projection"
    ),
    "common/scripted_effects/zg361_generated_mechanism_effects.txt": (
        "pre-B2 generated 361-mechanism provider inherited byte-for-byte"
    ),
}


class FreezeError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def record(path: Path, *, relative_to: Path | None = None) -> dict[str, object]:
    path = path.resolve()
    if not path.is_file():
        raise FreezeError(f"required input is missing: {path}")
    label = (
        path.relative_to(relative_to.resolve()).as_posix()
        if relative_to is not None
        else str(path)
    )
    return {"path": label, "bytes": path.stat().st_size, "sha256": sha256(path)}


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise FreezeError(f"JSON root is not an object: {path}")
    return value


def run(command: list[str], *, env: dict[str, str] | None = None) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    return {
        "argv": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_log(path: Path, result: dict[str, object]) -> dict[str, object]:
    path.write_text(
        str(result["stdout"]) + str(result["stderr"]),
        encoding="utf-8",
        newline="\n",
    )
    return record(path)


def native_source_rows() -> tuple[list[dict[str, object]], str]:
    paths = [NATIVE_ROOT / "CMakeLists.txt"]
    for tree in (NATIVE_ROOT / "include", NATIVE_ROOT / "src"):
        paths.extend(
            path
            for path in tree.rglob("*")
            if path.is_file() and path.suffix.lower() in {".cpp", ".hpp", ".h", ".c"}
        )
    paths = sorted(paths, key=lambda value: str(value).lower())
    rows = [record(path, relative_to=NATIVE_ROOT) for path in paths]
    # Match build_fresh.ps1 exactly: its fingerprint uses Windows-relative
    # paths even though the portable inventory above uses POSIX separators.
    native_prefix = str(NATIVE_ROOT.resolve())
    relative_windows = [
        str(path.resolve())[len(native_prefix):].lstrip("\\/") for path in paths
    ]
    lines = [
        f"{relative}\0{sha256(path)}"
        for relative, path in zip(relative_windows, paths, strict=True)
    ]
    fingerprint = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest().upper()
    return rows, fingerprint


def tracked_validation_rows() -> list[dict[str, object]]:
    result = run(
        [
            "git",
            "ls-files",
            "--",
            "ck3_autonomous_player/native_bridge/research",
            "ck3_autonomous_player/native_bridge/tools/build_fresh.ps1",
            "docs/ck3-native-ai",
        ]
    )
    if result["returncode"] != 0:
        raise FreezeError("git ls-files failed while binding validation inputs")
    values = [line.strip() for line in str(result["stdout"]).splitlines() if line.strip()]
    return [record(ROOT / value, relative_to=ROOT) for value in sorted(values)]


def tree_rows(root: Path) -> dict[str, dict[str, object]]:
    return {
        path.relative_to(root).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(root.rglob("*"), key=lambda value: value.as_posix())
        if path.is_file()
    }


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


def _top_level_event_entries(path: Path) -> list[tuple[str, str]]:
    """Return top-level namespaced event blocks without guessing event metadata."""

    text = path.read_text(encoding="utf-8-sig")
    masked = _mask_comments_and_strings(text)
    entries: list[tuple[str, str]] = []
    pattern = re.compile(
        r"(?m)^(zg361[A-Za-z0-9_]*\.[0-9]+)\s*=\s*\{"
    )
    for match in pattern.finditer(masked):
        opening = masked.find("{", match.start(), match.end())
        depth = 0
        end = None
        for index in range(opening, len(masked)):
            if masked[index] == "{":
                depth += 1
            elif masked[index] == "}":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end is None:
            raise FreezeError(f"unterminated event block {match.group(1)} in {path}")
        entries.append((match.group(1), text[match.start():end]))
    return entries


def _block_references(block: str) -> tuple[set[str], set[str], set[str]]:
    masked = _mask_comments_and_strings(block)
    effects = set(CUSTOM_EFFECT_CALL_RE.findall(masked))
    events = set(CUSTOM_EVENT_ID_RE.findall(masked))
    events.update(CUSTOM_EVENT_DIRECT_CALL_RE.findall(masked))
    triggers = set(CUSTOM_TRIGGER_CALL_RE.findall(masked))
    triggers.update(CUSTOM_TRIGGER_ARGUMENT_RE.findall(masked))
    return effects, events, triggers


def central_effect_call_closure(
    product_source: Path,
    *,
    roots: tuple[str, ...] = CENTRAL_ROOT_EFFECTS,
    required_effect_provider_files: frozenset[str] = (
        REQUIRED_CENTRAL_EFFECT_PROVIDER_FILES
    ),
    required_event_provider_files: frozenset[str] = (
        REQUIRED_CENTRAL_EVENT_PROVIDER_FILES
    ),
) -> dict[str, object]:
    """Resolve reachable custom effect and event calls from central roots."""

    sys.path.insert(0, str(MOD_ROOT / "tools"))
    from zg361_effect_sharding import top_level_effect_entries

    directory = product_source / "common" / "scripted_effects"
    effect_providers: dict[str, tuple[str, str]] = {}
    duplicate_effects: set[str] = set()
    for path in sorted(directory.glob("*.txt"), key=lambda value: value.name):
        relative = path.relative_to(product_source).as_posix()
        for entry in top_level_effect_entries(path.read_bytes()):
            if entry.name in effect_providers:
                duplicate_effects.add(entry.name)
            else:
                effect_providers[entry.name] = (relative, entry.block)

    event_providers: dict[str, tuple[str, str]] = {}
    duplicate_events: set[str] = set()
    event_directory = product_source / "events"
    for path in sorted(event_directory.glob("*.txt"), key=lambda value: value.name):
        relative = path.relative_to(product_source).as_posix()
        for name, block in _top_level_event_entries(path):
            if name in event_providers:
                duplicate_events.add(name)
            else:
                event_providers[name] = (relative, block)

    trigger_providers: dict[str, tuple[str, str]] = {}
    duplicate_triggers: set[str] = set()
    trigger_directory = product_source / "common" / "scripted_triggers"
    for path in sorted(trigger_directory.glob("*.txt"), key=lambda value: value.name):
        relative = path.relative_to(product_source).as_posix()
        for entry in top_level_effect_entries(path.read_bytes()):
            if entry.name in trigger_providers:
                duplicate_triggers.add(entry.name)
            else:
                trigger_providers[entry.name] = (relative, entry.block)

    material_effect_edges: set[tuple[str, str, str]] = set()
    material_event_edges: set[tuple[str, str, str]] = set()
    material_trigger_edges: set[tuple[str, str, str]] = set()
    material_missing_effects: set[str] = set()
    material_missing_events: set[str] = set()
    material_missing_triggers: set[str] = set()
    for caller_kind, provider_map in (
        ("effect", effect_providers),
        ("event", event_providers),
        ("trigger", trigger_providers),
    ):
        for caller, (_, block) in provider_map.items():
            effect_references, event_references, trigger_references = (
                _block_references(block)
            )
            if caller_kind == "effect":
                effect_references.discard(caller)
            elif caller_kind == "event":
                event_references.discard(caller)
            else:
                trigger_references.discard(caller)
            for reference in effect_references:
                material_effect_edges.add((caller_kind, caller, reference))
                if reference not in effect_providers:
                    material_missing_effects.add(reference)
            for reference in event_references:
                material_event_edges.add((caller_kind, caller, reference))
                if reference not in event_providers:
                    material_missing_events.add(reference)
            for reference in trigger_references:
                material_trigger_edges.add((caller_kind, caller, reference))
                if reference not in trigger_providers:
                    material_missing_triggers.add(reference)

    queue = deque(("effect", name) for name in roots)
    reachable_effects: set[str] = set()
    reachable_events: set[str] = set()
    reachable_triggers: set[str] = set()
    missing_effects: set[str] = set()
    missing_events: set[str] = set()
    missing_triggers: set[str] = set()
    edges: set[tuple[str, str, str, str]] = set()
    while queue:
        kind, name = queue.popleft()
        reachable = {
            "effect": reachable_effects,
            "event": reachable_events,
            "trigger": reachable_triggers,
        }[kind]
        missing = {
            "effect": missing_effects,
            "event": missing_events,
            "trigger": missing_triggers,
        }[kind]
        providers = {
            "effect": effect_providers,
            "event": event_providers,
            "trigger": trigger_providers,
        }[kind]
        if name in reachable or name in missing:
            continue
        provider = providers.get(name)
        if provider is None:
            missing.add(name)
            continue
        reachable.add(name)
        effect_references, event_references, trigger_references = (
            _block_references(provider[1])
        )
        if kind == "effect":
            effect_references.discard(name)
        elif kind == "event":
            event_references.discard(name)
        else:
            trigger_references.discard(name)
        for reference in sorted(effect_references):
            edges.add((kind, name, "effect", reference))
            if reference not in reachable_effects:
                queue.append(("effect", reference))
        for reference in sorted(event_references):
            edges.add((kind, name, "event", reference))
            if reference not in reachable_events:
                queue.append(("event", reference))
        for reference in sorted(trigger_references):
            edges.add((kind, name, "trigger", reference))
            if reference not in reachable_triggers:
                queue.append(("trigger", reference))

    effect_provider_files = sorted(
        {effect_providers[name][0] for name in reachable_effects}
    )
    event_provider_files = sorted(
        {event_providers[name][0] for name in reachable_events}
    )
    trigger_provider_files = sorted(
        {trigger_providers[name][0] for name in reachable_triggers}
    )
    effect_filenames = {Path(path).name for path in effect_provider_files}
    event_filenames = {Path(path).name for path in event_provider_files}
    missing_effect_provider_files = sorted(
        required_effect_provider_files - effect_filenames
    )
    missing_event_provider_files = sorted(
        required_event_provider_files - event_filenames
    )
    return {
        "roots": list(roots),
        "reachable_effect_count": len(reachable_effects),
        "reachable_effects": sorted(reachable_effects),
        "reachable_event_count": len(reachable_events),
        "reachable_events": sorted(reachable_events),
        "reachable_trigger_count": len(reachable_triggers),
        "reachable_triggers": sorted(reachable_triggers),
        "edges": [
            {
                "caller_kind": caller_kind,
                "caller": caller,
                "callee_kind": callee_kind,
                "callee": callee,
            }
            for caller_kind, caller, callee_kind, callee in sorted(edges)
        ],
        "effect_provider_files": effect_provider_files,
        "event_provider_files": event_provider_files,
        "trigger_provider_files": trigger_provider_files,
        "provider_files": sorted(
            effect_provider_files + event_provider_files + trigger_provider_files
        ),
        "missing_effects": sorted(missing_effects),
        "missing_events": sorted(missing_events),
        "missing_triggers": sorted(missing_triggers),
        "duplicate_effect_providers": sorted(duplicate_effects),
        "duplicate_event_providers": sorted(duplicate_events),
        "duplicate_trigger_providers": sorted(duplicate_triggers),
        "required_effect_provider_files": sorted(required_effect_provider_files),
        "required_event_provider_files": sorted(required_event_provider_files),
        "missing_required_effect_provider_files": missing_effect_provider_files,
        "missing_required_event_provider_files": missing_event_provider_files,
        "material_projection": {
            "effect_definition_count": len(effect_providers),
            "event_definition_count": len(event_providers),
            "trigger_definition_count": len(trigger_providers),
            "effect_reference_count": len(material_effect_edges),
            "event_reference_count": len(material_event_edges),
            "trigger_reference_count": len(material_trigger_edges),
            "missing_effects": sorted(material_missing_effects),
            "missing_events": sorted(material_missing_events),
            "missing_triggers": sorted(material_missing_triggers),
            "green": not (
                material_missing_effects
                or material_missing_events
                or material_missing_triggers
            ),
        },
        "green": not (
            missing_effects
            or missing_events
            or missing_triggers
            or duplicate_effects
            or duplicate_events
            or duplicate_triggers
            or missing_effect_provider_files
            or missing_event_provider_files
            or material_missing_effects
            or material_missing_events
            or material_missing_triggers
        ),
    }


def predecessor_live_red_evidence(root: Path) -> dict[str, object]:
    outer_report_path = root / "report.json"
    cell_report_path = root / "cell" / "report.json"
    error_log_path = root / "cell" / "final_error.log"
    evidence_index_path = root / "evidence-index.json"
    outer_report = read_json(outer_report_path)
    cell_report = read_json(cell_report_path)
    error_log = error_log_path.read_text(encoding="utf-8-sig", errors="replace")
    unknown_effects = re.findall(
        r"Unknown effect: (zg361_[A-Za-z0-9_]+_effect)", error_log
    )
    cleanup = cell_report.get("native_cleanup")
    cleanup_green = (
        isinstance(cleanup, dict)
        and cleanup.get("result") == "GREEN"
        and not cleanup.get("failed_checks")
    )
    green = (
        outer_report.get("result") == "RED"
        and cell_report.get("result") == "RED"
        and len(unknown_effects) == 2
        and set(unknown_effects) == EXPECTED_PREDECESSOR_UNKNOWN_EFFECTS
        and PREDECESSOR_CALLER_FILE in error_log.replace("\\", "/")
        and cleanup_green
    )
    if not green:
        raise FreezeError(
            "predecessor B3 RED evidence no longer matches its material-closure root cause"
        )
    return {
        "classification": "material-projection-closure-red",
        "loader_performance_claimed": False,
        "artifact_root": str(root),
        "unknown_effect_line_count": len(unknown_effects),
        "unknown_effects": sorted(set(unknown_effects)),
        "caller_file": PREDECESSOR_CALLER_FILE,
        "missing_provider_file": (
            "common/scripted_effects/"
            "zg361_phase2_central_003_dispatch_control_effects.txt"
        ),
        "cleanup_green": cleanup_green,
        "files": {
            "outer_report": record(outer_report_path),
            "cell_report": record(cell_report_path),
            "final_error_log": record(error_log_path),
            "evidence_index": record(evidence_index_path),
        },
        "preserved": True,
    }


def predecessor_event_live_red_evidence(root: Path) -> dict[str, object]:
    outer_report_path = root / "report.json"
    cell_report_path = root / "cell" / "report.json"
    error_log_path = root / "cell" / "final_error.log"
    evidence_index_path = root / "evidence-index.json"
    outer_report = read_json(outer_report_path)
    cell_report = read_json(cell_report_path)
    error_log = error_log_path.read_text(encoding="utf-8-sig", errors="replace")
    missing_events = re.findall(
        r"Event \[(zg361[A-Za-z0-9_]*\.[0-9]+)\] not found", error_log
    )
    cleanup = cell_report.get("native_cleanup")
    cleanup_green = (
        isinstance(cleanup, dict)
        and cleanup.get("result") == "GREEN"
        and not cleanup.get("failed_checks")
    )
    green = (
        outer_report.get("result") == "RED"
        and cell_report.get("result") == "RED"
        and len(missing_events) == 2
        and set(missing_events) == EXPECTED_EVENT_PREDECESSOR_MISSING_EVENTS
        and EVENT_PREDECESSOR_CALLER_FILE in error_log.replace("\\", "/")
        and cleanup_green
    )
    if not green:
        raise FreezeError(
            "predecessor B3 event RED evidence no longer matches its "
            "material-closure root cause"
        )
    return {
        "classification": "material-projection-event-closure-red",
        "loader_performance_claimed": False,
        "size_ab_triggered": False,
        "artifact_root": str(root),
        "missing_event_line_count": len(missing_events),
        "missing_events": sorted(set(missing_events)),
        "caller_file": EVENT_PREDECESSOR_CALLER_FILE,
        "missing_provider_file": (
            "events/zg361_phase2_central_001_serial_dispatch_events.txt"
        ),
        "cleanup_green": cleanup_green,
        "files": {
            "outer_report": record(outer_report_path),
            "cell_report": record(cell_report_path),
            "final_error_log": record(error_log_path),
            "evidence_index": record(evidence_index_path),
        },
        "preserved": True,
    }


def predecessor_parameterized_event_live_red_evidence(
    root: Path,
) -> dict[str, object]:
    outer_report_path = root / "report.json"
    cell_report_path = root / "cell" / "report.json"
    error_log_path = root / "cell" / "final_error.log"
    game_log_path = root / "cell" / "final_game.log"
    evidence_index_path = root / "evidence-index.json"
    outer_report = read_json(outer_report_path)
    cell_report = read_json(cell_report_path)
    error_log = error_log_path.read_text(encoding="utf-8-sig", errors="replace")
    game_log = game_log_path.read_text(encoding="utf-8-sig", errors="replace")
    pattern = r"Event \[(zg361[A-Za-z0-9_]*\.[0-9]+)\] not found"
    error_missing_events = re.findall(pattern, error_log)
    game_missing_events = re.findall(pattern, game_log)
    cleanup = cell_report.get("native_cleanup")
    cleanup_green = (
        isinstance(cleanup, dict)
        and cleanup.get("result") == "GREEN"
        and not cleanup.get("failed_checks")
    )
    error_reason = str(cell_report.get("error_reason", ""))
    green = (
        outer_report.get("result") == "RED"
        and cell_report.get("result") == "RED"
        and cell_report.get("duration_seconds") == 312.77
        and cell_report.get("loader_gate_executed") is False
        and cell_report.get("gameplay_acceptance_executed") is False
        and "reached frontend but did not enter Load Save/In Game" in error_reason
        and len(error_missing_events)
        == len(EXPECTED_PARAMETERIZED_EVENT_PREDECESSOR_MISSING_EVENTS)
        and len(game_missing_events)
        == len(EXPECTED_PARAMETERIZED_EVENT_PREDECESSOR_MISSING_EVENTS)
        and set(error_missing_events)
        == EXPECTED_PARAMETERIZED_EVENT_PREDECESSOR_MISSING_EVENTS
        and set(game_missing_events)
        == EXPECTED_PARAMETERIZED_EVENT_PREDECESSOR_MISSING_EVENTS
        and PARAMETERIZED_EVENT_PREDECESSOR_CALLER_FILE
        in error_log.replace("\\", "/")
        and PARAMETERIZED_EVENT_PREDECESSOR_CALLER_FILE
        in game_log.replace("\\", "/")
        and cleanup_green
    )
    if not green:
        raise FreezeError(
            "predecessor B3 parameterized-event RED evidence no longer matches "
            "its material-closure root cause"
        )
    return {
        "classification": "material-projection-parameterized-event-closure-red",
        "loader_performance_claimed": False,
        "size_ab_triggered": False,
        "artifact_root": str(root),
        "duration_seconds": cell_report.get("duration_seconds"),
        "frontend_reached": True,
        "load_save_or_in_game_reached": False,
        "missing_event_line_count": len(error_missing_events),
        "missing_events": sorted(set(error_missing_events)),
        "caller_file": PARAMETERIZED_EVENT_PREDECESSOR_CALLER_FILE,
        "root_cause": (
            "EVENT=<custom-event-id> arguments were absent from the B3 "
            "effect/event closure graph"
        ),
        "cleanup_green": cleanup_green,
        "files": {
            "outer_report": record(outer_report_path),
            "cell_report": record(cell_report_path),
            "final_error_log": record(error_log_path),
            "final_game_log": record(game_log_path),
            "evidence_index": record(evidence_index_path),
        },
        "preserved": True,
    }


def predecessor_trigger_live_red_evidence(root: Path) -> dict[str, object]:
    outer_report_path = root / "report.json"
    cell_report_path = root / "cell" / "report.json"
    error_log_path = root / "cell" / "final_error.log"
    game_log_path = root / "cell" / "final_game.log"
    evidence_index_path = root / "evidence-index.json"
    outer_report = read_json(outer_report_path)
    cell_report = read_json(cell_report_path)
    error_log = error_log_path.read_text(encoding="utf-8-sig", errors="replace")
    game_log = game_log_path.read_text(encoding="utf-8-sig", errors="replace")
    missing_triggers = re.findall(
        r"Unknown trigger:?\s+(zg361_[A-Za-z0-9_]+_trigger)", error_log
    )
    counts = Counter(missing_triggers)
    cleanup = cell_report.get("native_cleanup")
    cleanup_green = (
        isinstance(cleanup, dict)
        and cleanup.get("result") == "GREEN"
        and not cleanup.get("failed_checks")
    )
    error_reason = str(cell_report.get("error_reason", ""))
    green = (
        outer_report.get("result") == "RED"
        and cell_report.get("result") == "RED"
        and cell_report.get("duration_seconds") == 317.408
        and cell_report.get("loader_gate_executed") is False
        and cell_report.get("gameplay_acceptance_executed") is False
        and "reached frontend but did not enter Load Save/In Game" in error_reason
        and len(missing_triggers) == 6
        and set(missing_triggers) == EXPECTED_TRIGGER_PREDECESSOR_MISSING_TRIGGERS
        and dict(counts) == EXPECTED_TRIGGER_PREDECESSOR_COUNTS
        and TRIGGER_PREDECESSOR_CALLER_FILE in error_log.replace("\\", "/")
        and not game_log
        and cleanup_green
    )
    if not green:
        raise FreezeError(
            "predecessor B3 trigger RED evidence no longer matches its "
            "material-closure root cause"
        )
    return {
        "classification": "material-projection-trigger-closure-red",
        "loader_performance_claimed": False,
        "size_ab_triggered": False,
        "artifact_root": str(root),
        "duration_seconds": cell_report.get("duration_seconds"),
        "frontend_reached": True,
        "load_save_or_in_game_reached": False,
        "unknown_trigger_line_count": len(missing_triggers),
        "unknown_trigger_counts": dict(sorted(counts.items())),
        "unknown_triggers": sorted(set(missing_triggers)),
        "caller_file": TRIGGER_PREDECESSOR_CALLER_FILE,
        "cleanup_green": cleanup_green,
        "files": {
            "outer_report": record(outer_report_path),
            "cell_report": record(cell_report_path),
            "final_error_log": record(error_log_path),
            "final_game_log": record(game_log_path),
            "evidence_index": record(evidence_index_path),
        },
        "preserved": True,
    }


def closure_expansion_evidence(attempt: Path) -> dict[str, object]:
    expansion_path = attempt / "closure-expansion.json"
    release_manifest_path = attempt / "canonical-release.manifest.json"
    expansion = read_json(expansion_path)
    added_files = expansion.get("added_files")
    rounds = expansion.get("rounds")
    green = (
        expansion.get("kind")
        == "zg361_phase2_b3_material_custom_call_closure_expansion"
        and expansion.get("green") is True
        and expansion.get("final_missing_effects") == []
        and expansion.get("final_missing_events") == []
        and expansion.get("final_missing_triggers") == []
        and isinstance(added_files, list)
        and expansion.get("added_file_count") == len(added_files)
        and isinstance(rounds, list)
        and len(rounds) > 0
    )
    if not green:
        raise FreezeError("material custom-call closure expansion evidence is RED")
    return {
        "green": True,
        "round_count": len(rounds),
        "added_file_count": len(added_files),
        "final_effect_definition_count": expansion.get(
            "final_effect_definition_count"
        ),
        "final_event_definition_count": expansion.get(
            "final_event_definition_count"
        ),
        "final_trigger_definition_count": expansion.get(
            "final_trigger_definition_count"
        ),
        "expansion": record(expansion_path),
        "canonical_release_manifest": record(release_manifest_path),
    }


def projection_delta(baseline: Path, candidate: Path) -> list[dict[str, object]]:
    before = tree_rows(baseline)
    after = tree_rows(candidate)
    rows: list[dict[str, object]] = []
    for relative in sorted(set(before) | set(after)):
        old = before.get(relative)
        new = after.get(relative)
        if old == new:
            continue
        rows.append(
            {
                "path": relative,
                "operation": "added" if old is None else "removed" if new is None else "replaced",
                "before": old,
                "after": new,
            }
        )
    return rows


def effect_boundaries(product_source: Path, delta: list[dict[str, object]]) -> dict[str, object]:
    sys.path.insert(0, str(MOD_ROOT / "tools"))
    from zg361_effect_sharding import top_level_effect_entries

    directory = product_source / "common" / "scripted_effects"
    counts = {
        path.relative_to(product_source).as_posix(): len(
            top_level_effect_entries(path.read_bytes())
        )
        for path in sorted(directory.glob("*.txt"))
    }
    delta_effect_paths = {
        str(row["path"])
        for row in delta
        if str(row["path"]).startswith("common/scripted_effects/")
        and row["operation"] != "removed"
    }
    delta_over_hard = [
        {"path": path, "definitions": counts[path]}
        for path in sorted(delta_effect_paths)
        if counts[path] > HARD_EFFECT_MAX
    ]
    b3_counts = {
        name: counts[f"common/scripted_effects/{name}"] for name in B3_EFFECT_SHARDS
    }
    case_kernel_shards = sorted(
        path.name for path in directory.glob("*.txt")
        if CASE_KERNEL_SHARD_PATTERN.fullmatch(path.name)
    )
    probation_shards = sorted(
        path.name for path in directory.glob("*.txt")
        if path.name in REQUIRED_PROBATION_SHARDS
    )
    forbidden_monoliths_present = sorted(
        name for name in FORBIDDEN_SPLIT_MONOLITHS if (directory / name).is_file()
    )
    all_over_hard = [
        {"path": path, "definitions": count}
        for path, count in sorted(counts.items())
        if count > HARD_EFFECT_MAX
    ]
    unexpected_inherited = [
        row for row in all_over_hard if row["path"] not in INHERITED_OVERSIZE
    ]
    return {
        "target_per_file": TARGET_EFFECT_MAX,
        "hard_max_per_file": HARD_EFFECT_MAX,
        "b3_manager_shard_counts": b3_counts,
        "b3_manager_total_effects": sum(b3_counts.values()),
        "b3_manager_max_effects_per_file": max(b3_counts.values()),
        "case_kernel_shards": case_kernel_shards,
        "case_kernel_shard_count": len(case_kernel_shards),
        "required_probation_shards": probation_shards,
        "forbidden_split_monoliths_present": forbidden_monoliths_present,
        "delta_effect_files": len(delta_effect_paths),
        "delta_over_hard_max": delta_over_hard,
        "all_product_over_hard_max": all_over_hard,
        "inherited_oversize_reasons": INHERITED_OVERSIZE,
        "unexpected_inherited_oversize": unexpected_inherited,
        "green": (
            not delta_over_hard
            and not unexpected_inherited
            and len(case_kernel_shards) == EXPECTED_CASE_KERNEL_SHARDS
            and set(probation_shards) == REQUIRED_PROBATION_SHARDS
            and not forbidden_monoliths_present
            and max(b3_counts.values()) <= TARGET_EFFECT_MAX
            and sum(b3_counts.values()) == 43
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--baseline-source", type=Path, required=True)
    parser.add_argument("--canonical-base", required=True)
    parser.add_argument("--projection", required=True)
    parser.add_argument("--expected-source-fingerprint", required=True)
    parser.add_argument("--ck3-exe", type=Path, required=True)
    parser.add_argument("--ctest", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--pipe", required=True)
    parser.add_argument("--repository-manifest", type=Path, required=True)
    parser.add_argument("--predecessor-live-red", type=Path, required=True)
    parser.add_argument("--predecessor-event-live-red", type=Path, required=True)
    parser.add_argument(
        "--predecessor-parameterized-event-live-red", type=Path, required=True
    )
    parser.add_argument("--predecessor-trigger-live-red", type=Path, required=True)
    args = parser.parse_args(argv)

    attempt = args.attempt_dir.resolve()
    baseline = args.baseline_source.resolve()
    source = attempt / "product-source"
    product = attempt / "product"
    projection_path = attempt / "projection.json"
    materialization_path = attempt / "materialization.json"
    build = attempt / "native-build"
    dll = build / "xar_ck3_bridge.dll"
    injector = build / "xar_ck3_bridge_injector.exe"
    for directory in (attempt, baseline, source, product, build):
        if not directory.is_dir():
            raise FreezeError(f"required directory is missing: {directory}")
    if not re.fullmatch(r"[0-9a-f]{40}", args.canonical_base.lower()):
        raise FreezeError("canonical base must be a full Git commit")
    if not re.fullmatch(r"\\\\\.\\pipe\\xar_ck3_bridge_zg361_[0-9a-f]{32}", args.pipe):
        raise FreezeError("pipe must satisfy the formal unique Phase2 contract")

    head_result = run(["git", "rev-parse", "HEAD"])
    head = str(head_result["stdout"]).strip()
    ancestor = run(["git", "merge-base", "--is-ancestor", args.canonical_base, head])
    native_diff = run(["git", "status", "--short", "--", str(NATIVE_ROOT)])
    if ancestor["returncode"] != 0 or native_diff["stdout"]:
        raise FreezeError("canonical base is not merged or native sources are dirty")

    source_inputs, source_fingerprint = native_source_rows()
    if source_fingerprint != args.expected_source_fingerprint.upper():
        raise FreezeError(
            f"native source fingerprint drifted: {source_fingerprint} != "
            f"{args.expected_source_fingerprint.upper()}"
        )
    exe_row = record(args.ck3_exe)
    if exe_row["sha256"] != EXPECTED_EXE_SHA256:
        raise FreezeError("CK3 executable does not match exact build 1.19.0.6")

    projection_payload = read_json(projection_path)
    materialization = read_json(materialization_path)
    if (
        projection_payload.get("projection") != args.projection
        or materialization.get("projection") != args.projection
        or materialization.get("tree_sha256") != projection_payload.get("source_tree_sha256")
    ):
        raise FreezeError("product projection/materialization identity mismatch")
    source_rows = tree_rows(source)
    product_rows = tree_rows(product)
    if source_rows != product_rows:
        raise FreezeError("materialized product differs from its frozen source")
    delta = projection_delta(baseline, source)
    boundaries = effect_boundaries(source, delta)
    if boundaries["green"] is not True:
        raise FreezeError(f"effect boundary gate is RED: {boundaries}")
    central_closure = central_effect_call_closure(source)
    if central_closure["green"] is not True:
        raise FreezeError(f"central effect call closure is RED: {central_closure}")
    predecessor_red = predecessor_live_red_evidence(
        args.predecessor_live_red.resolve()
    )
    predecessor_event_red = predecessor_event_live_red_evidence(
        args.predecessor_event_live_red.resolve()
    )
    predecessor_parameterized_event_red = (
        predecessor_parameterized_event_live_red_evidence(
            args.predecessor_parameterized_event_live_red.resolve()
        )
    )
    predecessor_trigger_red = predecessor_trigger_live_red_evidence(
        args.predecessor_trigger_live_red.resolve()
    )
    expansion_evidence = closure_expansion_evidence(attempt)

    python = str(args.python.resolve())
    ctest_result = run(
        [str(args.ctest.resolve()), "--test-dir", str(build), "--output-on-failure"]
    )
    ctest_log = write_log(attempt / "native-ctest.txt", ctest_result)
    native_green = (
        ctest_result["returncode"] == 0
        and "100% tests passed" in str(ctest_result["stdout"])
        and f"{EXPECTED_NATIVE_TESTS}/{EXPECTED_NATIVE_TESTS}" in str(ctest_result["stdout"])
    )

    static_commands = (
        [python, "mod_zhongguo_style/tools/gen_361_phase2_central_runtime.py", "--check"],
        [python, "mod_zhongguo_style/tools/test_zg361_phase2_central_runtime.py"],
        [python, "-O", "mod_zhongguo_style/tools/test_zg361_phase2_central_runtime.py"],
        [python, "mod_zhongguo_style/tools/gen_361_manager_governance_runtime.py", "--check"],
        [python, "mod_zhongguo_style/tools/test_zg361_manager_governance_runtime.py"],
        [python, "-O", "mod_zhongguo_style/tools/test_zg361_manager_governance_runtime.py"],
        [python, "tools/test_freeze_zg361_phase2_b3_no_launch.py"],
        [python, "-O", "tools/test_freeze_zg361_phase2_b3_no_launch.py"],
        [python, "tools/test_expand_zg361_phase2_b3_projection_closure.py"],
        [python, "-O", "tools/test_expand_zg361_phase2_b3_projection_closure.py"],
    )
    static_results = [run(command) for command in static_commands]
    static_green = all(result["returncode"] == 0 for result in static_results)

    preflight_argv = [
        python,
        "tools/run_zhongguo_acceptance.py",
        "--preflight",
        "--phase2-live-batch",
        "--bridge-dll",
        str(dll),
        "--bridge-injector",
        str(injector),
        "--bridge-pipe",
        args.pipe,
        "--phase2-seed-contract",
        str(ROOT / "tools" / "zg361_phase2_seed_contract.json"),
        "--phase2-product-source",
        str(source),
        "--phase2-product-projection",
        args.projection,
        "--phase2-product-projection-manifest",
        str(projection_path),
    ]
    environment = os.environ.copy()
    environment["XAR_CK3_EXE"] = str(args.ck3_exe.resolve())
    preflight_result = run(preflight_argv, env=environment)
    preflight_log = write_log(attempt / "formal-no-launch-preflight.txt", preflight_result)
    formal_green = (
        preflight_result["returncode"] == 0
        and "ZHONGGUO 361 ACCEPTANCE PREFLIGHT: GREEN" in str(preflight_result["stdout"])
    )

    action_cells = [
        {
            **record(ROOT / relative, relative_to=ROOT),
            "classification": "action-cell-only-not-a-mod-product-file",
            "included_in_product_projection": False,
            "live_claim_changed_by_this_freeze": False,
        }
        for relative in ACTION_CELL_ONLY
    ]
    input_rows = {
        "native_build_sources": source_inputs,
        "native_validation_inputs": tracked_validation_rows(),
        "formal_runner": record(ROOT / "tools" / "run_zhongguo_acceptance.py", relative_to=ROOT),
        "b3_action_cell": record(ROOT / "tools" / "zg361_phase2_b3_manager_governance_action_cell.py", relative_to=ROOT),
        "seed_contract": record(ROOT / "tools" / "zg361_phase2_seed_contract.json", relative_to=ROOT),
        "historical_b2_r10_contract": record(ROOT / "tools" / "zg361_phase2_seed_production_closure.json", relative_to=ROOT),
        "projection_utility": record(ROOT / "tools" / "zg361_phase2_product_projection.py", relative_to=ROOT),
        "projection_closure_expander": record(
            ROOT / "tools" / "expand_zg361_phase2_b3_projection_closure.py",
            relative_to=ROOT,
        ),
        "ck3_executable": exe_row,
    }

    all_green = (
        native_green
        and static_green
        and formal_green
        and boundaries["green"] is True
        and central_closure["green"] is True
    )
    live_artifacts = attempt / "artifacts-live"
    launch_argv = [value for value in preflight_argv if value != "--preflight"]
    launch_argv.extend(["--artifacts-dir", str(live_artifacts), "--discard-userdir"])
    launch_command = (
        subprocess.list2cmdline(launch_argv) if all_green else None
    )
    manifest: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_phase2_b3_no_launch_candidate",
        "status": "GREEN_NO_LAUNCH" if all_green else "RED_NO_LAUNCH",
        "readiness": "static-ready-live-pending",
        "ck3_launched": False,
        "canonical_base_commit": args.canonical_base.lower(),
        "source_commit": head,
        "native_build": {
            "source_fingerprint_sha256": source_fingerprint,
            "build_fresh_tests_ran": True,
            "dependency_gate": "ck3_11906.hpp-recorded",
            "ctest": {
                "green": native_green,
                "total": EXPECTED_NATIVE_TESTS,
                "log": ctest_log,
            },
            "dll": record(dll),
            "injector": record(injector),
        },
        "product_projection": {
            "name": args.projection,
            "source": str(source),
            "product": str(product),
            "file_count": len(source_rows),
            "bytes": sum(int(row["bytes"]) for row in source_rows.values()),
            "source_tree_sha256": projection_payload.get("source_tree_sha256"),
            "formal_overlay_tree_sha256": projection_payload.get("formal_overlay_tree_sha256"),
            "file_list_sha256": projection_payload.get("file_list_sha256"),
            "manifest": record(projection_path),
            "materialization": record(materialization_path),
            "historical_b2_baseline": {
                "path": str(baseline),
                "projection_manifest": record(baseline.parent / "projection.json"),
                "mutated": False,
            },
            "delta": delta,
            "effect_boundaries": boundaries,
            "central_effect_call_closure": central_closure,
            "closure_expansion": expansion_evidence,
        },
        "predecessor_live_red": predecessor_red,
        "predecessor_event_live_red": predecessor_event_red,
        "predecessor_parameterized_event_live_red": (
            predecessor_parameterized_event_red
        ),
        "predecessor_trigger_live_red": predecessor_trigger_red,
        "action_cell_only_inputs": action_cells,
        "static_checks": [
            {
                "argv": result["argv"],
                "returncode": result["returncode"],
                "green": result["returncode"] == 0,
            }
            for result in static_results
        ],
        "formal_no_launch_preflight": {
            "green": formal_green,
            "argv": preflight_argv,
            "log": preflight_log,
        },
        "inputs": input_rows,
        "launch": {
            "authorized_by_preflight": all_green,
            "pipe": args.pipe if all_green else None,
            "argv": launch_argv if all_green else None,
            "windows_command": launch_command,
            "executed": False,
        },
        "claims": {
            "b3_live_complete": False,
            "provider_observed_live_artifact": None,
            "action_cell_only_live_claims_unchanged": True,
            "historical_r10_contract_mutated": False,
        },
    }
    external_manifest = attempt / "attempt-manifest.json"
    write_json(external_manifest, manifest)
    write_json(args.repository_manifest.resolve(), manifest)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "manifest": str(external_manifest),
                "repository_manifest": str(args.repository_manifest.resolve()),
                "dll_sha256": manifest["native_build"]["dll"]["sha256"],
                "injector_sha256": manifest["native_build"]["injector"]["sha256"],
                "projection_tree_sha256": projection_payload.get("source_tree_sha256"),
                "launch_command": launch_command,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if all_green else 1


if __name__ == "__main__":
    raise SystemExit(main())
