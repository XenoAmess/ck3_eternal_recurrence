#!/usr/bin/env python3
"""Compare two browser previews against the exact same MCP-native crop.

This consumes aligned-content PNGs already captured by the structured CK3
framebuffer v3 contract.  It performs no game launch, OCR, keyboard, mouse, or
network I/O.  Reusing the same native pixels keeps session-specific frame and
surface variation out of an A/B renderer comparison.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.bridge.coat_of_arms_framebuffer import _masked_metrics  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("native_summary", type=Path)
    parser.add_argument("baseline_corpus", type=Path)
    parser.add_argument("candidate_corpus", type=Path)
    parser.add_argument("output", type=Path)
    return parser


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _metrics(reference_path: Path, native_path: Path) -> tuple[dict[str, object], int]:
    reference = np.asarray(Image.open(reference_path).convert("RGBA"), dtype=np.uint8)
    native = np.asarray(Image.open(native_path).convert("RGBA"), dtype=np.uint8)
    if reference.shape != native.shape or reference.shape[0] != reference.shape[1]:
        raise ValueError(
            f"reference/native dimensions differ: {reference.shape} != {native.shape}"
        )
    side = reference.shape[0]
    erosion_radius = max(1, round(side * 0.02))
    mask = cv2.erode(
        native[:, :, 3],
        np.ones((erosion_radius * 2 + 1, erosion_radius * 2 + 1), dtype=np.uint8),
    )
    mask = cv2.bitwise_and(mask, reference[:, :, 3])
    return _masked_metrics(reference[:, :, :3], native[:, :, :3], mask), int(
        np.count_nonzero(mask)
    )


def _relative_improvement(baseline: float, candidate: float) -> float:
    return (baseline - candidate) / baseline if baseline else 0.0


def main() -> int:
    args = _parser().parse_args()
    native_summary = json.loads(args.native_summary.read_text(encoding="utf-8"))
    cases = native_summary.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("native summary has no cases")

    output_cases: list[dict[str, object]] = []
    for case in cases:
        case_id = case.get("id") if isinstance(case, dict) else None
        native_crop = case.get("native_crop") if isinstance(case, dict) else None
        summary_framebuffer = case.get("framebuffer") if isinstance(case, dict) else None
        if (
            not isinstance(case_id, str)
            or not isinstance(native_crop, dict)
            or not isinstance(native_crop.get("path"), str)
            or not isinstance(summary_framebuffer, dict)
            or not isinstance(summary_framebuffer.get("metrics"), dict)
        ):
            raise ValueError("native summary case is incomplete")
        native_path = Path(native_crop["path"])
        baseline_path = args.baseline_corpus / case_id / "canonical-preview-230.png"
        candidate_path = args.candidate_corpus / case_id / "canonical-preview-230.png"
        baseline, baseline_mask_pixels = _metrics(baseline_path, native_path)
        candidate, candidate_mask_pixels = _metrics(candidate_path, native_path)
        if baseline_mask_pixels != candidate_mask_pixels:
            raise ValueError(f"{case_id} comparison masks differ")

        native_metrics = summary_framebuffer["metrics"]
        # OpenCV's threaded float reduction can drift below one part per
        # million when the exact same pixels are rescored in another process.
        candidate_matches_native_summary = all(
            abs(float(candidate[key]) - float(native_metrics[key])) <= 1e-6
            for key in ("meanAbsoluteError", "colorMse", "edgeLoss")
        )
        output_cases.append(
            {
                "id": case_id,
                "native_crop": {
                    "path": str(native_path),
                    "bytes": native_path.stat().st_size,
                    "sha256": _sha256(native_path),
                },
                "comparison_mask_pixels": baseline_mask_pixels,
                "baseline": {
                    "path": str(baseline_path),
                    "sha256": _sha256(baseline_path),
                    "metrics": baseline,
                },
                "candidate": {
                    "path": str(candidate_path),
                    "sha256": _sha256(candidate_path),
                    "metrics": candidate,
                    "matches_native_summary": candidate_matches_native_summary,
                },
                "candidate_relative_improvement": {
                    key: _relative_improvement(
                        float(baseline[key]), float(candidate[key])
                    )
                    for key in ("meanAbsoluteError", "colorMse", "edgeLoss")
                },
                "candidate_improves_mae_and_edge": (
                    float(candidate["meanAbsoluteError"])
                    < float(baseline["meanAbsoluteError"])
                    and float(candidate["edgeLoss"]) < float(baseline["edgeLoss"])
                ),
            }
        )

    report = {
        "schema": "ck3-coat-of-arms-same-native-preview-comparison-v1",
        "contract": "same-mcp-aligned-content-mask-and-metrics-v3",
        "native_summary": {
            "path": str(args.native_summary),
            "sha256": _sha256(args.native_summary),
        },
        "baseline_corpus": str(args.baseline_corpus),
        "candidate_corpus": str(args.candidate_corpus),
        "case_count": len(output_cases),
        "all_candidates_match_native_summary": all(
            row["candidate"]["matches_native_summary"] for row in output_cases
        ),
        "all_candidates_improve_mae_and_edge": all(
            row["candidate_improves_mae_and_edge"] for row in output_cases
        ),
        "cases": output_cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: report[key] for key in (
        "schema",
        "case_count",
        "all_candidates_match_native_summary",
        "all_candidates_improve_mae_and_edge",
    )}, ensure_ascii=False, indent=2))
    for row in output_cases:
        improvement = row["candidate_relative_improvement"]
        print(
            f"{row['id']}: MAE {float(improvement['meanAbsoluteError']):.2%}; "
            f"edge {float(improvement['edgeLoss']):.2%}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
