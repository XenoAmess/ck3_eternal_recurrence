#!/usr/bin/env python3
"""Read-only final completion gate for the ZhongGuo phase-two promo.

The gate consumes existing xar_promo candidate, probe, audit and export files
plus two project review receipts and one real publication receipt.  It hashes
and cross-binds those files but never creates media, exports, or publishes.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlparse


KIND = "zg361_phase2_final_promo_completion"
ATTESTATION_KIND = "zg361_phase2_final_promo_completion_attestation"
REVIEW_KIND = "zg361_phase2_1x_review_receipt"
PUBLISH_KIND = "zg361_phase2_publish_receipt"
DELIVERABLE_ID = "zhongguo-361-phase2-video"
EXPORT_MANIFEST_NAME = "release-bundle-manifest.json"
_SHA = re.compile(r"^[0-9A-Fa-f]{64}$")
PENDING_CODES = (
    "candidate_media_pending",
    "claims_audit_pending",
    "review_round_1_pending",
    "review_round_2_pending",
    "export_pending",
    "publish_target_pending",
    "publish_pending",
)


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
    if not (
        isinstance(value.get("bytes"), int)
        and not isinstance(value.get("bytes"), bool)
        and value.get("bytes") == record["bytes"]
        and isinstance(value.get("sha256"), str)
        and _SHA.fullmatch(str(value["sha256"])) is not None
        and str(value["sha256"]).upper() == record["sha256"]
    ):
        return None
    return path, record


def _timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _publish_locator(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    hostname = (parsed.hostname or "").casefold()
    reserved = (
        not hostname
        or hostname == "localhost"
        or hostname.endswith(".invalid")
        or hostname.endswith(".test")
        or hostname in {"example.com", "example.org", "example.net"}
    )
    return (
        parsed.scheme == "https"
        and not reserved
        and bool(parsed.path not in {"", "/"} or parsed.query)
    )


def _media_binding(value: object, record: Mapping[str, object]) -> bool:
    return (
        isinstance(value, Mapping)
        and value.get("bytes") == record.get("bytes")
        and isinstance(value.get("sha256"), str)
        and str(value["sha256"]).upper() == record.get("sha256")
    )


def validate_final_promo_completion(
    attestation_path: Path | None,
    *,
    footage_intake: Mapping[str, object],
    publish_target: Mapping[str, object] | None = None,
    deliverable_id: str = DELIVERABLE_ID,
) -> dict[str, object]:
    """Return COMPLETE only when every immutable final boundary is closed."""

    if not isinstance(deliverable_id, str) or not deliverable_id.strip():
        raise ValueError("deliverable_id must be a non-empty string")

    footage_green = footage_intake.get("result") == "GREEN"
    target_gate = publish_target if isinstance(publish_target, Mapping) else {}
    target_green = target_gate.get("result") == "GREEN"
    target = target_gate.get("target") if isinstance(target_gate.get("target"), Mapping) else {}
    target_authority = (
        target_gate.get("authority")
        if isinstance(target_gate.get("authority"), Mapping)
        else {}
    )
    result: dict[str, object] = {
        "schema_version": 1,
        "kind": KIND,
        "result": "RED",
        "status": "pending",
        "reason_codes": ([] if footage_green else ["footage_pending"]),
        "attestation": None,
        "deliverable_artifact_id": deliverable_id,
        "publish_target": dict(target_gate),
        "candidate_media": None,
        "checks": {
            "footage_green": footage_green,
            "candidate_media_verified": False,
            "claims_audit_verified": False,
            "review_round_1_verified": False,
            "review_round_2_verified": False,
            "export_verified": False,
            "publish_target_verified": target_green,
            "publish_verified": False,
        },
        "execution_attestation": {
            "media_generated": False,
            "export_performed": False,
            "publish_performed": False,
        },
        "errors": [],
    }
    reason_codes = list(result["reason_codes"])
    checks = result["checks"]
    assert isinstance(checks, dict)
    errors: list[str] = []
    if attestation_path is None or not attestation_path.expanduser().resolve().is_file():
        reason_codes.extend(PENDING_CODES)
        result["reason_codes"] = reason_codes
        result["errors"] = ["completion_attestation_missing"]
        return result

    attestation = attestation_path.expanduser().resolve()
    try:
        payload = _json(attestation)
        result["attestation"] = _sha256(attestation)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        reason_codes.extend(PENDING_CODES)
        result["reason_codes"] = reason_codes
        result["errors"] = [f"completion_attestation_invalid:{type(error).__name__}"]
        return result
    if payload.get("schema_version") != 1 or payload.get("kind") != ATTESTATION_KIND:
        errors.append("completion_attestation_header_invalid")
    attempt_id = payload.get("attempt_id")
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        errors.append("attempt_id_invalid")

    candidate = payload.get("candidate") if isinstance(payload.get("candidate"), Mapping) else {}
    media_bound = _bound_file(candidate.get("media"))
    probe_bound = _bound_file(candidate.get("bound_probe"))
    run_bound = _bound_file(candidate.get("run_manifest"))
    media_path = media_bound[0] if media_bound else None
    media_record = media_bound[1] if media_bound else {}
    candidate_ok = bool(media_bound and probe_bound and run_bound)
    probe_payload: Mapping[str, object] = {}
    run_payload: Mapping[str, object] = {}
    if candidate_ok:
        try:
            probe_payload = _json(probe_bound[0])
            run_payload = _json(run_bound[0])
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            candidate_ok = False
    if candidate_ok:
        subject = probe_payload.get("subject")
        ffprobe = probe_payload.get("ffprobe") if isinstance(probe_payload.get("ffprobe"), Mapping) else {}
        streams = ffprobe.get("streams") if isinstance(ffprobe.get("streams"), list) else []
        format_row = ffprobe.get("format") if isinstance(ffprobe.get("format"), Mapping) else {}
        videos = [row for row in streams if isinstance(row, Mapping) and row.get("codec_type") == "video"]
        audios = [row for row in streams if isinstance(row, Mapping) and row.get("codec_type") == "audio"]
        try:
            duration = float(format_row.get("duration"))
        except (TypeError, ValueError, OverflowError):
            duration = 0.0
        probe_filename = format_row.get("filename")
        probe_path_ok = (
            isinstance(probe_filename, str)
            and Path(probe_filename).expanduser().resolve() == media_path
        )
        video_ok = len(videos) == 1 and (
            videos[0].get("codec_name") == "h264"
            and videos[0].get("pix_fmt") == "yuv420p"
            and videos[0].get("width") == 1920
            and videos[0].get("height") == 1080
        )
        audio_ok = len(audios) == 1 and (
            audios[0].get("codec_name") == "aac"
            and str(audios[0].get("sample_rate")) == "48000"
            and audios[0].get("channels") == 2
        )
        artifacts = run_payload.get("artifacts") if isinstance(run_payload.get("artifacts"), list) else []
        deliverables = [
            row for row in artifacts
            if isinstance(row, Mapping)
            and row.get("id") == deliverable_id
            and row.get("role") == "deliverable"
            and _media_binding(row, media_record)
        ]
        signoffs = run_payload.get("signoffs") if isinstance(run_payload.get("signoffs"), list) else []
        matching_signoffs = [
            row for row in signoffs
            if isinstance(row, Mapping)
            and row.get("artifact_id") == deliverable_id
        ]
        latest_signoff = matching_signoffs[-1] if matching_signoffs else {}
        deliverable_path_ok = len(deliverables) == 1 and (
            isinstance(deliverables[0].get("path"), str)
            and not Path(str(deliverables[0]["path"])).is_absolute()
            and (run_bound[0].parent / str(deliverables[0]["path"])).resolve().is_file()
        )
        signoff_ok = (
            latest_signoff.get("decision") == "approved"
            and _media_binding(
                {
                    "bytes": latest_signoff.get("artifact_bytes"),
                    "sha256": latest_signoff.get("artifact_sha256"),
                },
                media_record,
            )
            and isinstance(latest_signoff.get("reviewer"), str)
            and bool(str(latest_signoff["reviewer"]).strip())
            and _timestamp(latest_signoff.get("reviewed_at"))
        )
        candidate_ok = (
            probe_payload.get("format_version") == 1
            and probe_payload.get("kind") == "xar-promo-bound-media-probe"
            and _media_binding(subject, media_record)
            and probe_path_ok
            and str(format_row.get("size")) == str(media_record.get("bytes"))
            and 0 < duration < 1200
            and video_ok
            and audio_ok
            and run_payload.get("format_version") == 1
            and run_payload.get("kind") == "xar_promo_run_manifest"
            and isinstance(run_payload.get("run"), Mapping)
            and run_payload["run"].get("id") == attempt_id
            and deliverable_path_ok
            and signoff_ok
        )
    checks["candidate_media_verified"] = candidate_ok
    result["candidate_media"] = dict(media_record) if candidate_ok else None

    audit_bound = _bound_file(payload.get("claims_audit"))
    audit_ok = bool(audit_bound and candidate_ok)
    audit_payload: Mapping[str, object] = {}
    if audit_ok:
        try:
            audit_payload = _json(audit_bound[0])
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            audit_ok = False
    if audit_ok:
        automated = audit_payload.get("automated_audit") if isinstance(audit_payload.get("automated_audit"), Mapping) else {}
        manual = audit_payload.get("manual_signoff")
        audit_ok = (
            audit_payload.get("format_version") == 1
            and audit_payload.get("kind") == "xar_promo_audit_report"
            and _media_binding(audit_payload.get("subject"), media_record)
            and automated.get("status") == "passed"
            and automated.get("subject_sha256") == media_record.get("sha256")
            and automated.get("manual_approval_granted") is False
            and manual == {"state": "not-provided"}
        )
    checks["claims_audit_verified"] = audit_ok

    reviews = payload.get("reviews") if isinstance(payload.get("reviews"), list) else []
    review_payloads: list[Mapping[str, object]] = []
    for value in reviews:
        bound = _bound_file(value)
        if bound is None:
            continue
        try:
            review_payloads.append(_json(bound[0]))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            pass
    review_scopes = ("claims-and-source-pass", "final-candidate-pass")
    review_valid: list[bool] = []
    for scope in review_scopes:
        matches = [row for row in review_payloads if row.get("scope") == scope]
        review_valid.append(
            len(reviews) == 2
            and len(review_payloads) == 2
            and len(matches) == 1
            and matches[0].get("schema_version") == 1
            and matches[0].get("kind") == REVIEW_KIND
            and matches[0].get("result") == "GREEN"
            and matches[0].get("attempt_id") == attempt_id
            and matches[0].get("playback_speed") == 1
            and matches[0].get("full_duration_reviewed") is True
            and matches[0].get("decision") == "approved"
            and isinstance(matches[0].get("reviewer"), str)
            and bool(str(matches[0]["reviewer"]).strip())
            and _timestamp(matches[0].get("reviewed_at"))
            and _media_binding(matches[0].get("candidate_media"), media_record)
            and audit_bound is not None
            and matches[0].get("claims_audit_sha256") == audit_bound[1]["sha256"]
        )
    reviewers = [
        str(row.get("reviewer"))
        for row in review_payloads
        if row.get("scope") in review_scopes
    ]
    independent = len(reviewers) == 2 and len(set(reviewers)) == 2
    checks["review_round_1_verified"] = review_valid[0] and independent
    checks["review_round_2_verified"] = review_valid[1] and independent

    export = payload.get("export") if isinstance(payload.get("export"), Mapping) else {}
    bundle_raw = export.get("bundle_root")
    bundle_root = (
        Path(bundle_raw).expanduser().resolve()
        if isinstance(bundle_raw, str) and Path(bundle_raw).is_absolute()
        else None
    )
    export_manifest_bound = _bound_file(export.get("manifest"))
    export_ok = bool(bundle_root and bundle_root.is_dir() and export_manifest_bound and run_bound and candidate_ok)
    exported_record: Mapping[str, object] = {}
    if export_ok:
        try:
            export_payload = _json(export_manifest_bound[0])
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            export_ok = False
            export_payload = {}
    else:
        export_payload = {}
    if export_ok:
        files = export_payload.get("files") if isinstance(export_payload.get("files"), list) else []
        exported = [row for row in files if isinstance(row, Mapping) and row.get("category") == "deliverable"]
        if len(exported) == 1:
            exported_record = exported[0]
            exported_path = bundle_root / str(exported[0].get("path"))
            exported_bound = _bound_file({**dict(exported[0]), "path": str(exported_path)})
        else:
            exported_bound = None
        source_run = export_payload.get("source_run") if isinstance(export_payload.get("source_run"), Mapping) else {}
        expected_files = {
            str(row.get("path"))
            for row in files
            if isinstance(row, Mapping) and isinstance(row.get("path"), str)
        }
        actual_files = {
            path.relative_to(bundle_root).as_posix()
            for path in bundle_root.rglob("*")
            if path.is_file()
        }
        exported_source = (
            exported_record.get("source")
            if isinstance(exported_record.get("source"), Mapping)
            else {}
        )
        export_ok = (
            export_manifest_bound[0] == bundle_root / EXPORT_MANIFEST_NAME
            and export_payload.get("format_version") == 1
            and export_payload.get("kind") == "xar_promo_release_bundle"
            and source_run.get("run_id") == attempt_id
            and source_run.get("bytes") == run_bound[1]["bytes"]
            and str(source_run.get("sha256", "")).upper() == run_bound[1]["sha256"]
            and export_payload.get("operations")
            == {
                "network_used": False,
                "publish_performed": False,
                "source_material_mutated": False,
            }
            and exported_bound is not None
            and _media_binding(exported_record, media_record)
            and exported_source.get("kind") == "run-artifact"
            and exported_source.get("artifact_id") == deliverable_id
            and exported_source.get("role") == "deliverable"
            and _media_binding(exported_source, media_record)
            and actual_files == expected_files | {EXPORT_MANIFEST_NAME}
        )
    checks["export_verified"] = export_ok

    publish_bound = _bound_file(payload.get("publication"))
    publish_ok = bool(
        target_green and publish_bound and export_ok and export_manifest_bound
    )
    if publish_ok:
        try:
            publish_payload = _json(publish_bound[0])
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            publish_ok = False
            publish_payload = {}
    else:
        publish_payload = {}
    if publish_ok:
        locator = publish_payload.get("locator")
        publish_ok = (
            publish_payload.get("schema_version") == 1
            and publish_payload.get("kind") == PUBLISH_KIND
            and publish_payload.get("result") == "GREEN"
            and publish_payload.get("attempt_id") == attempt_id
            and publish_payload.get("target_id") == target.get("target_id")
            and publish_payload.get("platform") == target.get("platform")
            and publish_payload.get("account_id") == target.get("account_id")
            and isinstance(target_authority.get("sha256"), str)
            and publish_payload.get("target_authority_sha256")
            == target_authority.get("sha256")
            and publish_payload.get("remote_verified") is True
            and _timestamp(publish_payload.get("published_at"))
            and _publish_locator(locator)
            and isinstance(locator, str)
            and isinstance(target.get("locator_prefix"), str)
            and locator.startswith(str(target["locator_prefix"]))
            and _media_binding(publish_payload.get("candidate_media"), media_record)
            and _media_binding(publish_payload.get("exported_media"), media_record)
            and _media_binding(
                publish_payload.get("export_manifest"), export_manifest_bound[1]
            )
        )
    checks["publish_verified"] = publish_ok

    code_by_check = {
        "candidate_media_verified": "candidate_media_pending",
        "claims_audit_verified": "claims_audit_pending",
        "review_round_1_verified": "review_round_1_pending",
        "review_round_2_verified": "review_round_2_pending",
        "export_verified": "export_pending",
        "publish_target_verified": "publish_target_pending",
        "publish_verified": "publish_pending",
    }
    reason_codes.extend(
        code for check, code in code_by_check.items() if checks[check] is not True
    )
    if errors:
        reason_codes.append("completion_attestation_invalid")
    result["reason_codes"] = list(dict.fromkeys(reason_codes))
    result["errors"] = errors
    if not result["reason_codes"]:
        result["result"] = "GREEN"
        result["status"] = "COMPLETE"
    return result


__all__ = [
    "ATTESTATION_KIND",
    "KIND",
    "PENDING_CODES",
    "PUBLISH_KIND",
    "REVIEW_KIND",
    "validate_final_promo_completion",
]
