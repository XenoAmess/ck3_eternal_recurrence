#!/usr/bin/env python3
"""Build the ZhongGuo 361 Chinese-first bilingual promo video.

This is a development compositor, not a CK3 recorder.  Its manifest can use
generated title cards, explicit placeholder cards, existing stills, or existing
video clips.  Placeholder cards are visibly watermarked and remain forbidden in
release validation.

Narration is synthesized cue-by-cue with Microsoft Edge TTS voice
``zh-CN-XiaoxiaoNeural``.  Every cue keeps its Chinese text, MP3, metadata, and
measured duration.  Simplified Chinese primary subtitles and English secondary
subtitles are burned into the picture at the same cue boundaries.  Content-
addressed filenames and ``--take-id`` preserve previous process material.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SHARED_TOOLS = REPOSITORY_ROOT / "tools"
if str(SHARED_TOOLS) not in sys.path:
    sys.path.insert(0, str(SHARED_TOOLS))

import build_full_agent_showcase as shared  # noqa: E402


FORMAT_VERSION = 1
BUILD_FORMAT_VERSION = 1
KIND = "zg361_chinese_first_promo"
VOICE = "zh-CN-XiaoxiaoNeural"
EDGE_TTS_RATE = "+0%"
EDGE_TTS_VOLUME = "+0%"
EDGE_TTS_PITCH = "+0Hz"
MAX_DURATION_SECONDS = 20 * 60
STATIC_DURATION_GUARD_SECONDS = 18 * 60
DEFAULT_FPS = 30
DEFAULT_CRF = 18
DEFAULT_PRESET = "medium"
DEFAULT_MIN_CHAPTER_SECONDS = 4.0
DEFAULT_TAIL_PADDING_SECONDS = 0.80
ALLOWED_PROMO_TYPES = {"title_card", "placeholder_card", "still", "video_clip"}
ALLOWED_MATERIAL_STATUS = {"generated", "placeholder", "captured"}
REQUIRED_TOPICS = {
    "forced_distribution",
    "calibration",
    "peer_review",
    "pip",
    "bottom_elimination",
    "promotion_packet",
    "hc",
    "okr_kpi",
    "upward_management",
    "credit_claims",
    "appeal",
    "jingcha",
    "scoreboard",
}
TOPIC_KEYWORDS = {
    "forced_distribution": ("强制分布", "forced distribution"),
    "calibration": ("校准", "calibration"),
    "peer_review": ("背靠背", "back-to-back"),
    "pip": ("PIP", "pip"),
    "bottom_elimination": ("末位", "bottom"),
    "promotion_packet": ("晋升包", "promotion packet"),
    "hc": ("HC", "headcount"),
    "okr_kpi": ("OKR", "KPI"),
    "upward_management": ("向上管理", "managing up"),
    "credit_claims": ("抢功", "credit"),
    "appeal": ("申诉", "appeal"),
    "jingcha": ("京察", "Jingcha"),
    "scoreboard": ("考核榜", "scoreboard"),
}

WIDTH = shared.WIDTH
HEIGHT = shared.HEIGHT
ZH_SUBTITLE_FONT = "Microsoft YaHei UI"
EN_SUBTITLE_FONT = "Segoe UI"
ZH_SUBTITLE_SIZE = 46
EN_SUBTITLE_SIZE = 30
SUBTITLE_MAX_WIDTH = 1920
SUBTITLE_MAX_LINES = 2
ZH_SUBTITLE_MARGIN_V = 152
EN_SUBTITLE_MARGIN_V = 66


class PromoError(shared.ShowcaseError):
    """A user-actionable promo project or media failure."""


def _required_string(container: dict[str, Any], key: str, context: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PromoError(f"{context}.{key} must be a non-empty string")
    return value.strip()


def _optional_string(
    container: dict[str, Any], key: str, default: str = ""
) -> str:
    value = container.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise PromoError(f"{key} must be a string when present")
    return value.strip()


def _number(
    container: dict[str, Any],
    key: str,
    default: float,
    context: str,
    *,
    minimum: float = 0.0,
) -> float:
    value = container.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PromoError(f"{context}.{key} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        raise PromoError(f"{context}.{key} must be at least {minimum}")
    return result


def _text_lines(value: Any, key: str, context: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise PromoError(f"{context}.{key} must be an array")
    result: list[str] = []
    for index, row in enumerate(value):
        if not isinstance(row, str) or not row.strip():
            raise PromoError(f"{context}.{key}[{index}] must be non-empty text")
        result.append(row.strip())
    return result


def _resolve_path(value: str, manifest_directory: Path) -> Path:
    candidate = Path(os.path.expandvars(os.path.expanduser(value)))
    if not candidate.is_absolute():
        candidate = manifest_directory / candidate
    return candidate.resolve()


def _read_json(path: Path, context: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise PromoError(f"could not read {context}: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise PromoError(f"invalid JSON in {context}: {path}: {exc}") from exc


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-") or "chapter"


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest().upper()


def _han_count(text: str) -> int:
    return len(re.findall(r"[\u3400-\u9fff]", text))


def estimate_spoken_seconds(text: str) -> float:
    """Conservative Xiaoxiao duration estimate for offline preflight.

    Exact release timing always comes from ffprobe on cue MP3s.  This estimate
    deliberately leaves a two-minute guard below the hard twenty-minute limit.
    """

    han = _han_count(text)
    latin_words = len(re.findall(r"[A-Za-z0-9]+(?:[._+-][A-Za-z0-9]+)*", text))
    major_pauses = len(re.findall(r"[。！？!?；;]", text))
    minor_pauses = len(re.findall(r"[，、：,:]", text))
    return max(
        1.0,
        han / 4.10
        + latin_words / 2.55
        + major_pauses * 0.18
        + minor_pauses * 0.08,
    )


def _source_record(
    value: Any,
    *,
    manifest_directory: Path,
    context: str,
    default_label: str,
    role: str,
) -> shared.SourceRecord:
    if isinstance(value, str):
        raw_path = value
        label = default_label
    elif isinstance(value, dict):
        raw_path = _required_string(value, "path", context)
        label = _optional_string(value, "label", default_label) or default_label
    else:
        raise PromoError(f"{context} must be a path string or object")
    path = _resolve_path(raw_path, manifest_directory)
    if not path.is_file():
        raise PromoError(f"required promo material was not found: {context}: {path}")
    return shared.SourceRecord(
        path=path,
        label=label,
        role=role,
        bytes=path.stat().st_size,
        sha256=shared._sha256(path),
    )


def load_manifest(path: Path) -> tuple[dict[str, Any], list[shared.Chapter]]:
    manifest_path = path.expanduser().resolve()
    payload = _read_json(manifest_path, "promo manifest")
    if not isinstance(payload, dict):
        raise PromoError("promo manifest root must be an object")
    if payload.get("format_version") != FORMAT_VERSION:
        raise PromoError(
            f"format_version must be {FORMAT_VERSION}, got "
            f"{payload.get('format_version')!r}"
        )
    if payload.get("kind") != KIND:
        raise PromoError(f"manifest kind must be {KIND!r}")
    voice = _required_string(payload, "voice", "manifest")
    if voice != VOICE:
        raise PromoError(f"manifest voice must be exactly {VOICE!r}, got {voice!r}")
    if payload.get("primary_language") != "zh-CN":
        raise PromoError("manifest primary_language must be 'zh-CN'")
    subtitle_languages = payload.get("subtitle_languages")
    if subtitle_languages != ["zh-CN", "en"]:
        raise PromoError("manifest subtitle_languages must be ['zh-CN', 'en']")
    if payload.get("skip_ck3_loading_opening") is not True:
        raise PromoError("skip_ck3_loading_opening must be true")
    limit = _number(
        payload,
        "duration_limit_seconds",
        MAX_DURATION_SECONDS,
        "manifest",
        minimum=1.0,
    )
    if limit > MAX_DURATION_SECONDS:
        raise PromoError("duration_limit_seconds may not exceed 1200")

    rows = payload.get("chapters")
    if not isinstance(rows, list) or not rows:
        raise PromoError("manifest.chapters must be a non-empty array")
    manifest_directory = manifest_path.parent
    global_minimum = _number(
        payload,
        "minimum_chapter_seconds",
        DEFAULT_MIN_CHAPTER_SECONDS,
        "manifest",
        minimum=0.1,
    )
    global_padding = _number(
        payload,
        "narration_padding_seconds",
        DEFAULT_TAIL_PADDING_SECONDS,
        "manifest",
    )

    chapters: list[shared.Chapter] = []
    seen_ids: set[str] = set()
    seen_capture_ids: set[str] = set()
    all_topics: set[str] = set()
    all_zh: list[str] = []
    all_en: list[str] = []
    estimate_total = 0.0

    for index, raw in enumerate(rows):
        context = f"chapter[{index}]"
        if not isinstance(raw, dict):
            raise PromoError(f"{context} must be an object")
        chapter_id = _required_string(raw, "id", context)
        if chapter_id in seen_ids:
            raise PromoError(f"duplicate chapter id: {chapter_id}")
        seen_ids.add(chapter_id)
        promo_type = _required_string(raw, "type", context)
        if promo_type not in ALLOWED_PROMO_TYPES:
            raise PromoError(
                f"{context}.type must be one of {sorted(ALLOWED_PROMO_TYPES)}"
            )
        material_status = _required_string(raw, "material_status", context)
        if material_status not in ALLOWED_MATERIAL_STATUS:
            raise PromoError(
                f"{context}.material_status must be one of "
                f"{sorted(ALLOWED_MATERIAL_STATUS)}"
            )
        expected_status = {
            "title_card": "generated",
            "placeholder_card": "placeholder",
            "still": "captured",
            "video_clip": "captured",
        }[promo_type]
        if material_status != expected_status:
            raise PromoError(
                f"{context}: {promo_type} requires material_status="
                f"{expected_status!r}"
            )

        capture = raw.get("capture")
        if promo_type == "placeholder_card":
            if not isinstance(capture, dict):
                raise PromoError(f"{context}.capture is required for a placeholder")
            capture_id = _required_string(capture, "id", f"{context}.capture")
            _required_string(capture, "shot", f"{context}.capture")
            if capture_id in seen_capture_ids:
                raise PromoError(f"duplicate capture id: {capture_id}")
            seen_capture_ids.add(capture_id)
        elif capture is not None and not isinstance(capture, dict):
            raise PromoError(f"{context}.capture must be an object when present")

        title_zh = _required_string(raw, "title_zh", context)
        title_en = _required_string(raw, "title_en", context)
        status = raw.get("status")
        if not isinstance(status, dict):
            raise PromoError(f"{context}.status must be an object")
        status_zh = _required_string(status, "zh", f"{context}.status")
        status_en = _required_string(status, "en", f"{context}.status")
        classification = _required_string(
            status, "classification", f"{context}.status"
        )

        cue_rows = raw.get("cues")
        if not isinstance(cue_rows, list) or not cue_rows:
            raise PromoError(f"{context}.cues must be a non-empty array")
        cues: list[dict[str, str]] = []
        for cue_index, cue in enumerate(cue_rows):
            cue_context = f"{context}.cues[{cue_index}]"
            if not isinstance(cue, dict):
                raise PromoError(f"{cue_context} must be an object")
            zh = _required_string(cue, "zh", cue_context)
            en = _required_string(cue, "en", cue_context)
            spoken = _optional_string(cue, "spoken_zh", zh) or zh
            cues.append({"zh": zh, "en": en, "spoken_zh": spoken})
            all_zh.extend((zh, spoken))
            all_en.append(en)

        topics = raw.get("topics", [])
        if not isinstance(topics, list) or any(
            not isinstance(row, str) or not row.strip() for row in topics
        ):
            raise PromoError(f"{context}.topics must be an array of strings")
        normalized_topics = {row.strip() for row in topics}
        all_topics.update(normalized_topics)

        sources: list[shared.SourceRecord] = []
        source_path: Path | None = None
        if promo_type in {"still", "video_clip"}:
            if "source" not in raw:
                raise PromoError(f"{context}.source is required for {promo_type}")
            primary = _source_record(
                raw["source"],
                manifest_directory=manifest_directory,
                context=f"{context}.source",
                default_label="Live visual source",
                role="visual",
            )
            sources.append(primary)
            source_path = primary.path
            if not isinstance(capture, dict):
                raise PromoError(f"{context}.capture is required for live material")
            capture_id = _required_string(capture, "id", f"{context}.capture")
            if capture_id in seen_capture_ids:
                raise PromoError(f"duplicate capture id: {capture_id}")
            seen_capture_ids.add(capture_id)
            if capture.get("exclude_ck3_loading") is not True:
                raise PromoError(
                    f"{context}.capture.exclude_ck3_loading must be true"
                )
        elif "source" in raw:
            raise PromoError(f"{context}: {promo_type} may not define source")

        evidence = raw.get("evidence_sources", [])
        if not isinstance(evidence, list):
            raise PromoError(f"{context}.evidence_sources must be an array")
        for evidence_index, value in enumerate(evidence):
            sources.append(
                _source_record(
                    value,
                    manifest_directory=manifest_directory,
                    context=f"{context}.evidence_sources[{evidence_index}]",
                    default_label=f"Evidence {evidence_index + 1}",
                    role="evidence",
                )
            )

        start_seconds = _number(raw, "start_seconds", 0.0, context)
        end_seconds: float | None = None
        if "end_seconds" in raw:
            end_seconds = _number(raw, "end_seconds", 0.0, context, minimum=0.001)
            if end_seconds <= start_seconds:
                raise PromoError(
                    f"{context}.end_seconds must be greater than start_seconds"
                )
        elif "clip_duration_seconds" in raw:
            clip_duration = _number(
                raw, "clip_duration_seconds", 0.0, context, minimum=0.001
            )
            end_seconds = start_seconds + clip_duration
        if promo_type != "video_clip" and (
            start_seconds != 0.0 or end_seconds is not None
        ):
            raise PromoError(f"{context}: clip timing is only valid for video_clip")

        minimum = _number(
            raw,
            "min_duration_seconds",
            global_minimum,
            context,
            minimum=0.1,
        )
        padding = _number(
            raw,
            "tail_padding_seconds",
            global_padding,
            context,
        )
        narration = " ".join(row["spoken_zh"] for row in cues)
        estimated = max(
            minimum,
            sum(estimate_spoken_seconds(row["spoken_zh"]) for row in cues)
            + padding,
        )
        estimate_total += estimated

        # The shared Chapter is deliberately reused for media plumbing.  Its
        # narration_en field carries Chinese here; the promo sidecar labels it
        # correctly and no shared show-off sidecar is emitted.
        chapter = shared.Chapter(
            index=index,
            chapter_id=chapter_id,
            kind="video_clip" if promo_type == "video_clip" else (
                "still" if promo_type == "still" else "title_card"
            ),
            title_en=title_en,
            title_zh=title_zh,
            narration_en=narration,
            subtitle_zh=" ".join(row["zh"] for row in cues),
            status_en=status_en,
            status_zh=status_zh,
            classification=classification,
            body_en=_text_lines(raw.get("body_en"), "body_en", context),
            body_zh=_text_lines(raw.get("body_zh"), "body_zh", context),
            sources=sources,
            source_path=source_path,
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            min_duration_seconds=minimum,
            tail_padding_seconds=padding,
            fit=_optional_string(raw, "fit", "contain").lower() or "contain",
            raw=raw,
        )
        if chapter.fit not in {"contain", "cover"}:
            raise PromoError(f"{context}.fit must be 'contain' or 'cover'")
        chapter.promo_type = promo_type
        chapter.material_status = material_status
        chapter.promo_cues = cues
        chapter.promo_topics = sorted(normalized_topics)
        chapter.estimated_duration_seconds = estimated
        chapter.promo_cue_durations = []
        chapter.promo_layouts = []
        chapters.append(chapter)

    missing_topics = sorted(REQUIRED_TOPICS - all_topics)
    if missing_topics:
        raise PromoError(
            "promo script is missing required topic tags: " + ", ".join(missing_topics)
        )
    zh_corpus = "\n".join(all_zh)
    en_corpus = "\n".join(all_en).lower()
    for topic in sorted(REQUIRED_TOPICS):
        zh_keyword, en_keyword = TOPIC_KEYWORDS[topic]
        if zh_keyword.lower() not in zh_corpus.lower():
            raise PromoError(f"topic {topic} lacks Chinese script keyword {zh_keyword!r}")
        if en_keyword.lower() not in en_corpus:
            raise PromoError(f"topic {topic} lacks English subtitle keyword {en_keyword!r}")
    if estimate_total > min(limit, STATIC_DURATION_GUARD_SECONDS):
        raise PromoError(
            f"offline duration estimate is {estimate_total:.1f}s; it must stay at or "
            f"below {min(limit, STATIC_DURATION_GUARD_SECONDS):.1f}s so live TTS has guard room"
        )
    payload["_estimated_duration_seconds"] = round(estimate_total, 3)
    payload["_placeholder_count"] = sum(
        1 for chapter in chapters if chapter.material_status == "placeholder"
    )
    return payload, chapters


def _layout_lines(draw, text: str, font, *, language: str) -> tuple[list[str], list[float]]:
    lines = [row for row in shared.wrap_text(draw, text, font, SUBTITLE_MAX_WIDTH) if row]
    if not lines:
        raise PromoError(f"{language} subtitle produced no renderable line")
    if len(lines) > SUBTITLE_MAX_LINES:
        raise PromoError(
            f"{language} subtitle needs {len(lines)} lines; split the manifest cue "
            f"so each language fits in {SUBTITLE_MAX_LINES} lines"
        )
    widths = [float(draw.textlength(row, font=font)) for row in lines]
    if max(widths) > SUBTITLE_MAX_WIDTH + 0.01:
        raise PromoError(
            f"{language} subtitle exceeded the {SUBTITLE_MAX_WIDTH}px safe width"
        )
    return lines, widths


def prepare_subtitle_layouts(
    chapters: Sequence[shared.Chapter], fonts: shared.Fonts
) -> None:
    canvas = shared.Image.new("L", (1, 1))
    draw = shared.ImageDraw.Draw(canvas)
    zh_font = fonts.chinese(ZH_SUBTITLE_SIZE, bold=True)
    en_font = fonts.english(EN_SUBTITLE_SIZE, bold=True)
    for chapter in chapters:
        layouts: list[dict[str, Any]] = []
        for cue in chapter.promo_cues:
            zh_lines, zh_widths = _layout_lines(
                draw, cue["zh"], zh_font, language="Chinese"
            )
            en_lines, en_widths = _layout_lines(
                draw, cue["en"], en_font, language="English"
            )
            layouts.append(
                {
                    "zh_lines": zh_lines,
                    "en_lines": en_lines,
                    "zh_widths": zh_widths,
                    "en_widths": en_widths,
                }
            )
        chapter.promo_layouts = layouts


def _cue_fingerprint(text: str, *, voice: str, take_id: str) -> str:
    return _hash_payload(
        {
            "format": BUILD_FORMAT_VERSION,
            "provider": "edge-tts",
            "provider_version": shared.EDGE_TTS_VERSION or "unknown",
            "voice": voice,
            "rate": EDGE_TTS_RATE,
            "volume": EDGE_TTS_VOLUME,
            "pitch": EDGE_TTS_PITCH,
            "text": text,
            "take_id": take_id,
        }
    )


def _load_valid_audio_cache(
    media: Path, metadata_path: Path, *, fingerprint: str, ffprobe: Path
) -> tuple[dict[str, Any], float] | None:
    if not media.is_file() or not metadata_path.is_file():
        return None
    try:
        metadata = _read_json(metadata_path, "Edge TTS cue metadata")
        if not isinstance(metadata, dict):
            return None
        if metadata.get("fingerprint") != fingerprint:
            return None
        if metadata.get("media_sha256") != shared._sha256(media):
            return None
        duration = shared._narration_duration(shared.probe_media(ffprobe, media), media)
    except shared.ShowcaseError:
        return None
    return metadata, duration


def _synthesize_cue(
    *,
    chapter: shared.Chapter,
    cue_index: int,
    cue: dict[str, str],
    chapter_directory: Path,
    voice: str,
    take_id: str,
    ffprobe: Path,
) -> tuple[Path, float, dict[str, Any]]:
    fingerprint = _cue_fingerprint(cue["spoken_zh"], voice=voice, take_id=take_id)
    stem = f"cue-{cue_index + 1:03d}.{fingerprint[:16].lower()}"
    text_path = chapter_directory / f"{stem}.zh-CN.txt"
    media_path = chapter_directory / f"{stem}.zh-CN.mp3"
    metadata_path = chapter_directory / f"{stem}.edge-tts.json"
    if not text_path.exists():
        text_path.write_text(cue["spoken_zh"] + "\n", encoding="utf-8")
    cached = _load_valid_audio_cache(
        media_path, metadata_path, fingerprint=fingerprint, ffprobe=ffprobe
    )
    if cached is not None:
        metadata, duration = cached
        return media_path, duration, metadata

    if shared.edge_tts is None:
        raise PromoError(
            "edge-tts is required; use tools\\.venv\\Scripts\\python.exe"
        )
    temporary = chapter_directory / f".{stem}.{os.getpid()}.partial.mp3"
    if temporary.exists():
        raise PromoError(f"stale partial cue exists: {temporary}")
    try:
        communicator = shared.edge_tts.Communicate(
            cue["spoken_zh"],
            voice,
            rate=EDGE_TTS_RATE,
            volume=EDGE_TTS_VOLUME,
            pitch=EDGE_TTS_PITCH,
        )
        communicator.save_sync(str(temporary))
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise PromoError(
                f"Edge TTS produced no cue audio for {chapter.chapter_id} cue "
                f"{cue_index + 1}"
            )
        duration = shared._narration_duration(
            shared.probe_media(ffprobe, temporary), temporary
        )
        metadata = {
            "format_version": 1,
            "fingerprint": fingerprint,
            "provider": "edge-tts",
            "provider_version": shared.EDGE_TTS_VERSION or "unknown",
            "voice": voice,
            "settings": {
                "rate": EDGE_TTS_RATE,
                "volume": EDGE_TTS_VOLUME,
                "pitch": EDGE_TTS_PITCH,
            },
            "take_id": take_id,
            "duration_seconds": round(duration, 6),
            "media_sha256": shared._sha256(temporary),
            "text_sha256": hashlib.sha256(
                cue["spoken_zh"].encode("utf-8")
            ).hexdigest().upper(),
        }
        os.replace(temporary, media_path)
        _atomic_json(metadata_path, metadata)
        return media_path, duration, metadata
    except PromoError:
        raise
    except Exception as exc:
        raise PromoError(
            f"Edge TTS failed for {chapter.chapter_id} cue {cue_index + 1}: {exc}"
        ) from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def synthesize_chapter(
    chapter: shared.Chapter,
    chapter_directory: Path,
    *,
    voice: str,
    take_id: str,
    ffmpeg: Path,
    ffprobe: Path,
) -> None:
    cue_media: list[Path] = []
    cue_durations: list[float] = []
    cue_metadata: list[dict[str, Any]] = []
    for cue_index, cue in enumerate(chapter.promo_cues):
        media, duration, metadata = _synthesize_cue(
            chapter=chapter,
            cue_index=cue_index,
            cue=cue,
            chapter_directory=chapter_directory,
            voice=voice,
            take_id=take_id,
            ffprobe=ffprobe,
        )
        cue_media.append(media)
        cue_durations.append(duration)
        cue_metadata.append(metadata)

    aggregate_fingerprint = _hash_payload(
        {
            "format": BUILD_FORMAT_VERSION,
            "cue_sha256": [shared._sha256(path) for path in cue_media],
            "take_id": take_id,
        }
    )
    stem = f"narration.{aggregate_fingerprint[:16].lower()}"
    concat_path = chapter_directory / f"{stem}.concat.txt"
    narration_path = chapter_directory / f"{stem}.zh-CN.mp3"
    metadata_path = chapter_directory / f"{stem}.build.json"
    concat_rows: list[str] = []
    for media in cue_media:
        if "'" in media.name:
            raise PromoError(f"unexpected apostrophe in cue path: {media}")
        concat_rows.append(f"file '{media.name}'")
    concat_text = "\n".join(concat_rows) + "\n"
    if not concat_path.exists():
        concat_path.write_text(concat_text, encoding="utf-8")

    cached = _load_valid_audio_cache(
        narration_path,
        metadata_path,
        fingerprint=aggregate_fingerprint,
        ffprobe=ffprobe,
    )
    if cached is None:
        temporary = chapter_directory / f".{stem}.{os.getpid()}.partial.mp3"
        if temporary.exists():
            raise PromoError(f"stale partial narration exists: {temporary}")
        try:
            shared.run_checked(
                [
                    ffmpeg,
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    concat_path.name,
                    "-vn",
                    "-c:a",
                    "libmp3lame",
                    "-q:a",
                    "2",
                    "-ar",
                    "48000",
                    "-ac",
                    "2",
                    temporary.name,
                ],
                cwd=chapter_directory,
                action=f"concatenating narration for '{chapter.chapter_id}'",
            )
            aggregate_duration = shared._narration_duration(
                shared.probe_media(ffprobe, temporary), temporary
            )
            metadata = {
                "format_version": 1,
                "fingerprint": aggregate_fingerprint,
                "provider": "edge-tts",
                "provider_version": shared.EDGE_TTS_VERSION or "unknown",
                "voice": voice,
                "settings": {
                    "rate": EDGE_TTS_RATE,
                    "volume": EDGE_TTS_VOLUME,
                    "pitch": EDGE_TTS_PITCH,
                },
                "take_id": take_id,
                "duration_seconds": round(aggregate_duration, 6),
                "media_sha256": shared._sha256(temporary),
                "cues": cue_metadata,
            }
            os.replace(temporary, narration_path)
            _atomic_json(metadata_path, metadata)
        finally:
            if temporary.exists():
                temporary.unlink()
    else:
        metadata, aggregate_duration = cached

    chapter.narration_path = narration_path
    chapter.narration_duration_seconds = aggregate_duration
    chapter.voice = voice
    chapter.tts_provider = "edge-tts"
    chapter.tts_provider_version = shared.EDGE_TTS_VERSION or "unknown"
    chapter.tts_settings = {
        "rate": EDGE_TTS_RATE,
        "volume": EDGE_TTS_VOLUME,
        "pitch": EDGE_TTS_PITCH,
    }
    chapter.promo_cue_durations = cue_durations
    chapter.shot_duration_seconds = max(
        chapter.min_duration_seconds,
        aggregate_duration + chapter.tail_padding_seconds,
    )


def _classification_color(classification: str) -> tuple[int, int, int]:
    if "placeholder" in classification.lower():
        return (238, 162, 52)
    return shared._classification_color(classification)


def _draw_status_badge(image, chapter: shared.Chapter, fonts: shared.Fonts) -> None:
    draw = shared.ImageDraw.Draw(image, "RGBA")
    color = _classification_color(chapter.classification)
    zh_font = fonts.chinese(23, bold=True)
    en_font = fonts.english(18, bold=True)
    width = 450
    left, top, right, bottom = WIDTH - width - 62, 58, WIDTH - 62, 154
    draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=22,
        fill=(8, 12, 22, 226),
        outline=(*color, 255),
        width=4,
    )
    draw.text((left + 28, top + 15), chapter.status_zh, font=zh_font, fill=(250, 251, 254, 255))
    draw.text((left + 28, top + 55), chapter.status_en, font=en_font, fill=(185, 207, 235, 255))


def _draw_overlay(chapter: shared.Chapter, fonts: shared.Fonts):
    overlay = shared.Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = shared.ImageDraw.Draw(overlay, "RGBA")
    color = _classification_color(chapter.classification)
    draw.rounded_rectangle((58, 58, 1690, 248), radius=28, fill=(5, 9, 17, 206))
    draw.rounded_rectangle((58, 58, 75, 248), radius=8, fill=(*color, 255))
    draw.text(
        (105, 78),
        f"第 {chapter.index + 1:02d} 章  /  CHAPTER {chapter.index + 1:02d}",
        font=fonts.chinese(21, bold=True),
        fill=(*color, 255),
    )
    shared.draw_text_block(
        draw,
        (105, 118),
        chapter.title_zh,
        font=fonts.chinese(43, bold=True),
        fill=(250, 251, 254, 255),
        max_width=1515,
        line_height=52,
        max_lines=1,
    )
    shared.draw_text_block(
        draw,
        (107, 181),
        chapter.title_en,
        font=fonts.english(26, bold=True),
        fill=(180, 207, 240, 255),
        max_width=1500,
        line_height=34,
        max_lines=1,
    )
    _draw_status_badge(overlay, chapter, fonts)
    return overlay


def _render_title_card(
    chapter: shared.Chapter, fonts: shared.Fonts, destination: Path
) -> None:
    image = shared._base_background().convert("RGBA")
    draw = shared.ImageDraw.Draw(image, "RGBA")
    accent = _classification_color(chapter.classification)
    draw.text(
        (170, 92),
        "天朝特色 361 制  /  ZHONGGUO 361 STYLE",
        font=fonts.chinese(27, bold=True),
        fill=(*accent, 255),
    )
    draw.rounded_rectangle((170, 152, WIDTH - 170, 164), radius=6, fill=(*accent, 255))
    zh_bottom = shared.draw_text_block(
        draw,
        (170, 224),
        chapter.title_zh,
        font=fonts.chinese(76, bold=True),
        fill=(250, 251, 254, 255),
        max_width=WIDTH - 340,
        line_height=94,
        max_lines=2,
    )
    en_bottom = shared.draw_text_block(
        draw,
        (174, zh_bottom + 22),
        chapter.title_en,
        font=fonts.english(39, bold=True),
        fill=(185, 209, 239, 255),
        max_width=WIDTH - 348,
        line_height=50,
        max_lines=2,
    )
    if chapter.body_zh or chapter.body_en:
        panel_top = max(650, en_bottom + 46)
        panel_bottom = 1090
        draw.rounded_rectangle(
            (170, panel_top, WIDTH - 170, panel_bottom),
            radius=28,
            fill=(7, 11, 21, 165),
            outline=(75, 92, 124, 180),
            width=2,
        )
        middle = WIDTH // 2
        draw.line((middle, panel_top + 32, middle, panel_bottom - 32), fill=(75, 92, 124, 180), width=2)
        zh_y = panel_top + 40
        for line in chapter.body_zh:
            zh_y = shared.draw_text_block(
                draw,
                (220, zh_y),
                f"• {line}",
                font=fonts.chinese(29, bold=True),
                fill=(235, 239, 247, 255),
                max_width=middle - 300,
                line_height=42,
                max_lines=2,
            ) + 16
        en_y = panel_top + 40
        for line in chapter.body_en:
            en_y = shared.draw_text_block(
                draw,
                (middle + 54, en_y),
                f"• {line}",
                font=fonts.english(26, bold=True),
                fill=(183, 207, 237, 255),
                max_width=middle - 300,
                line_height=38,
                max_lines=2,
            ) + 16
    _draw_status_badge(image, chapter, fonts)
    image.convert("RGB").save(destination, format="PNG", optimize=True)


def _render_placeholder(
    chapter: shared.Chapter, fonts: shared.Fonts, destination: Path
) -> None:
    image = shared._base_background().convert("RGBA")
    draw = shared.ImageDraw.Draw(image, "RGBA")
    accent = (238, 162, 52)
    capture = chapter.raw["capture"]
    draw.rounded_rectangle(
        (120, 100, WIDTH - 120, 1060),
        radius=42,
        fill=(9, 12, 20, 190),
        outline=(*accent, 255),
        width=6,
    )
    draw.text(
        (180, 155),
        "占位镜头 · 尚未实录",
        font=fonts.chinese(68, bold=True),
        fill=(*accent, 255),
    )
    draw.text(
        (184, 247),
        "PLACEHOLDER · LIVE CK3 CAPTURE PENDING",
        font=fonts.english(35, bold=True),
        fill=(246, 218, 163, 255),
    )
    draw.rounded_rectangle((180, 320, WIDTH - 180, 332), radius=6, fill=(*accent, 255))
    y = shared.draw_text_block(
        draw,
        (180, 390),
        chapter.title_zh,
        font=fonts.chinese(56, bold=True),
        fill=(250, 251, 254, 255),
        max_width=WIDTH - 360,
        line_height=70,
        max_lines=2,
    )
    y = shared.draw_text_block(
        draw,
        (184, y + 15),
        chapter.title_en,
        font=fonts.english(30, bold=True),
        fill=(184, 207, 238, 255),
        max_width=WIDTH - 368,
        line_height=40,
        max_lines=2,
    )
    draw.text(
        (184, max(660, y + 48)),
        f"素材编号 / CAPTURE ID: {capture['id']}",
        font=fonts.english(25, bold=True),
        fill=(*accent, 255),
    )
    shared.draw_text_block(
        draw,
        (184, max(720, y + 104)),
        capture["shot"],
        font=fonts.chinese(31),
        fill=(222, 228, 239, 255),
        max_width=WIDTH - 368,
        line_height=46,
        max_lines=4,
    )
    _draw_status_badge(image, chapter, fonts)
    image.convert("RGB").save(destination, format="PNG", optimize=True)


def render_visual(
    chapter: shared.Chapter, fonts: shared.Fonts, chapter_directory: Path
) -> tuple[Path, bool]:
    visual_fingerprint = _hash_payload(
        {
            "format": BUILD_FORMAT_VERSION,
            "chapter": chapter.raw,
            "source_sha256": [row.sha256 for row in chapter.sources],
        }
    )
    promo_type = chapter.promo_type
    if promo_type == "video_clip":
        destination = chapter_directory / f"overlay.{visual_fingerprint[:16].lower()}.png"
        if not destination.exists():
            _draw_overlay(chapter, fonts).save(destination, format="PNG", optimize=True)
        return destination, True
    destination = chapter_directory / f"frame.{visual_fingerprint[:16].lower()}.png"
    if destination.exists():
        return destination, False
    if promo_type == "title_card":
        _render_title_card(chapter, fonts, destination)
    elif promo_type == "placeholder_card":
        _render_placeholder(chapter, fonts, destination)
    elif promo_type == "still":
        if chapter.source_path is None:
            raise PromoError(f"chapter {chapter.chapter_id} has no still source")
        try:
            with shared.Image.open(chapter.source_path) as source:
                image = shared._fit_image(source, mode=chapter.fit).convert("RGBA")
        except (OSError, ValueError) as exc:
            raise PromoError(f"could not decode still source {chapter.source_path}: {exc}") from exc
        image.alpha_composite(_draw_overlay(chapter, fonts))
        image.convert("RGB").save(destination, format="PNG", optimize=True)
    else:
        raise PromoError(f"unsupported promo type: {promo_type}")
    return destination, False


def _ass_escape(text: str) -> str:
    return shared._ass_escape(text)


def _ass_document(events: Sequence[tuple[float, float, str, str]]) -> str:
    header = f"""[Script Info]
Title: ZhongGuo 361 promo - Chinese primary bilingual subtitles
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ChinesePrimary,{ZH_SUBTITLE_FONT},{ZH_SUBTITLE_SIZE},&H00FFFFFF,&H000000FF,&H00101018,&H84081018,-1,0,0,0,100,100,0,0,1,3,1,2,300,300,{ZH_SUBTITLE_MARGIN_V},1
Style: EnglishSecondary,{EN_SUBTITLE_FONT},{EN_SUBTITLE_SIZE},&H00CFE2FA,&H000000FF,&H00101018,&H84081018,-1,0,0,0,100,100,0,0,1,2,1,2,320,320,{EN_SUBTITLE_MARGIN_V},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    rows = [
        f"Dialogue: {0 if style == 'ChinesePrimary' else 1},"
        f"{shared._ass_timestamp(start)},{shared._ass_timestamp(end)},"
        f"{style},,0,0,0,,{{\\q2}}{_ass_escape(text)}"
        for start, end, style, text in events
    ]
    return header + "\n".join(rows) + "\n"


def _chapter_events(
    chapter: shared.Chapter, *, offset: float = 0.0
) -> list[tuple[float, float, str, str]]:
    if not chapter.promo_cue_durations:
        durations = [estimate_spoken_seconds(row["spoken_zh"]) for row in chapter.promo_cues]
    else:
        durations = chapter.promo_cue_durations
    if len(durations) != len(chapter.promo_layouts):
        raise PromoError(f"internal cue layout mismatch for {chapter.chapter_id}")
    events: list[tuple[float, float, str, str]] = []
    cursor = 0.04
    for duration, layout in zip(durations, chapter.promo_layouts):
        end = cursor + max(0.25, duration)
        events.append(
            (offset + cursor, offset + end, "ChinesePrimary", "\n".join(layout["zh_lines"]))
        )
        events.append(
            (offset + cursor, offset + end, "EnglishSecondary", "\n".join(layout["en_lines"]))
        )
        cursor = end
    return events


def write_chapter_ass(chapter: shared.Chapter, destination: Path) -> None:
    destination.write_text(
        _ass_document(_chapter_events(chapter)), encoding="utf-8-sig"
    )


def write_global_ass(
    chapters: Sequence[shared.Chapter], destination: Path
) -> None:
    events: list[tuple[float, float, str, str]] = []
    cursor = 0.0
    for chapter in chapters:
        events.extend(_chapter_events(chapter, offset=cursor))
        cursor += chapter.encoded_duration_seconds or chapter.shot_duration_seconds or 0.0
    destination.write_text(_ass_document(events), encoding="utf-8-sig")


def _seconds(value: float) -> str:
    return f"{value:.6f}"


def encode_segment(
    chapter: shared.Chapter,
    chapter_directory: Path,
    *,
    fonts: shared.Fonts,
    ffmpeg: Path,
    ffprobe: Path,
    fps: int,
    crf: int,
    preset: str,
) -> None:
    if chapter.narration_path is None or chapter.shot_duration_seconds is None:
        raise PromoError("internal error: narration is not ready")
    visual, is_video = render_visual(chapter, fonts, chapter_directory)
    ass_fingerprint = _hash_payload(
        {
            "format": BUILD_FORMAT_VERSION,
            "layouts": chapter.promo_layouts,
            "durations": chapter.promo_cue_durations,
        }
    )
    ass_path = chapter_directory / f"subtitles.{ass_fingerprint[:16].lower()}.zh-CN+en.ass"
    if not ass_path.exists():
        write_chapter_ass(chapter, ass_path)
    fingerprint = _hash_payload(
        {
            "format": BUILD_FORMAT_VERSION,
            "chapter": chapter.raw,
            "sources": [row.sidecar() for row in chapter.sources],
            "narration": shared._sha256(chapter.narration_path),
            "visual": shared._sha256(visual),
            "ass": shared._sha256(ass_path),
            "duration": chapter.shot_duration_seconds,
            "fps": fps,
            "crf": crf,
            "preset": preset,
        }
    )
    segment = chapter_directory / f"segment.{fingerprint[:16].lower()}.mp4"
    metadata_path = chapter_directory / f"segment.{fingerprint[:16].lower()}.build.json"
    if segment.is_file() and metadata_path.is_file():
        try:
            metadata = _read_json(metadata_path, "cached promo segment")
            if (
                isinstance(metadata, dict)
                and metadata.get("fingerprint") == fingerprint
                and metadata.get("segment_sha256") == shared._sha256(segment)
            ):
                info = shared.validate_encoded_media(
                    shared.probe_media(ffprobe, segment),
                    segment,
                    expected_duration=chapter.shot_duration_seconds,
                    duration_tolerance=0.25,
                )
                chapter.segment_path = segment
                chapter.encoded_duration_seconds = float(info["duration"])
                print(f"[{chapter.index + 1:02d}] reuse {chapter.chapter_id}: {segment}")
                return
        except shared.ShowcaseError:
            pass

    common_tail: list[str | Path] = [
        "-map", "[v]", "-map", "[a]", "-t", _seconds(chapter.shot_duration_seconds),
        "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
        "-profile:v", "high", "-level:v", "5.1", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-metadata:s:a:0", "language=zho", "-movflags", "+faststart", segment.name,
    ]
    audio_filter = (
        f"aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"apad,atrim=duration={_seconds(chapter.shot_duration_seconds)},asetpts=N/SR/TB"
    )
    if is_video:
        if chapter.source_path is None or chapter.source_duration_seconds is None:
            raise PromoError("internal error: video source was not probed")
        available_end = chapter.end_seconds or chapter.source_duration_seconds
        available = available_end - chapter.start_seconds
        video_filter = (
            f"[0:v]trim=duration={_seconds(available)},setpts=PTS-STARTPTS,"
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0x060910,setsar=1,"
            f"fps={fps},tpad=stop_mode=clone:stop_duration={_seconds(chapter.shot_duration_seconds)},"
            f"trim=duration={_seconds(chapter.shot_duration_seconds)}[base];"
            "[1:v]format=rgba[overlay];"
            f"[base][overlay]overlay=0:0:shortest=1,ass={ass_path.name},format=yuv420p[v];"
            f"[2:a]{audio_filter}[a]"
        )
        command: list[str | Path] = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-ss", _seconds(chapter.start_seconds), "-i", chapter.source_path,
            "-loop", "1", "-framerate", str(fps), "-i", visual.name,
            "-i", chapter.narration_path.name, "-filter_complex", video_filter,
            *common_tail,
        ]
    else:
        video_filter = (
            f"[0:v]trim=duration={_seconds(chapter.shot_duration_seconds)},"
            f"setpts=PTS-STARTPTS,fps={fps},ass={ass_path.name},format=yuv420p[v];"
            f"[1:a]{audio_filter}[a]"
        )
        command = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-framerate", str(fps), "-i", visual.name,
            "-i", chapter.narration_path.name, "-filter_complex", video_filter,
            *common_tail,
        ]
    print(f"[{chapter.index + 1:02d}] encode {chapter.chapter_id}: {chapter.shot_duration_seconds:.2f}s")
    shared.run_checked(
        command,
        cwd=chapter_directory,
        action=f"encoding promo chapter '{chapter.chapter_id}'",
    )
    info = shared.validate_encoded_media(
        shared.probe_media(ffprobe, segment),
        segment,
        expected_duration=chapter.shot_duration_seconds,
        duration_tolerance=0.25,
    )
    chapter.segment_path = segment
    chapter.encoded_duration_seconds = float(info["duration"])
    _atomic_json(
        metadata_path,
        {
            "format_version": 1,
            "fingerprint": fingerprint,
            "segment": str(segment),
            "segment_sha256": shared._sha256(segment),
        },
    )


def _archive_output(path: Path) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = path.parent / "superseded" / stamp / path.name
    archive.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(archive))
    return archive


def concat_segments(
    chapters: Sequence[shared.Chapter],
    *,
    build_directory: Path,
    output: Path,
    ffmpeg: Path,
    ffprobe: Path,
    archive_existing: bool,
) -> dict[str, Any]:
    fingerprint = _hash_payload(
        [shared._sha256(chapter.segment_path) for chapter in chapters if chapter.segment_path]
    )
    concat_path = build_directory / f"concat.{fingerprint[:16].lower()}.txt"
    rows: list[str] = []
    for chapter in chapters:
        if chapter.segment_path is None:
            raise PromoError("internal error: segment missing")
        relative = chapter.segment_path.relative_to(build_directory).as_posix()
        if "'" in relative:
            raise PromoError(f"apostrophe in concat path: {relative}")
        rows.append(f"file '{relative}'")
    if not concat_path.exists():
        concat_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    sidecar = output.with_suffix(".video.json")
    if output.exists() or sidecar.exists():
        if not archive_existing:
            raise PromoError(
                f"output already exists: {output}; choose a new filename or use "
                "--archive-existing to preserve it under superseded/"
            )
        if output.exists():
            archived = _archive_output(output)
            print(f"ARCHIVE: {archived}")
        if sidecar.exists():
            archived = _archive_output(sidecar)
            print(f"ARCHIVE: {archived}")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.stem}.{os.getpid()}.partial.mp4")
    if temporary.exists():
        raise PromoError(f"stale partial output exists: {temporary}")
    shared.run_checked(
        [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", concat_path.name,
            "-c", "copy", "-movflags", "+faststart", temporary,
        ],
        cwd=build_directory,
        action="concatenating ZhongGuo 361 promo",
    )
    expected = sum(
        chapter.encoded_duration_seconds or chapter.shot_duration_seconds or 0.0
        for chapter in chapters
    )
    info = shared.validate_encoded_media(
        shared.probe_media(ffprobe, temporary),
        temporary,
        expected_duration=expected,
        duration_tolerance=max(0.45, len(chapters) * 0.08),
    )
    if float(info["duration"]) >= MAX_DURATION_SECONDS:
        raise PromoError(
            f"encoded video is {float(info['duration']):.3f}s; it must be shorter than 1200s"
        )
    os.replace(temporary, output)
    return info


def write_sidecar(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
    chapters: Sequence[shared.Chapter],
    output: Path,
    output_info: dict[str, Any],
    global_ass: Path,
    take_id: str,
    ffmpeg: Path,
    ffprobe: Path,
) -> Path:
    cursor = 0.0
    chapter_rows: list[dict[str, Any]] = []
    for chapter in chapters:
        duration = chapter.encoded_duration_seconds or chapter.shot_duration_seconds or 0.0
        chapter_rows.append(
            {
                "index": chapter.index,
                "id": chapter.chapter_id,
                "type": chapter.promo_type,
                "material_status": chapter.material_status,
                "title_zh": chapter.title_zh,
                "title_en": chapter.title_en,
                "start_seconds": round(cursor, 3),
                "end_seconds": round(cursor + duration, 3),
                "duration_seconds": round(duration, 3),
                "topics": chapter.promo_topics,
                "status": {
                    "zh": chapter.status_zh,
                    "en": chapter.status_en,
                    "classification": chapter.classification,
                },
                "sources": [row.sidecar() for row in chapter.sources],
                "cues": [
                    {
                        **cue,
                        "duration_seconds": round(cue_duration, 3),
                        "layout": layout,
                    }
                    for cue, cue_duration, layout in zip(
                        chapter.promo_cues,
                        chapter.promo_cue_durations,
                        chapter.promo_layouts,
                    )
                ],
                "narration": {
                    "provider": chapter.tts_provider,
                    "provider_version": chapter.tts_provider_version,
                    "voice": chapter.voice,
                    "settings": chapter.tts_settings,
                    "path": str(chapter.narration_path),
                    "sha256": shared._sha256(chapter.narration_path),
                },
                "segment": {
                    "path": str(chapter.segment_path),
                    "sha256": shared._sha256(chapter.segment_path),
                },
            }
        )
        cursor += duration
    video = output_info["video"]
    audio = output_info["audio"]
    project_status = str(manifest.get("project_status", ""))
    if "smoke" in project_status:
        readiness = "pipeline_smoke"
        honest_boundary = (
            "Pipeline smoke only: it validates narration, subtitles, and media "
            "plumbing; it is not a promo candidate and proves no CK3 gameplay."
        )
    elif manifest["_placeholder_count"]:
        readiness = "draft_animatic"
        honest_boundary = (
            "Placeholder chapters are an animatic only; no final promo or live "
            "gameplay claim is made."
        )
    else:
        readiness = "rendered_candidate"
        honest_boundary = (
            "Media candidate only; release validation and full content sampling "
            "remain required."
        )
    payload = {
        "format_version": 1,
        "kind": KIND,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "readiness": readiness,
        "honest_boundary": honest_boundary,
        "take_id": take_id,
        "manifest": {
            "path": str(manifest_path),
            "bytes": manifest_path.stat().st_size,
            "sha256": shared._sha256(manifest_path),
        },
        "language": {
            "primary": "Simplified Chinese narration and visual hierarchy",
            "subtitles": ["Simplified Chinese primary", "English secondary"],
            "voice": VOICE,
        },
        "video": {
            "path": str(output),
            "bytes": output.stat().st_size,
            "sha256": shared._sha256(output),
            "duration_seconds": round(float(output_info["duration"]), 3),
            "width": video.get("width"),
            "height": video.get("height"),
            "codec": video.get("codec_name"),
            "pixel_format": video.get("pix_fmt"),
            "audio_codec": audio.get("codec_name"),
            "audio_sample_rate": int(audio.get("sample_rate", 0)),
            "audio_channels": audio.get("channels"),
            "audio_language": (audio.get("tags") or {}).get("language"),
        },
        "subtitles": {
            "kind": "burned bilingual ASS",
            "path": str(global_ass),
            "sha256": shared._sha256(global_ass),
            "safe_width_px": SUBTITLE_MAX_WIDTH,
            "max_lines_per_language": SUBTITLE_MAX_LINES,
        },
        "placeholder_count": manifest["_placeholder_count"],
        "tools": {"ffmpeg": str(ffmpeg), "ffprobe": str(ffprobe)},
        "chapters": chapter_rows,
    }
    sidecar = output.with_suffix(".video.json")
    _atomic_json(sidecar, payload)
    return sidecar


def _positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def _crf(value: str) -> int:
    parsed = _positive_integer(value)
    if parsed > 51:
        raise argparse.ArgumentTypeError("must be in the range 1..51")
    return parsed


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--manifest", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--work-dir", type=Path, required=True)
    result.add_argument("--take-id", default="take-01")
    result.add_argument("--ffmpeg")
    result.add_argument("--ffprobe")
    result.add_argument("--fps", type=_positive_integer, default=DEFAULT_FPS)
    result.add_argument("--crf", type=_crf, default=DEFAULT_CRF)
    result.add_argument("--preset", default=DEFAULT_PRESET)
    result.add_argument(
        "--archive-existing",
        action="store_true",
        help="move an existing output/sidecar under superseded/ before rendering",
    )
    result.add_argument(
        "--validate-only",
        action="store_true",
        help="offline validation: no TTS, no directories, no media writes",
    )
    return result


def build(args: argparse.Namespace) -> tuple[Path, Path]:
    if shared.PIL_IMPORT_ERROR is not None:
        raise PromoError(
            "Pillow is required; use tools\\.venv\\Scripts\\python.exe"
        ) from shared.PIL_IMPORT_ERROR
    if shared.EDGE_TTS_IMPORT_ERROR is not None:
        raise PromoError(
            "edge-tts is required; use tools\\.venv\\Scripts\\python.exe"
        ) from shared.EDGE_TTS_IMPORT_ERROR
    if shared.EDGE_TTS_VERSION != "7.2.8":
        raise PromoError(
            f"edge-tts 7.2.8 is required, got {shared.EDGE_TTS_VERSION!r}"
        )
    manifest_path = args.manifest.expanduser().resolve()
    output = args.output.expanduser().resolve()
    work_directory = args.work_dir.expanduser().resolve()
    if output.suffix.lower() != ".mp4":
        raise PromoError("--output must use the .mp4 extension")
    if not isinstance(args.take_id, str) or not args.take_id.strip():
        raise PromoError("--take-id must be non-empty")
    take_id = args.take_id.strip()

    manifest, chapters = load_manifest(manifest_path)
    ffmpeg = shared.find_program(args.ffmpeg, "ffmpeg")
    ffprobe = shared.find_program(args.ffprobe, "ffprobe", sibling_of=ffmpeg)
    fonts = shared.find_fonts()
    shared.preflight_video_sources(chapters, ffprobe)
    prepare_subtitle_layouts(chapters, fonts)
    if args.validate_only:
        print(
            "VALID: "
            f"chapters={len(chapters)}; placeholders={manifest['_placeholder_count']}; "
            f"estimated={manifest['_estimated_duration_seconds']:.1f}s; "
            f"voice={VOICE}; bilingual_subtitles=zh-CN+en; loading_opening=excluded"
        )
        return output, output.with_suffix(".video.json")

    build_key = _hash_payload(
        {
            "manifest_sha256": shared._sha256(manifest_path),
            "take_id": take_id,
            "build_format": BUILD_FORMAT_VERSION,
        }
    )
    build_directory = work_directory / f"zg361-promo-{build_key[:16].lower()}"
    build_directory.mkdir(parents=True, exist_ok=True)
    for chapter in chapters:
        chapter_directory = build_directory / f"{chapter.index:03d}-{_safe_slug(chapter.chapter_id)}"
        chapter_directory.mkdir(parents=True, exist_ok=True)
        synthesize_chapter(
            chapter,
            chapter_directory,
            voice=VOICE,
            take_id=take_id,
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
        )
    exact_duration = sum(chapter.shot_duration_seconds or 0.0 for chapter in chapters)
    if exact_duration >= MAX_DURATION_SECONDS:
        raise PromoError(
            f"TTS-derived duration is {exact_duration:.3f}s; split or shorten the "
            "script before encoding because the video must stay under 1200s"
        )
    for chapter in chapters:
        chapter_directory = build_directory / f"{chapter.index:03d}-{_safe_slug(chapter.chapter_id)}"
        encode_segment(
            chapter,
            chapter_directory,
            fonts=fonts,
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
            fps=args.fps,
            crf=args.crf,
            preset=args.preset,
        )
    global_ass = build_directory / f"promo.{build_key[:16].lower()}.zh-CN+en.ass"
    if not global_ass.exists():
        write_global_ass(chapters, global_ass)
    output_info = concat_segments(
        chapters,
        build_directory=build_directory,
        output=output,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
        archive_existing=args.archive_existing,
    )
    sidecar = write_sidecar(
        manifest_path=manifest_path,
        manifest=manifest,
        chapters=chapters,
        output=output,
        output_info=output_info,
        global_ass=global_ass,
        take_id=take_id,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
    )
    print(f"VIDEO:   {output}")
    print(f"SIDECAR: {sidecar}")
    print(f"WORK:    {build_directory}")
    return output, sidecar


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        build(args)
    except PromoError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("ERROR: interrupted", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
