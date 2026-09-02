#!/usr/bin/env python3
"""Classify private phase-two post-call observer heartbeat evidence."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any


OBSERVER_KEY = "phase2_post_call_observer_v1"
MAX_LIST_COUNT = 4096
SELECTED_TARGET_RVA = 0x88B480
CONTROL_FIELDS = ("private_build", "installed", "failure")
TELEMETRY_FIELDS = (
    "hit_count",
    "nonempty_list_count",
    "descriptor_seen_count",
    "selected_event_count",
    "selected_state0_count",
    "selected_state2_count",
    "selected_state3_count",
    "selected_other_state_count",
    "read_failure_count",
    "scan_truncated_count",
    "last_producer_list",
    "last_list_begin",
    "last_list_count",
    "raw_last_descriptor",
    "raw_last_task",
    "raw_last_owner",
    "raw_last_callback",
    "raw_last_callback_slot2_target",
    "raw_last_state",
    "last_descriptor",
    "last_task",
    "last_owner",
    "last_callback",
    "last_callback_slot2_target",
    "last_state",
    "last_thread_id",
    "last_timestamp_qpc",
)
CUMULATIVE_FIELDS = TELEMETRY_FIELDS[:10]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _collect_heartbeats(value: Any, output: list[dict[str, Any]]) -> None:
    if isinstance(value, dict):
        if value.get("type") == "heartbeat":
            output.append(value)
        for child in value.values():
            _collect_heartbeats(child, output)
    elif isinstance(value, list):
        for child in value:
            _collect_heartbeats(child, output)


def collect_heartbeats(runner_report: dict[str, Any]) -> list[dict[str, Any]]:
    discovered: list[dict[str, Any]] = []
    _collect_heartbeats(runner_report, discovered)
    by_identity: dict[tuple[int, int], dict[str, Any]] = {}
    for heartbeat in discovered:
        sequence = heartbeat.get("sequence")
        pid = heartbeat.get("pid")
        if _nonnegative_integer(pid) and _nonnegative_integer(sequence):
            by_identity[(pid, sequence)] = heartbeat
    return [by_identity[key] for key in sorted(by_identity)]


def _nonnegative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _distribution(values: list[int]) -> list[dict[str, int]]:
    return [
        {"value": value, "sample_count": count}
        for value, count in sorted(Counter(values).items())
    ]


def _context_issues(sample: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    hit_count = sample["hit_count"]
    list_count = sample["last_list_count"]
    descriptor_count = sample["descriptor_seen_count"]
    selected_count = sample["selected_event_count"]
    if hit_count == 0:
        return issues
    for field in ("last_producer_list", "last_thread_id", "last_timestamp_qpc"):
        if sample[field] == 0:
            issues.append(f"{field}-zero-after-hit")
    if list_count > MAX_LIST_COUNT:
        issues.append("last-list-count-exceeds-v1-scan-bound")
    if list_count > 0 and sample["last_list_begin"] == 0:
        issues.append("nonempty-list-begin-zero")
    if sample["read_failure_count"] > 0:
        issues.append("read-failure-observed")
    if sample["scan_truncated_count"] > 0:
        issues.append("scan-truncation-observed")
    if descriptor_count > 0:
        for field in (
            "raw_last_descriptor",
            "raw_last_task",
            "raw_last_owner",
            "raw_last_callback",
            "raw_last_callback_slot2_target",
        ):
            if sample[field] == 0:
                issues.append(f"{field}-zero-after-scan")
    if selected_count > 0:
        for field in (
            "last_descriptor",
            "last_task",
            "last_owner",
            "last_callback",
            "last_callback_slot2_target",
        ):
            if sample[field] == 0:
                issues.append(f"{field}-zero-after-selection")
        target = sample["last_callback_slot2_target"]
        module_candidate = target - SELECTED_TARGET_RVA
        if target and (module_candidate <= 0 or module_candidate % 0x10000 != 0):
            issues.append("selected-slot2-not-module-plus-frozen-rva")
        if sample["last_state"] not in (0, 2, 3):
            issues.append("selected-last-state-outside-typed-matrix")
    return issues


def analyze(runner_report: dict[str, Any]) -> dict[str, Any]:
    heartbeats = collect_heartbeats(runner_report)
    expected_fields = set(CONTROL_FIELDS + TELEMETRY_FIELDS)
    schema_errors: list[str] = []
    samples: list[dict[str, Any]] = []
    missing_observer: list[dict[str, int]] = []
    for heartbeat in heartbeats:
        observer = heartbeat.get(OBSERVER_KEY)
        identity = {"pid": heartbeat["pid"], "sequence": heartbeat["sequence"]}
        if not isinstance(observer, dict):
            missing_observer.append(identity)
            continue
        missing = sorted(expected_fields - set(observer))
        extra = sorted(set(observer) - expected_fields)
        invalid: list[str] = []
        if observer.get("private_build") is not True:
            invalid.append("private_build")
        if not isinstance(observer.get("installed"), bool):
            invalid.append("installed")
        for field in ("failure",) + TELEMETRY_FIELDS:
            if field in observer and not _nonnegative_integer(observer[field]):
                invalid.append(field)
        if missing or extra or invalid:
            schema_errors.append(
                f"pid {identity['pid']} sequence {identity['sequence']} "
                f"missing={','.join(missing) or '-'} extra={','.join(extra) or '-'} "
                f"invalid={','.join(sorted(set(invalid))) or '-'}"
            )
            continue
        samples.append({**identity, **observer})

    counter_regressions: list[dict[str, Any]] = []
    qpc_regressions: list[dict[str, int]] = []
    relational_errors: list[dict[str, Any]] = []
    for previous, current in zip(samples, samples[1:]):
        if previous["pid"] != current["pid"]:
            continue
        fields = [
            field
            for field in CUMULATIVE_FIELDS
            if current[field] < previous[field]
        ]
        if fields:
            counter_regressions.append(
                {
                    "pid": current["pid"],
                    "previous_sequence": previous["sequence"],
                    "sequence": current["sequence"],
                    "fields": fields,
                }
            )
        if (
            previous["last_timestamp_qpc"] > 0
            and current["last_timestamp_qpc"] > 0
            and current["last_timestamp_qpc"] < previous["last_timestamp_qpc"]
        ):
            qpc_regressions.append(
                {
                    "pid": current["pid"],
                    "previous_sequence": previous["sequence"],
                    "sequence": current["sequence"],
                }
            )
    for sample in samples:
        errors: list[str] = []
        if sample["nonempty_list_count"] > sample["hit_count"]:
            errors.append("nonempty-list-count-exceeds-hit-count")
        if sample["scan_truncated_count"] > sample["nonempty_list_count"]:
            errors.append("scan-truncated-count-exceeds-nonempty-count")
        if sample["selected_event_count"] > sample["descriptor_seen_count"]:
            errors.append("selected-count-exceeds-descriptor-count")
        state_sum = sum(
            sample[field]
            for field in (
                "selected_state0_count",
                "selected_state2_count",
                "selected_state3_count",
                "selected_other_state_count",
            )
        )
        if state_sum < sample["selected_event_count"]:
            errors.append("selected-state-sum-below-selected-count")
        if errors:
            relational_errors.append(
                {"pid": sample["pid"], "sequence": sample["sequence"], "errors": errors}
            )

    final = samples[-1] if samples else None
    context_issues = _context_issues(final) if final else []
    if missing_observer or (not samples and not schema_errors):
        decision, status = "observer-schema-missing", "RED"
    elif schema_errors:
        decision, status = "observer-schema-invalid", "RED"
    elif any(not sample["installed"] or sample["failure"] != 0 for sample in samples):
        decision, status = "observer-install-or-runtime-failure", "RED"
    elif counter_regressions or qpc_regressions or relational_errors:
        decision, status = "observer-counter-contract-invalid", "RED"
    elif final is None or final["hit_count"] == 0:
        decision, status = "no-hook-hit", "NO-GO"
    elif context_issues:
        decision, status = "context-incomplete", "NO-GO"
    elif final["selected_event_count"] > 0:
        decision, status = f"selected-state{final['last_state']}", "GREEN"
    elif final["nonempty_list_count"] == 0:
        decision, status = "empty-list", "NO-GO"
    elif final["descriptor_seen_count"] > 0:
        decision, status = "scan-no-selected", "NO-GO"
    else:
        decision, status = "context-incomplete", "NO-GO"

    observed_states = [
        state
        for state, field in (
            (0, "selected_state0_count"),
            (2, "selected_state2_count"),
            (3, "selected_state3_count"),
        )
        if final and final[field] > 0
    ]
    recommendation = {
        "kind": "none",
        "reason": "typed selected task state was observed",
    }
    if decision == "scan-no-selected":
        recommendation = {
            "kind": "private-slot2-rva-histogram-with-task-identity",
            "reason": (
                "v1 proves a complete bounded scan but retains only the last raw "
                "descriptor; a histogram of every descriptor callback slot2 RVA "
                "keyed by task/owner is the smallest distinct selector diagnosis"
            ),
            "do_not_repeat": "the existing 0x3407DA1 v1 last-value-only capture",
        }

    return {
        "contract": "phase2-post-call-live-postprocess-v1",
        "status": status,
        "decision": decision,
        "read_only": True,
        "schema": {
            "observer_key": OBSERVER_KEY,
            "telemetry_field_count": len(TELEMETRY_FIELDS),
            "required_control_fields": list(CONTROL_FIELDS),
            "missing_observer_samples": missing_observer,
            "errors": schema_errors,
        },
        "heartbeat": {
            "discovered_count": len(heartbeats),
            "valid_observer_sample_count": len(samples),
            "counter_regressions": counter_regressions,
            "qpc_regressions": qpc_regressions,
            "relational_errors": relational_errors,
            "final_sequence": final["sequence"] if final else None,
        },
        "scan": {
            "maximum_list_count": MAX_LIST_COUNT,
            "final_hit_count": final["hit_count"] if final else None,
            "final_nonempty_list_count": final["nonempty_list_count"] if final else None,
            "final_descriptor_seen_count": final["descriptor_seen_count"] if final else None,
            "final_read_failure_count": final["read_failure_count"] if final else None,
            "final_scan_truncated_count": final["scan_truncated_count"] if final else None,
            "last_producer_list": final["last_producer_list"] if final else None,
            "last_list_begin": final["last_list_begin"] if final else None,
            "last_list_count": final["last_list_count"] if final else None,
        },
        "raw_last": {
            field.removeprefix("raw_last_"): final[field] if final else None
            for field in TELEMETRY_FIELDS
            if field.startswith("raw_last_")
        },
        "selected": {
            "event_count": final["selected_event_count"] if final else None,
            "state_counts": {
                "0": final["selected_state0_count"] if final else None,
                "2": final["selected_state2_count"] if final else None,
                "3": final["selected_state3_count"] if final else None,
                "other": final["selected_other_state_count"] if final else None,
            },
            "observed_typed_states": observed_states,
            "last_descriptor": final["last_descriptor"] if final else None,
            "last_task": final["last_task"] if final else None,
            "last_owner": final["last_owner"] if final else None,
            "last_callback": final["last_callback"] if final else None,
            "last_callback_slot2_target": (
                final["last_callback_slot2_target"] if final else None
            ),
            "last_state": final["last_state"] if final else None,
        },
        "context": {
            "issues": context_issues,
            "thread_distribution": _distribution(
                [sample["last_thread_id"] for sample in samples if sample["hit_count"] > 0]
            ),
            "qpc_monotonic": not qpc_regressions,
            "last_thread_id": final["last_thread_id"] if final else None,
            "last_timestamp_qpc": final["last_timestamp_qpc"] if final else None,
        },
        "next_observation": recommendation,
        "decision_matrix": [
            {"condition": "observer missing, extra/missing field, or invalid type", "decision": "observer-schema-missing/invalid", "status": "RED"},
            {"condition": "installed=false or failure!=0", "decision": "observer-install-or-runtime-failure", "status": "RED"},
            {"condition": "counter/QPC/relational contract invalid", "decision": "observer-counter-contract-invalid", "status": "RED"},
            {"condition": "hit_count == 0", "decision": "no-hook-hit", "status": "NO-GO"},
            {"condition": "hit with missing identities, read failures, count>4096, or truncation", "decision": "context-incomplete", "status": "NO-GO"},
            {"condition": "hits observed and every list was empty", "decision": "empty-list", "status": "NO-GO"},
            {"condition": "bounded descriptors scanned but selected_event_count == 0", "decision": "scan-no-selected", "status": "NO-GO"},
            {"condition": "selected last state is 0, 2, or 3", "decision": "selected-state0/2/3", "status": "GREEN"},
        ],
        "limits": [
            "v1 retains only the last raw and selected identity, not a per-descriptor history",
            "typed GREEN proves private observation only and does not promote native readiness",
            "the parser neither launches CK3 nor mutates game/source evidence",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-report", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    runner_bytes = args.runner_report.read_bytes()
    result = analyze(json.loads(runner_bytes.decode("utf-8")))
    result["input_evidence"] = {
        "runner_report": str(args.runner_report.resolve()),
        "runner_report_sha256": sha256(runner_bytes),
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["status"] in ("GREEN", "NO-GO") else 1


if __name__ == "__main__":
    raise SystemExit(main())
