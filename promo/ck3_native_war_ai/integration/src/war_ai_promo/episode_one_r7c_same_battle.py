"""Render Episode 1 R7C with muted CK3-style colors and a clear caption strip."""

from __future__ import annotations

import hashlib
from functools import lru_cache
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

from .captions import subtitle_document
from .common import font, lines, load
from .episode_one_math_sample import _artifact


FRAME_LABELS = {
    245: "原始墨西拿战斗 · 开场",
    250: "守方约 1,288 / 攻方约 330",
    260: "守方约 1,288 / 攻方约 2,003",
    275: "源日：守方约 1,222 / 攻方约 1,921",
    280: "下一状态：守方约 1,156 / 攻方约 1,860",
    300: "原始战局 · 主战继续",
    390: "原始战局 · 主战后段",
    400: "追击：守方现役 0 / 攻方约 4,576",
    420: "追击末段：守方现役 0 / 攻方约 4,576",
    423: "原始战局终局 · 守方战败",
}


@lru_cache(maxsize=16)
def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _frame(source: Path, second: int, *, ffmpeg: str, work: Path) -> Path:
    if second not in FRAME_LABELS:
        raise ValueError(f"Unreviewed source frame second {second}")
    path = work / "source-frames" / f"messina-original-{second:03d}s.png"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        run_command(CommandSpec.create(
            [ffmpeg, "-nostdin", "-n", "-hide_banner", "-loglevel", "error",
             "-ss", str(second), "-i", str(source), "-frames:v", "1", str(path)],
            label=f"R7-original-frame-{second}", partial_artifacts=[path]),
            audit_directory=work / "audit" / "source-frames" / str(second))
    with Image.open(path) as image:
        if image.size != (1024, 768):
            raise ValueError(f"Original frame {second} has unexpected size {image.size}")
    return path


def _text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str,
          size: int, *, fill: str, bold: bool = False) -> None:
    draw.text(xy, value, font=font(size, bold), fill=fill)


def _stage(row: dict, index: int, source_frame: Path, target_frame: Path, output: Path) -> None:
    canvas = Image.new("RGB", (2560, 1440), "#181B1D")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 2559, 72), fill="#33272A")
    draw.rectangle((0, 72, 2559, 79), fill="#8B7568")
    _text(draw, (34, 7), row["visual_title"], 46, fill="#E9E0D3", bold=True)
    frame_second = row["source_time_seconds"] if index < 2 else row["target_time_seconds"]
    frame = source_frame if index < 2 else target_frame
    with Image.open(frame) as original:
        picture = original.convert("RGB").resize((1344, 1008), Image.Resampling.LANCZOS)
    canvas.paste(picture, (24, 92))
    draw.rectangle((20, 88, 1372, 1104), outline="#796D61", width=3)
    draw.rounded_rectangle((40, 102, 1290, 180), radius=9, fill="#202529")
    _text(draw, (57, 110), f"原版实机定格 · 原片 {frame_second} 秒", 31,
          fill="#D3C1A7", bold=True)
    _text(draw, (57, 149), FRAME_LABELS[frame_second], 26, fill="#E5DDD1")
    draw.rounded_rectangle((1394, 92, 2538, 1104), radius=10,
                           fill="#242627", outline="#796D61", width=2)
    _text(draw, (1430, 116), "同场计算 / UI 对照", 34,
          fill="#D3C1A7", bold=True)
    _text(draw, (1430, 167), "墨西拿 · CombatID 16777218", 28,
          fill="#E9E0D3")
    for claim_index, claim in enumerate(row["visual_lines"]):
        top = 233 + claim_index * 269
        active = claim_index <= index
        draw.rounded_rectangle((1424, top, 2506, top + 243), radius=8,
                               fill="#303437" if active else "#292C2F",
                               outline="#9B806E" if active else "#56585A", width=2)
        _text(draw, (1445, top + 13), f"{claim_index + 1:02d}", 31,
              fill="#D3C1A7" if active else "#9F9A93", bold=True)
        for claim_size in (40, 37, 34, 31):
            wrapped = lines(claim, claim_size, 960, True)
            if len(wrapped) <= 4:
                break
        else:
            raise ValueError(f"{row['id']} claim {claim_index + 1} exceeds four lines")
        line_step = claim_size + 12
        first_line_y = top + max(18, (243 - len(wrapped) * line_step) // 2)
        for line_index, line in enumerate(wrapped):
            _text(draw, (1510, first_line_y + line_step * line_index), line, claim_size,
                  fill="#F1ECE4" if active else "#A9AAA9", bold=active)
    draw.rectangle((0, 1120, 2559, 1439), fill="#121416")
    draw.rectangle((0, 1120, 2559, 1126), fill="#796D61")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        canvas.save(stream, format="PNG")


def _paired_clip(row: dict, source_video: Path, target: Path,
                 *, ffmpeg: str, work: Path) -> Path:
    duration = float(row["duration_seconds"])
    if duration < 4:
        raise ValueError(f"{row['id']}: narration too short")
    first = _frame(source_video, int(row["source_time_seconds"]), ffmpeg=ffmpeg, work=work)
    last = _frame(source_video, int(row["target_time_seconds"]), ffmpeg=ffmpeg, work=work)
    drawing = work / "paired-drawings" / row["id"]
    drawing.mkdir(parents=True, exist_ok=False)
    stages = [drawing / f"stage-{index}.png" for index in range(3)]
    for index, stage in enumerate(stages):
        _stage(row, index, first, last, stage)
    fade = min(0.4, duration / 12)
    frame_duration = (duration + 2 * fade) / 3
    offset_1 = frame_duration - fade
    offset_2 = 2 * offset_1
    filters = [
        f"[{index}:v]trim=duration={frame_duration:.6f},settb=AVTB,setpts=PTS-STARTPTS,format=yuv420p[s{index}]"
        for index in range(3)
    ] + [
        f"[s0][s1]xfade=transition=fade:duration={fade:.6f}:offset={offset_1:.6f}[ab]",
        f"[ab][s2]xfade=transition=fade:duration={fade:.6f}:offset={offset_2:.6f},format=yuv420p[v]",
    ]
    argv = [ffmpeg, "-nostdin", "-n", "-hide_banner", "-loglevel", "warning"]
    for stage in stages:
        argv += ["-loop", "1", "-framerate", "30", "-i", str(stage)]
    argv += ["-filter_complex_threads", "1", "-filter_complex", ";".join(filters),
             "-map", "[v]", "-an", "-t", f"{duration:.6f}", "-r", "30",
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
             "-threads", "4", str(target)]
    target.parent.mkdir(parents=True, exist_ok=True)
    run_command(CommandSpec.create(argv, label="R7-same-battle-" + row["id"],
                                   partial_artifacts=[target]),
                audit_directory=work / "audit" / "paired-clips" / row["id"])
    (drawing / "visual-plan.json").write_text(json.dumps({
        "cue_id": row["id"], "source_combat_id": 16777218,
        "source_video": str(source_video), "source_video_sha256": _sha256(source_video),
        "source_time_seconds": row["source_time_seconds"],
        "target_time_seconds": row["target_time_seconds"],
        "source_frame_sha256": _sha256(first), "target_frame_sha256": _sha256(last),
        "stage_frames": [str(path) for path in stages],
        "visible_claims": row["visual_lines"], "duration_seconds": duration,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def compose(config, run, *, config_path, run_path, workdir,
            adapter_factory, preset_factory, validate_only):
    del config_path, adapter_factory, preset_factory, validate_only
    if config.project_id != "ck3-war-ai-episode-01-r7c-same-battle":
        raise ValueError("Wrong ProjectConfig for original Messina recut")
    inputs = load(_artifact(run, run_path, "r7-production-inputs"))
    rows = inputs["cues"]
    if len(rows) != 23 or len({row["id"] for row in rows}) != 23:
        raise ValueError("Expected 23 unique Messina cues")
    if inputs["provider"] != "edge" or inputs["human_signoff"] != "not-provided":
        raise ValueError("Expected unsigned EdgeTTS production inputs")
    total = sum(row["duration_seconds"] for row in rows)
    if not 1200 <= total <= 2400:
        raise ValueError(f"Episode length {total} outside 20–40 minutes")
    source = _artifact(run, run_path, "messina-original-900s-film")
    work = Path(workdir)
    ffmpeg = os.environ.get("WAR_PROMO_FFMPEG", "ffmpeg")
    ffprobe = os.environ.get("WAR_PROMO_FFPROBE", "ffprobe")
    measured = probe_media(ffprobe, source,
                           audit_directory=work / "audit" / "original-film-probe")
    if measured.require_duration() < 430 or measured.video_streams[0].width != 1024:
        raise ValueError("Unexpected original Messina source media")
    by_id = {row["id"]: row for row in rows}
    segments = []
    for row in rows:
        duration = float(row["duration_seconds"])
        if not math.isfinite(duration) or duration < row["speech_duration_seconds"]:
            raise ValueError(f"Invalid R7 duration for {row['id']}")
        if row.get("visual_kind") != "card" or len(row["visual_lines"]) != 3:
            raise ValueError(f"{row['id']}: expected original-footage paired calculation")
        segments.append(SegmentDraft(
            segment_id=row["id"],
            visual_source=VisualSource(row["id"], VIDEO,
                                       Path("visuals") / (row["id"] + ".mp4"),
                                       "original-Messina-game-frame-and-native-math",
                                       requires_resolution=True),
            render_options=RenderOptions(2560, 1440, 30, duration,
                                         preset="veryfast", crf=21),
            subtitles={"zh-CN": row["zh"], "en": row["en"]},
            prepared_narration=_artifact(run, run_path, "audio." + row["id"]),
        ))

    def resolve_visual(source_ref, *, workdir):
        row = by_id[source_ref.source_id]
        return _paired_clip(row, source, Path(workdir) / source_ref.path,
                            ffmpeg=ffmpeg, work=Path(workdir))

    def visual_probe(path):
        measured = probe_media(ffprobe, path,
                               audit_directory=work / "audit" / "visual-probe" / path.stem)
        stream = measured.video_streams[0]
        return VisualProbeResult("video/mp4", stream.width, stream.height)

    def subtitle_renderer(segment, narration, *, workdir):
        del narration, workdir
        return subtitle_document(by_id[segment.segment_id])

    return PipelineInvocation(
        PipelineDraft(config, tuple(segments), Path("episode-01-r7c-messina-unmixed.mp4"),
                      "episode-01-r7c-messina-unmixed-v1", "video/mp4"),
        PipelineDependencies(ffmpeg, subtitle_renderer, run_command, visual_probe,
                             visual_resolver=resolve_visual), work)
