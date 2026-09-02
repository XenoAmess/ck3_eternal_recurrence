#!/usr/bin/env python3
"""Classify bounded private G2 native-callsite observer evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_MANIFEST_SHA256 = (
    "469ACAC772AFBA730FD4C669ADE3CFB2728AC0F81B796C9BEF88B5C093B64FDD"
)
EXPECTED_SOURCE_COMMIT = "36fafd811b29bba11758d1ebc3929be8cbd4c9d4"
EXPECTED_SOURCE_ZIP_SHA256 = (
    "F3F3E81EFFE0D832A280A81AF96FC2FB267BE6D9A134AB3A0F35F3BA95841E17"
)
EXPECTED_REPORT_KIND = "ck3_g2_truce_native_callsite_observer_live_acceptance"
EXPECTED_OBSERVER_KEY = "g2_truce_native_callsite_observer_v1"
EXPECTED_CALL_RVAS = (0x2EDAF0F, 0x2EDB59E)
MAX_REPORT_BYTES = 32 * 1024 * 1024
MAX_SAMPLES = 512
INT32_MIN = -(1 << 31)
INT32_MAX = (1 << 31) - 1
COUNTER_FIELDS = ("pre_call_count", "post_call_count")
POINTER_FIELDS = (
    "last_script_value",
    "last_effect_context",
    "last_evaluation_context",
)
PRE_CONTEXT_FIELDS = ("last_pre_thread_id", "last_pre_timestamp_qpc")
POST_CONTEXT_FIELDS = ("last_post_thread_id", "last_post_timestamp_qpc")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _nonnegative(value: Any) -> bool:
    return _is_int(value) and value >= 0


def _positive(value: Any) -> bool:
    return _is_int(value) and value > 0


def _validate_manifest(
    manifest: dict[str, Any],
    manifest_sha256: str,
    expected_manifest_sha256: str,
    expected_source_commit: str,
    expected_source_zip_sha256: str,
) -> dict[str, Any]:
    source = manifest.get("source")
    candidate = manifest.get("candidate")
    files = candidate.get("files") if isinstance(candidate, dict) else None
    source_zip = files.get("source_zip") if isinstance(files, dict) else None
    boundaries = manifest.get("boundaries")
    boundaries = boundaries if isinstance(boundaries, dict) else {}
    checks = {
        "manifest_sha256": manifest_sha256 == expected_manifest_sha256,
        "source_commit": isinstance(source, dict)
        and source.get("commit") == expected_source_commit,
        "source_zip_sha256": isinstance(source_zip, dict)
        and source_zip.get("sha256") == expected_source_zip_sha256,
        "heartbeat_schema": manifest.get("heartbeat_schema")
        == EXPECTED_OBSERVER_KEY,
        "report_schema": manifest.get("report_schema") == EXPECTED_REPORT_KIND,
        "direct_evaluator_disabled": boundaries.get("direct_evaluator_enabled")
        is False,
        "heartbeat_only": boundaries.get("heartbeat_only") is True,
    }
    return {"checks": checks, "ok": all(checks.values())}


def _validate_policy(report: dict[str, Any]) -> dict[str, Any]:
    policy = report.get("policy")
    policy = policy if isinstance(policy, dict) else {}
    source_invariant = report.get("source_invariant")
    source_invariant = (
        source_invariant if isinstance(source_invariant, dict) else {}
    )
    exact_build_proof = report.get("exact_build_proof")
    exact_build_proof = (
        exact_build_proof if isinstance(exact_build_proof, dict) else {}
    )
    cleanup = report.get("cleanup")
    cleanup = cleanup if isinstance(cleanup, dict) else {}
    checks = {
        "report_kind": report.get("kind") == EXPECTED_REPORT_KIND,
        "heartbeat_only": policy.get("heartbeat_only") is True,
        "no_mcp_queries": policy.get("mcp_queries") == [],
        "no_evaluator_requests": policy.get("evaluator_requests") == [],
        "no_context_effects": policy.get("context_effects") == [],
        "no_mutation_commands": policy.get("mutation_commands") == [],
        "no_time_advance": policy.get("time_advanced") is False,
        "source_unchanged": source_invariant.get("unchanged") is True,
        "exact_build_proven": exact_build_proof.get("ok") is True,
        "managed_cleanup_proven": cleanup.get("ok") is True,
    }
    return {"checks": checks, "ok": all(checks.values())}


def _validate_sample(sample: Any) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(sample, dict):
        return None, ["sample_not_object"]
    if sample.get("schema_ok") is not True:
        errors.append("producer_schema_red")
    if sample.get("installed_mask") != 3:
        errors.append("installed_mask_not_two_sites")
    if sample.get("failure") != 0:
        errors.append("observer_failure_nonzero")
    if not _nonnegative(sample.get("sequence")):
        errors.append("sequence_invalid")
    if not _positive(sample.get("pid")):
        errors.append("pid_invalid")
    rows = sample.get("callsites")
    if not isinstance(rows, list) or len(rows) != 2:
        return None, errors + ["callsites_not_two_rows"]
    normalized_rows: list[dict[str, int]] = []
    for index, raw in enumerate(rows):
        row_errors: list[str] = []
        if not isinstance(raw, dict):
            errors.append(f"site{index}_not_object")
            continue
        if raw.get("call_instruction_rva") != EXPECTED_CALL_RVAS[index]:
            row_errors.append(f"site{index}_call_rva_mismatch")
        fields = (
            COUNTER_FIELDS
            + POINTER_FIELDS
            + PRE_CONTEXT_FIELDS
            + POST_CONTEXT_FIELDS
        )
        for field in fields:
            if not _nonnegative(raw.get(field)):
                row_errors.append(f"site{index}_{field}_invalid")
        return_eax = raw.get("last_return_eax")
        if not _is_int(return_eax) or not INT32_MIN <= return_eax <= INT32_MAX:
            row_errors.append(f"site{index}_return_eax_invalid")
        if row_errors:
            errors.extend(row_errors)
            continue
        row = {
            field: int(raw[field])
            for field in COUNTER_FIELDS
            + POINTER_FIELDS
            + PRE_CONTEXT_FIELDS
            + POST_CONTEXT_FIELDS
        }
        row["call_instruction_rva"] = int(raw["call_instruction_rva"])
        row["last_return_eax"] = int(return_eax)
        if row["post_call_count"] > row["pre_call_count"]:
            errors.append(f"site{index}_post_exceeds_pre")
        if row["pre_call_count"] > 0 and not all(
            row[field] > 0 for field in POINTER_FIELDS + PRE_CONTEXT_FIELDS
        ):
            errors.append(f"site{index}_pre_context_incomplete")
        if row["post_call_count"] > 0 and not all(
            row[field] > 0 for field in POST_CONTEXT_FIELDS
        ):
            errors.append(f"site{index}_post_context_incomplete")
        normalized_rows.append(row)
    if errors or len(normalized_rows) != 2:
        return None, errors
    return {
        "sequence": int(sample["sequence"]),
        "pid": int(sample["pid"]),
        "callsites": normalized_rows,
    }, []


def _signature(sample: dict[str, Any]) -> tuple[Any, ...]:
    values: list[Any] = []
    for row in sample["callsites"]:
        values.extend(
            row[field]
            for field in (
                "call_instruction_rva",
                *COUNTER_FIELDS,
                *POINTER_FIELDS,
                *PRE_CONTEXT_FIELDS,
                "last_return_eax",
                *POST_CONTEXT_FIELDS,
            )
        )
    return tuple(values)


def _validate_session_identity(
    report: dict[str, Any], samples: list[dict[str, Any]]
) -> dict[str, Any]:
    readiness = report.get("readiness")
    readiness = readiness if isinstance(readiness, dict) else {}
    session = report.get("session")
    session = session if isinstance(session, dict) else {}
    anchor = report.get("driver_anchor")
    anchor = anchor if isinstance(anchor, dict) else {}
    checkpoint = anchor.get("last_checkpoint")
    checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    identity = {
        "snapshot_id": readiness.get("snapshot_id"),
        "snapshot_revision": readiness.get("revision"),
        "native_revision": readiness.get("native_revision"),
        "date_raw": readiness.get("date_raw"),
        "connection_generation": readiness.get("connection_generation"),
        "episode_run_id": readiness.get("episode_run_id"),
        "episode_character_id": readiness.get("episode_character_id"),
        "process_id": readiness.get("bridge_pid"),
    }
    checks = {
        "map_ready": readiness.get("map_ready") is True,
        "paused": readiness.get("paused") is True,
        "snapshot_id": isinstance(identity["snapshot_id"], str)
        and bool(identity["snapshot_id"]),
        "snapshot_revision": _positive(identity["snapshot_revision"]),
        "native_revision": _positive(identity["native_revision"]),
        "date_raw": _is_int(identity["date_raw"])
        and INT32_MIN <= identity["date_raw"] <= INT32_MAX,
        "connection_generation": _positive(
            identity["connection_generation"]
        ),
        "episode_run_id": isinstance(identity["episode_run_id"], str)
        and bool(identity["episode_run_id"]),
        "episode_character_id": _positive(identity["episode_character_id"]),
        "played_character_matches_episode": readiness.get(
            "played_character_id"
        )
        == identity["episode_character_id"],
        "driver_character_matches_episode": anchor.get(
            "episode_character_id"
        )
        == identity["episode_character_id"],
        "checkpoint_date_matches_frame": checkpoint.get("date_raw")
        == identity["date_raw"],
        "process_id": _positive(identity["process_id"]),
        "managed_session_ready": session.get("ok") is True,
        "managed_session_pid_matches": session.get("pid")
        == identity["process_id"],
        "all_samples_match_process": bool(samples)
        and all(
            sample.get("pid") == identity["process_id"]
            for sample in samples
        ),
    }
    return {"identity": identity, "checks": checks, "ok": all(checks.values())}


def _validate_runner_terminal(
    report: dict[str, Any], classification: str
) -> dict[str, Any]:
    observation = report.get("observation")
    observation = observation if isinstance(observation, dict) else {}
    result = observation.get("result")
    if classification == "two_site_return_observed":
        expected_results = {"two_stable_native_pre_post_samples"}
        expected_ok = True
        expected_status = "green"
        error_ok = report.get("error") is None
    elif classification == "no_native_callsite_hit":
        expected_results = {
            "observation_timeout_without_stable_native_return"
        }
        expected_ok = False
        expected_status = "red"
        error_ok = isinstance(report.get("error"), str)
    elif classification in {
        "pre_only_native_callsite",
        "incomplete_two_site_return",
    }:
        expected_results = {
            "observation_timeout_without_stable_native_return",
            "process_exit_before_stable_native_return",
        }
        expected_ok = False
        expected_status = "red"
        error_ok = isinstance(report.get("error"), str)
    else:
        expected_results = {
            "observer_schema_or_install_red",
            "not_started",
            "process_exit_before_stable_native_return",
            "observation_timeout_without_stable_native_return",
        }
        expected_ok = False
        expected_status = "red"
        error_ok = isinstance(report.get("error"), str)
    checks = {
        "runner_ok": report.get("ok") is expected_ok,
        "runner_status": report.get("status") == expected_status,
        "observation_result": result in expected_results,
        "error_coherent": error_ok,
    }
    return {"checks": checks, "ok": all(checks.values())}


def analyze(
    report: Any,
    manifest: Any,
    *,
    report_sha256: str,
    manifest_sha256: str,
    expected_manifest_sha256: str = EXPECTED_MANIFEST_SHA256,
    expected_source_commit: str = EXPECTED_SOURCE_COMMIT,
    expected_source_zip_sha256: str = EXPECTED_SOURCE_ZIP_SHA256,
) -> dict[str, Any]:
    report = report if isinstance(report, dict) else {}
    manifest = manifest if isinstance(manifest, dict) else {}
    manifest_proof = _validate_manifest(
        manifest,
        manifest_sha256,
        expected_manifest_sha256,
        expected_source_commit,
        expected_source_zip_sha256,
    )
    policy_proof = _validate_policy(report)
    observation = report.get("observation")
    samples_raw = (
        observation.get("samples") if isinstance(observation, dict) else None
    )
    bounded = isinstance(samples_raw, list) and len(samples_raw) <= MAX_SAMPLES
    samples_raw = samples_raw if isinstance(samples_raw, list) else []
    normalized: list[dict[str, Any]] = []
    sample_errors: list[dict[str, Any]] = []
    for index, sample in enumerate(samples_raw[:MAX_SAMPLES]):
        row, errors = _validate_sample(sample)
        if errors:
            sample_errors.append({"index": index, "errors": errors})
        elif row is not None:
            normalized.append(row)

    counter_regressions: list[dict[str, int]] = []
    for previous, current in zip(normalized, normalized[1:]):
        for site_index in range(2):
            for field in COUNTER_FIELDS:
                before = previous["callsites"][site_index][field]
                after = current["callsites"][site_index][field]
                if after < before:
                    counter_regressions.append(
                        {
                            "site_index": site_index,
                            "previous_sequence": previous["sequence"],
                            "sequence": current["sequence"],
                            "previous": before,
                            "current": after,
                        }
                    )

    final = normalized[-1] if normalized else None
    final_rows = final["callsites"] if final else []
    total_pre = sum(row["pre_call_count"] for row in final_rows)
    total_post = sum(row["post_call_count"] for row in final_rows)
    both_returned = bool(
        len(final_rows) == 2
        and all(row["post_call_count"] > 0 for row in final_rows)
    )
    stable_two = bool(
        len(normalized) >= 2
        and _signature(normalized[-1]) == _signature(normalized[-2])
    )
    session_identity_proof = _validate_session_identity(report, normalized)

    evidence_red = bool(
        manifest_proof["ok"] is not True
        or policy_proof["ok"] is not True
        or session_identity_proof["ok"] is not True
        or not bounded
        or sample_errors
        or counter_regressions
        or not normalized
    )
    if evidence_red:
        classification = "read_or_install_failure"
        status = "RED"
    elif total_pre == 0 and total_post == 0:
        classification = "no_native_callsite_hit"
        status = "NO-GO"
    elif total_pre > 0 and total_post == 0:
        classification = "pre_only_native_callsite"
        status = "RED"
    elif both_returned and stable_two:
        classification = "two_site_return_observed"
        status = "GREEN"
    else:
        classification = "incomplete_two_site_return"
        status = "NO-GO"

    terminal_proof = _validate_runner_terminal(report, classification)
    if terminal_proof["ok"] is not True:
        classification = "read_or_install_failure"
        status = "RED"

    evaluated_observable = classification == "two_site_return_observed"
    source = manifest.get("source")
    source = source if isinstance(source, dict) else {}
    candidate = manifest.get("candidate")
    candidate = candidate if isinstance(candidate, dict) else {}
    files = candidate.get("files")
    files = files if isinstance(files, dict) else {}
    source_zip = files.get("source_zip")
    source_zip = source_zip if isinstance(source_zip, dict) else {}
    return {
        "contract": "g2-truce-native-callsite-observer-live-postprocess-v1",
        "status": status,
        "classification": classification,
        "input_evidence": {
            "runner_report_sha256": report_sha256,
            "manifest_sha256": manifest_sha256,
            "expected_manifest_sha256": expected_manifest_sha256,
            "source_commit": source.get("commit"),
            "source_zip_sha256": source_zip.get("sha256"),
        },
        "proofs": {
            "manifest": manifest_proof,
            "runner_policy": policy_proof,
            "session_identity": session_identity_proof,
            "runner_terminal": terminal_proof,
            "samples_bounded": bounded,
            "sample_errors": sample_errors,
            "counter_regressions": counter_regressions,
            "stable_two_final_samples": stable_two,
        },
        "observer": {
            "key": EXPECTED_OBSERVER_KEY,
            "register_binding": {
                "RCX": "last_script_value",
                "RDX": "last_effect_context",
                "R8": "last_evaluation_context",
                "return_EAX": "last_return_eax",
            },
            "sample_count": len(normalized),
            "maximum_sample_count": MAX_SAMPLES,
            "final_total_pre_call_count": total_pre,
            "final_total_post_call_count": total_post,
            "final_callsites": copy_rows(final_rows),
        },
        "evaluated_days": {
            "observable": evaluated_observable,
            "site_0": final_rows[0]["last_return_eax"]
            if evaluated_observable
            else None,
            "site_1": final_rows[1]["last_return_eax"]
            if evaluated_observable
            else None,
            "source": "native return EAX" if evaluated_observable else None,
        },
        "session_identity": (
            dict(session_identity_proof["identity"])
            if session_identity_proof["ok"] is True
            else None
        ),
        "readiness": {
            "promoted": False,
            "public_readiness_changed": False,
            "reason": "private observer evidence never changes production readiness",
        },
        "boundaries": {
            "heartbeat_or_install_only_is_evaluated_days": False,
            "no_hit_is_evaluated_days": False,
            "direct_evaluator_invoked_by_postprocessor": False,
            "context_effect_executed": False,
            "mutation_executed": False,
        },
    }


def copy_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: value for key, value in row.items()} for row in rows]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-report", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--expected-manifest-sha256", default=EXPECTED_MANIFEST_SHA256
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report_bytes = args.runner_report.read_bytes()
    manifest_bytes = args.manifest.read_bytes()
    if len(report_bytes) > MAX_REPORT_BYTES:
        raise SystemExit("runner report exceeds bounded postprocessor limit")
    result = analyze(
        json.loads(report_bytes.decode("utf-8")),
        json.loads(manifest_bytes.decode("utf-8")),
        report_sha256=sha256(report_bytes),
        manifest_sha256=sha256(manifest_bytes),
        expected_manifest_sha256=args.expected_manifest_sha256.upper(),
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["status"] in ("GREEN", "NO-GO") else 1


if __name__ == "__main__":
    raise SystemExit(main())
