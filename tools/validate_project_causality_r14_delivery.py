#!/usr/bin/env python3
"""Validate the deterministic delivery contract around Project Causality r14."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "artifacts/project-causality/2026-09-20-r14"
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
REQUIRED_COPY = {
    "贤王",
    "open-kashek",
    "回望整部片子",
    "现在再回看四层",
    "同一组冻结条件下",
}
FORBIDDEN_COPY = {
    "runner",
    "production-live",
    "open_kaishek",
    "宗教通用域",
    "影片没有规定",
    "借一段事件",
    "沿着这条因果链向里走",
    "先把桌上的结果",
    "RED",
    "ACK",
    "War ID",
    "完整寿命已经画出实线",
    "蓄王",
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
    video = directory / "project-causality-r14-owner-voice-nomusic.mp4"
    sidecar_path = directory / "project-causality-r14-owner-voice-nomusic.video.json"
    plan_path = directory / "project-causality-r14.build-plan.json"
    srt_path = directory / "project-causality-r14.en.srt"
    config_path = ROOT / "promo/project_causality/r14/edit-config.json"
    report_path = ROOT / "docs/project-causality-r14-copy-polish.md"
    asset_source = ROOT / "tools/build_project_causality_r12_assets.py"
    for path in (
        video,
        sidecar_path,
        plan_path,
        srt_path,
        config_path,
        report_path,
        asset_source,
    ):
        if not path.is_file():
            raise RuntimeError(f"missing delivery file: {path}")

    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8-sig"))
    plan_text = plan_path.read_text(encoding="utf-8-sig")
    plan = json.loads(plan_text)
    config_text = config_path.read_text(encoding="utf-8-sig")
    config = json.loads(config_text)
    duration = float(sidecar["video"]["duration_seconds"])

    if sidecar["video"]["sha256"] != sha256(video):
        raise RuntimeError("video SHA-256 does not match sidecar")
    if len(plan["cues"]) != 119:
        raise RuntimeError("r14 plan does not contain 119 cues")
    if len(config.get("text_overrides", {})) != 45:
        raise RuntimeError("r14 config does not contain exactly 45 copy overrides")
    for cue_id, override in config["text_overrides"].items():
        missing = {"narration_en", "subtitle_zh", "subtitle_secondary"} - set(override)
        if missing:
            raise RuntimeError(f"r14 override {cue_id} is incomplete: {sorted(missing)}")
    if "\ufffd" in plan_text or "\ufffd" in config_text:
        raise RuntimeError("r14 plan or config contains replacement characters")

    spoken_copy = "\n".join(
        block["text"]
        for cue in plan["cues"]
        for block in cue["subtitle_blocks"]
    )
    missing_copy = sorted(value for value in REQUIRED_COPY if value not in spoken_copy)
    stale_copy = sorted(value for value in FORBIDDEN_COPY if value in spoken_copy)
    if missing_copy or stale_copy:
        raise RuntimeError(
            f"r14 copy contract failed: missing={missing_copy}, stale={stale_copy}"
        )

    srt_count = validate_srt(srt_path, duration)
    if sidecar["r14"]["english_srt_sha256"] != sha256(srt_path):
        raise RuntimeError("English SRT SHA-256 does not match sidecar")
    if sidecar["r14"]["music_track_present"]:
        raise RuntimeError("r14 review candidate unexpectedly contains a music track")
    if sidecar["r14"]["publication_authorized"]:
        raise RuntimeError("r14 review candidate must remain publication-unauthorized")

    source = asset_source.read_text(encoding="utf-8-sig")
    missing_ids = sorted(item_id for item_id in EXPECTED_WORKSHOP_IDS if item_id not in source)
    if missing_ids or "Steam 创意工坊 · 9 项已上架" not in source:
        raise RuntimeError(f"Workshop card is incomplete: missing={missing_ids}")

    print(
        "GREEN: r14 delivery contract | "
        f"119 cues | 45 rewritten cues | {srt_count} English subtitles | "
        "9 published Workshop items | copy/video/SRT contracts match"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
