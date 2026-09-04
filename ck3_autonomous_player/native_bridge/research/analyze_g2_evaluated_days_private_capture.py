#!/usr/bin/env python3
"""Classify one private G2 truce-duration capture without starting CK3.

The instrumented bridge deliberately resets the private index-7 observation
before returning the public war-termination payload.  Consequently the shared
terms runner can remain RED while its durable JSONL contains the two valid
read-only evaluator samples needed by GEN-034.  This postprocessor joins those
two evidence surfaces and accepts only two complete, same-frame capture groups.

The tool only reads an existing runner report and JSONL sidecar, then writes a
new analysis report.  It never imports the launcher or bridge driver.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


BOUNDARY_SCHEMA = "xar.ck3.g2_truce_private_evaluator_boundary.v1"
CAPTURE_SCHEMA = "xar.ck3.g2_truce_private_capture.v3"
ANALYSIS_SCHEMA = "xar.ck3.g2_evaluated_days_private_capture_analysis.v1"
EXACT_PATH = "root[7].default.children[1].children[0].children[0]"
TRUCE_VTABLE_RVA = 0x4461CA8
DURATION_OFFSET = 0x108
EVALUATOR_RVA = 0x3373000
EXPECTED_STAGES = ("pre_call", "post_call_1", "post_call_2")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-report", type=Path, required=True)
    parser.add_argument("--private-jsonl", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-war-id", type=int, required=True)
    parser.add_argument("--expected-character-id", type=int, required=True)
    parser.add_argument("--expected-date-raw", type=int, required=True)
    return parser


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _integer(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _address(value: object) -> int | None:
    if not isinstance(value, str) or re.fullmatch(r"0x[0-9A-Fa-f]+", value) is None:
        return None
    return int(value, 16)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _load_json(path: Path, name: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{name} is unavailable: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{name} root must be an object")
    return value


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"private JSONL is unavailable: {error}") from error
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"private JSONL line {line_number} is malformed: {error}"
            ) from error
        if not isinstance(value, dict):
            raise ValueError(f"private JSONL line {line_number} is not an object")
        rows.append(value)
    if not rows:
        raise ValueError("private JSONL contains no rows")
    return rows


def _runner_checks(
    report: dict[str, Any],
    *,
    war_id: int,
    character_id: int,
    date_raw: int,
) -> dict[str, bool]:
    requested = _mapping(report.get("requested_identity"))
    policy = _mapping(report.get("policy"))
    exact_build = _mapping(report.get("exact_build_proof"))
    sequence = _mapping(report.get("mcp_sequence"))
    sequence_checks = _mapping(sequence.get("checks"))
    cleanup = _mapping(report.get("cleanup"))
    source = _mapping(report.get("source_invariant"))
    exact_commands = [
        f"query-war-termination-terms-v1-{war_id}",
        f"query-war-termination-terms-v1-{war_id}",
    ]
    required_sequence_checks = (
        "official_tools_listed",
        "mcp_results_not_errors",
        "initial_paused",
        "expected_character",
        "expected_date",
        "between_same_paused_binding",
        "after_same_paused_binding",
        "query_sequence_successor",
        "normalized_payloads_equal",
        "binding_matches_revision",
    )
    return {
        "requested_identity": requested
        == {"war_id": war_id, "character_id": character_id, "date_raw": date_raw},
        "exact_build": exact_build.get("ok") is True,
        "two_same_frame_public_queries": all(
            sequence_checks.get(name) is True for name in required_sequence_checks
        ),
        "exact_query_commands": sequence.get("allowed_gameplay_commands")
        == exact_commands,
        "no_mutation_commands": sequence.get("mutation_commands") == []
        and policy.get("mutation_commands") == [],
        "time_not_advanced": policy.get("time_advanced") is False,
        "cleanup_proven": cleanup.get("ok") is True,
        "source_unchanged": source.get("unchanged") is True,
    }


def _split_groups(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for row in rows:
        current.append(row)
        if row.get("schema") == CAPTURE_SCHEMA:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def _boundary_identity(row: dict[str, Any]) -> tuple[object, ...]:
    return (
        row.get("exact_path"),
        row.get("truce_effect"),
        row.get("truce_vtable"),
        row.get("duration_script_value"),
        row.get("effect_context"),
        row.get("evaluation_context"),
        row.get("evaluator_function"),
    )


def _capture_group(
    rows: list[dict[str, Any]],
    *,
    war_id: int,
    character_id: int,
) -> dict[str, Any]:
    boundaries = rows[:-1] if rows else []
    summary = rows[-1] if rows else {}
    shape = _mapping(summary.get("loaded_tree_shape"))
    stages = [row.get("stage") for row in boundaries]
    identities = [_boundary_identity(row) for row in boundaries]
    boundary_identity_stable = bool(identities) and all(
        value == identities[0] for value in identities[1:]
    )
    truce = _address(boundaries[0].get("truce_effect")) if boundaries else None
    duration = (
        _address(boundaries[0].get("duration_script_value"))
        if boundaries
        else None
    )
    first_days = _integer(boundaries[1].get("evaluated_days")) if len(boundaries) > 1 else None
    second_days = _integer(boundaries[2].get("evaluated_days")) if len(boundaries) > 2 else None
    summary_truce = _address(shape.get("truce_effect"))
    summary_duration = _address(shape.get("duration_script_value"))
    has_three_boundaries = len(boundaries) == 3
    checks = {
        "four_rows": len(rows) == 4,
        "ordered_boundary_schemas": len(boundaries) == 3
        and all(row.get("schema") == BOUNDARY_SCHEMA for row in boundaries)
        and stages == list(EXPECTED_STAGES),
        "summary_schema": summary.get("schema") == CAPTURE_SCHEMA,
        "boundary_identity_stable": boundary_identity_stable,
        "exact_index7_path": len(boundaries) == 3
        and all(
            row.get("exact_path") == EXACT_PATH
            and row.get("exact_path_verified") is True
            for row in boundaries
        ),
        "truce_vtable_exact": len(boundaries) == 3
        and all(
            _address(row.get("truce_vtable_rva")) == TRUCE_VTABLE_RVA
            and _address(row.get("expected_truce_vtable_rva"))
            == TRUCE_VTABLE_RVA
            for row in boundaries
        ),
        "duration_pointer_exact": truce is not None
        and duration == truce + DURATION_OFFSET
        and len(boundaries) == 3
        and all(
            row.get("duration_offset_from_truce") == DURATION_OFFSET
            and row.get("duration_is_truce_plus_0x108") is True
            for row in boundaries
        ),
        "contexts_nonzero": len(boundaries) == 3
        and all(
            (_address(row.get("effect_context")) or 0) > 0
            and (_address(row.get("evaluation_context")) or 0) > 0
            for row in boundaries
        ),
        "evaluator_rva_exact": len(boundaries) == 3
        and all(
            _address(row.get("evaluator_function_rva")) == EVALUATOR_RVA
            and _address(row.get("expected_evaluator_function_rva"))
            == EVALUATOR_RVA
            for row in boundaries
        ),
        "call_progression_exact": len(boundaries) == 3
        and all(row.get("planned_call_count") == 2 for row in boundaries)
        and boundaries[0].get("completed_call_count") == 0
        and boundaries[0].get("evaluated_days") == -1
        and boundaries[1].get("completed_call_count") == 1
        and boundaries[2].get("completed_call_count") == 2,
        "two_equal_nonnegative_returns": first_days is not None
        and first_days >= 0
        and second_days == first_days,
        "summary_identity": summary.get("war_id") == war_id
        and summary.get("primary_attacker_character_id") == character_id,
        "summary_matches_boundary": has_three_boundaries
        and summary_truce == truce
        and summary_duration == duration
        and _address(shape.get("truce_vtable_rva")) == TRUCE_VTABLE_RVA
        and _address(shape.get("expected_truce_vtable_rva")) == TRUCE_VTABLE_RVA
        and shape.get("evaluator_effect_context") == boundaries[0].get(
            "effect_context"
        )
        and shape.get("evaluator_evaluation_context") == boundaries[0].get(
            "evaluation_context"
        ),
        "summary_private_complete": shape.get("targeted_index7_status")
        == "complete"
        and shape.get("default_capacity") == 4
        and shape.get("default_count") == 4
        and shape.get("hidden_index") == 1
        and shape.get("hidden_capacity") == 1
        and shape.get("hidden_child_count") == 1
        and shape.get("context_capacity") == 1
        and shape.get("context_child_count") == 1
        and shape.get("context_scope_count") == 1
        and shape.get("evaluator_capture_status") == "complete"
        and _address(shape.get("evaluator_function_rva")) == EVALUATOR_RVA
        and _address(shape.get("expected_evaluator_function_rva"))
        == EVALUATOR_RVA
        and shape.get("evaluator_first_days") == first_days
        and shape.get("evaluator_second_days") == second_days
        and shape.get("evaluator_call_count") == 2
        and shape.get("evaluator_nonnegative") is True
        and shape.get("evaluator_stable") is True,
        "context_destroyed": summary.get("context_destroyed") is True,
        "expiry_not_claimed": summary.get("expiry_observable") is False,
    }
    return {
        "evaluated_days": first_days if checks["two_equal_nonnegative_returns"] else None,
        "stages": stages,
        "checks": checks,
        "ok": all(checks.values()),
    }


def analyze(
    runner_report: dict[str, Any],
    private_rows: list[dict[str, Any]],
    *,
    war_id: int,
    character_id: int,
    date_raw: int,
) -> dict[str, Any]:
    groups = _split_groups(private_rows)
    group_results = [
        _capture_group(group, war_id=war_id, character_id=character_id)
        for group in groups
    ]
    days = [group.get("evaluated_days") for group in group_results]
    runner_checks = _runner_checks(
        runner_report,
        war_id=war_id,
        character_id=character_id,
        date_raw=date_raw,
    )
    checks = {
        "runner_read_only_same_frame": all(runner_checks.values()),
        "exactly_two_capture_groups": len(group_results) == 2,
        "both_capture_groups_complete": len(group_results) == 2
        and all(group.get("ok") is True for group in group_results),
        "same_evaluated_days_across_queries": len(days) == 2
        and days[0] is not None
        and days[1] == days[0],
    }
    ok = all(checks.values())
    return {
        "schema": ANALYSIS_SCHEMA,
        "status": "green_private_evaluated_days" if ok else "red",
        "ok": ok,
        "requested_identity": {
            "war_id": war_id,
            "character_id": character_id,
            "date_raw": date_raw,
        },
        "evaluated_days": days[0] if ok else None,
        "runner_report_status": runner_report.get("status"),
        "runner_report_ok": runner_report.get("ok"),
        "runner_checks": runner_checks,
        "private_row_count": len(private_rows),
        "capture_groups": group_results,
        "checks": checks,
        "readiness_boundary": {
            "private_evaluated_days_evidence": ok,
            "public_wire_promoted": False,
            "actual_expiry_observable": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
    }


def _write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def run(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    report_path = args.runner_report.expanduser().resolve()
    private_path = args.private_jsonl.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    if output_path.exists():
        raise FileExistsError(f"analysis output already exists: {output_path}")
    report = _load_json(report_path, "runner report")
    rows = _load_jsonl(private_path)
    result = analyze(
        report,
        rows,
        war_id=args.expected_war_id,
        character_id=args.expected_character_id,
        date_raw=args.expected_date_raw,
    )
    result["inputs"] = {
        "runner_report": str(report_path),
        "runner_report_sha256": _sha256(report_path),
        "private_jsonl": str(private_path),
        "private_jsonl_sha256": _sha256(private_path),
    }
    _write_json_atomic(output_path, result)
    return result, 0 if result["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result, exit_code = run(args)
    except BaseException as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "ok": result["ok"],
                "status": result["status"],
                "evaluated_days": result["evaluated_days"],
                "output": str(args.output.expanduser().resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
