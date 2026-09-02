#!/usr/bin/env python3
"""Aggregate two independently completed ZhongGuo phase-two promo cuts.

This tool is deliberately media-free.  It consumes hash-bound completion
reports (or the exact inputs used by the existing single-cut completion gate),
then enforces the boundaries that make two cuts two real deliverables.  It
never launches CK3, invokes TTS/FFmpeg, exports, reviews, or publishes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path

from zhongguo_phase2_capture_choreography import PHASE2_CAPTURE_SCENARIOS
from zhongguo_phase2_final_promo_completion import (
    ATTESTATION_KIND,
    KIND as SINGLE_COMPLETION_KIND,
    validate_final_promo_completion,
)
from zhongguo_phase2_promo_cuts import CUTS


KIND = "zg361_phase2_dual_cut_completion"
ATTESTATION_KIND_DUAL = "zg361_phase2_dual_cut_completion_attestation"
ROLES = tuple(cut.cut_id for cut in CUTS)
OUTPUT_NAMES = {
    cut.cut_id: cut.deliverable_relative_path.name for cut in CUTS
}
DELIVERABLE_IDS = {
    cut.cut_id: cut.deliverable_artifact_id for cut in CUTS
}
_SHA = re.compile(r"^[0-9A-Fa-f]{64}$")


def _sha256(path: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest().upper(),
    }


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return value


def _bound_file(value: object) -> tuple[Path, dict[str, object]] | None:
    if not isinstance(value, Mapping):
        return None
    raw_path = value.get("path")
    if not isinstance(raw_path, str) or not Path(raw_path).is_absolute():
        return None
    path = Path(raw_path).expanduser().resolve()
    if not path.is_file():
        return None
    record = _sha256(path)
    declared_sha = value.get("sha256")
    return (
        (path, record)
        if isinstance(value.get("bytes"), int)
        and not isinstance(value.get("bytes"), bool)
        and value.get("bytes") == record["bytes"]
        and isinstance(declared_sha, str)
        and _SHA.fullmatch(declared_sha) is not None
        and declared_sha.upper() == record["sha256"]
        else None
    )


def _contained(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _single_report(
    cut: Mapping[str, object], role: str | None = None
) -> tuple[dict[str, object] | None, str]:
    """Load an existing report or recompute it from exact receipt inputs."""

    completion = cut.get("completion")
    if not isinstance(completion, Mapping):
        return None, "completion_missing"
    mode = completion.get("mode")
    if mode == "report":
        bound = _bound_file(completion.get("report"))
        if bound is None:
            return None, "completion_report_not_hash_bound"
        try:
            return _json(bound[0]), ""
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            return None, "completion_report_invalid"
    if mode == "receipts":
        attestation = _bound_file(completion.get("attestation"))
        footage = _bound_file(completion.get("footage_intake"))
        target = _bound_file(completion.get("publish_target"))
        if attestation is None or footage is None or target is None:
            return None, "completion_receipts_not_hash_bound"
        try:
            footage_payload = _json(footage[0])
            target_payload = _json(target[0])
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            return None, "completion_receipts_invalid"
        expected_deliverable_id = (
            "zhongguo-361-phase2-video"
            if role is None
            else DELIVERABLE_IDS[role]
        )
        declared_deliverable_id = completion.get("deliverable_id")
        if (
            declared_deliverable_id is not None
            and declared_deliverable_id != expected_deliverable_id
        ):
            return None, "completion_deliverable_id_invalid"
        return (
            validate_final_promo_completion(
                attestation[0],
                footage_intake=footage_payload,
                publish_target=target_payload,
                deliverable_id=expected_deliverable_id,
            ),
            "",
        )
    return None, "completion_mode_invalid"


def _cut_identity(cut: Mapping[str, object], role: str) -> tuple[dict[str, object], list[str]]:
    errors: list[str] = []
    work_raw = cut.get("work_dir")
    work_dir = (
        Path(work_raw).expanduser().resolve()
        if isinstance(work_raw, str) and Path(work_raw).is_absolute()
        else None
    )
    if work_dir is None or not work_dir.is_dir():
        errors.append("work_dir_invalid")

    report, report_error = _single_report(cut, role)
    if report is None:
        errors.append(report_error)
        return {"role": role, "work_dir": None}, errors
    checks = report.get("checks") if isinstance(report.get("checks"), Mapping) else {}
    if not (
        report.get("schema_version") == 1
        and report.get("kind") == SINGLE_COMPLETION_KIND
        and report.get("result") == "GREEN"
        and report.get("status") == "COMPLETE"
        and report.get("reason_codes") == []
        and checks
        and all(value is True for value in checks.values())
    ):
        errors.append("single_cut_not_complete")
    if report.get("deliverable_artifact_id") != DELIVERABLE_IDS[role]:
        errors.append("deliverable_artifact_id_invalid")

    attestation = _bound_file(report.get("attestation"))
    candidate = _bound_file(report.get("candidate_media"))
    if attestation is None:
        errors.append("single_attestation_not_hash_bound")
    if candidate is None:
        errors.append("candidate_not_hash_bound")
    if attestation is None or candidate is None:
        return {"role": role, "work_dir": str(work_dir) if work_dir else None}, errors

    try:
        payload = _json(attestation[0])
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        errors.append("single_attestation_invalid")
        return {"role": role, "work_dir": str(work_dir) if work_dir else None}, errors
    attempt_id = payload.get("attempt_id")
    if payload.get("schema_version") != 1 or payload.get("kind") != ATTESTATION_KIND:
        errors.append("single_attestation_header_invalid")
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        errors.append("run_id_invalid")

    candidate_declared = payload.get("candidate")
    candidate_declared = candidate_declared if isinstance(candidate_declared, Mapping) else {}
    attested_candidate = _bound_file(candidate_declared.get("media"))
    if attested_candidate is None or attested_candidate[1] != candidate[1]:
        errors.append("candidate_report_attestation_mismatch")

    expected_name = OUTPUT_NAMES[role]
    if cut.get("output_name") != expected_name or candidate[0].name != expected_name:
        errors.append("output_name_invalid")

    export = payload.get("export") if isinstance(payload.get("export"), Mapping) else {}
    bundle_raw = export.get("bundle_root")
    bundle = (
        Path(bundle_raw).expanduser().resolve()
        if isinstance(bundle_raw, str) and Path(bundle_raw).is_absolute()
        else None
    )
    export_manifest = _bound_file(export.get("manifest"))
    exported_path: Path | None = None
    if bundle is None or export_manifest is None:
        errors.append("export_identity_missing")
    else:
        try:
            export_payload = _json(export_manifest[0])
            rows = export_payload.get("files") if isinstance(export_payload.get("files"), list) else []
            deliverables = [
                row for row in rows
                if isinstance(row, Mapping) and row.get("category") == "deliverable"
            ]
            if len(deliverables) == 1 and isinstance(deliverables[0].get("path"), str):
                exported_path = (bundle / str(deliverables[0]["path"])).resolve()
            if exported_path is None or exported_path.name != expected_name:
                errors.append("export_output_name_invalid")
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            errors.append("export_manifest_invalid")

    if work_dir is not None:
        owned = [attestation[0], candidate[0]]
        if bundle is not None:
            owned.append(bundle)
        if not all(_contained(path, work_dir) for path in owned):
            errors.append("work_dir_not_isolated")

    return {
        "role": role,
        "run_id": attempt_id,
        "work_dir": str(work_dir) if work_dir else None,
        "output_name": expected_name,
        "deliverable_artifact_id": DELIVERABLE_IDS[role],
        "candidate": candidate[1],
        "completion_attestation": attestation[1],
        "exported_path": str(exported_path) if exported_path else None,
        "single_completion_status": report.get("status"),
    }, errors


def _source_bindings(cut: Mapping[str, object]) -> tuple[dict[str, str], list[str]]:
    expected = [row.span_id for row in PHASE2_CAPTURE_SCENARIOS]
    rows = cut.get("source_spans")
    errors: list[str] = []
    if not isinstance(rows, list) or len(rows) != len(expected):
        return {}, ["source_spans_must_contain_exactly_eight_rows"]
    bound: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, Mapping) or row.get("span_id") not in expected:
            errors.append("source_span_id_invalid")
            continue
        span_id = str(row["span_id"])
        if span_id in bound:
            errors.append("source_span_id_duplicate")
            continue
        media = _bound_file(row.get("media"))
        if media is None:
            errors.append(f"source_span_not_hash_bound:{span_id}")
            continue
        bound[span_id] = str(media[1]["sha256"])
    if list(bound) != expected:
        errors.append("source_span_order_or_coverage_invalid")
    return bound, errors


def validate_dual_cut_completion(attestation_path: Path) -> dict[str, object]:
    """Return COMPLETE only when both independent cuts are fully complete."""

    path = attestation_path.expanduser().resolve()
    result: dict[str, object] = {
        "schema_version": 1,
        "kind": KIND,
        "result": "RED",
        "status": "pending",
        "reason_codes": [],
        "attestation": None,
        "cuts": [],
        "checks": {
            "roles_exact": False,
            "both_individually_complete": False,
            "run_ids_distinct": False,
            "work_dirs_distinct": False,
            "candidate_sha256_distinct": False,
            "output_names_exact_and_distinct": False,
            "same_eight_immutable_source_spans": False,
        },
        "errors": [],
        "execution_attestation": {
            "ck3_started": False,
            "tts_started": False,
            "ffmpeg_started": False,
            "media_generated": False,
            "export_performed": False,
            "publish_performed": False,
        },
    }
    errors: list[str] = []
    try:
        payload = _json(path)
        result["attestation"] = _sha256(path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        result["reason_codes"] = ["dual_attestation_invalid", "both_cuts_pending"]
        result["errors"] = [f"dual_attestation_invalid:{type(error).__name__}"]
        return result
    if payload.get("schema_version") != 1 or payload.get("kind") != ATTESTATION_KIND_DUAL:
        errors.append("dual_attestation_header_invalid")
    cuts = payload.get("cuts") if isinstance(payload.get("cuts"), list) else []
    roles = [row.get("role") for row in cuts if isinstance(row, Mapping)]
    checks = result["checks"]
    assert isinstance(checks, dict)
    checks["roles_exact"] = len(cuts) == 2 and roles == list(ROLES)
    if not checks["roles_exact"]:
        errors.append("roles_must_be_character_then_institution")

    identities: list[dict[str, object]] = []
    bindings: list[dict[str, str]] = []
    for index, role in enumerate(ROLES):
        cut = cuts[index] if index < len(cuts) and isinstance(cuts[index], Mapping) else {}
        identity, cut_errors = _cut_identity(cut, role)
        source, source_errors = _source_bindings(cut)
        identity["source_spans"] = source
        identity["errors"] = cut_errors + source_errors
        identities.append(identity)
        bindings.append(source)
        errors.extend(f"{role}:{error}" for error in identity["errors"])
    result["cuts"] = identities

    checks["both_individually_complete"] = all(
        row.get("single_completion_status") == "COMPLETE" and not row.get("errors")
        for row in identities
    )
    run_ids = [row.get("run_id") for row in identities]
    work_dirs = [str(row.get("work_dir", "")).casefold() for row in identities]
    candidate_shas = [
        row.get("candidate", {}).get("sha256")
        if isinstance(row.get("candidate"), Mapping) else None
        for row in identities
    ]
    output_names = [row.get("output_name") for row in identities]
    checks["run_ids_distinct"] = all(run_ids) and len(set(run_ids)) == 2
    checks["work_dirs_distinct"] = all(work_dirs) and len(set(work_dirs)) == 2
    checks["candidate_sha256_distinct"] = all(candidate_shas) and len(set(candidate_shas)) == 2
    checks["output_names_exact_and_distinct"] = (
        output_names == [OUTPUT_NAMES[role] for role in ROLES]
        and len(set(output_names)) == 2
    )
    checks["same_eight_immutable_source_spans"] = (
        len(bindings) == 2
        and len(bindings[0]) == 8
        and bindings[0] == bindings[1]
    )
    for name, valid in checks.items():
        if valid is not True:
            errors.append(name)
    result["errors"] = list(dict.fromkeys(errors))
    result["reason_codes"] = [] if not result["errors"] else ["both_cuts_pending"]
    if not result["errors"]:
        result["result"] = "GREEN"
        result["status"] = "COMPLETE"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error(f"refusing to overwrite existing output: {output}")
    report = validate_dual_cut_completion(args.input)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"output": str(output), "result": report["result"], "status": report["status"]}))
    return 0 if report["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
