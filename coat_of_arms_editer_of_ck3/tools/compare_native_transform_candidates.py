#!/usr/bin/env python3
"""Rank browser transform candidates against fixed-calibration CK3 crops."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--native-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    args = parse_args()
    repository = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repository / "ck3_autonomous_player" / "src"))
    from xar_autoplayer.bridge.coat_of_arms_framebuffer import _masked_metrics

    cases: list[dict[str, object]] = []
    for candidate_case in sorted(path for path in args.candidate_root.iterdir() if path.is_dir()):
        native_path = args.native_root / candidate_case.name / "native-crop.png"
        if not native_path.is_file():
            raise FileNotFoundError(native_path)
        with Image.open(native_path) as native_source:
            native_rgba = np.asarray(native_source.convert("RGBA"), dtype=np.uint8)
        side = native_rgba.shape[0]
        if native_rgba.shape != (side, side, 4):
            raise ValueError(f"{native_path} is not a square RGBA image")
        erosion_radius = max(1, round(side * 0.02))
        mask = cv2.erode(
            native_rgba[:, :, 3],
            np.ones((erosion_radius * 2 + 1, erosion_radius * 2 + 1), dtype=np.uint8),
        )
        rows: list[dict[str, object]] = []
        for candidate_path in sorted(candidate_case.glob("*.png")):
            with Image.open(candidate_path) as candidate_source:
                candidate_rgba = np.asarray(candidate_source.convert("RGBA"), dtype=np.uint8)
            if candidate_rgba.shape != native_rgba.shape:
                raise ValueError(f"{candidate_path} dimensions differ from native crop")
            comparison_mask = cv2.bitwise_and(mask, candidate_rgba[:, :, 3])
            metrics = _masked_metrics(
                candidate_rgba[:, :, :3],
                native_rgba[:, :, :3],
                comparison_mask,
            )
            score = 0.62 * float(metrics["colorMse"]) + 0.38 * float(metrics["edgeLoss"])
            rows.append(
                {
                    "candidate": candidate_path.stem,
                    "pngSha256": sha256(candidate_path),
                    "score": score,
                    "metrics": metrics,
                }
            )
        rows.sort(key=lambda row: (float(row["score"]), str(row["candidate"])))
        cases.append(
            {
                "case": candidate_case.name,
                "nativePngSha256": sha256(native_path),
                "erosionRadiusPixels": erosion_radius,
                "candidates": rows,
                "winner": rows[0]["candidate"],
            }
        )
    report = {
        "schema": "ck3-coa-native-transform-diagnostic-v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "metricContract": "masked-srgb8-mae-mse-gradient-l1-spatial-8x8-v1",
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for case in cases:
        winner = case["candidates"][0]
        print(
            f"{case['case']}: {winner['candidate']} "
            f"score={winner['score']:.9f} "
            f"mae={winner['metrics']['meanAbsoluteError']:.9f} "
            f"edge={winner['metrics']['edgeLoss']:.9f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
