"""Six-chapter Episode 2 composer for source-bound, prepared chapter reels.

This module never captures CK3 or chooses footage. A reel has to be prepared,
labelled, measured and preserved in the same native run before plan/build.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from pathlib import Path

from xar_promo.media import probe_media
from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.process import run_command
from xar_promo.render import RenderOptions
from xar_promo.sources import VIDEO, VisualProbeResult, VisualSource

from .captions import subtitle_document


CHAPTER_IDS = ("opening", "pursuit", "knights", "reinforcement", "terminal", "closing")
CARD_REPLAYS = {"E2-06": "085", "E2-07": "085", "E2-09": "024"}
CHAPTER_CARDS = {"reinforcement": ("E2-06", "E2-07"), "terminal": ("E2-09",)}
HEADING = re.compile(r"^## \d\d:\d\d[–-]\d\d:\d\d .+$", re.M)
FOOTNOTE = re.compile(r"\[\^[^\]]+\]")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _spoken(value: str) -> str:
    return re.sub(r"\s+", " ", FOOTNOTE.sub("", value).replace("**", "").replace("`", "")).strip()


def script_chapters(path: Path) -> dict[str, str]:
    """Extract only the six bounded narration sections from exact draft bytes."""
    draft = path.read_text(encoding="utf-8-sig")
    headings = list(HEADING.finditer(draft))
    if len(headings) != len(CHAPTER_IDS):
        raise ValueError(f"Episode 2 needs six timecoded chapters; found {len(headings)}")
    result = {}
    for index, heading in enumerate(headings):
        block = draft[heading.end():headings[index + 1].start() if index + 1 < len(headings) else len(draft)]
        begin = block.find("**旁白**：")
        end = block.find("**录制缺口**")
        if begin < 0 or end <= begin:
            raise ValueError(f"Missing bounded narration in chapter {CHAPTER_IDS[index]}")
        text = _spoken(block[begin + len("**旁白**："):end])
        if not text:
            raise ValueError(f"Empty narration in chapter {CHAPTER_IDS[index]}")
        result[CHAPTER_IDS[index]] = text
    return result


def editorial_check(config_path: Path, draft_path: Path, cards_dir: Path) -> dict:
    """Read-only source gate, usable before any production run or game screen."""
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config["project"]["id"] != "ck3-war-ai-battle-second-half":
        raise ValueError("wrong Episode 2 ProjectConfig")
    if [row["id"] for row in config["chapters"]] != list(CHAPTER_IDS):
        raise ValueError("six ProjectConfig chapters are not in script order")
    narration = script_chapters(draft_path)
    card_index = cards_dir / "calculation-cards.json"
    data = json.loads(card_index.read_text(encoding="utf-8"))
    if data["schema"] != "xar.war-ai.episode02.calculation-cards.v1":
        raise ValueError("unknown Episode 2 card schema")
    if {row["id"]: row["replay"] for row in data["cards"]} != CARD_REPLAYS:
        raise ValueError("calculation card replay identities changed")
    if data["replays"]["085"]["source_save_sha256"] == data["replays"]["024"]["source_save_sha256"]:
        raise ValueError("085 and 024 cannot be the same source replay")
    cards = {key: _sha(cards_dir / f"{key.lower()}-calculation.svg") for key in CARD_REPLAYS}
    return {"schema": "ck3-war-ai.episode02.editorial-check.v1",
            "status": "editorial-inputs-present-not-media-ready",
            "project_config_sha256": _sha(config_path), "narration_script_sha256": _sha(draft_path),
            "card_index_sha256": _sha(card_index), "card_sha256": cards,
            "chapter_ids": list(narration),
            "chapter_narration_characters": {key: len(value) for key, value in narration.items()},
            "replay_by_card": CARD_REPLAYS}


def _artifact(run, run_path: Path | None, artifact_id: str) -> Path:
    if run is None or run_path is None:
        raise ValueError("Episode 2 needs a native run with preserved production inputs")
    hits = [item for item in run.artifacts if item.artifact_id == artifact_id]
    if len(hits) != 1:
        raise ValueError(f"Expected exactly one preserved artifact {artifact_id}: found {len(hits)}")
    path = (Path(run_path).parent / hits[0].path).resolve(strict=True)
    if path.stat().st_size != hits[0].bytes or _sha(path) != hits[0].sha256.upper():
        raise ValueError(f"Preserved artifact bytes changed: {artifact_id}")
    return path


def _checked_source(run, run_path: Path, artifact_id: str, expected_sha: str) -> Path:
    path = _artifact(run, run_path, artifact_id)
    if _sha(path) != expected_sha.upper():
        raise ValueError(f"Editorial source hash changed: {artifact_id}")
    return path


def _reel_receipt(run, run_path: Path, row: dict, media: Path, card_hashes: dict[str, str]) -> None:
    receipt_path = _artifact(run, run_path, row["reel_receipt_artifact_id"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != "ck3-war-ai.episode02.chapter-reel.v1" or receipt.get("chapter_id") != row["id"]:
        raise ValueError(f"Wrong chapter reel receipt for {row['id']}")
    if receipt.get("media_sha256", "").upper() != _sha(media) or receipt.get("media_bytes") != media.stat().st_size:
        raise ValueError(f"Reel receipt media identity mismatch for {row['id']}")
    if receipt.get("duration_seconds") != row["duration_seconds"]:
        raise ValueError(f"Reel receipt duration mismatch for {row['id']}")
    expected_cards = set(CHAPTER_CARDS.get(row["id"], ()))
    actual_cards = receipt.get("cards", {})
    if set(actual_cards) != expected_cards or any(actual_cards[key].upper() != card_hashes[key] for key in expected_cards):
        raise ValueError(f"Reel card/replay binding mismatch for {row['id']}")
    spans = receipt.get("capture_spans", [])
    if not isinstance(spans, list) or not spans:
        raise ValueError(f"Chapter {row['id']} requires a sourced capture span")
    for span in spans:
        required = ("attempt_id", "source_save_sha256", "raw_video_sha256", "control_sha256",
                    "clean_span_receipt_artifact_id", "label_audit_artifact_id")
        if any(not span.get(key) for key in required):
            raise ValueError(f"Incomplete capture span provenance in {row['id']}")
        for key in ("source_save_sha256", "raw_video_sha256", "control_sha256"):
            if not re.fullmatch(r"[0-9A-Fa-f]{64}", span[key]):
                raise ValueError(f"Bad {key} in {row['id']}")
        _artifact(run, run_path, span["clean_span_receipt_artifact_id"])
        _artifact(run, run_path, span["label_audit_artifact_id"])
    if receipt.get("different_attempts_explicitly_labelled") is not True:
        raise ValueError(f"Replay boundary labels unverified in {row['id']}")


def compose(config, run, *, config_path, run_path, workdir,
            adapter_factory, preset_factory, validate_only):
    """Build only from measured audio and chapter reels already preserved in run."""
    del config_path, validate_only
    adapter, preset = adapter_factory(), preset_factory()
    if config.adapter != adapter["id"] or config.preset != preset["id"]:
        raise ValueError("Episode 2 adapter/preset mismatch")
    if config.project_id != "ck3-war-ai-battle-second-half" or tuple(x.chapter_id for x in config.chapters) != CHAPTER_IDS:
        raise ValueError("Wrong Episode 2 ProjectConfig")
    input_path = _artifact(run, run_path, "episode02-production-inputs-v1")
    inputs = json.loads(input_path.read_text(encoding="utf-8"))
    if inputs.get("schema") != "ck3-war-ai.episode02.production-inputs.v1" or inputs.get("human_signoff") != "not-provided":
        raise ValueError("Expected unsigned Episode 2 production inputs")
    script = _checked_source(run, run_path, "episode02-narration-script", inputs["narration_script_sha256"])
    card_index = _checked_source(run, run_path, "episode02-card-index", inputs["card_index_sha256"])
    card_data = json.loads(card_index.read_text(encoding="utf-8"))
    if (card_data.get("schema") != "xar.war-ai.episode02.calculation-cards.v1" or
            {item["id"]: item["replay"] for item in card_data["cards"]} != CARD_REPLAYS or
            card_data["replays"]["085"]["source_save_sha256"] ==
            card_data["replays"]["024"]["source_save_sha256"]):
        raise ValueError("Card index must retain separate 085/024 replay identities")
    card_hashes = inputs["card_sha256"]
    if set(card_hashes) != set(CARD_REPLAYS):
        raise ValueError("All three source-bound cards are required")
    for card_id, digest in card_hashes.items():
        _checked_source(run, run_path, f"episode02-card-{card_id}", digest)
    narration = script_chapters(script)
    rows = inputs["chapters"]
    if [row["id"] for row in rows] != list(CHAPTER_IDS):
        raise ValueError("Episode 2 production chapters must match ProjectConfig order")
    ffmpeg = os.environ.get("WAR_PROMO_FFMPEG", "ffmpeg")
    ffprobe = os.environ.get("WAR_PROMO_FFPROBE", "ffprobe")
    segments = []
    by_id = {}
    for row in rows:
        chapter_id = row["id"]
        duration = row["duration_seconds"]
        speech = row["speech_duration_seconds"]
        if (not isinstance(duration, (int, float)) or not math.isfinite(duration) or
                not isinstance(speech, (int, float)) or not math.isfinite(speech) or
                speech <= 0 or duration < speech):
            raise ValueError(f"Invalid measured chapter duration: {chapter_id}")
        if row["zh"] != narration[chapter_id] or not row["en"].strip():
            raise ValueError(f"Chapter subtitles do not match frozen spoken script: {chapter_id}")
        audio = _artifact(run, run_path, row["audio_artifact_id"])
        reel = _artifact(run, run_path, row["reel_artifact_id"])
        _reel_receipt(run, run_path, row, reel, card_hashes)
        measured_audio = probe_media(ffprobe, audio).require_duration()
        measured_reel = probe_media(ffprobe, reel).require_duration()
        if abs(measured_audio - speech) > .15 or measured_reel + .05 < duration:
            raise ValueError(f"Audio/reel duration does not cover chapter {chapter_id}")
        segment = SegmentDraft(
            segment_id=chapter_id,
            visual_source=VisualSource(chapter_id, VIDEO, reel, "source-bound-episode02-chapter-reel"),
            render_options=RenderOptions(2560, 1440, 30, duration, preset="veryfast", crf=21),
            subtitles={"zh-CN": row["zh"], "en": row["en"]},
            prepared_narration=audio,
        )
        segments.append(segment)
        by_id[chapter_id] = {**row, "shot_title": row["title"], "subtitle_mode": "short"}
    work = Path(workdir)

    def visual_probe(path):
        measured = probe_media(ffprobe, path, audit_directory=work / "audit" / "reel-probe" / path.stem)
        stream = measured.video_streams[0]
        return VisualProbeResult("video/mp4", stream.width, stream.height)

    def subtitle_renderer(segment, narration_artifact, *, workdir):
        del narration_artifact, workdir
        return subtitle_document(by_id[segment.segment_id])

    return PipelineInvocation(
        PipelineDraft(config, tuple(segments), Path("episode-02-second-half-unmixed.mp4"),
                      "episode02-second-half-unmixed-v1", "video/mp4"),
        PipelineDependencies(ffmpeg, subtitle_renderer, run_command, visual_probe), work)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--editorial-check", action="store_true", required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--cards-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(editorial_check(args.config, args.draft, args.cards_dir), ensure_ascii=False, indent=2))
