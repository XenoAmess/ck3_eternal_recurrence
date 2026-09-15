#!/usr/bin/env python3
"""Create a reviewable receipt from a native picture-corpus acceptance report.

The live report intentionally contains uploaded source text and PNG payloads.  This
tool keeps the evidence needed to reproduce and audit the run while replacing
those duplicated payloads with their existing byte counts and SHA-256 receipts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("native report root must be an object")
    return value, raw


def _structured(call: object) -> dict[str, Any]:
    if not isinstance(call, dict):
        return {}
    value = call.get("structured_content")
    return value if isinstance(value, dict) else {}


def _false_keys(value: object) -> list[str]:
    if not isinstance(value, dict):
        return []
    return sorted(str(key) for key, item in value.items() if item is not True)


def _receipt(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    kept = (
        "path",
        "bytes",
        "source_bytes",
        "source_sha256",
        "png_bytes",
        "png_sha256",
        "sha256",
        "logical_layers",
        "colored_emblem_blocks",
        "instances",
        "lines",
        "payload_kind",
        "raw_bytes",
        "raw_sha256",
        "wire_bytes",
        "wire_sha256",
        "line_endings_normalized",
        "structure",
        "semantic_projection",
    )
    return {key: value[key] for key in kept if key in value}


def _compact_calibration(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    complete = _structured(
        value.get("anchors_complete")
        if value.get("anchors_complete") is not None
        else value.get("complete")
    )
    calibration = complete.get("calibration")
    if not isinstance(calibration, dict):
        calibration = complete
    kept = (
        "calibrationId",
        "calibration_id",
        "framebufferSize",
        "rect",
        "differenceThreshold",
        "candidateComponentCount",
        "changedPixels",
        "captureWidth",
        "captureHeight",
        "contentRect",
        "selectedPixels",
        "beginPixelSha256",
        "completePixelSha256",
        "maskPngSha256",
        "selectionMaskSha256",
        "referenceIndependent",
        "fixedScreenCoordinatesUsed",
        "usesOcr",
        "usesKeyboard",
        "usesMouse",
        "route",
        "routeStable",
        "schema",
        "schemaVersion",
        "uvRegistered",
        "anchorPositions",
        "observedAnchorCenters",
        "canonicalToFramebufferAffine",
        "reprojectionErrors",
        "maximumReprojectionError",
        "maximumAllowedReprojectionError",
        "anchorDifferenceThreshold",
        "anchorBasePixelSha256",
        "anchorsCompletePixelSha256",
    )
    return {
        "ok": value.get("ok"),
        "calibration_id": value.get("calibration_id"),
        "checks": value.get("checks"),
        "failed_checks": _false_keys(value.get("checks")),
        "receipt": {key: calibration[key] for key in kept if key in calibration},
    }


def _compact_case(value: object, crop_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("picture-corpus case must be an object")
    identifier = value.get("id")
    if not isinstance(identifier, str):
        raise ValueError("picture-corpus case is missing a string id")

    roundtrip = value.get("roundtrip")
    if not isinstance(roundtrip, dict):
        roundtrip = {}
    native_copy = _structured(roundtrip.get("native_copy"))
    framebuffer = value.get("framebuffer")
    if not isinstance(framebuffer, dict):
        framebuffer = {}
    framebuffer_body = _structured(framebuffer.get("call"))
    comparison = framebuffer_body.get("comparison")
    if not isinstance(comparison, dict):
        comparison = {}
    best_match = comparison.get("bestMatch")
    if not isinstance(best_match, dict):
        best_match = {}

    roundtrip_checks = roundtrip.get("checks")
    semantic_checks = roundtrip.get("semantic_checks")
    framebuffer_checks = framebuffer.get("checks")
    best_kept = (
        "contentRect",
        "alignedContentPngBytes",
        "alignedContentPngSha256",
        "cropPngBytes",
        "cropPngSha256",
        "selectedPixels",
    )
    metrics = comparison.get("metrics")
    if not isinstance(metrics, dict):
        metrics = {}
    metric_kept = (
        "contract",
        "maskPixels",
        "meanAbsoluteError",
        "colorMse",
        "edgeLoss",
    )
    return {
        "id": identifier,
        "ok": value.get("ok"),
        "source": _receipt(value.get("source")),
        "reference": _receipt(value.get("reference")),
        "roundtrip": {
            "ok": roundtrip.get("ok"),
            "binding_mode": roundtrip.get("binding_mode"),
            "chunk_count": roundtrip.get("chunk_count"),
            "checks": roundtrip_checks,
            "failed_checks": _false_keys(roundtrip_checks),
            "semantic_checks": semantic_checks,
            "failed_semantic_checks": _false_keys(semantic_checks),
            "output_structure": roundtrip.get("output_structure"),
            "native_copy": _receipt(native_copy),
        },
        "framebuffer_ready_after_native_apply": value.get(
            "framebuffer_ready_after_native_apply"
        ),
        "framebuffer": {
            "ok": framebuffer.get("ok"),
            "checks": framebuffer_checks,
            "failed_checks": _false_keys(framebuffer_checks),
            "thresholds": framebuffer.get("thresholds"),
            "worst_spatial_mean_absolute_error": framebuffer.get(
                "worst_spatial_mean_absolute_error"
            ),
            # The full 8x8 spatial matrix remains in the immutable raw report.
            # Keeping only its already-computed maximum makes this review receipt
            # compact enough to inspect while preserving every declared gate.
            "metrics": {key: metrics[key] for key in metric_kept if key in metrics},
            "best_match": {
                key: best_match[key] for key in best_kept if key in best_match
            },
        },
        "native_crop": _receipt(crop_by_id.get(identifier)),
    }


def summarize(report: dict[str, Any], raw: bytes, source_path: Path) -> dict[str, Any]:
    sequence = report.get("sequence")
    if not isinstance(sequence, dict):
        raise ValueError("native report has no sequence object")
    corpus = sequence.get("picture_corpus")
    if not isinstance(corpus, dict):
        raise ValueError("native report has no picture_corpus object")
    cases = corpus.get("cases")
    if not isinstance(cases, list):
        raise ValueError("native report picture_corpus has no cases array")
    crop_rows = report.get("picture_corpus_native_crops")
    crop_by_id = {
        row["id"]: row
        for row in crop_rows
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    } if isinstance(crop_rows, list) else {}

    compact_cases = [_compact_case(value, crop_by_id) for value in cases]
    return {
        "schema": "ck3-coat-of-arms-picture-corpus-native-summary-v1",
        "source_report": {
            "path": source_path.as_posix(),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest().upper(),
        },
        "repository_head": report.get("repository_head"),
        "created_at": report.get("created_at"),
        "elapsed_seconds": report.get("elapsed_seconds"),
        "steam": report.get("steam"),
        "interaction_policy": report.get("interaction_policy"),
        "shared_ck3_slot": report.get("shared_ck3_slot"),
        "overall": {
            "report_ok": report.get("ok"),
            "report_error": report.get("error"),
            "sequence_ok": sequence.get("ok"),
            "corpus_ok": corpus.get("ok"),
            "case_count": corpus.get("case_count"),
            "passed": corpus.get("passed"),
            "failed": corpus.get("failed"),
        },
        "framebuffer_calibration": _compact_calibration(
            corpus.get("framebuffer_calibration")
        ),
        "cases": compact_cases,
        "cleanup": report.get("cleanup"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report, raw = _load(args.report)
    summary = summarize(report, raw, args.report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
