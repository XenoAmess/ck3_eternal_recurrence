#!/usr/bin/env python3
"""Plan and render the natural-owner-voice Project Causality r11 edit.

The builder never synthesizes speech.  It consumes the already generated,
unmodified IndexTTS WAV for each of the 98 narration cues, lets that WAV set
the minimum shot duration, regenerates bilingual ASS timing, and renders from
the clean chapter sources in the r6/r8/r9 manifests.  The subtitle-bearing r9
or r10 picture locks are deliberately not inputs.

Planning is cheap and is the default.  ``--render`` is intentionally gated on
an edit manifest for one continuous Robert capture; that prevents a review
render from silently falling back to the old discontinuous showcase clips.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import math
import os
import re
import sys
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import build_full_agent_showcase as showcase


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "promo/project_causality/r11/retime-config.json"
DEFAULT_AUDIO_DIR = (
    ROOT
    / "artifacts/project-causality/2026-09-19-r10-owner-voice/work/generated-cues"
)
DEFAULT_OUTPUT_DIR = ROOT / "artifacts/project-causality/2026-09-20-r11"
FPS = 30
ROBERT_SOURCE_KEY = "agent"


class R11BuildError(RuntimeError):
    """Raised when the r11 editorial contract cannot be satisfied."""


@dataclass(frozen=True)
class RobertSpan:
    cue_id: str
    source_start_seconds: float
    source_end_seconds: float
    playback_rate: float

    @property
    def output_seconds(self) -> float:
        return (self.source_end_seconds - self.source_start_seconds) / self.playback_rate


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise R11BuildError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise R11BuildError(f"JSON root must be an object: {path}")
    return value


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    return slug[:80] or "cue"


def _root_path(value: Any, context: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise R11BuildError(f"{context} must be a non-empty root-relative path")
    path = Path(value)
    return (path if path.is_absolute() else ROOT / path).resolve()


def _positive_number(value: Any, context: str, *, allow_zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise R11BuildError(f"{context} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < 0 or (result == 0 and not allow_zero):
        qualifier = "non-negative" if allow_zero else "positive"
        raise R11BuildError(f"{context} must be a finite {qualifier} number")
    return result


def _wav_duration(path: Path) -> float:
    try:
        with wave.open(str(path), "rb") as handle:
            frames = handle.getnframes()
            rate = handle.getframerate()
    except (OSError, wave.Error) as exc:
        raise R11BuildError(f"cannot read PCM WAV {path}: {exc}") from exc
    if frames <= 0 or rate <= 0:
        raise R11BuildError(f"WAV has no measurable audio: {path}")
    return frames / rate


def _selector_matches(chapter_id: str, row: dict[str, Any]) -> bool:
    if row.get("all") is True:
        return True
    ids = row.get("ids", [])
    prefixes = row.get("starts_with", [])
    if not isinstance(ids, list) or not all(isinstance(value, str) for value in ids):
        raise R11BuildError("composition.ids must be an array of strings")
    if not isinstance(prefixes, list) or not all(
        isinstance(value, str) for value in prefixes
    ):
        raise R11BuildError("composition.starts_with must be an array of strings")
    return chapter_id in ids or any(chapter_id.startswith(value) for value in prefixes)


def materialize_chapters(
    config: dict[str, Any],
) -> tuple[list[showcase.Chapter], dict[str, Path]]:
    input_values = config.get("inputs")
    if not isinstance(input_values, dict):
        raise R11BuildError("config.inputs must be an object")
    manifests: dict[str, Path] = {}
    catalogs: dict[str, list[showcase.Chapter]] = {}
    for key, value in input_values.items():
        path = _root_path(value, f"inputs.{key}")
        if not path.is_file():
            raise R11BuildError(f"input manifest is missing: {path}")
        try:
            _manifest, chapters = showcase.load_manifest(path)
        except showcase.ShowcaseError as exc:
            raise R11BuildError(f"invalid input manifest {path}: {exc}") from exc
        manifests[str(key)] = path
        catalogs[str(key)] = chapters

    composition = config.get("composition")
    if not isinstance(composition, list) or not composition:
        raise R11BuildError("config.composition must be a non-empty array")
    result: list[showcase.Chapter] = []
    used: set[tuple[str, str]] = set()
    for row_index, row in enumerate(composition):
        if not isinstance(row, dict):
            raise R11BuildError(f"composition[{row_index}] must be an object")
        source = row.get("source")
        if not isinstance(source, str) or source not in catalogs:
            raise R11BuildError(f"composition[{row_index}] has unknown source {source!r}")
        selected = [
            chapter
            for chapter in catalogs[source]
            if _selector_matches(chapter.chapter_id, row)
        ]
        expected = row.get("expected_count")
        if not isinstance(expected, int) or expected <= 0:
            raise R11BuildError(f"composition[{row_index}].expected_count must be positive")
        if len(selected) != expected:
            raise R11BuildError(
                f"composition[{row_index}] selected {len(selected)} {source} cue(s); "
                f"expected {expected}"
            )
        for chapter in selected:
            identity = (source, chapter.chapter_id)
            if identity in used:
                raise R11BuildError(f"composition selects {identity} more than once")
            used.add(identity)
            clone = copy.copy(chapter)
            clone.raw = copy.deepcopy(chapter.raw)
            clone.raw["r11_source_manifest_key"] = source
            result.append(clone)

    expected_total = config.get("contracts", {}).get("expected_cue_count")
    if len(result) != expected_total:
        raise R11BuildError(f"composition has {len(result)} cues; expected {expected_total}")
    ids = [chapter.chapter_id for chapter in result]
    if len(ids) != len(set(ids)):
        raise R11BuildError("final cue ids must be globally unique")
    for index, chapter in enumerate(result):
        chapter.index = index
    return result, manifests


def attach_natural_audio(
    chapters: Sequence[showcase.Chapter],
    *,
    audio_dir: Path,
    config: dict[str, Any],
) -> None:
    timing = config.get("timing", {})
    contracts = config.get("contracts", {})
    tail = _positive_number(
        timing.get("narration_tail_hold_seconds"),
        "timing.narration_tail_hold_seconds",
        allow_zero=True,
    )
    subtitle_tail = _positive_number(
        timing.get("subtitle_tail_hold_seconds"),
        "timing.subtitle_tail_hold_seconds",
        allow_zero=True,
    )
    block_policy = contracts.get("subtitle_block_policy")
    if block_policy != "paired-balanced":
        raise R11BuildError("r11 requires the paired-balanced subtitle block policy")
    for chapter in chapters:
        stem = f"{chapter.index:03d}-{_safe_slug(chapter.chapter_id)}"
        audio = audio_dir / f"{stem}.wav"
        metadata_path = audio_dir / f"{stem}.json"
        if not audio.is_file() or not metadata_path.is_file():
            raise R11BuildError(f"natural narration cache is incomplete for {chapter.chapter_id}")
        metadata = _load_json(metadata_path)
        if metadata.get("cue_id") != chapter.chapter_id:
            raise R11BuildError(f"narration metadata cue id mismatch: {metadata_path}")
        text_hash = hashlib.sha256(chapter.narration_en.encode("utf-8")).hexdigest().upper()
        if metadata.get("text_sha256") != text_hash:
            raise R11BuildError(f"narration text changed after synthesis: {chapter.chapter_id}")
        if metadata.get("wav_sha256") != _sha256(audio):
            raise R11BuildError(f"narration WAV hash mismatch: {audio}")
        duration = _wav_duration(audio)
        delay = float(chapter.raw.get("narration_delay_seconds", 0.0))
        chapter.narration_path = audio.resolve()
        chapter.narration_duration_seconds = duration
        chapter.voice = "authorized-owner-reference"
        chapter.tts_provider = "IndexTTS-2.5"
        chapter.tts_provider_version = str(metadata.get("model_revision", "unknown"))
        chapter.tts_settings = {"mode": "natural-reference-emotion", "tempo": "1.0"}
        chapter.tail_padding_seconds = tail
        chapter.shot_duration_seconds = delay + duration + tail
        chapter.raw["subtitle_block_policy"] = block_policy
        chapter.raw["subtitle_tail_hold_seconds"] = subtitle_tail
        chapter.raw["r11_audio_tempo"] = 1.0


def _agent_chapters(chapters: Sequence[showcase.Chapter]) -> list[showcase.Chapter]:
    return [
        chapter
        for chapter in chapters
        if chapter.raw.get("r11_source_manifest_key") == ROBERT_SOURCE_KEY
    ]


def apply_clean_video_overrides(
    chapters: Sequence[showcase.Chapter], config: dict[str, Any]
) -> None:
    """Replace known stale clean clips with later continuous clean captures.

    r6 remains the copy/timeline authority, but the r9 coat-of-arms capture is
    the corrected visual authority.  Its three output cues consume one
    contiguous source interval at a uniform playback rate, so the longer
    natural voice cannot cause a repeated first-20-seconds clip or a frozen
    tail.
    """

    values = config.get("clean_video_overrides", [])
    if not isinstance(values, list):
        raise R11BuildError("config.clean_video_overrides must be an array")
    chapter_index = {chapter.chapter_id: chapter for chapter in chapters}
    for index, value in enumerate(values):
        if not isinstance(value, dict):
            raise R11BuildError(f"clean_video_overrides[{index}] must be an object")
        master = _root_path(value.get("master"), f"clean_video_overrides[{index}].master")
        if not master.is_file():
            raise R11BuildError(f"clean video override is missing: {master}")
        cue_ids = value.get("cue_ids")
        if not isinstance(cue_ids, list) or not cue_ids or not all(
            isinstance(cue_id, str) for cue_id in cue_ids
        ):
            raise R11BuildError(f"clean_video_overrides[{index}].cue_ids is invalid")
        try:
            selected = [chapter_index[cue_id] for cue_id in cue_ids]
        except KeyError as exc:
            raise R11BuildError(
                f"clean video override references an unknown cue: {exc.args[0]}"
            ) from exc
        if any(chapter.kind != "video_clip" for chapter in selected):
            raise R11BuildError("clean video overrides may target only video_clip cues")
        source_start = _positive_number(
            value.get("source_start_seconds"),
            f"clean_video_overrides[{index}].source_start_seconds",
            allow_zero=True,
        )
        source_end = _positive_number(
            value.get("source_end_seconds"),
            f"clean_video_overrides[{index}].source_end_seconds",
        )
        if source_end <= source_start:
            raise R11BuildError(f"clean_video_overrides[{index}] has an empty interval")
        output_total = sum(float(chapter.shot_duration_seconds or 0.0) for chapter in selected)
        if output_total <= 0:
            raise R11BuildError("clean video override has no output duration")
        playback_rate = (source_end - source_start) / output_total
        master_hash = _sha256(master)
        record = showcase.SourceRecord(
            path=master,
            label=str(value.get("id", "continuous clean visual override")),
            role="continuous-clean-visual-master",
            bytes=master.stat().st_size,
            sha256=master_hash,
        )
        cursor = source_start
        for cue_index, chapter in enumerate(selected):
            duration = float(chapter.shot_duration_seconds or 0.0)
            end = source_end if cue_index == len(selected) - 1 else cursor + duration * playback_rate
            chapter.source_path = master
            chapter.sources = [record]
            chapter.start_seconds = cursor
            chapter.end_seconds = end
            chapter.raw["source"] = str(master)
            chapter.raw["start_seconds"] = cursor
            chapter.raw["end_seconds"] = end
            chapter.raw["source_playback_rate"] = playback_rate
            chapter.raw["r11_clean_video_override"] = str(value.get("id", "unnamed"))
            cursor = end


def allocate_provisional_robert_timing(
    chapters: Sequence[showcase.Chapter], *, target_seconds: float
) -> None:
    agent = _agent_chapters(chapters)
    base = [float(chapter.shot_duration_seconds or 0.0) for chapter in agent]
    if target_seconds + 1e-6 < sum(base):
        raise R11BuildError(
            f"provisional Robert target {target_seconds:.3f}s is shorter than "
            f"its natural narration floor {sum(base):.3f}s"
        )
    extra = target_seconds - sum(base)
    weights = [max(1.0, chapter.min_duration_seconds) for chapter in agent]
    weight_sum = sum(weights)
    for chapter, floor, weight in zip(agent, base, weights):
        chapter.shot_duration_seconds = floor + extra * weight / weight_sum
        chapter.raw["r11_robert_visual_status"] = "provisional-awaiting-continuous-master"


def load_robert_edit(path: Path, expected_ids: Sequence[str]) -> tuple[Path, list[RobertSpan]]:
    payload = _load_json(path)
    if payload.get("schema") != "project-causality-r11-robert-continuous-edit.v1":
        raise R11BuildError(f"unsupported Robert edit schema: {path}")
    master = _root_path(payload.get("master"), "robert_edit.master")
    if not master.is_file():
        raise R11BuildError(f"continuous Robert master is missing: {master}")
    values = payload.get("spans")
    if not isinstance(values, list) or len(values) != len(expected_ids):
        raise R11BuildError(
            f"Robert edit needs {len(expected_ids)} ordered spans; got "
            f"{len(values) if isinstance(values, list) else 'non-array'}"
        )
    spans: list[RobertSpan] = []
    for index, (value, expected_id) in enumerate(zip(values, expected_ids)):
        if not isinstance(value, dict) or value.get("cue_id") != expected_id:
            raise R11BuildError(f"Robert span {index} must target {expected_id}")
        start = _positive_number(
            value.get("source_start_seconds"),
            f"robert_edit.spans[{index}].source_start_seconds",
            allow_zero=True,
        )
        end = _positive_number(
            value.get("source_end_seconds"),
            f"robert_edit.spans[{index}].source_end_seconds",
        )
        rate = _positive_number(
            value.get("playback_rate"), f"robert_edit.spans[{index}].playback_rate"
        )
        if end <= start:
            raise R11BuildError(f"Robert span {expected_id} has an empty source interval")
        if spans and abs(start - spans[-1].source_end_seconds) > 1 / FPS + 1e-6:
            raise R11BuildError(
                f"Robert source continuity breaks before {expected_id}: "
                f"{spans[-1].source_end_seconds:.6f} -> {start:.6f}"
            )
        spans.append(RobertSpan(expected_id, start, end, rate))
    return master, spans


def apply_robert_edit(
    chapters: Sequence[showcase.Chapter],
    *,
    master: Path,
    spans: Sequence[RobertSpan],
    minimum_seconds: float,
    maximum_seconds: float,
) -> None:
    agent = _agent_chapters(chapters)
    if [row.cue_id for row in spans] != [row.chapter_id for row in agent]:
        raise R11BuildError("Robert edit cue order does not match the film composition")
    output_total = sum(row.output_seconds for row in spans)
    if output_total < minimum_seconds - 1e-6 or output_total > maximum_seconds + 1e-6:
        raise R11BuildError(
            f"Robert montage is {output_total:.3f}s; required range is "
            f"{minimum_seconds:.3f}..{maximum_seconds:.3f}s"
        )
    master_hash = _sha256(master)
    record = showcase.SourceRecord(
        path=master.resolve(),
        label="Continuous Robert 1066 clean master",
        role="continuous-gameplay-master",
        bytes=master.stat().st_size,
        sha256=master_hash,
    )
    for chapter, span in zip(agent, spans):
        floor = float(chapter.shot_duration_seconds or 0.0)
        if span.output_seconds + 1 / FPS < floor:
            raise R11BuildError(
                f"Robert span {span.cue_id} outputs {span.output_seconds:.3f}s, "
                f"shorter than its natural narration floor {floor:.3f}s"
            )
        chapter.source_path = master.resolve()
        chapter.sources = [record]
        chapter.start_seconds = span.source_start_seconds
        chapter.end_seconds = span.source_end_seconds
        chapter.shot_duration_seconds = span.output_seconds
        chapter.raw["source"] = str(master.resolve())
        chapter.raw["start_seconds"] = span.source_start_seconds
        chapter.raw["end_seconds"] = span.source_end_seconds
        chapter.raw["source_playback_rate"] = span.playback_rate
        chapter.raw["r11_robert_visual_status"] = "continuous-master-speed-ramp"


def validate_timeline(chapters: Sequence[showcase.Chapter], config: dict[str, Any]) -> None:
    contracts = config.get("contracts", {})
    timing = config.get("timing", {})
    gate_sfx_policy = str(contracts.get("gate_sound_effect_policy", "preserve"))
    if gate_sfx_policy not in {"preserve", "remove"}:
        raise R11BuildError(f"unsupported gate sound-effect policy: {gate_sfx_policy}")
    gates = [chapter for chapter in chapters if chapter.raw.get("chapter_gate") is True]
    if len(gates) != contracts.get("expected_gate_count"):
        raise R11BuildError(f"final composition has {len(gates)} chapter gates")
    expected_delay = float(contracts.get("gate_narration_delay_seconds"))
    for chapter in gates:
        if abs(float(chapter.raw.get("narration_delay_seconds", 0.0)) - expected_delay) > 1e-6:
            raise R11BuildError(f"gate delay changed for {chapter.chapter_id}")
        has_sound_effect = any(source.role == "sound-effect" for source in chapter.sources)
        if gate_sfx_policy == "preserve" and not has_sound_effect:
            raise R11BuildError(f"gate sound effect is missing for {chapter.chapter_id}")
        if gate_sfx_policy == "remove" and has_sound_effect:
            raise R11BuildError(f"gate sound effect remains for {chapter.chapter_id}")
    for chapter in chapters:
        delay = float(chapter.raw.get("narration_delay_seconds", 0.0))
        floor = delay + float(chapter.narration_duration_seconds or 0.0) + float(
            chapter.tail_padding_seconds
        )
        if float(chapter.shot_duration_seconds or 0.0) + 1 / FPS < floor:
            raise R11BuildError(f"natural narration is truncated in {chapter.chapter_id}")
        if chapter.raw.get("r11_audio_tempo") != 1.0:
            raise R11BuildError(f"audio tempo modification is forbidden: {chapter.chapter_id}")
    total = sum(float(chapter.shot_duration_seconds or 0.0) for chapter in chapters)
    maximum = float(timing.get("maximum_film_seconds"))
    if total > maximum + 1e-6:
        raise R11BuildError(f"r11 timeline is {total:.3f}s; maximum is {maximum:.3f}s")


def build_subtitle_plan(
    chapters: Sequence[showcase.Chapter],
) -> tuple[list[dict[str, Any]], list[tuple[float, float, str]]]:
    cursor = 0.0
    rows: list[dict[str, Any]] = []
    all_subtitles: list[tuple[float, float, str]] = []
    for chapter in chapters:
        duration = float(chapter.shot_duration_seconds or 0.0)
        subtitles = showcase._chapter_subtitle_cues(chapter, timeline_offset=cursor)
        all_subtitles.extend(subtitles)
        delay = float(chapter.raw.get("narration_delay_seconds", 0.0))
        narration_end = cursor + delay + float(chapter.narration_duration_seconds or 0.0)
        rows.append(
            {
                "index": chapter.index,
                "id": chapter.chapter_id,
                "source_manifest": chapter.raw.get("r11_source_manifest_key"),
                "start_seconds": round(cursor, 6),
                "end_seconds": round(cursor + duration, 6),
                "duration_seconds": round(duration, 6),
                "narration": {
                    "path": str(chapter.narration_path),
                    "sha256": _sha256(chapter.narration_path) if chapter.narration_path else None,
                    "start_seconds": round(cursor + delay, 6),
                    "end_seconds": round(narration_end, 6),
                    "duration_seconds": round(float(chapter.narration_duration_seconds or 0.0), 6),
                    "tempo": 1.0,
                },
                "subtitle_blocks": [
                    {
                        "start_seconds": round(start, 6),
                        "end_seconds": round(end, 6),
                        "text": text,
                    }
                    for start, end, text in subtitles
                ],
                "visual": {
                    "kind": chapter.kind,
                    "clean_source": str(chapter.source_path) if chapter.source_path else None,
                    "source_start_seconds": chapter.start_seconds,
                    "source_end_seconds": chapter.end_seconds,
                    "source_playback_rate": float(chapter.raw.get("source_playback_rate", 1.0)),
                    "uses_old_burned_picture_lock": False,
                },
                "chapter_gate": bool(chapter.raw.get("chapter_gate")),
                "sound_effect": next(
                    (str(source.path) for source in chapter.sources if source.role == "sound-effect"),
                    None,
                ),
            }
        )
        cursor += duration
    return rows, all_subtitles


def write_plan(
    *,
    path: Path,
    config_path: Path,
    config: dict[str, Any],
    manifests: dict[str, Path],
    chapters: Sequence[showcase.Chapter],
    robert_edit: Path | None,
) -> tuple[dict[str, Any], Path]:
    rows, subtitles = build_subtitle_plan(chapters)
    total = sum(float(chapter.shot_duration_seconds or 0.0) for chapter in chapters)
    agent = _agent_chapters(chapters)
    agent_total = sum(float(chapter.shot_duration_seconds or 0.0) for chapter in agent)
    ass_path = path.with_suffix(".zh-CN.ass")
    ass_path.parent.mkdir(parents=True, exist_ok=True)
    ass_path.write_text(showcase._ass_document(subtitles), encoding="utf-8-sig")
    payload = {
        "schema": "project-causality-r11-build-plan.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "config": {"path": str(config_path), "sha256": _sha256(config_path)},
        "source_manifests": {
            key: {"path": str(value), "sha256": _sha256(value)}
            for key, value in manifests.items()
        },
        "timeline": {
            "cue_count": len(chapters),
            "subtitle_block_count": len(subtitles),
            "duration_seconds": round(total, 6),
            "duration_minutes": round(total / 60, 3),
            "maximum_seconds": config["timing"]["maximum_film_seconds"],
            "audio_tempo_modified": False,
            "subtitle_timing_basis": "measured natural IndexTTS WAV durations",
            "subtitle_tail_hold_seconds": config["timing"]["subtitle_tail_hold_seconds"],
        },
        "robert_showcase": {
            "duration_seconds": round(agent_total, 6),
            "accepted_seconds": [
                config["timing"]["agent_showcase_minimum_seconds"],
                config["timing"]["agent_showcase_maximum_seconds"],
            ],
            "continuous_master_applied": robert_edit is not None,
            "edit_manifest": str(robert_edit) if robert_edit else None,
            "speed_changes_allowed": True,
            "source_time_discontinuities_allowed": False,
        },
        "render_policy": {
            "clean_manifest_sources_only": True,
            "old_burned_subtitle_picture_lock_allowed": False,
            "chapter_gate_delay_preserved": True,
            "chapter_gate_sfx_policy": config.get("contracts", {}).get(
                "gate_sound_effect_policy", "preserve"
            ),
            "chapter_gate_delay_and_sfx_preserved": config.get("contracts", {}).get(
                "gate_sound_effect_policy", "preserve"
            ) == "preserve",
            "render_requires_continuous_robert_master": True,
        },
        "subtitles": {"path": str(ass_path), "sha256": _sha256(ass_path)},
        "cues": rows,
    }
    _atomic_json(path, payload)
    return payload, ass_path


def render(
    *,
    chapters: Sequence[showcase.Chapter],
    config_path: Path,
    config: dict[str, Any],
    plan_path: Path,
    output_dir: Path,
    output: Path,
    force: bool,
    ffmpeg_override: str | None,
    ffprobe_override: str | None,
    preset: str,
    crf: int,
) -> Path:
    ffmpeg = showcase.find_program(ffmpeg_override, "ffmpeg")
    ffprobe = showcase.find_program(ffprobe_override, "ffprobe", sibling_of=ffmpeg)
    fonts = showcase.find_fonts()
    showcase.preflight_video_sources(list(chapters), ffprobe)
    work = output_dir / "work"
    work.mkdir(parents=True, exist_ok=True)
    for chapter in chapters:
        directory = work / f"{chapter.index:03d}-{_safe_slug(chapter.chapter_id)}"
        directory.mkdir(parents=True, exist_ok=True)
        showcase.encode_segment(
            chapter,
            directory,
            fonts=fonts,
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
            fps=FPS,
            crf=crf,
            preset=preset,
            force=force,
        )
    global_ass = work / "project-causality-r11.zh-CN.ass"
    showcase.write_global_ass(chapters, global_ass)
    output_info = showcase.concat_segments(
        chapters,
        build_directory=work,
        output=output,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
    )
    sidecar = showcase.write_sidecar(
        manifest_path=config_path,
        manifest=config,
        chapters=chapters,
        output=output,
        output_info=output_info,
        global_ass=global_ass,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
    )
    payload = _load_json(sidecar)
    payload["kind"] = "project_causality_r11_natural_owner_voice_candidate"
    payload["language"] = {
        "primary": "Simplified Chinese authorized-owner-reference narration and burned subtitles",
        "secondary": "English in-frame titles and burned subtitles",
    }
    payload["r11"] = {
        "plan": str(plan_path),
        "plan_sha256": _sha256(plan_path),
        "audio_tempo_modified": False,
        "clean_source_rebuild": True,
        "old_burned_subtitle_picture_lock_used": False,
        "publication_authorized": False,
    }
    _atomic_json(sidecar, payload)
    return sidecar


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    result.add_argument("--audio-dir", type=Path, default=DEFAULT_AUDIO_DIR)
    result.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    result.add_argument("--output", type=Path)
    result.add_argument("--plan-output", type=Path)
    result.add_argument("--robert-edit", type=Path)
    result.add_argument("--render", action="store_true")
    result.add_argument("--force", action="store_true")
    result.add_argument("--ffmpeg")
    result.add_argument("--ffprobe")
    result.add_argument("--preset", default="medium")
    result.add_argument("--crf", type=int, default=18)
    return result


def run(args: argparse.Namespace) -> tuple[Path, Path | None]:
    config_path = args.config.expanduser().resolve()
    audio_dir = args.audio_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    plan_path = (
        args.plan_output.expanduser().resolve()
        if args.plan_output
        else output_dir / "project-causality-r11.build-plan.json"
    )
    output = (
        args.output.expanduser().resolve()
        if args.output
        else output_dir / "project-causality-r11-owner-voice-nomusic.mp4"
    )
    config = _load_json(config_path)
    if config.get("schema") != "project-causality-r11-natural-voice-retime.v1":
        raise R11BuildError(f"unsupported r11 config schema: {config_path}")
    chapters, manifests = materialize_chapters(config)
    fonts = showcase.find_fonts()
    showcase.prepare_subtitle_layouts(chapters, fonts)
    attach_natural_audio(chapters, audio_dir=audio_dir, config=config)
    apply_clean_video_overrides(chapters, config)

    timing = config["timing"]
    minimum_agent = float(timing["agent_showcase_minimum_seconds"])
    maximum_agent = float(timing["agent_showcase_maximum_seconds"])
    edit_path: Path | None = None
    if args.robert_edit:
        edit_path = args.robert_edit.expanduser().resolve()
        agent_ids = [chapter.chapter_id for chapter in _agent_chapters(chapters)]
        master, spans = load_robert_edit(edit_path, agent_ids)
        apply_robert_edit(
            chapters,
            master=master,
            spans=spans,
            minimum_seconds=minimum_agent,
            maximum_seconds=maximum_agent,
        )
    else:
        allocate_provisional_robert_timing(
            chapters,
            target_seconds=float(timing["provisional_agent_showcase_seconds"]),
        )
    validate_timeline(chapters, config)
    plan, _ass = write_plan(
        path=plan_path,
        config_path=config_path,
        config=config,
        manifests=manifests,
        chapters=chapters,
        robert_edit=edit_path,
    )
    print(
        f"PLAN: {plan_path} | {plan['timeline']['cue_count']} cues | "
        f"{plan['timeline']['subtitle_block_count']} subtitle blocks | "
        f"{plan['timeline']['duration_minutes']:.3f} min",
        flush=True,
    )
    if not args.render:
        return plan_path, None
    if edit_path is None:
        raise R11BuildError(
            "--render requires --robert-edit so the final video cannot reuse the "
            "old discontinuous Robert clips"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    sidecar = render(
        chapters=chapters,
        config_path=config_path,
        config=config,
        plan_path=plan_path,
        output_dir=output_dir,
        output=output,
        force=args.force,
        ffmpeg_override=args.ffmpeg,
        ffprobe_override=args.ffprobe,
        preset=args.preset,
        crf=args.crf,
    )
    print(f"VIDEO: {output}", flush=True)
    print(f"SIDECAR: {sidecar}", flush=True)
    return plan_path, sidecar


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        run(args)
    except (R11BuildError, showcase.ShowcaseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
