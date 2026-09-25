"""R0217 EdgeTTS arithmetic pilot: source-bound cards plus labelled CK3 context."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw
from xar_promo.media import probe_media
from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.process import CommandSpec, run_command
from xar_promo.render import RenderOptions
from xar_promo.sources import VIDEO, VisualProbeResult, VisualSource
from xar_promo.subtitles import AssCue, AssDocumentConfig, AssStyleConfig, SubtitleTrackConfig, render_ass_document

from .captions import caption_cues, subtitle_document
from .common import font, lines, load
from .episode_one_observation import gameplay_clip
from .visuals import BG, GOLD, INK, MUTED, PANEL, box, heraldic_mark, make_canvas


def _artifact(run, run_path: Path, artifact_id: str) -> Path:
    matches = [item for item in run.artifacts if item.artifact_id == artifact_id]
    if len(matches) != 1:
        raise ValueError(f"Expected one artifact {artifact_id}; found {len(matches)}")
    return (run_path.parent / matches[0].path).resolve(strict=True)


def _text(draw: ImageDraw.ImageDraw, x: int, y: int, value: str, size: int,
          *, color: str = INK, bold: bool = False, width: int | None = None) -> None:
    rows = lines(value, size, width, bold) if width else [value]
    for index, line in enumerate(rows):
        draw.text((x, y + index * size * 1.3), line,
                  font=font(size, bold), fill=color)


def _card(row: dict, active: int, path: Path) -> None:
    image = make_canvas()
    draw = ImageDraw.Draw(image)
    heraldic_mark(draw, (140, 126), 72, GOLD)
    _text(draw, 209, 78, "十字军之王 III · 原版战斗算术", 38,
          color=GOLD, bold=True)
    _text(draw, 148, 190, row["visual_title"], 76, bold=True, width=2210)
    _text(draw, 153, 320, row.get("source_label", "R0217 · 单个主阶段 tick · Q100000"), 40,
          color=MUTED)
    for index, line in enumerate(row["visual_lines"]):
        top = 431 + 207 * index
        selected = index <= active
        box(draw, (148, top, 2412, top + 181),
            PANEL if selected else "#29211A", GOLD if index == active else "#66513A")
        draw.rectangle((181, top + 29, 193, top + 149),
                       fill=GOLD if index == active else "#66513A")
        _text(draw, 224, top + 32, f"0{index + 1}", 56,
              color=GOLD if selected else MUTED, bold=True)
        _text(draw, 342, top + 38, line, 57 if len(line) < 37 else 47,
              color=INK if selected else MUTED, bold=index == active,
              width=1980)
    draw.line((146, 1081, 2414, 1081), fill="#66513A", width=2)
    _text(draw, 155, 1101, row.get("footer", "原版 1.19.0.6 · 数字来源：docs/ck3-native-ai/battle-simulation.md · R0217"),
          30, color=GOLD)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        image.save(stream, format="PNG")


def _card_clip(row: dict, target: Path, ffmpeg: str, work: Path) -> Path:
    duration = float(row["duration_seconds"])
    if duration < 4:
        raise ValueError("A numeric card requires at least four seconds")
    drawings = work / "drawings" / row["id"]
    drawings.mkdir(parents=True, exist_ok=False)
    frames = [drawings / f"stage-{index}.png" for index in range(3)]
    for index, frame in enumerate(frames):
        _card(row, index, frame)
    fade = min(0.4, duration / 12)
    frame_duration = (duration + 2 * fade) / 3
    first = frame_duration - fade
    second = 2 * first
    filters = [
        f"[{index}:v]trim=duration={frame_duration:.6f},settb=AVTB,setpts=PTS-STARTPTS,format=yuv420p[s{index}]"
        for index in range(3)
    ]
    filters += [
        f"[s0][s1]xfade=transition=fade:duration={fade:.6f}:offset={first:.6f}[ab]",
        f"[ab][s2]xfade=transition=fade:duration={fade:.6f}:offset={second:.6f},format=yuv420p[v]",
    ]
    argv = [ffmpeg, "-nostdin", "-n", "-hide_banner", "-loglevel", "warning"]
    for frame in frames:
        argv += ["-loop", "1", "-framerate", "30", "-i", str(frame)]
    argv += ["-filter_complex_threads", "1", "-filter_complex", ";".join(filters),
             "-map", "[v]", "-an", "-t", f"{duration:.6f}", "-r", "30",
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
             "-threads", "4", str(target)]
    target.parent.mkdir(parents=True, exist_ok=True)
    run_command(CommandSpec.create(argv, label=f"R0217-math-card-{row['id']}",
                                   partial_artifacts=[target]),
                audit_directory=work / "audit" / "cards" / row["id"])
    (drawings / "visual-plan.json").write_text(json.dumps({
        "cue_id": row["id"], "source_case": row.get("source_label", "R0217"),
        "source_scope": row.get("source_scope", "one native main-phase tick"),
        "stage_frames": [str(path) for path in frames], "duration_seconds": duration,
        "claims": row["visual_lines"], "human_signoff": "not-provided",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def _gameplay_captions(row: dict) -> str:
    cues = [AssCue(cue.cue_id, "zh", cue.start_seconds,
                   cue.end_seconds, cue.text)
            for cue in caption_cues(row) if cue.track_id == "zh"]
    track = SubtitleTrackConfig("zh", "zh-CN", 2, AssStyleConfig(
        name="ChineseGameplay", font_name="Microsoft YaHei", font_size=49,
        bold=True, alignment=8, margin_left=370, margin_right=370,
        margin_vertical=238, outline=2.5))
    return render_ass_document(
        AssDocumentConfig(row["shot_title"], 2560, 1440,
                          duration_seconds=row["duration_seconds"]),
        [track], cues, available_font_names={"Microsoft YaHei"})


def _gameplay_overlay(path: Path) -> None:
    image = Image.new("RGBA", (2560, 1440), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for left, right in [(0, 319), (2240, 2559)]:
        draw.rectangle((left, 0, right, 1439), fill=(30, 21, 16, 255))
    draw.line((315, 0, 315, 1439), fill=GOLD, width=4)
    draw.line((2244, 0, 2244, 1439), fill=GOLD, width=4)
    heraldic_mark(draw, (158, 155), 101, GOLD)
    for y, line in [(265, "原版实机"), (350, "墨西拿"), (450, "独立重放"),
                    (565, "非 R0217")]:
        _text(draw, 35, y, line, 42 if y < 400 else 35,
              color=GOLD if y in (265, 565) else INK, bold=y in (265, 565))
    for y, line in [(265, "CK3"), (333, "1.19.0.6"), (470, "战场背景"),
                    (535, "数字另案")]:
        _text(draw, 2265, y, line, 39 if y == 265 else 31,
              color=GOLD if y in (265, 535) else INK, bold=y == 265)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        image.save(stream, format="PNG")


def compose(config, run, *, config_path, run_path, workdir,
            adapter_factory, preset_factory, validate_only):
    del config_path, adapter_factory, preset_factory, validate_only
    if config.project_id != "ck3-native-war-ai-episode-01-math-pilot":
        raise ValueError("Wrong project for R0217 math pilot")
    inputs = load(_artifact(run, run_path, "math-production-inputs"))
    rows = inputs["cues"]
    if inputs["provider"] != "edge" or inputs["human_signoff"] != "not-provided":
        raise ValueError("Expected unsigned EdgeTTS pilot")
    if len(rows) != 8 or [row["id"] for row in rows] != [f"M{index:02d}" for index in range(1, 9)]:
        raise ValueError("Expected exact eight-cue math pilot")
    if rows[0]["visual_kind"] != "gameplay" or any(row["visual_kind"] != "card" for row in rows[1:]):
        raise ValueError("Unexpected pilot visual sequence")
    if not 120 <= sum(row["duration_seconds"] for row in rows) <= 360:
        raise ValueError("Pilot duration outside 2–6 minutes")
    gameplay = _artifact(run, run_path, "labelled-messina-context-source")
    work = Path(workdir)
    ffmpeg = os.environ.get("WAR_PROMO_FFMPEG", "ffmpeg")
    ffprobe = os.environ.get("WAR_PROMO_FFPROBE", "ffprobe")
    overlay = work / "drawings" / "messina-provenance-overlay.png"
    _gameplay_overlay(overlay)
    by_id = {row["id"]: row for row in rows}
    segments = []
    for row in rows:
        duration = float(row["duration_seconds"])
        if not math.isfinite(duration) or duration < row["speech_duration_seconds"]:
            raise ValueError(f"Invalid cue duration: {row['id']}")
        segments.append(SegmentDraft(
            segment_id=row["id"],
            visual_source=VisualSource(row["id"], VIDEO,
                                       Path("visuals") / f"{row['id']}.mp4",
                                       "separate-labelled-CK3-context" if row["id"] == "M01"
                                       else "R0217-source-bound-math-card", requires_resolution=True),
            render_options=RenderOptions(2560, 1440, 30, duration,
                                         preset="veryfast", crf=21),
            subtitles={"zh-CN": row["zh"], "en": row["en"]},
            prepared_narration=_artifact(run, run_path, row["audio_artifact_id"]),
        ))

    def resolve_visual(source, *, workdir):
        row = by_id[source.source_id]
        target = Path(workdir) / source.path
        if source.source_id == "M01":
            return gameplay_clip(gameplay, overlay,
                                 {"id": "M01", "gameplay_start_seconds": 0},
                                 float(row["duration_seconds"]), target, ffmpeg, Path(workdir))
        return _card_clip(row, target, ffmpeg, Path(workdir))

    def visual_probe(path):
        measured = probe_media(ffprobe, path,
                               audit_directory=work / "audit" / "probe" / path.stem)
        stream = measured.video_streams[0]
        return VisualProbeResult("video/mp4", stream.width, stream.height)

    def subtitle_renderer(segment, narration, *, workdir):
        del narration, workdir
        row = by_id[segment.segment_id]
        return _gameplay_captions(row) if row["id"] == "M01" else subtitle_document(row)

    return PipelineInvocation(
        PipelineDraft(config, tuple(segments), Path("episode-01-math-pilot-unmixed.mp4"),
                      "episode-01-math-pilot-unmixed-v1", "video/mp4"),
        PipelineDependencies(ffmpeg, subtitle_renderer, run_command, visual_probe,
                             visual_resolver=resolve_visual), work)
