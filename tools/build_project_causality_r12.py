#!/usr/bin/env python3
"""Build the publication-oriented, no-music Project Causality r12 film."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

import build_full_agent_showcase as showcase
import build_project_causality_owner_voice as owner_voice
import build_project_causality_r11 as r11


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "promo/project_causality/r12/edit-config.json"
DEFAULT_OUTPUT_DIR = ROOT / "artifacts/project-causality/2026-09-20-r12"
DEFAULT_OLD_AUDIO = (
    ROOT / "artifacts/project-causality/2026-09-19-r10-owner-voice/work/generated-cues"
)
DEFAULT_NEW_AUDIO = DEFAULT_OUTPUT_DIR / "work/generated-cues"
DEFAULT_INDEX_REPO = ROOT / "artifacts/project-causality/private/index-tts"
DEFAULT_VOICE_REFERENCE = (
    ROOT / "artifacts/project-causality/private/voice/owner-reference-indextts.wav"
)
FPS = 30


class R12BuildError(RuntimeError):
    pass


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def apply_text_overrides(
    chapters: Sequence[showcase.Chapter], config: dict[str, Any]
) -> None:
    raw = config.get("text_overrides", {})
    if not isinstance(raw, dict):
        raise R12BuildError("text_overrides must be an object")
    by_id = {chapter.chapter_id: chapter for chapter in chapters}
    allowed = {
        "title_en",
        "title_zh",
        "narration_en",
        "subtitle_zh",
        "subtitle_secondary",
    }
    for cue_id, values in raw.items():
        if cue_id not in by_id or not isinstance(values, dict):
            raise R12BuildError(f"invalid text override: {cue_id}")
        unknown = set(values) - allowed
        if unknown:
            raise R12BuildError(f"unsupported text fields for {cue_id}: {sorted(unknown)}")
        chapter = by_id[cue_id]
        for name, value in values.items():
            if not isinstance(value, str) or not value.strip():
                raise R12BuildError(f"text override {cue_id}.{name} must be non-empty")
            setattr(chapter, name, value.strip())
            chapter.raw[name] = value.strip()


def validate_text_integrity(chapters: Sequence[showcase.Chapter]) -> None:
    """Reject lossy-decoded copy before it reaches subtitles or owner-voice TTS."""
    fields = ("title_en", "title_zh", "narration_en", "subtitle_zh", "subtitle_secondary")
    for chapter in chapters:
        for name in fields:
            value = getattr(chapter, name, None)
            if isinstance(value, str) and "\ufffd" in value:
                raise R12BuildError(
                    f"text contains a Unicode replacement character: {chapter.chapter_id}.{name}"
                )


def use_continuous_agent_timing(chapters: Sequence[showcase.Chapter]) -> None:
    """Let the chronological Robert span map own visual duration per cue.

    The r9 standalone showcase used a uniform 42-second editorial floor.  R12
    carries longer natural narration but divides one continuous 388-second
    master at semantic events, so only the actual narration duration is the
    per-cue floor; the source spans remain gapless and authoritative.
    """
    for chapter in r11._agent_chapters(chapters):
        chapter.min_duration_seconds = 0.0
        chapter.raw["r12_timing_authority"] = "continuous-robert-source-span"


def audio_catalog(directories: Sequence[Path]) -> dict[tuple[str, str], tuple[Path, dict[str, Any]]]:
    result: dict[tuple[str, str], tuple[Path, dict[str, Any]]] = {}
    for directory in directories:
        if not directory.is_dir():
            continue
        for metadata_path in sorted(directory.glob("*.json")):
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                continue
            cue_id = metadata.get("cue_id")
            digest = metadata.get("text_sha256")
            wav = metadata_path.with_suffix(".wav")
            if isinstance(cue_id, str) and isinstance(digest, str) and wav.is_file():
                result[(cue_id, digest.upper())] = (wav.resolve(), metadata)
    return result


def synthesize_missing_audio(
    chapters: Sequence[showcase.Chapter],
    *,
    old_audio: Path,
    new_audio: Path,
    index_repo: Path,
    model_dir: Path,
    voice_reference: Path,
    enabled: bool,
) -> None:
    catalog = audio_catalog([old_audio, new_audio])
    pending: list[owner_voice.Cue] = []
    for chapter in chapters:
        key = (chapter.chapter_id, text_hash(chapter.narration_en))
        if key not in catalog:
            pending.append(
                owner_voice.Cue(
                    index=chapter.index,
                    cue_id=chapter.chapter_id,
                    text=chapter.narration_en,
                    start=0.0,
                    end=1.0,
                    narration_delay=0.0,
                    sound_effect=None,
                    source_label="r12",
                )
            )
    if not pending:
        return
    if not enabled:
        names = ", ".join(cue.cue_id for cue in pending[:8])
        raise R12BuildError(
            f"{len(pending)} narration cue(s) need synthesis; rerun with --synthesize: {names}"
        )
    new_audio.mkdir(parents=True, exist_ok=True)
    owner_voice.synthesize_cues(
        pending,
        index_repo=index_repo,
        model_dir=model_dir,
        voice_reference=voice_reference,
        generated_dir=new_audio,
        force=False,
    )


def attach_audio(
    chapters: Sequence[showcase.Chapter],
    *,
    config: dict[str, Any],
    old_audio: Path,
    new_audio: Path,
) -> None:
    catalog = audio_catalog([old_audio, new_audio])
    timing = config["timing"]
    tail = float(timing["narration_tail_hold_seconds"])
    subtitle_tail = float(timing["subtitle_tail_hold_seconds"])
    for chapter in chapters:
        key = (chapter.chapter_id, text_hash(chapter.narration_en))
        found = catalog.get(key)
        if found is None:
            raise R12BuildError(f"narration cache is missing for {chapter.chapter_id}")
        wav, metadata = found
        if metadata.get("wav_sha256") != r11._sha256(wav):
            raise R12BuildError(f"narration WAV hash mismatch: {wav}")
        duration = r11._wav_duration(wav)
        delay = float(chapter.raw.get("narration_delay_seconds", 0.0))
        chapter.narration_path = wav
        chapter.narration_duration_seconds = duration
        chapter.voice = "authorized-owner-reference"
        chapter.tts_provider = "IndexTTS-2.5"
        chapter.tts_provider_version = str(metadata.get("model_revision", "unknown"))
        chapter.tts_settings = {"mode": "natural-reference-emotion", "tempo": "1.0"}
        chapter.tail_padding_seconds = tail
        chapter.shot_duration_seconds = max(
            float(chapter.min_duration_seconds), delay + duration + tail
        )
        chapter.raw["subtitle_block_policy"] = "paired-balanced"
        chapter.raw["subtitle_tail_hold_seconds"] = subtitle_tail
        chapter.raw["r11_audio_tempo"] = 1.0


def apply_visual_overrides(
    chapters: Sequence[showcase.Chapter], config: dict[str, Any]
) -> None:
    raw = config.get("visual_overrides", {})
    if not isinstance(raw, dict):
        raise R12BuildError("visual_overrides must be an object")
    by_id = {chapter.chapter_id: chapter for chapter in chapters}
    for cue_id, values in raw.items():
        if cue_id not in by_id or not isinstance(values, dict):
            raise R12BuildError(f"invalid visual override: {cue_id}")
        path = r11._root_path(values.get("source"), f"visual_overrides.{cue_id}.source")
        if not path.is_file():
            raise R12BuildError(f"visual override source is missing: {path}")
        start = float(values.get("start_seconds", 0.0))
        end = float(values.get("end_seconds", 0.0))
        if start < 0 or end <= start:
            raise R12BuildError(f"invalid visual interval for {cue_id}")
        chapter = by_id[cue_id]
        duration = float(chapter.shot_duration_seconds or 0.0)
        if duration <= 0:
            raise R12BuildError(f"visual target has no duration: {cue_id}")
        chapter.kind = "video_clip"
        chapter.source_path = path
        chapter.start_seconds = start
        chapter.end_seconds = end
        chapter.sources = [
            showcase.SourceRecord(
                path=path,
                label="r12 native-topology motion plate",
                role="clean-motion-visual",
                bytes=path.stat().st_size,
                sha256=r11._sha256(path),
            )
        ]
        chapter.raw["source"] = str(path)
        chapter.raw["start_seconds"] = start
        chapter.raw["end_seconds"] = end
        chapter.raw["source_playback_rate"] = (end - start) / duration
        chapter.raw["r12_visual_override"] = True


def subtitle_time(value: float) -> str:
    milliseconds = max(0, int(round(value * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def english_blocks(text: str, *, maximum: int = 105) -> list[str]:
    sentences = [value.strip() for value in re.split(r"(?<=[.!?])\s+", text) if value.strip()]
    if not sentences:
        return [text.strip()]
    result: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > maximum:
            result.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        result.append(current)
    return result


def write_english_srt(
    chapters: Sequence[showcase.Chapter], english: dict[str, str], path: Path
) -> None:
    cursor = 0.0
    rows: list[str] = []
    index = 1
    for chapter in chapters:
        duration = float(chapter.shot_duration_seconds or 0.0)
        delay = float(chapter.raw.get("narration_delay_seconds", 0.0))
        start = cursor + delay + min(0.2, duration / 10)
        end = min(
            cursor + duration - 0.1,
            cursor + delay + float(chapter.narration_duration_seconds or 0.0) + 1.0,
        )
        blocks = english_blocks(english[chapter.chapter_id])
        weights = [max(1, len(block)) for block in blocks]
        total_weight = sum(weights)
        local = start
        for position, (block, weight) in enumerate(zip(blocks, weights)):
            block_end = end if position == len(blocks) - 1 else local + (end - start) * weight / total_weight
            rows.extend(
                [str(index), f"{subtitle_time(local)} --> {subtitle_time(block_end)}", block, ""]
            )
            index += 1
            local = block_end
        cursor += duration
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows), encoding="utf-8-sig", newline="\n")


def timeline_starts(chapters: Sequence[showcase.Chapter]) -> dict[str, float]:
    result: dict[str, float] = {}
    cursor = 0.0
    for chapter in chapters:
        result[chapter.chapter_id] = cursor
        cursor += float(chapter.shot_duration_seconds or 0.0)
    result["__end__"] = cursor
    return result


def chapter_markers(chapters: Sequence[showcase.Chapter]) -> list[tuple[str, float]]:
    starts = timeline_starts(chapters)
    values = [
        ("开场｜为什么需要 project 因果律", starts[chapters[0].chapter_id]),
        ("咒｜今天已经可以使用的产品", starts["spell-gate-r8"]),
        ("罗贝尔｜从主菜单开始的连续自主游玩", starts["fresh-ruler-selection"]),
        ("术｜一条改动怎样走到发布", starts["method-gate-r8"]),
        ("道｜什么才算真的完成", starts["principle-gate-r8"]),
        ("辉煌愿景｜四个无限演进 Loop", starts["vision-gate-r8"]),
        ("从这里开始｜已有 Mod 与新创作者", starts["cta-two-entrances"]),
    ]
    return values


def metadata_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("=", "\\=").replace(";", "\\;").replace("#", "\\#")


def write_chapter_metadata(chapters: Sequence[showcase.Chapter], path: Path) -> None:
    markers = chapter_markers(chapters)
    total = timeline_starts(chapters)["__end__"]
    rows = [";FFMETADATA1", "title=Project Causality — 伪天司的辉煌愿景"]
    for index, (title, start) in enumerate(markers):
        end = markers[index + 1][1] if index + 1 < len(markers) else total
        rows.extend(
            [
                "[CHAPTER]",
                "TIMEBASE=1/1000",
                f"START={int(round(start * 1000))}",
                f"END={int(round(end * 1000))}",
                f"title={metadata_escape(title)}",
            ]
        )
    path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def write_youtube_chapters(chapters: Sequence[showcase.Chapter], path: Path) -> None:
    def stamp(value: float) -> str:
        seconds = int(value)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"

    path.write_text(
        "\n".join(f"{stamp(start)} {title}" for title, start in chapter_markers(chapters)) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def run_checked(command: Sequence[str | Path], *, context: str) -> None:
    print("RUN:", " ".join(str(value) for value in command), flush=True)
    result = subprocess.run([str(value) for value in command], check=False)
    if result.returncode:
        raise R12BuildError(f"{context} failed with exit code {result.returncode}")


def render(
    *,
    chapters: Sequence[showcase.Chapter],
    english: dict[str, str],
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
        directory = work / f"{chapter.index:03d}-{r11._safe_slug(chapter.chapter_id)}"
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

    chinese_ass = work / "project-causality-r12.zh-Hans.ass"
    showcase.write_global_ass(chapters, chinese_ass)
    english_srt = output_dir / "project-causality-r12.en.srt"
    chapters_meta = work / "project-causality-r12.ffmetadata"
    youtube_chapters = output_dir / "project-causality-r12.chapters.txt"
    write_english_srt(chapters, english, english_srt)
    write_chapter_metadata(chapters, chapters_meta)
    write_youtube_chapters(chapters, youtube_chapters)

    intermediate = work / "project-causality-r12-intermediate.mp4"
    showcase.concat_segments(
        chapters,
        build_directory=work,
        output=intermediate,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
    )
    temporary = output.with_name(f".{output.stem}.partial.mp4")
    temporary.unlink(missing_ok=True)
    run_checked(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            intermediate,
            "-i",
            english_srt,
            "-i",
            chapters_meta,
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-map",
            "1:0",
            "-map_metadata",
            "0",
            "-map_chapters",
            "2",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-af",
            "loudnorm=I=-16:LRA=7:TP=-1.5",
            "-c:s",
            "mov_text",
            "-metadata:s:a:0",
            "language=zho",
            "-metadata:s:s:0",
            "language=eng",
            "-metadata:s:s:0",
            "title=English",
            "-metadata",
            "title=Project Causality — 伪天司的辉煌愿景",
            "-movflags",
            "+faststart",
            temporary,
        ],
        context="publication remux",
    )
    temporary.replace(output)
    output_info = showcase.validate_encoded_media(
        showcase.probe_media(ffprobe, output),
        output,
        expected_duration=timeline_starts(chapters)["__end__"],
        duration_tolerance=max(0.5, len(chapters) * 0.08),
    )
    sidecar = showcase.write_sidecar(
        manifest_path=config_path,
        manifest=config,
        chapters=chapters,
        output=output,
        output_info=output_info,
        global_ass=chinese_ass,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
    )
    payload = r11._load_json(sidecar)
    payload["kind"] = "project_causality_r12_publication_candidate_no_music"
    payload["language"] = {
        "primary": "Simplified Chinese authorized-owner-reference narration and burned subtitles",
        "secondary": "selectable English mov_text subtitle track",
    }
    payload["r12"] = {
        "plan": str(plan_path),
        "plan_sha256": r11._sha256(plan_path),
        "audio_tempo_modified": False,
        "music_track_present": False,
        "continuous_robert_source": True,
        "main_menu_establishing_hold_seconds": 3.0,
        "english_srt": str(english_srt),
        "english_srt_sha256": r11._sha256(english_srt),
        "chapters": str(youtube_chapters),
        "chapters_sha256": r11._sha256(youtube_chapters),
        "publication_authorized": False,
    }
    r11._atomic_json(sidecar, payload)
    return sidecar


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    result.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    result.add_argument("--output", type=Path)
    result.add_argument("--plan-output", type=Path)
    result.add_argument("--robert-edit", type=Path, required=True)
    result.add_argument("--old-audio-dir", type=Path, default=DEFAULT_OLD_AUDIO)
    result.add_argument("--new-audio-dir", type=Path, default=DEFAULT_NEW_AUDIO)
    result.add_argument("--index-repo", type=Path, default=DEFAULT_INDEX_REPO)
    result.add_argument("--model-dir", type=Path)
    result.add_argument("--voice-reference", type=Path, default=DEFAULT_VOICE_REFERENCE)
    result.add_argument("--synthesize", action="store_true")
    result.add_argument("--render", action="store_true")
    result.add_argument("--force", action="store_true")
    result.add_argument("--ffmpeg")
    result.add_argument("--ffprobe")
    result.add_argument("--preset", default="fast")
    result.add_argument("--crf", type=int, default=18)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        config_path = args.config.expanduser().resolve()
        config = r11._load_json(config_path)
        if config.get("schema") != "project-causality-r12-publication-edit.v1":
            raise R12BuildError(f"unsupported r12 config schema: {config_path}")
        output_dir = args.output_dir.expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output = (
            args.output.expanduser().resolve()
            if args.output
            else output_dir / "project-causality-r12-owner-voice-nomusic.mp4"
        )
        plan_path = (
            args.plan_output.expanduser().resolve()
            if args.plan_output
            else output_dir / "project-causality-r12.build-plan.json"
        )
        old_audio = args.old_audio_dir.expanduser().resolve()
        new_audio = args.new_audio_dir.expanduser().resolve()
        index_repo = args.index_repo.expanduser().resolve()
        model_dir = (args.model_dir or index_repo / "checkpoints").expanduser().resolve()
        voice_reference = args.voice_reference.expanduser().resolve()

        chapters, manifests = r11.materialize_chapters(config)
        apply_text_overrides(chapters, config)
        validate_text_integrity(chapters)
        use_continuous_agent_timing(chapters)
        english = {
            chapter.chapter_id: str(chapter.subtitle_secondary or chapter.title_en)
            for chapter in chapters
        }
        for chapter in chapters:
            chapter.subtitle_secondary = None
            chapter.raw.pop("subtitle_secondary", None)
        fonts = showcase.find_fonts()
        showcase.prepare_subtitle_layouts(chapters, fonts)
        synthesize_missing_audio(
            chapters,
            old_audio=old_audio,
            new_audio=new_audio,
            index_repo=index_repo,
            model_dir=model_dir,
            voice_reference=voice_reference,
            enabled=args.synthesize,
        )
        attach_audio(chapters, config=config, old_audio=old_audio, new_audio=new_audio)
        r11.apply_clean_video_overrides(chapters, config)
        robert_edit = args.robert_edit.expanduser().resolve()
        agent = r11._agent_chapters(chapters)
        master, spans = r11.load_robert_edit(
            robert_edit, [chapter.chapter_id for chapter in agent]
        )
        r11.apply_robert_edit(
            chapters,
            master=master,
            spans=spans,
            minimum_seconds=float(config["timing"]["agent_showcase_minimum_seconds"]),
            maximum_seconds=float(config["timing"]["agent_showcase_maximum_seconds"]),
        )
        apply_visual_overrides(chapters, config)
        r11.validate_timeline(chapters, config)
        plan, _ass = r11.write_plan(
            path=plan_path,
            config_path=config_path,
            config=config,
            manifests=manifests,
            chapters=chapters,
            robert_edit=robert_edit,
        )
        plan["schema"] = "project-causality-r12-build-plan.v1"
        plan["subtitle_strategy"] = {
            "burned": "Simplified Chinese",
            "selectable": "English",
            "bilingual_burned": False,
        }
        plan["music"] = {"present": False, "status": "explicitly deferred by owner"}
        plan["chapter_markers"] = [
            {"title": title, "start_seconds": round(start, 3)}
            for title, start in chapter_markers(chapters)
        ]
        r11._atomic_json(plan_path, plan)
        print(
            f"PLAN: {plan_path} | {len(chapters)} cues | "
            f"{plan['timeline']['duration_minutes']:.3f} min",
            flush=True,
        )
        if args.render:
            sidecar = render(
                chapters=chapters,
                english=english,
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
        return 0
    except (R12BuildError, r11.R11BuildError, showcase.ShowcaseError, owner_voice.BuildError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
