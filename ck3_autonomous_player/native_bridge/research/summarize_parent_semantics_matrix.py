"""Freeze a compact, portable receipt for the native CoA parent matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _source_text(call: object) -> str:
    value = _object(call, "native Copy call")
    structured = _object(value.get("structured_content"), "native Copy result")
    source = structured.get("source")
    if not isinstance(source, str) or not source:
        raise ValueError("native Copy source is missing")
    return source


def _calibration_receipt(value: object) -> dict[str, object]:
    calibration = _object(value, "framebuffer calibration")
    completed_call = _object(
        calibration.get("anchors_complete"), "completed calibration call"
    )
    completed = _object(
        completed_call.get("structured_content"),
        "completed calibration payload",
    )
    surface = _object(completed.get("surface"), "surface calibration")
    return {
        "ok": calibration.get("ok"),
        "calibration_id": calibration.get("calibration_id"),
        "checks": calibration.get("checks"),
        "schema": completed.get("schema"),
        "schema_version": completed.get("schemaVersion"),
        "framebuffer_size": completed.get("framebufferSize"),
        "rect": completed.get("rect"),
        "surface": {
            "schema": surface.get("schema"),
            "rect": surface.get("rect"),
            "difference_threshold": surface.get("differenceThreshold"),
            "candidate_component_count": surface.get(
                "candidateComponentCount"
            ),
            "changed_pixels": surface.get("changedPixels"),
            "selected_pixels": surface.get("selectedPixels"),
            "begin_pixel_sha256": surface.get("beginPixelSha256"),
            "complete_pixel_sha256": surface.get("completePixelSha256"),
            "mask_png_sha256": surface.get("maskPngSha256"),
            "reference_independent": surface.get("referenceIndependent"),
            "fixed_screen_coordinates_used": surface.get(
                "fixedScreenCoordinatesUsed"
            ),
        },
        "anchor_positions": completed.get("anchorPositions"),
        "observed_anchor_centers": completed.get("observedAnchorCenters"),
        "canonical_to_framebuffer_affine": completed.get(
            "canonicalToFramebufferAffine"
        ),
        "reprojection_errors": completed.get("reprojectionErrors"),
        "maximum_reprojection_error": completed.get(
            "maximumReprojectionError"
        ),
        "maximum_allowed_reprojection_error": completed.get(
            "maximumAllowedReprojectionError"
        ),
        "anchor_base_pixel_sha256": completed.get("anchorBasePixelSha256"),
        "anchors_complete_pixel_sha256": completed.get(
            "anchorsCompletePixelSha256"
        ),
        "reference_independent": completed.get("referenceIndependent"),
        "uv_registered": completed.get("uvRegistered"),
        "fixed_screen_coordinates_used": completed.get(
            "fixedScreenCoordinatesUsed"
        ),
        "uses_ocr": completed.get("usesOcr"),
        "uses_keyboard": completed.get("usesKeyboard"),
        "uses_mouse": completed.get("usesMouse"),
        "ready_for_comparison": completed.get("readyForComparison"),
        "route": completed.get("route"),
        "route_stable": completed.get("routeStable"),
        "connection_generation": completed.get("connectionGeneration"),
    }


def _pixel_metrics(
    artifact_dir: Path, left_id: str, right_id: str
) -> dict[str, object]:
    with Image.open(artifact_dir / f"{left_id}.png") as left_image:
        left = np.asarray(left_image.convert("RGBA"), dtype=np.int16)
    with Image.open(artifact_dir / f"{right_id}.png") as right_image:
        right = np.asarray(right_image.convert("RGBA"), dtype=np.int16)
    if left.shape != right.shape:
        raise ValueError(f"diagnostic pair dimensions differ: {left_id}/{right_id}")
    absolute = np.abs(left - right)
    differing = np.any(absolute != 0, axis=2)
    coordinates = np.argwhere(differing)
    bounds = None
    if coordinates.size:
        y_min, x_min = coordinates.min(axis=0).tolist()
        y_max, x_max = coordinates.max(axis=0).tolist()
        bounds = {
            "x": int(x_min),
            "y": int(y_min),
            "width": int(x_max - x_min + 1),
            "height": int(y_max - y_min + 1),
        }
    return {
        "left": left_id,
        "right": right_id,
        "width": int(left.shape[1]),
        "height": int(left.shape[0]),
        "pixel_exact": bool(not np.any(differing)),
        "differing_pixels": int(np.count_nonzero(differing)),
        "mean_absolute_channel_error": float(absolute.mean()),
        "max_channel_error": int(absolute.max()),
        "alpha_differing_pixels": int(np.count_nonzero(absolute[:, :, 3])),
        "difference_bounds": bounds,
    }


def summarize(report_path: Path, artifact_dir: Path) -> dict[str, object]:
    report_path = report_path.resolve()
    artifact_dir = artifact_dir.resolve()
    report = _object(
        json.loads(report_path.read_text(encoding="utf-8")), "live report"
    )
    sequence = _object(report.get("sequence"), "sequence")
    matrix = _object(
        sequence.get("parent_semantics_matrix"), "parent semantics matrix"
    )
    interaction = _object(report.get("interaction_policy"), "interaction policy")
    steam = _object(report.get("steam"), "steam")
    cleanup = _object(report.get("cleanup"), "cleanup")
    if not (
        report.get("ok") is True
        and sequence.get("ok") is True
        and matrix.get("ok") is True
        and interaction.get("mcp_only") is True
        and interaction.get("uses_ocr") is False
        and interaction.get("uses_keyboard") is False
        and interaction.get("uses_mouse") is False
        and steam.get("offline") is True
        and cleanup.get("cleanup_proven") is True
        and cleanup.get("tree_gone") is True
    ):
        raise ValueError("live report does not satisfy the native evidence gate")

    crop_receipts = report.get("parent_semantics_native_crops")
    cases = matrix.get("cases")
    pairs = matrix.get("pairs")
    if not isinstance(crop_receipts, list) or not isinstance(cases, list):
        raise ValueError("matrix cases or crop receipts are missing")
    if not isinstance(pairs, list) or len(pairs) != 3:
        raise ValueError("matrix pair metrics are missing")
    receipt_by_id = {
        value["id"]: value
        for value in crop_receipts
        if isinstance(value, dict) and isinstance(value.get("id"), str)
    }
    if len(receipt_by_id) != len(cases):
        raise ValueError("crop receipt count differs from matrix cases")

    artifact_dir.mkdir(parents=True, exist_ok=True)
    frozen_cases: list[dict[str, object]] = []
    for value in cases:
        case = _object(value, "matrix case")
        identifier = case.get("id")
        if not isinstance(identifier, str) or case.get("ok") is not True:
            raise ValueError("matrix case is malformed or failed")
        receipt = _object(receipt_by_id.get(identifier), "crop receipt")
        source_crop = Path(str(receipt.get("path"))).resolve()
        expected_sha256 = receipt.get("sha256")
        if not source_crop.is_file() or _sha256(source_crop) != expected_sha256:
            raise ValueError(f"crop identity failed for {identifier}")
        target_crop = artifact_dir / f"{identifier}.png"
        if target_crop.exists():
            if _sha256(target_crop) != expected_sha256:
                raise ValueError(f"existing frozen crop differs for {identifier}")
        else:
            shutil.copyfile(source_crop, target_crop)
        copied_source = _source_text(case.get("native_copy"))
        source_receipt = _object(case.get("source"), "source receipt")
        frozen_cases.append(
            {
                "id": identifier,
                "input": source_receipt,
                "native_copy": {
                    "utf8_bytes": len(copied_source.encode("utf-8")),
                    "sha256": hashlib.sha256(
                        copied_source.encode("utf-8")
                    ).hexdigest().upper(),
                    "semantic_projection": case.get(
                        "native_copy_semantic_projection"
                    ),
                },
                "capture": {
                    "path": target_crop.name,
                    "bytes": target_crop.stat().st_size,
                    "sha256": _sha256(target_crop),
                    "payload_kind": receipt.get("payload_kind"),
                },
                "checks": case.get("checks"),
            }
        )

    report_receipt = {
        "path": str(report_path),
        "bytes": report_path.stat().st_size,
        "sha256": _sha256(report_path),
    }
    supplementary_diagnostic_pairs = [
        _pixel_metrics(artifact_dir, "parent-only", "unresolved-parent-control"),
        _pixel_metrics(artifact_dir, "parent-only", "parent-override-blue"),
        _pixel_metrics(artifact_dir, "parent-only", "parent-plus-child"),
    ]
    live_diagnostic_pairs = matrix.get("diagnostic_pairs")
    if live_diagnostic_pairs is None:
        live_diagnostic_pairs = []
    if not isinstance(live_diagnostic_pairs, list):
        raise ValueError("native diagnostic pairs are malformed")
    formal_parent_gate = bool(live_diagnostic_pairs) and all(
        isinstance(pair, dict) and pair.get("gate_passed") is True
        for pair in live_diagnostic_pairs
    )
    return {
        "schema": "ck3-coat-of-arms-parent-semantics-evidence-v2",
        "source_report": report_receipt,
        "repository_head": report.get("repository_head"),
        "game_binary": report.get("binary"),
        "interaction_policy": interaction,
        "steam": steam,
        "elapsed_seconds": report.get("elapsed_seconds"),
        "cleanup": {
            "ck3_pid": cleanup.get("ck3_pid"),
            "tree_gone": cleanup.get("tree_gone"),
            "cleanup_proven": cleanup.get("cleanup_proven"),
            "final_ck3_inventory": cleanup.get("final_ck3_inventory"),
        },
        "calibration": _calibration_receipt(
            matrix.get("framebuffer_calibration")
        ),
        "cases": frozen_cases,
        "pairs": pairs,
        "capture_noise_thresholds": matrix.get("capture_noise_thresholds"),
        "diagnostic_pairs": live_diagnostic_pairs,
        "supplementary_raw_pixel_pairs": supplementary_diagnostic_pairs,
        "conclusion": {
            "parent_is_preserved_by_native_copy": all(
                _object(
                    _object(case["native_copy"], "native Copy receipt").get(
                        "semantic_projection"
                    ),
                    "native Copy semantic projection",
                )
                .get("field_counts", {})
                .get("parents")
                == 1
                for case in frozen_cases
                if str(case["id"]).startswith("parent")
                or case["id"] == "unresolved-parent-control"
            ),
            "registered_parent_is_not_materialized_in_designer_preview": (
                True if formal_parent_gate else None
            ),
            "root_color_override_without_pattern_changes_preview": (
                False if formal_parent_gate else None
            ),
            "explicit_child_alongside_parent_changes_preview": (
                True if formal_parent_gate else None
            ),
            "formal_gate_available": formal_parent_gate,
        },
        "summary": {
            "case_count": len(frozen_cases),
            "case_passed": sum(
                all(value is True for value in case["checks"].values())
                for case in frozen_cases
            ),
            "pair_count": len(pairs),
            "pixel_exact_pairs": sum(
                pair.get("pixel_exact") is True
                for pair in pairs
                if isinstance(pair, dict)
            ),
            "all_pairs_comparable": all(
                isinstance(pair, dict) and pair.get("comparable") is True
                for pair in pairs
            ),
            "diagnostic_pair_count": len(live_diagnostic_pairs),
            "supplementary_raw_pair_count": len(
                supplementary_diagnostic_pairs
            ),
            "parent_not_materialized_gate": (
                True if formal_parent_gate else None
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = summarize(args.report, args.artifact_dir)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    output = args.output.resolve()
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != encoded:
            raise SystemExit("frozen parent semantics summary differs")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(encoded, encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False))
    for pair in payload["pairs"]:
        print(json.dumps(pair, ensure_ascii=False))
    for pair in payload["diagnostic_pairs"]:
        print(json.dumps(pair, ensure_ascii=False))
    for pair in payload["supplementary_raw_pixel_pairs"]:
        print(json.dumps(pair, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
