#!/usr/bin/env python3
"""Classify private phase-two wrapper-entry heartbeat evidence."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_CALLSITE_COUNT = 618
EXPECTED_CALLSITE_LIST_SHA256 = (
    "32B88FEACB2D43E2284C116C53A448D8C1F14FDBD4B2BFB97C0725622E861A8C"
)
OBSERVER_KEY = "phase2_wrapper_entry_observer_v1"
REQUIRED_FIELDS = (
    "installed",
    "failure",
    "entry_count",
    "last_return_address",
    "last_callsite_rva",
    "last_scheduler_owner",
    "last_producer_list",
    "last_thread_id",
    "last_timestamp_qpc",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def canonical_rva_digest(rvas: list[int]) -> str:
    payload = json.dumps(
        [f"0x{rva:X}" for rva in rvas], separators=(",", ":")
    ).encode("ascii")
    return sha256(payload)


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
        if not isinstance(sequence, int) or isinstance(sequence, bool):
            continue
        if not isinstance(pid, int) or isinstance(pid, bool):
            continue
        by_identity[(pid, sequence)] = heartbeat
    return [by_identity[key] for key in sorted(by_identity)]


def parse_callsite_artifact(artifact: dict[str, Any]) -> set[int]:
    source = artifact.get("source")
    callers = artifact.get("direct_callers")
    if not isinstance(source, dict) or not isinstance(callers, dict):
        raise ValueError("caller artifact is missing source/direct_callers")
    if str(source.get("sha256", "")).upper() != EXPECTED_EXE_SHA256:
        raise ValueError("caller artifact executable identity changed")
    raw_rvas = callers.get("call_rvas")
    if not isinstance(raw_rvas, list):
        raise ValueError("caller artifact call_rvas is not a list")
    try:
        rvas = [int(value, 16) for value in raw_rvas]
    except (TypeError, ValueError) as error:
        raise ValueError("caller artifact contains an invalid call RVA") from error
    if len(rvas) != EXPECTED_CALLSITE_COUNT or len(set(rvas)) != len(rvas):
        raise ValueError("caller artifact count or uniqueness changed")
    if canonical_rva_digest(rvas) != EXPECTED_CALLSITE_LIST_SHA256:
        raise ValueError("caller artifact canonical callsite digest changed")
    return set(rvas)


def _nonnegative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _distribution(values: list[int]) -> list[dict[str, int]]:
    return [
        {"value": value, "sample_count": count}
        for value, count in sorted(Counter(values).items())
    ]


def analyze(
    runner_report: dict[str, Any], caller_artifact: dict[str, Any]
) -> dict[str, Any]:
    callsites = parse_callsite_artifact(caller_artifact)
    heartbeats = collect_heartbeats(runner_report)
    schema_errors: list[str] = []
    samples: list[dict[str, int | bool]] = []
    for heartbeat in heartbeats:
        observer = heartbeat.get(OBSERVER_KEY)
        if not isinstance(observer, dict):
            continue
        missing = [field for field in REQUIRED_FIELDS if field not in observer]
        if missing:
            schema_errors.append(
                f"sequence {heartbeat['sequence']} missing: {','.join(missing)}"
            )
            continue
        installed = observer["installed"]
        numeric_fields = REQUIRED_FIELDS[1:]
        invalid = [
            field
            for field in numeric_fields
            if not _nonnegative_integer(observer[field])
        ]
        if not isinstance(installed, bool):
            invalid.append("installed")
        if invalid:
            schema_errors.append(
                f"sequence {heartbeat['sequence']} invalid: {','.join(invalid)}"
            )
            continue
        samples.append(
            {
                "pid": heartbeat["pid"],
                "sequence": heartbeat["sequence"],
                **{field: observer[field] for field in REQUIRED_FIELDS},
            }
        )

    counter_regressions = [
        {
            "previous_sequence": previous["sequence"],
            "sequence": current["sequence"],
            "previous_entry_count": previous["entry_count"],
            "entry_count": current["entry_count"],
        }
        for previous, current in zip(samples, samples[1:])
        if previous["pid"] == current["pid"]
        and current["entry_count"] < previous["entry_count"]
    ]
    final = samples[-1] if samples else None
    positive_samples = [sample for sample in samples if sample["entry_count"] > 0]
    caller_values = [int(sample["last_callsite_rva"]) for sample in positive_samples]
    owner_values = [int(sample["last_scheduler_owner"]) for sample in positive_samples]
    carrier_values = [int(sample["last_producer_list"]) for sample in positive_samples]
    invalid_callsites = sorted({value for value in caller_values if value not in callsites})
    zero_context_fields = sorted(
        {
            field
            for sample in positive_samples
            for field in (
                "last_return_address",
                "last_scheduler_owner",
                "last_producer_list",
                "last_thread_id",
                "last_timestamp_qpc",
            )
            if sample[field] == 0
        }
    )
    qpc_regressions = [
        {
            "previous_sequence": previous["sequence"],
            "sequence": current["sequence"],
            "previous_qpc": previous["last_timestamp_qpc"],
            "qpc": current["last_timestamp_qpc"],
        }
        for previous, current in zip(positive_samples, positive_samples[1:])
        if previous["pid"] == current["pid"]
        and current["last_timestamp_qpc"] < previous["last_timestamp_qpc"]
    ]

    if not samples:
        decision = "observer-schema-missing"
        status = "RED"
    elif schema_errors:
        decision = "observer-schema-invalid"
        status = "RED"
    elif any(not sample["installed"] or sample["failure"] != 0 for sample in samples):
        decision = "observer-install-or-runtime-failure"
        status = "RED"
    elif counter_regressions:
        decision = "entry-counter-regressed"
        status = "RED"
    elif qpc_regressions:
        decision = "entry-qpc-regressed"
        status = "RED"
    elif final is not None and final["entry_count"] == 0:
        decision = "no-entry-observed"
        status = "NO-GO"
    elif invalid_callsites:
        decision = "entry-caller-outside-frozen-set"
        status = "RED"
    elif zero_context_fields:
        decision = "entry-context-incomplete"
        status = "NO-GO"
    else:
        decision = "entry-caller-owner-carrier-observed"
        status = "GREEN"

    nonzero_carriers = {value for value in carrier_values if value != 0}
    if not positive_samples:
        carrier_change = "not-observed"
    elif len(nonzero_carriers) > 1:
        carrier_change = "changed-across-sampled-last-values"
    elif len(nonzero_carriers) == 1:
        carrier_change = "stable-across-sampled-last-values"
    else:
        carrier_change = "zero-in-sampled-last-values"

    return {
        "contract": "phase2-wrapper-entry-live-postprocess-v1",
        "status": status,
        "decision": decision,
        "read_only": True,
        "heartbeat": {
            "discovered_count": len(heartbeats),
            "valid_observer_sample_count": len(samples),
            "schema_errors": schema_errors,
            "counter_regressions": counter_regressions,
            "final_entry_count": final["entry_count"] if final else None,
        },
        "return_dimension": {
            "status": "not_observed_by_v1",
            "affects_decision": False,
            "entry_no_return_classification": "not_evaluated",
        },
        "caller": {
            "frozen_callsite_count": len(callsites),
            "frozen_callsite_list_sha256": EXPECTED_CALLSITE_LIST_SHA256,
            "sampled_last_value_distribution": _distribution(caller_values),
            "invalid_sampled_callsites": invalid_callsites,
        },
        "scheduler_owner": {
            "sampled_last_value_distribution": _distribution(owner_values),
            "distinct_nonzero_count": len({value for value in owner_values if value}),
        },
        "producer_list_carrier": {
            "sampled_last_value_distribution": _distribution(carrier_values),
            "distinct_nonzero_count": len(nonzero_carriers),
            "change_classification": carrier_change,
        },
        "context": {
            "zero_fields_in_positive_entry_samples": zero_context_fields,
            "thread_distribution": _distribution(
                [int(sample["last_thread_id"]) for sample in positive_samples]
            ),
            "qpc_monotonic": all(
                current["last_timestamp_qpc"] >= previous["last_timestamp_qpc"]
                for previous, current in zip(positive_samples, positive_samples[1:])
                if previous["pid"] == current["pid"]
            ),
            "qpc_regressions": qpc_regressions,
        },
        "decision_matrix": [
            {"condition": "observer object absent or invalid", "decision": "observer-schema-missing/invalid", "status": "RED"},
            {"condition": "installed=false or failure!=0", "decision": "observer-install-or-runtime-failure", "status": "RED"},
            {"condition": "entry_count regresses", "decision": "entry-counter-regressed", "status": "RED"},
            {"condition": "positive-entry QPC regresses", "decision": "entry-qpc-regressed", "status": "RED"},
            {"condition": "final entry_count == 0", "decision": "no-entry-observed", "status": "NO-GO"},
            {"condition": "sampled caller is outside frozen 618-callsite set", "decision": "entry-caller-outside-frozen-set", "status": "RED"},
            {"condition": "positive entry with zero caller context", "decision": "entry-context-incomplete", "status": "NO-GO"},
            {"condition": "positive entry with frozen caller and nonzero context", "decision": "entry-caller-owner-carrier-observed", "status": "GREEN"},
            {"condition": "return count unavailable in frozen v1", "decision": "not_observed_by_v1", "status": "NOT-RED"},
        ],
        "limits": [
            "distributions count sampled last values, not every wrapper entry",
            "return lifetime is not observed by frozen observer v1 and does not affect the decision",
            "no public ABI/readiness or game state is changed",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-report", type=Path, required=True)
    parser.add_argument("--caller-artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    runner_bytes = args.runner_report.read_bytes()
    caller_bytes = args.caller_artifact.read_bytes()
    result = analyze(
        json.loads(runner_bytes.decode("utf-8")),
        json.loads(caller_bytes.decode("utf-8")),
    )
    result["input_evidence"] = {
        "runner_report": str(args.runner_report.resolve()),
        "runner_report_sha256": sha256(runner_bytes),
        "caller_artifact": str(args.caller_artifact.resolve()),
        "caller_artifact_sha256": sha256(caller_bytes),
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
