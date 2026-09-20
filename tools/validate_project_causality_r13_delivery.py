#!/usr/bin/env python3
"""Validate the small, deterministic delivery contract around Project Causality r13."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "artifacts/project-causality/2026-09-20-r13"
EXPECTED_WORKSHOP_IDS = {
    "3784706360",
    "3787304042",
    "3792585972",
    "3790635143",
    "3798133925",
    "3800124956",
    "3798404599",
    "3797711947",
    "3801490405",
}
TIME_RE = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> "
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})$"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def seconds(parts: tuple[str, ...]) -> float:
    hours, minutes, seconds_value, millis = (int(value) for value in parts)
    return hours * 3600 + minutes * 60 + seconds_value + millis / 1000


def validate_srt(path: Path, duration: float) -> int:
    text = path.read_text(encoding="utf-8-sig")
    if not text.strip() or "\ufffd" in text:
        raise RuntimeError("English SRT is empty or contains replacement characters")
    blocks = re.split(r"\n\s*\n", text.strip())
    previous_end = 0.0
    for expected, block in enumerate(blocks, start=1):
        lines = block.splitlines()
        if len(lines) < 3 or int(lines[0]) != expected:
            raise RuntimeError(f"invalid SRT block {expected}")
        match = TIME_RE.fullmatch(lines[1])
        if not match:
            raise RuntimeError(f"invalid SRT timing at block {expected}: {lines[1]}")
        start = seconds(match.groups()[:4])
        end = seconds(match.groups()[4:])
        if start < previous_end - 0.002 or end <= start or end > duration + 0.1:
            raise RuntimeError(f"invalid SRT interval at block {expected}")
        previous_end = end
    return len(blocks)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    directory = args.artifact_dir.expanduser().resolve()
    video = directory / "project-causality-r13-owner-voice-nomusic.mp4"
    sidecar_path = directory / "project-causality-r13-owner-voice-nomusic.video.json"
    plan_path = directory / "project-causality-r13.build-plan.json"
    srt_path = directory / "project-causality-r13.en.srt"
    audit_path = ROOT / "docs/project-causality-r13-line-audit.md"
    asset_source = ROOT / "tools/build_project_causality_r12_assets.py"
    for path in (video, sidecar_path, plan_path, srt_path, audit_path, asset_source):
        if not path.is_file():
            raise RuntimeError(f"missing delivery file: {path}")

    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8-sig"))
    plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    duration = float(sidecar["video"]["duration_seconds"])
    if sidecar["video"]["sha256"] != sha256(video):
        raise RuntimeError("video SHA-256 does not match sidecar")
    if len(plan["cues"]) != 119:
        raise RuntimeError("r13 plan does not contain 119 cues")
    if "\ufffd" in plan_path.read_text(encoding="utf-8-sig"):
        raise RuntimeError("build plan contains replacement characters")
    srt_count = validate_srt(srt_path, duration)
    if sidecar["r13"]["english_srt_sha256"] != sha256(srt_path):
        raise RuntimeError("English SRT SHA-256 does not match sidecar")

    source = asset_source.read_text(encoding="utf-8-sig")
    missing_ids = sorted(item_id for item_id in EXPECTED_WORKSHOP_IDS if item_id not in source)
    if missing_ids or "Steam 创意工坊 · 9 项已上架" not in source:
        raise RuntimeError(f"Workshop card is incomplete: missing={missing_ids}")

    audit = audit_path.read_text(encoding="utf-8-sig")
    audited_rows = len(re.findall(r"^\| \d+ \|", audit, flags=re.MULTILINE))
    if audited_rows != 328:
        raise RuntimeError(f"expected 328 audited lines, got {audited_rows}")

    print(
        "GREEN: r13 delivery contract | "
        f"119 cues | {srt_count} English subtitles | 328 audited units | "
        "9 published Workshop items | video/SRT hashes match"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
