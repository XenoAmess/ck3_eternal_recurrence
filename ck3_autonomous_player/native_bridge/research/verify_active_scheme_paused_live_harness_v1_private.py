#!/usr/bin/env python3
"""Verify one GREEN raw-first active-scheme paused-live harness report."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from active_scheme_paused_live_harness_v1_private import (
    REPORT_SCHEMA,
    STAGES,
    CandidateError,
    load_candidate,
    validate_completed_stage_payloads,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def verify_report(
    report_path: Path,
    candidate_manifest: Path,
    expected_candidate_sha256: str,
    ledger_dir: Path,
) -> list[str]:
    errors: list[str] = []
    try:
        candidate = load_candidate(candidate_manifest, expected_candidate_sha256)
        report = json.loads(report_path.read_bytes())
    except (CandidateError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [str(exc)]
    if not isinstance(report, dict) or report.get("schema") != REPORT_SCHEMA:
        return ["report schema mismatch"]
    if report.get("candidate_manifest_sha256") != candidate.manifest_sha256:
        errors.append("candidate manifest hash mismatch")
    if report.get("candidate_id") != candidate.candidate_id:
        errors.append("candidate id mismatch")
    if report.get("interaction_key") != candidate.interaction_key or report.get("scheme_type_key") != candidate.scheme_type_key:
        errors.append("interaction/type mismatch")
    if report.get("status") != "GREEN" or report.get("failure") != "none":
        errors.append(f"report is RED: {report.get('failure')}")
    if report.get("submit_call_count") != 1:
        errors.append("submit call count is not exactly one")
    if report.get("same_candidate_retry_allowed") is not False:
        errors.append("same-candidate retry was not disabled")
    events = report.get("events")
    if not isinstance(events, list) or [event.get("stage") for event in events if isinstance(event, dict)] != list(STAGES):
        errors.append("stage order mismatch")
    elif any(
        event.get("ordinal") != index + 1
        or event.get("status") != "raw_persisted_before_parse"
        for index, event in enumerate(events)
    ):
        errors.append("stage event is not raw-first GREEN")
    raw_artifacts = report.get("raw_artifacts")
    raw_payloads: dict[str, dict[str, Any]] = {}
    if not isinstance(raw_artifacts, dict) or set(raw_artifacts) != set(STAGES):
        errors.append("raw artifact set mismatch")
    else:
        root = report_path.parent.resolve()
        for stage in STAGES:
            binding = raw_artifacts[stage]
            if not isinstance(binding, dict) or not isinstance(binding.get("path"), str):
                errors.append(f"invalid raw binding: {stage}")
                continue
            path = (root / binding["path"]).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                errors.append(f"raw path leaves evidence root: {stage}")
                continue
            if not path.is_file():
                errors.append(f"missing raw artifact: {stage}")
            elif path.stat().st_size != binding.get("size") or _sha256(path) != binding.get("sha256"):
                errors.append(f"raw artifact binding mismatch: {stage}")
            else:
                try:
                    payload = json.loads(path.read_bytes())
                except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    errors.append(f"raw artifact JSON invalid {stage}: {exc}")
                else:
                    if isinstance(payload, dict):
                        raw_payloads[stage] = payload
                    else:
                        errors.append(f"raw artifact is not an object: {stage}")
    if set(raw_payloads) == set(STAGES):
        try:
            validate_completed_stage_payloads(candidate, raw_payloads)
        except (CandidateError, KeyError, TypeError) as exc:
            errors.append(f"persisted stage contract mismatch: {exc}")
    marker_name = report.get("attempt_marker")
    marker = ledger_dir / marker_name if isinstance(marker_name, str) else None
    if marker is None or not marker.is_file():
        errors.append("attempt marker missing")
    else:
        try:
            marker_payload: Any = json.loads(marker.read_bytes())
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"attempt marker invalid: {exc}")
        else:
            if (
                not isinstance(marker_payload, dict)
                or marker_payload.get("candidate_manifest_sha256") != candidate.manifest_sha256
                or marker_payload.get("consumed") is not True
                or marker_payload.get("status") != "GREEN"
                or marker_payload.get("submit_call_count") != 1
            ):
                errors.append("attempt marker contract mismatch")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--expected-candidate-sha256", required=True)
    parser.add_argument("--ledger-dir", type=Path, required=True)
    args = parser.parse_args()
    errors = verify_report(
        args.report,
        args.candidate,
        args.expected_candidate_sha256,
        args.ledger_dir,
    )
    if errors:
        for error in errors:
            print(f"RED: {error}", file=sys.stderr)
        return 1
    print("GREEN: active-scheme paused-live report is raw-first, hash-bound, single-submit, fresh, and consumed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
