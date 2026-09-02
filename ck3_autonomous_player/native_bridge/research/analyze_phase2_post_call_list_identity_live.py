#!/usr/bin/env python3
"""Validate and summarize the bounded phase-two list-identity live capture."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any


OBSERVER_KEY = "phase2_post_call_list_identity_observer_v1"
EXPECTED_RUNNER_SHA256 = (
    "109CB334D56B6A50F75F8AA8C4A9EBD349B2703A28ED71694E90E0262BE15471"
)
MAX_LIST_COUNT = 4096
SAMPLE_CAPACITY = 64
HISTOGRAM_CAPACITY = 64
LOADER_CALLBACK_RVA = 0x88B480
EXPECTED_OBSERVER_FIELDS = {
    "private_build", "installed", "failure", "snapshot_consistent",
    "hit_count", "capture_count", "capture_contention_count",
    "snapshot_sequence", "last_producer_list", "last_list_begin",
    "last_list_count", "last_scan_count", "last_read_failure_count",
    "last_scan_truncated_count", "last_sample_count",
    "last_sample_overflow_count", "last_histogram_bin_count",
    "last_histogram_overflow_count", "last_selected_target_count",
    "last_thread_id", "last_timestamp_qpc", "samples", "histogram",
}
SAMPLE_FIELDS = {
    "descriptor_index", "read_complete", "descriptor", "task", "owner",
    "callback", "callback_slot2_target", "callback_slot2_rva", "state",
}
HISTOGRAM_FIELDS = {
    "callback_slot2_target", "callback_slot2_rva", "count", "first_task",
    "first_owner", "last_task", "last_owner",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _collect(value: Any, found: list[dict[str, Any]]) -> None:
    if isinstance(value, dict):
        observer = value.get(OBSERVER_KEY)
        if isinstance(observer, dict):
            found.append(observer)
        for child in value.values():
            _collect(child, found)
    elif isinstance(value, list):
        for child in value:
            _collect(child, found)


def _uint(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def analyze(report: dict[str, Any]) -> dict[str, Any]:
    observers: list[dict[str, Any]] = []
    _collect(report, observers)
    errors: list[str] = []
    if len(observers) != 1:
        errors.append(f"expected-one-observer-got-{len(observers)}")
    observer = observers[-1] if observers else {}
    missing = sorted(EXPECTED_OBSERVER_FIELDS - set(observer))
    extra = sorted(set(observer) - EXPECTED_OBSERVER_FIELDS)
    if missing:
        errors.append("missing-fields:" + ",".join(missing))
    if extra:
        errors.append("extra-fields:" + ",".join(extra))

    for key, value in observer.items():
        if key in {"private_build", "installed", "snapshot_consistent"}:
            if not isinstance(value, bool):
                errors.append(f"{key}-not-bool")
        elif key not in {"samples", "histogram"} and not _uint(value):
            errors.append(f"{key}-not-uint")
    samples = observer.get("samples", [])
    histogram = observer.get("histogram", [])
    if not isinstance(samples, list):
        errors.append("samples-not-list")
        samples = []
    if not isinstance(histogram, list):
        errors.append("histogram-not-list")
        histogram = []
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict) or set(sample) != SAMPLE_FIELDS:
            errors.append(f"sample-{index}-schema")
            continue
        for key, value in sample.items():
            if key == "read_complete":
                if not isinstance(value, bool):
                    errors.append(f"sample-{index}-{key}-not-bool")
            elif not _uint(value):
                errors.append(f"sample-{index}-{key}-not-uint")
    for index, row in enumerate(histogram):
        if not isinstance(row, dict) or set(row) != HISTOGRAM_FIELDS:
            errors.append(f"histogram-{index}-schema")
            continue
        for key, value in row.items():
            if not _uint(value):
                errors.append(f"histogram-{index}-{key}-not-uint")

    def number(key: str) -> int:
        value = observer.get(key, 0)
        return value if _uint(value) else 0

    relations = [
        (number("hit_count") == number("capture_count"), "hit-capture-mismatch"),
        (number("last_list_count") <= MAX_LIST_COUNT, "list-over-bound"),
        (number("last_scan_count") <= number("last_list_count"), "scan-over-list"),
        (number("last_sample_count") == len(samples), "sample-count-mismatch"),
        (number("last_histogram_bin_count") == len(histogram), "histogram-count-mismatch"),
        (number("last_sample_count") <= SAMPLE_CAPACITY, "sample-over-capacity"),
        (number("last_histogram_bin_count") <= HISTOGRAM_CAPACITY, "histogram-over-capacity"),
        (sum(row.get("count", 0) for row in histogram if isinstance(row, dict)) == number("last_scan_count"), "histogram-total-mismatch"),
    ]
    errors.extend(label for okay, label in relations if not okay)
    if samples:
        indices = [sample.get("descriptor_index") for sample in samples]
        if indices != list(range(len(samples))):
            errors.append("sample-indices-not-contiguous")
        if any(not sample.get("read_complete") for sample in samples):
            errors.append("incomplete-sample")

    overflow = {
        key: number(key)
        for key in (
            "capture_contention_count", "last_read_failure_count",
            "last_scan_truncated_count", "last_sample_overflow_count",
            "last_histogram_overflow_count",
        )
    }
    if any(overflow.values()):
        errors.append("bounded-capture-loss-or-overflow")
    if observer and (
        observer.get("private_build") is not True
        or observer.get("installed") is not True
        or number("failure") != 0
        or observer.get("snapshot_consistent") is not True
        or number("snapshot_sequence") % 2 != 0
    ):
        errors.append("observer-control-invalid")

    slot2 = Counter(sample.get("callback_slot2_rva") for sample in samples)
    owners = Counter(sample.get("owner") for sample in samples)
    states = Counter(sample.get("state") for sample in samples)
    task_stride = [
        samples[i]["task"] - samples[i - 1]["task"]
        for i in range(1, len(samples))
    ]
    descriptor_stride = [
        samples[i]["descriptor"] - samples[i - 1]["descriptor"]
        for i in range(1, len(samples))
    ]
    if errors:
        status, decision = "RED", "list-identity-contract-invalid"
    elif number("last_scan_count") == 0:
        status, decision = "NO-GO", "empty-or-unscanned-list"
    elif number("last_selected_target_count"):
        status, decision = "GREEN", "loader-callback-present"
    else:
        status, decision = "GREEN", "complete-list-excludes-loader-callback"

    return {
        "contract": "phase2-post-call-list-identity-live-postprocess-v1",
        "status": status,
        "decision": decision,
        "read_only": True,
        "validation": {"errors": errors, "overflow": overflow},
        "observer": {
            "installed": observer.get("installed"),
            "failure": observer.get("failure"),
            "snapshot_consistent": observer.get("snapshot_consistent"),
            "hit_count": number("hit_count"),
            "capture_count": number("capture_count"),
            "list_count": number("last_list_count"),
            "scan_count": number("last_scan_count"),
            "sample_count": len(samples),
            "histogram_bin_count": len(histogram),
            "selected_loader_callback_count": number("last_selected_target_count"),
            "thread_id": number("last_thread_id"),
            "timestamp_qpc": number("last_timestamp_qpc"),
        },
        "identity": {
            "slot2_rva_distribution": [
                {"rva": f"0x{value:X}", "count": count}
                for value, count in sorted(slot2.items())
            ],
            "owner_distribution": [
                {"owner": f"0x{value:X}", "count": count}
                for value, count in sorted(owners.items())
            ],
            "state_distribution": [
                {"state": value, "count": count}
                for value, count in sorted(states.items())
            ],
            "unique_task_count": len({sample["task"] for sample in samples}),
            "task_equals_callback_count": sum(
                sample["task"] == sample["callback"] for sample in samples
            ),
            "task_stride_distribution": sorted(Counter(task_stride).items()),
            "descriptor_stride_distribution": sorted(Counter(descriptor_stride).items()),
            "contains_loader_callback_rva": LOADER_CALLBACK_RVA in slot2,
        },
        "conclusion": {
            "bounded_list_complete": status == "GREEN",
            "current_list_is_loader_completion_list": (
                status == "GREEN" and LOADER_CALLBACK_RVA in slot2
            ),
            "static_identity_required": (
                f"resolve shared slot2 RVA 0x{next(iter(slot2)):X}"
                if len(slot2) == 1 else "resolve observed slot2 distribution"
            ),
        },
        "limits": [
            "the v1 live schema records callback slot2 but not callback vptr",
            "a shared slot2 implementation cannot uniquely identify an RTTI specialization",
            "this parser does not launch CK3 or alter public ABI/readiness",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-report", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    raw = args.runner_report.read_bytes()
    digest = sha256(raw)
    if digest != EXPECTED_RUNNER_SHA256:
        raise ValueError("runner report is not the frozen list-identity live artifact")
    result = analyze(json.loads(raw.decode("utf-8")))
    result["input_evidence"] = {
        "runner_report": str(args.runner_report.resolve()),
        "runner_report_sha256": digest,
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["status"] in {"GREEN", "NO-GO"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
