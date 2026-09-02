#!/usr/bin/env python3
"""Classify the bounded Phase-2 producer slot2 histogram v2 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


OBSERVER_KEY = "phase2_producer_slot2_histogram_observer_v2"
REPORT_SCHEMA = "phase2-producer-slot2-histogram-v2"
SELECTED_SLOT2_RVA = 0x88B480
HISTOGRAM_CAPACITY = 64
IDENTITY_FIELDS = (
    "task_pointer",
    "task_state",
    "callback_pointer",
    "vptr",
    "slot2_target",
    "slot2_rva",
    "owner_pointer",
    "thread_id",
    "timestamp_qpc",
)
SCALAR_FIELDS = (
    "failure",
    "producer_0x3B9CFD2_entry_count",
    "producer_0x3B9CFD7_entry_count",
    "histogram_capacity",
    "histogram_bin_count",
    "histogram_overflow_count",
    "histogram_read_failure_count",
    "selected_slot2_rva",
    "selected_count",
    "read_failure_count",
)
OBSERVER_FIELDS = (
    "private_build",
    "installed",
    *SCALAR_FIELDS,
    "callback_slot2_rva_histogram",
    "selected_first",
    "selected_last",
)
CUMULATIVE_FIELDS = (
    "producer_0x3B9CFD2_entry_count",
    "producer_0x3B9CFD7_entry_count",
    "histogram_overflow_count",
    "histogram_read_failure_count",
    "selected_count",
    "read_failure_count",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _uint(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


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
    unique: dict[tuple[int, int], dict[str, Any]] = {}
    for heartbeat in discovered:
        pid = heartbeat.get("pid")
        sequence = heartbeat.get("sequence")
        if _uint(pid) and _uint(sequence):
            unique[(pid, sequence)] = heartbeat
    return [unique[key] for key in sorted(unique)]


def _identity(value: Any, label: str) -> tuple[dict[str, int] | None, list[str]]:
    if value is None:
        return None, []
    if not isinstance(value, dict):
        return None, [f"{label}-not-object"]
    missing = sorted(set(IDENTITY_FIELDS) - set(value))
    extra = sorted(set(value) - set(IDENTITY_FIELDS))
    invalid = sorted(
        field for field in IDENTITY_FIELDS if field in value and not _uint(value[field])
    )
    issues: list[str] = []
    if missing:
        issues.append(f"{label}-missing:{','.join(missing)}")
    if extra:
        issues.append(f"{label}-extra:{','.join(extra)}")
    if invalid:
        issues.append(f"{label}-invalid:{','.join(invalid)}")
    if issues:
        return None, issues
    return {field: int(value[field]) for field in IDENTITY_FIELDS}, []


def _histogram(value: Any) -> tuple[list[dict[str, int]], list[str]]:
    if not isinstance(value, list):
        return [], ["histogram-not-list"]
    rows: list[dict[str, int]] = []
    issues: list[str] = []
    seen: set[int] = set()
    for index, row in enumerate(value):
        if not isinstance(row, dict) or set(row) != {"slot2_rva", "count"}:
            issues.append(f"histogram-bin-{index}-schema")
            continue
        rva, count = row.get("slot2_rva"), row.get("count")
        if not _uint(rva) or not _uint(count) or count == 0:
            issues.append(f"histogram-bin-{index}-invalid")
            continue
        if rva in seen:
            issues.append(f"histogram-bin-{index}-duplicate-rva")
            continue
        seen.add(rva)
        rows.append({"slot2_rva": int(rva), "count": int(count)})
    return rows, issues


def _identity_issues(
    runner: dict[str, Any], manifest: dict[str, Any], manifest_sha256: str
) -> list[str]:
    issues: list[str] = []
    gate = runner.get("list_domain_observer_gate")
    if not isinstance(gate, dict) or gate.get("result") != "GREEN":
        return ["runner-observer-gate-not-green"]
    gate_manifest = gate.get("observer_manifest")
    if not isinstance(gate_manifest, dict) or str(
        gate_manifest.get("sha256", "")
    ).upper() != manifest_sha256:
        issues.append("observer-manifest-sha-mismatch")
    if manifest.get("kind") != "zg361_phase2_native_observer_seam":
        issues.append("observer-manifest-kind-mismatch")
    if manifest.get("result") != "GREEN":
        issues.append("observer-manifest-not-green")

    source_commit = manifest.get("source_git_commit")
    if runner.get("frozen_git_commit") != source_commit:
        issues.append("source-commit-mismatch")
    session = manifest.get("session_binding")
    source = runner.get("source_identity")
    external = runner.get("external_dependencies")
    bridge = runner.get("bridge")
    binding = runner.get("binding")
    build = manifest.get("build")
    exact = manifest.get("exact_build")
    seam = manifest.get("seam")
    report_contract = manifest.get("report_contract")
    if not all(
        isinstance(row, dict)
        for row in (session, source, external, bridge, binding, build, exact, seam, report_contract)
    ):
        return issues + ["runner-or-manifest-identity-section-missing"]
    assert isinstance(session, dict) and isinstance(source, dict)
    assert isinstance(external, dict) and isinstance(bridge, dict)
    assert isinstance(binding, dict) and isinstance(build, dict)
    assert isinstance(exact, dict) and isinstance(seam, dict)
    assert isinstance(report_contract, dict)
    source_zip = source.get("source_zip")
    source_tree = source.get("clean_source_tree")
    dependency_hashes = external.get("sha256_before")
    if not isinstance(source_zip, dict) or not isinstance(source_tree, dict):
        issues.append("runner-source-identity-missing")
    else:
        if str(source_zip.get("sha256", "")).lower() != str(
            session.get("source_zip_sha256", "")
        ).lower():
            issues.append("source-zip-sha-mismatch")
        if str(source_tree.get("tree_sha256", "")).lower() != str(
            session.get("clean_source_tree_sha256", "")
        ).lower():
            issues.append("source-tree-sha-mismatch")
    if bridge.get("pipe") != session.get("pipe_name"):
        issues.append("pipe-identity-mismatch")
    if not isinstance(dependency_hashes, dict):
        issues.append("runner-dependency-hashes-missing")
    else:
        for runner_key, manifest_row, manifest_key in (
            ("game_executable", exact, "game_executable_sha256"),
            ("bridge_dll", build, "bridge_dll_sha256"),
            ("bridge_injector", build, "bridge_injector_sha256"),
        ):
            if str(dependency_hashes.get(runner_key, "")).lower() != str(
                manifest_row.get(manifest_key, "")
            ).lower():
                issues.append(f"{runner_key}-sha-mismatch")
    if seam.get("heartbeat_object") != OBSERVER_KEY:
        issues.append("observer-key-mismatch")
    if report_contract.get("schema") != REPORT_SCHEMA:
        issues.append("observer-report-schema-mismatch")
    if not _uint(binding.get("bridge_pid")) or binding.get("bridge_pid") == 0:
        issues.append("runner-bridge-pid-missing")
    return issues


def analyze(
    runner_report: dict[str, Any],
    observer_manifest: dict[str, Any],
    *,
    observer_manifest_sha256: str,
) -> dict[str, Any]:
    identity_issues = _identity_issues(
        runner_report, observer_manifest, observer_manifest_sha256
    )
    heartbeats = collect_heartbeats(runner_report)
    schema_errors: list[str] = []
    samples: list[dict[str, Any]] = []
    missing_observer: list[dict[str, int]] = []
    for heartbeat in heartbeats:
        observer = heartbeat.get(OBSERVER_KEY)
        sample_identity = {
            "pid": int(heartbeat["pid"]),
            "sequence": int(heartbeat["sequence"]),
        }
        if not isinstance(observer, dict):
            missing_observer.append(sample_identity)
            continue
        missing = sorted(set(OBSERVER_FIELDS) - set(observer))
        extra = sorted(set(observer) - set(OBSERVER_FIELDS))
        invalid = sorted(
            field for field in SCALAR_FIELDS if field in observer and not _uint(observer[field])
        )
        if not isinstance(observer.get("private_build"), bool):
            invalid.append("private_build")
        if not isinstance(observer.get("installed"), bool):
            invalid.append("installed")
        histogram, histogram_issues = _histogram(
            observer.get("callback_slot2_rva_histogram")
        )
        first, first_issues = _identity(
            observer.get("selected_first"), "selected-first"
        )
        last, last_issues = _identity(
            observer.get("selected_last"), "selected-last"
        )
        issues = histogram_issues + first_issues + last_issues
        if missing or extra or invalid or issues:
            schema_errors.append(
                f"pid {sample_identity['pid']} sequence {sample_identity['sequence']} "
                f"missing={','.join(missing) or '-'} extra={','.join(extra) or '-'} "
                f"invalid={','.join(sorted(set(invalid))) or '-'} "
                f"issues={','.join(issues) or '-'}"
            )
            continue
        samples.append(
            {
                **sample_identity,
                **observer,
                "callback_slot2_rva_histogram": histogram,
                "selected_first": first,
                "selected_last": last,
            }
        )

    regressions: list[dict[str, Any]] = []
    for previous, current in zip(samples, samples[1:]):
        if previous["pid"] != current["pid"]:
            continue
        fields = [field for field in CUMULATIVE_FIELDS if current[field] < previous[field]]
        previous_bins = {
            row["slot2_rva"]: row["count"]
            for row in previous["callback_slot2_rva_histogram"]
        }
        current_bins = {
            row["slot2_rva"]: row["count"]
            for row in current["callback_slot2_rva_histogram"]
        }
        if any(current_bins.get(rva, -1) < count for rva, count in previous_bins.items()):
            fields.append("histogram")
        if fields:
            regressions.append(
                {
                    "pid": current["pid"],
                    "previous_sequence": previous["sequence"],
                    "sequence": current["sequence"],
                    "fields": sorted(set(fields)),
                }
            )

    relational_errors: list[str] = []
    context_issues: list[str] = []
    final = samples[-1] if samples else None
    if final is not None:
        d2 = final["producer_0x3B9CFD2_entry_count"]
        d7 = final["producer_0x3B9CFD7_entry_count"]
        bins = {
            row["slot2_rva"]: row["count"]
            for row in final["callback_slot2_rva_histogram"]
        }
        histogram_total = sum(bins.values())
        selected_count = final["selected_count"]
        first = final["selected_first"]
        last = final["selected_last"]
        if final["histogram_capacity"] != HISTOGRAM_CAPACITY:
            relational_errors.append("histogram-capacity-drifted")
        if final["histogram_bin_count"] != len(bins):
            relational_errors.append("histogram-bin-count-mismatch")
        if len(bins) > HISTOGRAM_CAPACITY:
            relational_errors.append("histogram-exceeds-bound")
        if final["selected_slot2_rva"] != SELECTED_SLOT2_RVA:
            relational_errors.append("selected-slot2-rva-drifted")
        if d2 != d7:
            relational_errors.append("producer-entry-return-count-mismatch")
        if (
            histogram_total
            + final["histogram_overflow_count"]
            + final["histogram_read_failure_count"]
            != d7
        ):
            relational_errors.append("histogram-total-does-not-cover-d7")
        if bins.get(SELECTED_SLOT2_RVA, 0) != selected_count:
            relational_errors.append("selected-count-disagrees-with-histogram")
        if selected_count == 0:
            if first is not None or last is not None:
                relational_errors.append("zero-selected-retained-identity")
        elif first is None or last is None:
            context_issues.append("selected-first-or-last-identity-missing")
        else:
            for label, identity in (("first", first), ("last", last)):
                pointer_fields = (
                    "task_pointer",
                    "callback_pointer",
                    "vptr",
                    "slot2_target",
                    "owner_pointer",
                    "thread_id",
                    "timestamp_qpc",
                )
                if any(identity[field] == 0 for field in pointer_fields):
                    context_issues.append(f"selected-{label}-identity-has-zero-pointer")
                if identity["slot2_rva"] != SELECTED_SLOT2_RVA:
                    context_issues.append(f"selected-{label}-slot2-rva-drifted")
                if identity["task_state"] not in (0, 1, 2, 3):
                    context_issues.append(f"selected-{label}-state-outside-known-range")
            stable_fields = tuple(
                field for field in IDENTITY_FIELDS if field != "timestamp_qpc"
            )
            if any(first[field] != last[field] for field in stable_fields):
                context_issues.append("selected-first-last-state-or-identity-mismatch")
            if first["timestamp_qpc"] > last["timestamp_qpc"]:
                context_issues.append("selected-first-last-qpc-regressed")

    bound_pid = None
    binding = runner_report.get("binding")
    if isinstance(binding, dict) and _uint(binding.get("bridge_pid")):
        bound_pid = binding["bridge_pid"]
    heartbeat_pids = sorted({sample["pid"] for sample in samples})
    if heartbeat_pids and (len(heartbeat_pids) != 1 or heartbeat_pids[0] != bound_pid):
        identity_issues.append("heartbeat-pid-does-not-match-session-binding")

    if identity_issues:
        status, decision = "RED", "evidence-identity-mismatch"
    elif missing_observer or schema_errors:
        status, decision = "RED", "observer-schema-missing-or-invalid"
    elif not samples:
        status, decision = "NO-GO", "no-observer-heartbeat"
    elif any(
        sample["private_build"] is not True
        or sample["installed"] is not True
        or sample["failure"] != 0
        for sample in samples
    ):
        status, decision = "RED", "observer-install-or-runtime-failure"
    elif regressions or relational_errors:
        status, decision = "RED", "observer-counter-or-histogram-invalid"
    elif final is None or final["producer_0x3B9CFD2_entry_count"] == 0:
        status, decision = "NO-GO", "no-producer-entry"
    elif (
        final["histogram_overflow_count"] > 0
        or final["histogram_read_failure_count"] > 0
        or final["read_failure_count"] > 0
    ):
        status, decision = "NO-GO", "histogram-incomplete"
    elif final["selected_count"] == 0:
        status, decision = "NO-GO", "selected-not-observed"
    elif context_issues:
        status, decision = "NO-GO", "selected-state-or-identity-inconsistent"
    else:
        status, decision = "GREEN", "selected-consistent-next-gate"

    return {
        "contract": "phase2-producer-histogram-live-postprocess-v2",
        "status": status,
        "decision": decision,
        "next_gate_allowed": decision == "selected-consistent-next-gate",
        "read_only": True,
        "identity": {
            "issues": identity_issues,
            "observer_manifest_sha256": observer_manifest_sha256,
            "source_git_commit": runner_report.get("frozen_git_commit"),
            "bridge_pid": bound_pid,
            "heartbeat_pids": heartbeat_pids,
        },
        "heartbeat": {
            "discovered_count": len(heartbeats),
            "valid_observer_sample_count": len(samples),
            "missing_observer_samples": missing_observer,
            "schema_errors": schema_errors,
            "counter_regressions": regressions,
            "final_sequence": final["sequence"] if final else None,
        },
        "histogram": {
            "capacity": HISTOGRAM_CAPACITY,
            "selected_slot2_rva": f"0x{SELECTED_SLOT2_RVA:X}",
            "final_bin_count": final["histogram_bin_count"] if final else None,
            "final_bins": final["callback_slot2_rva_histogram"] if final else None,
            "final_overflow_count": final["histogram_overflow_count"] if final else None,
            "final_histogram_read_failure_count": final[
                "histogram_read_failure_count"
            ] if final else None,
            "final_read_failure_count": final["read_failure_count"] if final else None,
            "relational_errors": relational_errors,
        },
        "producer": {
            "final_0x3B9CFD2_entry_count": final["producer_0x3B9CFD2_entry_count"] if final else None,
            "final_0x3B9CFD7_entry_count": final["producer_0x3B9CFD7_entry_count"] if final else None,
        },
        "selected": {
            "count": final["selected_count"] if final else None,
            "first_identity": final["selected_first"] if final else None,
            "last_identity": final["selected_last"] if final else None,
            "context_issues": context_issues,
        },
        "decision_matrix": [
            {"condition": "manifest/source/session identity mismatch", "status": "RED", "decision": "evidence-identity-mismatch"},
            {"condition": "observer schema/install/counters invalid", "status": "RED", "decision": "observer-*-invalid"},
            {"condition": "no producer hit", "status": "NO-GO", "decision": "no-producer-entry"},
            {"condition": "histogram overflow or read failure", "status": "NO-GO", "decision": "histogram-incomplete"},
            {"condition": "selected_count == 0", "status": "NO-GO", "decision": "selected-not-observed"},
            {"condition": "selected first/last state or identity differs", "status": "NO-GO", "decision": "selected-state-or-identity-inconsistent"},
            {"condition": "selected_count > 0 and complete first/last identity agrees", "status": "GREEN", "decision": "selected-consistent-next-gate"},
        ],
        "limits": [
            "GREEN authorizes only the next acceptance gate, not public readiness",
            "the postprocessor does not launch CK3 or mutate source/live evidence",
            "the v1 last-only D2/D7 live is input evidence and must not be repeated",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-report", type=Path, required=True)
    parser.add_argument("--observer-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    runner_bytes = args.runner_report.read_bytes()
    manifest_bytes = args.observer_manifest.read_bytes()
    result = analyze(
        json.loads(runner_bytes.decode("utf-8")),
        json.loads(manifest_bytes.decode("utf-8")),
        observer_manifest_sha256=sha256(manifest_bytes),
    )
    result["input_evidence"] = {
        "runner_report": str(args.runner_report.resolve()),
        "runner_report_sha256": sha256(runner_bytes),
        "observer_manifest": str(args.observer_manifest.resolve()),
        "observer_manifest_sha256": sha256(manifest_bytes),
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
