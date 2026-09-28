"""Six-chapter Episode 2 composer for source-bound, prepared chapter reels.

This module never captures CK3 or chooses footage. A reel has to be prepared,
labelled, measured and preserved in the same native run before plan/build.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
from pathlib import Path

from xar_promo.adapters.ck3.capture import load_capture_bundle
from xar_promo.media import probe_media
from xar_promo.model import RunManifest
from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.process import run_command
from xar_promo.render import RenderOptions
from xar_promo.sources import VIDEO, VisualProbeResult, VisualSource

from .captions import caption_cues, subtitle_document
from .episode_two_subtitle_contract import (
    HISTORICAL_SCOPE, compact, derive_boundaries, require_audio_coverage,
)
from .episode_two_pts_contract import validate_pts_span


CHAPTER_IDS = ("opening", "pursuit", "knights", "reinforcement", "terminal", "closing")
CARD_REPLAYS = {
    "E2-02": "004", "E2-03": "004", "E2-04": "039_040",
    "E2-05A": "020", "E2-05B": "070", "E2-05C": "036_038",
    "E2-06": "085", "E2-07": "085", "E2-09": "024",
}
CHAPTER_CARDS = {
    "pursuit": ("E2-02", "E2-03"),
    "knights": ("E2-04", "E2-05A", "E2-05B", "E2-05C"),
    "reinforcement": ("E2-06", "E2-07"),
    "terminal": ("E2-09",),
}
HISTORICAL_PRIMARY = {
    "004": "B4F8C8D4E2827650E4401E9FBAB34DE62558641A424382A4C460FEDBD261E160",
    "039_040": "EC61C0FD308E09B95FED5F7D9AB0BEFA01054DD87ECD45A4D9897BEBBFC2DA14",
    "020": "D5F0442FF068C4BC78C30622047D2831D3F094A0CF68C0AE2AEB1CC5B0CD2729",
    "070": "35ADD14D501D094B32D40564B39B713705AE5A46FB6670024ADA776A4C1A0A47",
    "036_038": "713DB2C37504411A2E81CAF05B198E2AEC700D7B7612F68BEF1EF3BB05EFC5AC",
    "085": "A7F01C89BE66B34A6F2862BAEFC4354EF74507B6D5178E2949C381DEDC32FD88",
    "024": "E55CEFA0AEB57D2F27A0EEF5D9516B85DB9FA5722551A4A83A5BB909DF5BE96F",
}
HEADING = re.compile(r"^## \d\d:\d\d[–-]\d\d:\d\d .+$", re.M)
FOOTNOTE = re.compile(r"\[\^[^\]]+\]")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


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


def _card_replays(data: dict) -> dict[str, str]:
    if data.get("schema") != "xar.war-ai.episode02.calculation-cards.v1":
        raise ValueError("Unknown Episode 2 card index")
    rows = data["cards"]
    replays = {item["id"]: item["replay"] for item in rows}
    if (len(rows) != len(CARD_REPLAYS) or set(replays) != set(CARD_REPLAYS)
            or replays["E2-02"] != replays["E2-03"]
            or replays["E2-06"] != replays["E2-07"]
            or len({replays["E2-04"], replays["E2-05A"],
                    replays["E2-05B"], replays["E2-05C"]}) != 4
            or any(replay not in data["replays"] for replay in replays.values())):
        raise ValueError("Nine cards lack separate source replay identities")
    terminal = _replay_primary(data["replays"][replays["E2-09"]])
    reinforcement = _replay_primary(data["replays"][replays["E2-06"]])
    if terminal == reinforcement:
        raise ValueError("Terminal writer and reinforcement cannot share a replay receipt")
    pursuit = data["replays"][replays["E2-02"]]
    if replays["E2-02"] == "004" and (
            pursuit.get("source_save_sha256", "").upper() !=
            "45CCE7E9A7E505C878F661333DE30D6B459DA638259A9E99990A226CE564245F"
            or pursuit.get("source_day27_checkpoint_sha256", "").upper() !=
            "F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3"):
        raise ValueError("004 card index must distinguish contact cold-load from day-27 checkpoint")
    return replays


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
    replay_by_card = _card_replays(data)
    cards = {key: _sha(cards_dir / f"{key.lower()}-calculation.svg") for key in CARD_REPLAYS}
    return {"schema": "ck3-war-ai.episode02.editorial-check.v1",
            "status": "editorial-inputs-present-not-media-ready",
            "project_config_sha256": _sha(config_path), "narration_script_sha256": _sha(draft_path),
            "card_index_sha256": _sha(card_index), "card_sha256": cards,
            "chapter_ids": list(narration),
            "chapter_narration_characters": {key: len(value) for key, value in narration.items()},
            "replay_by_card": replay_by_card}


def _artifact(run, run_path: Path | None, artifact_id: str) -> Path:
    if run is None or run_path is None:
        raise ValueError("Episode 2 needs a native run with preserved production inputs")
    hits = [item for item in run.artifacts if item.artifact_id == artifact_id]
    if len(hits) != 1:
        raise ValueError(f"Expected exactly one preserved artifact {artifact_id}: found {len(hits)}")
    path = (Path(run_path).parent / hits[0].path).resolve(strict=True)
    if not path.is_relative_to(Path(run_path).parent.resolve()):
        raise ValueError(f"Preserved artifact escapes native run: {artifact_id}")
    if path.stat().st_size != hits[0].bytes or _sha(path) != hits[0].sha256.upper():
        raise ValueError(f"Preserved artifact bytes changed: {artifact_id}")
    return path


def _checked_source(run, run_path: Path, artifact_id: str, expected_sha: str,
                    expected_bytes: int) -> Path:
    hits = [item for item in run.artifacts if item.artifact_id == artifact_id]
    if (not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9A-Fa-f]{64}", expected_sha)
            or type(expected_bytes) is not int or expected_bytes < 1
            or len(hits) != 1 or hits[0].bytes != expected_bytes
            or hits[0].sha256.upper() != expected_sha.upper()):
        raise ValueError(f"Editorial source hash changed: {artifact_id}")
    return _artifact(run, run_path, artifact_id)


def _replay_primary(source: dict) -> str:
    """The older 085/024 rows identify their primary receipt by source kind."""
    digest = (source.get("primary_receipt_sha256") or source.get("source_finish_sha256")
              or source.get("source_terminal_sha256"))
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9A-Fa-f]{64}", digest):
        raise ValueError("Replay lacks an exact primary receipt SHA-256")
    return digest.upper()


def _capture_audit_contract(clean: dict, label: dict, span: dict, reel_sha: str,
                            reel_duration: float, bundle, label_frame: Path) -> None:
    """Bind a real reel span to the CK3 adapter's verified clean frames."""
    span_id = clean.get("span_id")
    if (clean.get("schema") != "ck3-war-ai.episode02.clean-span-audit.v1"
            or clean.get("result") != "GREEN"
            or not isinstance(span_id, str) or not span_id
            or clean.get("attempt_id") != span["attempt_id"]
            or clean.get("raw_video_sha256", "").upper() != span["raw_video_sha256"].upper()
            or clean.get("raw_video_bytes") != span["raw_video_bytes"]
            or clean.get("report_sha256", "").upper() != bundle.report.sha256
            or clean.get("timeline_sha256", "").upper() != bundle.timeline.sha256
            or clean.get("evidence_index_sha256", "").upper() != bundle.evidence_index.sha256
            or bundle.raw_capture.sha256 != span["raw_video_sha256"].upper()
            or bundle.raw_capture.bytes != span["raw_video_bytes"]):
        raise ValueError(f"Clean-span audit is not bound to the real capture: {span['attempt_id']}")
    source_span = bundle.clean_span(span_id)
    if (clean.get("begin_seconds") != source_span.begin_seconds
            or clean.get("end_seconds") != source_span.end_seconds):
        raise ValueError(f"Clean-span bounds differ from CK3 adapter: {span_id}")
    frame_at = label.get("frame_at_seconds")
    label_text = label.get("label_text")
    if (label.get("schema") != "ck3-war-ai.episode02.source-label-audit.v1"
            or label.get("status") != "visible"
            or label.get("attempt_id") != span["attempt_id"]
            or label.get("raw_video_sha256", "").upper() != span["raw_video_sha256"].upper()
            or label.get("reel_sha256", "").upper() != reel_sha
            or not isinstance(label_text, str) or span["attempt_id"] not in label_text
            or not isinstance(frame_at, (int, float)) or isinstance(frame_at, bool)
            or not math.isfinite(frame_at) or not 0 <= frame_at <= reel_duration
            or label.get("frame_sha256", "").upper() != _sha(label_frame)
            or label.get("frame_bytes") != label_frame.stat().st_size):
        raise ValueError(f"Source label lacks same-attempt declared-frame binding: {span['attempt_id']}")


def _capture_audits(run, run_path: Path, span: dict, reel_sha: str,
                    reel_duration: float,
                    *, synthetic: bool) -> None:
    clean_path = _artifact(run, run_path, span["clean_span_receipt_artifact_id"])
    label_path = _artifact(run, run_path, span["label_audit_artifact_id"])
    clean = json.loads(clean_path.read_text(encoding="utf-8"))
    label = json.loads(label_path.read_text(encoding="utf-8"))
    if synthetic:
        if (clean.get("schema") != "synthetic.clean-span.v1"
                or label.get("schema") != "synthetic.source-label.v1"):
            raise ValueError("Synthetic smoke requires explicit synthetic span audits")
        return
    if (clean.get("schema") != "ck3-war-ai.episode02.clean-span-audit.v1"
            or clean.get("result") != "GREEN"
            or clean.get("attempt_id") != span["attempt_id"]
            or not isinstance(clean.get("span_id"), str)
            or not clean["span_id"]):
        raise ValueError("Real capture needs a same-attempt GREEN clean-span audit")
    root = clean.get("capture_artifact_root")
    if not isinstance(root, str) or not Path(root).is_absolute():
        raise ValueError("Real clean-span audit requires an absolute CK3 capture bundle root")
    bundle = load_capture_bundle(root, required_span_ids=[clean.get("span_id", "")])
    frame = _checked_source(run, run_path, label["frame_artifact_id"],
                            label["frame_sha256"], label["frame_bytes"])
    _capture_audit_contract(clean, label, span, reel_sha, reel_duration, bundle, frame)
    source_span = bundle.clean_span(clean["span_id"])
    raw = _checked_source(run, run_path, span["raw_video_artifact_id"],
                          span["raw_video_sha256"], span["raw_video_bytes"])
    probe = _checked_source(run, run_path, span["raw_video_pts_probe_artifact_id"],
                            span["raw_video_pts_probe_sha256"], span["raw_video_pts_probe_bytes"])
    recorder = _checked_source(run, run_path, span["raw_video_recorder_final_artifact_id"],
                               span["raw_video_recorder_final_sha256"],
                               span["raw_video_recorder_final_bytes"])
    validate_pts_span(raw, probe, recorder, source_span.begin_seconds,
                      source_span.end_seconds,
                      verified_raw_identity={"bytes": span["raw_video_bytes"],
                                             "sha256": span["raw_video_sha256"].upper()})


def _bound_tts_sentences(run, run_path: Path, row: dict, script: Path,
                         snapshot: Path) -> list[dict]:
    """Require original native TTS run, render, request and Edge event bytes."""
    chapter_id = row["id"]
    source = row.get("tts_source")
    if not isinstance(source, dict):
        raise ValueError(f"{chapter_id} lacks native TTS source identity")
    native_path = _checked_source(
        run, run_path, source["native_run_artifact_id"],
        source["native_run_sha256"], source["native_run_bytes"])
    render_path = _checked_source(
        run, run_path, source["render_manifest_artifact_id"],
        source["render_manifest_sha256"], source["render_manifest_bytes"])
    native = json.loads(native_path.read_text(encoding="utf-8"))
    RunManifest.from_mapping(native)
    render = json.loads(render_path.read_text(encoding="utf-8"))
    if (native["run"]["id"] != source.get("run_id")
            or native["project_config"]["sha256"].upper() != _sha(snapshot)
            or native["project_config"]["bytes"] != snapshot.stat().st_size
            or render.get("schema") != "ck3.episode02.selected-narration-render.v1"
            or render.get("status") != "selected-chapters-rendered-not-human-reviewed"
            or render.get("source_draft", {}).get("sha256", "").upper() != _sha(script)
            or render.get("source_draft", {}).get("bytes") != script.stat().st_size):
        raise ValueError(f"{chapter_id} TTS run/render does not bind the frozen script")
    original = {item["id"]: item for item in native["artifacts"]}
    for item_id, expected_sha, expected_bytes in (
            ("render-manifest", source["render_manifest_sha256"], source["render_manifest_bytes"]),
            ("source-draft", _sha(script), script.stat().st_size),
            (f"chapter-{chapter_id}", row["audio_sha256"], row["audio_bytes"])):
        item = original.get(item_id)
        if (item is None or item["sha256"].upper() != expected_sha.upper()
                or item["bytes"] != expected_bytes):
            raise ValueError(f"{chapter_id} source TTS artifact changed: {item_id}")
    chapters = [item for item in render.get("chapters", []) if item.get("id") == chapter_id]
    if (len(chapters) != 1 or
            chapters[0]["audio"]["sha256"].upper() != row["audio_sha256"].upper()
            or chapters[0]["audio"]["bytes"] != row["audio_bytes"]
            or chapters[0].get("speech_seconds") != row["speech_duration_seconds"]):
        raise ValueError(f"{chapter_id} source TTS chapter audio/duration changed")
    historical = chapter_id in ("terminal", "closing")
    scope = HISTORICAL_SCOPE if historical else "general-edit-proxy"
    selected = CHAPTER_IDS[4:] if historical else CHAPTER_IDS[:4]
    held = CHAPTER_IDS[:4] if historical else CHAPTER_IDS[4:]
    if (source.get("source_audio_artifact_id") != f"chapter-{chapter_id}"
            or source.get("usage_scope") != scope
            or tuple(render.get("selected_chapters", ())) != selected
            or tuple(render.get("held_chapters", ())) != held
            or (historical and (render.get("usage_scope") != HISTORICAL_SCOPE
                                or render.get("new_e2_09_live_verified") is not False))
            or (not historical and render.get("usage_scope") is not None)):
        raise ValueError(f"{chapter_id} TTS usage boundary changed")
    expected = [item for item in render["paragraphs"] if item["chapter_id"] == chapter_id]
    paragraphs = source.get("paragraphs")
    if not isinstance(paragraphs, list) or len(paragraphs) != len(expected):
        raise ValueError(f"{chapter_id} TTS paragraph identities missing")
    files = {}
    for index, (actual, recorded) in enumerate(zip(paragraphs, expected)):
        if (actual.get("paragraph_index") != index
                or recorded["paragraph_index"] != index
                or actual.get("duration_seconds") != recorded["duration_seconds"]
                or actual.get("text_sha256", "").upper() != recorded["text_sha256"].upper()):
            raise ValueError(f"{chapter_id} TTS paragraph order/text changed: {index}")
        for prefix, field in (("request", "request"), ("events", "response_events")):
            old = recorded[field]
            if (actual.get(f"{prefix}_sha256", "").upper() != old["sha256"].upper()
                    or actual.get(f"{prefix}_bytes") != old["bytes"]):
                raise ValueError(f"{chapter_id} TTS {prefix} identity changed: {index}")
        request_path = _checked_source(
            run, run_path, actual["request_artifact_id"],
            actual["request_sha256"], actual["request_bytes"])
        events_path = _checked_source(
            run, run_path, actual["events_artifact_id"],
            actual["events_sha256"], actual["events_bytes"])
        request = json.loads(request_path.read_text(encoding="utf-8"))
        if (historical and request.get("usage_scope") != HISTORICAL_SCOPE):
            raise ValueError(f"{chapter_id} historical TTS request lost its usage boundary")
        files[index] = (request_path, events_path)
    boundaries, source_text, last_end = derive_boundaries(
        chapter_id, paragraphs, lambda item: files[item["paragraph_index"]])
    if (source_text != compact(row["zh"])
            or row.get("sentence_boundaries") != boundaries):
        raise ValueError(f"{chapter_id} subtitles do not match source Edge sentence events")
    require_audio_coverage(chapter_id, boundaries, row["speech_duration_seconds"], last_end)
    return boundaries


def _rendered_subtitle_gate(row: dict, measured_audio_seconds: float) -> tuple[int, int]:
    """Check every source word survives caption grouping within the actual MP3."""
    if row.get("visual_kind") not in (None, "card"):
        raise ValueError("Episode 2 requires a bilingual subtitle layout for every reel")
    cues = caption_cues(row)
    chinese = [cue for cue in cues if cue.track_id == "zh"]
    english = [cue for cue in cues if cue.track_id == "en"]
    if (not chinese or not english
            or compact("".join(cue.text for cue in chinese)) != compact(html.unescape(row["zh"]))
            or compact("".join(cue.text for cue in english)) != compact(row["en"])):
        raise ValueError(f"Caption grouping lost spoken or translated text: {row['id']}")
    for cue in cues:
        if (not math.isfinite(cue.start_seconds) or not math.isfinite(cue.end_seconds)
                or not 0 <= cue.start_seconds < cue.end_seconds <= measured_audio_seconds + .002
                or cue.end_seconds > row["duration_seconds"] + .002):
            raise ValueError(f"Caption cue exceeds measured MP3/chapter duration: {row['id']}")
    return len(chinese), len(english)


def _reel_receipt(run, run_path: Path, row: dict, media: Path,
                  card_hashes: dict[str, str], card_data: dict,
                  card_replays: dict[str, str], *, synthetic: bool) -> dict:
    receipt_path = _checked_source(run, run_path, row["reel_receipt_artifact_id"],
                                   row["reel_receipt_sha256"], row["reel_receipt_bytes"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    media_sha = row["reel_sha256"].upper()
    if receipt.get("schema") != "ck3-war-ai.episode02.chapter-reel.v1" or receipt.get("chapter_id") != row["id"]:
        raise ValueError(f"Wrong chapter reel receipt for {row['id']}")
    if (receipt.get("media_sha256", "").upper() != media_sha
            or receipt.get("media_bytes") != media.stat().st_size):
        raise ValueError(f"Reel receipt media identity mismatch for {row['id']}")
    if receipt.get("duration_seconds") != row["duration_seconds"]:
        raise ValueError(f"Reel receipt duration mismatch for {row['id']}")
    if receipt.get("reel_width") != 2560 or receipt.get("reel_height") != 1440:
        raise ValueError(f"Chapter reel lacks a 2560x1440 resolution claim: {row['id']}")
    expected_cards = set(CHAPTER_CARDS.get(row["id"], ()))
    actual_cards = receipt.get("cards", {})
    if set(actual_cards) != expected_cards:
        raise ValueError(f"Reel card/replay binding mismatch for {row['id']}")
    spans = receipt.get("capture_spans", [])
    if not isinstance(spans, list) or not spans:
        raise ValueError(f"Chapter {row['id']} requires a sourced capture span")
    for span in spans:
        required = ("attempt_id", "cold_load_save_sha256", "cold_load_save_bytes",
                    "cold_load_save_artifact_id", "raw_video_sha256", "raw_video_bytes",
                    "raw_video_artifact_id", "control_sha256", "control_bytes",
                    "control_artifact_id", "clean_span_receipt_artifact_id",
                    "label_audit_artifact_id")
        if not synthetic:
            required += ("raw_video_pts_probe_artifact_id", "raw_video_pts_probe_sha256",
                         "raw_video_pts_probe_bytes",
                         "raw_video_recorder_final_artifact_id",
                         "raw_video_recorder_final_sha256",
                         "raw_video_recorder_final_bytes")
        if any(not span.get(key) for key in required):
            raise ValueError(f"Incomplete capture span provenance in {row['id']}")
        for prefix in ("cold_load_save", "control"):
            _checked_source(run, run_path, span[f"{prefix}_artifact_id"],
                            span[f"{prefix}_sha256"], span[f"{prefix}_bytes"])
        _checked_source(run, run_path, span["raw_video_artifact_id"],
                        span["raw_video_sha256"], span["raw_video_bytes"])
        width, height = span.get("raw_video_width"), span.get("raw_video_height")
        if (type(width) is not int or type(height) is not int or min(width, height) < 1
                or span.get("upscaled_to_reel") is not (width < 2560 or height < 1440)
                or span.get("resampled_to_reel") is not (width != 2560 or height != 1440)):
            raise ValueError(f"Raw capture resolution claim is inconsistent: {row['id']}")
        checkpoint = span.get("midrun_checkpoint_save_artifact_id")
        if checkpoint is not None:
            _checked_source(run, run_path, checkpoint,
                            span["midrun_checkpoint_save_sha256"],
                            span["midrun_checkpoint_save_bytes"])
        _capture_audits(run, run_path, span, media_sha, row["duration_seconds"],
                        synthetic=synthetic)
    for card_id in expected_cards:
        card = actual_cards[card_id]
        replay = card_replays[card_id]
        source = card_data["replays"][replay]
        primary = _replay_primary(source)
        if (card.get("sha256", "").upper() != card_hashes[card_id]
                or card.get("replay") != replay
                or card.get("primary_receipt_sha256", "").upper() != primary):
            raise ValueError(f"Card {card_id} is not bound to its indexed replay")
        indexed_cold = source.get("source_save_sha256")
        if indexed_cold and card.get("indexed_cold_load_save_sha256", "").upper() != indexed_cold.upper():
            raise ValueError(f"Card {card_id} confuses cold-load save with replay checkpoint")
        checkpoint = source.get("source_day27_checkpoint_sha256")
        if checkpoint and card.get("indexed_midrun_checkpoint_save_sha256", "").upper() != checkpoint.upper():
            raise ValueError(f"Card {card_id} omits the separate in-run checkpoint")
        mode = card.get("evidence_mode")
        if mode == "historical_research_card":
            if HISTORICAL_PRIMARY.get(replay) != primary:
                raise ValueError(f"Historical card {card_id} no longer matches frozen research")
            audit_path = _artifact(run, run_path, card["visible_label_audit_artifact_id"])
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            label = card.get("visible_label_text", "")
            if (audit.get("schema") != "ck3-war-ai.episode02.card-label-audit.v1"
                    or audit.get("status") != "visible"
                    or audit.get("card_id") != card_id
                    or audit.get("reel_sha256", "").upper() != media_sha
                    or audit.get("label_text") != label
                    or replay not in label
                    or "历史研究" not in label
                    or "非当前录制" not in label):
                raise ValueError(f"Historical card {card_id} lacks a visible source boundary")
        elif mode == "current_run_recomputed":
            if primary == HISTORICAL_PRIMARY.get(replay):
                raise ValueError(f"Old {replay} figures cannot be relabelled as current footage")
            recomputed_path = _artifact(run, run_path, card["recomputed_receipt_artifact_id"])
            recomputed = json.loads(recomputed_path.read_text(encoding="utf-8"))
            if (recomputed.get("schema") != "ck3-war-ai.episode02.recomputed-card.v1"
                    or recomputed.get("card_id") != card_id
                    or recomputed.get("card_sha256", "").upper() != card_hashes[card_id]
                    or recomputed.get("source_primary_receipt_sha256", "").upper() != primary
                    or not any(span["attempt_id"] == recomputed.get("capture_attempt_id")
                               and span["cold_load_save_sha256"].upper() ==
                               recomputed.get("cold_load_save_sha256", "").upper()
                               for span in spans)):
                raise ValueError(f"Current card {card_id} lacks same-attempt recomputation")
        else:
            raise ValueError(f"Card {card_id} needs explicit historical or current evidence mode")
    if receipt.get("different_attempts_explicitly_labelled") is not True:
        raise ValueError(f"Replay boundary labels unverified in {row['id']}")
    return receipt


def compose(config, run, *, config_path, run_path, workdir,
            adapter_factory, preset_factory, validate_only):
    """Build only from measured audio and chapter reels already preserved in run."""
    del validate_only
    adapter, preset = adapter_factory(), preset_factory()
    if config.adapter != adapter["id"] or config.preset != preset["id"]:
        raise ValueError("Episode 2 adapter/preset mismatch")
    if config.project_id != "ck3-war-ai-battle-second-half" or tuple(x.chapter_id for x in config.chapters) != CHAPTER_IDS:
        raise ValueError("Wrong Episode 2 ProjectConfig")
    input_path = _artifact(run, run_path, "episode02-production-inputs-v1")
    inputs = json.loads(input_path.read_text(encoding="utf-8"))
    if inputs.get("schema") != "ck3-war-ai.episode02.production-inputs.v1" or inputs.get("human_signoff") != "not-provided":
        raise ValueError("Expected unsigned Episode 2 production inputs")
    snapshot = Path(config_path).resolve(strict=True)
    if (snapshot.stat().st_size != run.project_config.bytes
            or _sha(snapshot) != run.project_config.sha256.upper()
            or inputs.get("project_config_sha256", "").upper() != _sha(snapshot)
            or inputs.get("project_config_bytes") != snapshot.stat().st_size):
        raise ValueError("Production inputs do not bind the native run ProjectConfig snapshot")
    script = _checked_source(run, run_path, "episode02-narration-script",
                             inputs["narration_script_sha256"], inputs["narration_script_bytes"])
    card_index = _checked_source(run, run_path, "episode02-card-index",
                                 inputs["card_index_sha256"], inputs["card_index_bytes"])
    card_data = json.loads(card_index.read_text(encoding="utf-8"))
    card_replays = _card_replays(card_data)
    if inputs.get("replay_by_card") != card_replays:
        raise ValueError("Production card replay bindings differ from the preserved index")
    card_hashes = inputs["card_sha256"]
    card_bytes = inputs["card_bytes"]
    if set(card_hashes) != set(CARD_REPLAYS) or set(card_bytes) != set(CARD_REPLAYS):
        raise ValueError("All nine source-bound cards are required")
    for card_id, digest in card_hashes.items():
        _checked_source(run, run_path, f"episode02-card-{card_id}", digest, card_bytes[card_id])
    narration = script_chapters(script)
    rows = inputs["chapters"]
    if [row["id"] for row in rows] != list(CHAPTER_IDS):
        raise ValueError("Episode 2 production chapters must match ProjectConfig order")
    ffmpeg = os.environ.get("WAR_PROMO_FFMPEG", "ffmpeg")
    ffprobe = os.environ.get("WAR_PROMO_FFPROBE", "ffprobe")
    segments = []
    by_id = {}
    reel_sources = {}
    audio_sources = {}
    synthetic = inputs.get("synthetic") is True
    for chapter_index, row in enumerate(rows):
        chapter_id = row["id"]
        duration = row["duration_seconds"]
        speech = row["speech_duration_seconds"]
        if (not isinstance(duration, (int, float)) or not math.isfinite(duration) or
                not isinstance(speech, (int, float)) or not math.isfinite(speech) or
                speech <= 0 or duration < speech):
            raise ValueError(f"Invalid measured chapter duration: {chapter_id}")
        if row["zh"] != narration[chapter_id] or not row["en"].strip():
            raise ValueError(f"Chapter subtitles do not match frozen spoken script: {chapter_id}")
        if row.get("visual_kind") not in (None, "card"):
            raise ValueError("Episode 2 requires a bilingual subtitle layout for every reel")
        if row["title"] != config.chapters[chapter_index].title.get("zh-CN"):
            raise ValueError(f"Chapter metadata title differs from ProjectConfig: {chapter_id}")
        if synthetic:
            if row.get("tts_source") is not None or row.get("sentence_boundaries"):
                raise ValueError("Synthetic smoke may only use its explicit synthetic subtitle fallback")
        else:
            _bound_tts_sentences(run, run_path, row, script, snapshot)
        audio = _checked_source(run, run_path, row["audio_artifact_id"],
                                row["audio_sha256"], row["audio_bytes"])
        reel = _checked_source(run, run_path, row["reel_artifact_id"],
                               row["reel_sha256"], row["reel_bytes"])
        receipt = _reel_receipt(run, run_path, row, reel, card_hashes, card_data,
                                card_replays, synthetic=synthetic)
        if reel.resolve() in reel_sources:
            raise ValueError("Each chapter requires its own labelled reel")
        reel_sources[reel.resolve()] = (row, receipt)
        audio_sources[chapter_id] = audio
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
        row, receipt = reel_sources[path.resolve()]
        duration = measured.require_duration()
        stream = measured.video_streams[0]
        if (stream.width != receipt["reel_width"] or stream.height != receipt["reel_height"]
                or stream.average_frame_rate != 30
                or duration + .002 < row["duration_seconds"]):
            raise ValueError(f"Measured reel resolution/fps/duration differs: {row['id']}")
        for index, span in enumerate(receipt["capture_spans"]):
            raw = _artifact(run, run_path, span["raw_video_artifact_id"])
            source_probe = probe_media(
                ffprobe, raw, audit_directory=work / "audit" / "raw-probe" /
                f"{row['id']}-{index:02d}")
            source = source_probe.video_streams[0]
            if (source.width != span["raw_video_width"]
                    or source.height != span["raw_video_height"]
                    or span["upscaled_to_reel"] is not
                    (source.width < stream.width or source.height < stream.height)
                    or span["resampled_to_reel"] is not
                    (source.width != stream.width or source.height != stream.height)):
                raise ValueError(f"Measured raw capture dimensions differ: {row['id']}")
        return VisualProbeResult("video/mp4", stream.width, stream.height)

    def subtitle_renderer(segment, narration_artifact, *, workdir):
        del narration_artifact, workdir
        row = by_id[segment.segment_id]
        audio = audio_sources[segment.segment_id]
        measured = probe_media(ffprobe, audio,
                               audit_directory=work / "audit" / "audio-probe" /
                               segment.segment_id).require_duration()
        if abs(measured - row["speech_duration_seconds"]) > .15:
            raise ValueError(f"Measured audio duration differs: {segment.segment_id}")
        _rendered_subtitle_gate(row, measured)
        return subtitle_document(row)

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
