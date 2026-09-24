"""Full Episode 1 EdgeTTS observation composer with bounded CK3 gameplay.

Gameplay is an independent same-checkpoint replay. It is never used as a
frame-exact visual proof for a numeric receipt from the diverged original run.
"""

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

from .captions import subtitle_document
from .common import font, lines, load
from .visuals import BG, PANEL, INK, MUTED, GOLD, RED, GREEN, make_canvas, box, heraldic_mark


def artifact(run, run_path: Path, identifier: str) -> Path:
    hits = [item for item in run.artifacts if item.artifact_id == identifier]
    if len(hits) != 1:
        raise ValueError(f"expected one preserved artifact: {identifier}")
    return (run_path.parent / hits[0].path).resolve()


def put_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str,
             size: int, *, color=INK, bold=False, width=None) -> None:
    rows = lines(value, size, width, bold) if width else [value]
    for index, line in enumerate(rows):
        draw.text((xy[0], xy[1] + index * size * 1.35), line,
                  font=font(size, bold), fill=color)


def card_image(row: dict, path: Path, active: int) -> None:
    image = make_canvas()
    draw = ImageDraw.Draw(image)
    heraldic_mark(draw, (137, 121), 68, GOLD)
    put_text(draw, (206, 74), "十字军之王 III · 一场仗是怎么算出来的", 38,
             color=GOLD, bold=True)
    put_text(draw, (153, 184), row["visual_title"], 77, bold=True, width=2240)
    put_text(draw, (158, 309), "原版机制 · 按游戏实际结算顺序阅读", 39,
             color=MUTED)
    colors = [GOLD, RED, GREEN]
    for index, point in enumerate(row["visual_points"]):
        x = 143 + index * 765
        chosen = index == active
        box(draw, (x, 451, x + 711, 956), PANEL if chosen else "#29211A",
            GOLD if chosen else "#66513A")
        draw.rectangle((x + 31, 489, x + 46, 890),
                       fill=colors[index] if chosen else "#66513A")
        put_text(draw, (x + 79, 505), f"0{index + 1}", 46,
                 color=GOLD if chosen else MUTED, bold=True)
        put_text(draw, (x + 79, 604), point, 52 if len(point) < 17 else 43,
                 color=INK if chosen else MUTED, bold=chosen, width=568)
    draw.line((145, 1028, 2414, 1028), fill="#66513A", width=2)
    put_text(draw, (158, 1065), "证据范围：" + row["evidence"], 30,
             color=GOLD, width=2200)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        image.save(stream, format="PNG")


def gameplay_overlay(path: Path) -> None:
    image = Image.new("RGBA", (2560, 1440), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 319, 1439), fill=(30, 21, 16, 255))
    draw.rectangle((2240, 0, 2559, 1439), fill=(30, 21, 16, 255))
    draw.line((315, 0, 315, 1439), fill=GOLD, width=4)
    draw.line((2244, 0, 2244, 1439), fill=GOLD, width=4)
    heraldic_mark(draw, (158, 154), 101, GOLD)
    put_text(draw, (52, 270), "原版实机", 46, color=GOLD, bold=True)
    put_text(draw, (52, 347), "墨西拿战斗", 37, color=INK)
    put_text(draw, (52, 453), "同存档", 37, color=INK)
    put_text(draw, (52, 512), "独立重放", 37, color=INK)
    put_text(draw, (2264, 256), "CK3", 47, color=GOLD, bold=True)
    put_text(draw, (2264, 322), "1.19.0.6", 34, color=INK)
    put_text(draw, (2264, 480), "第 6 天后", 32, color=MUTED)
    put_text(draw, (2264, 533), "与研究回执", 31, color=MUTED)
    put_text(draw, (2264, 585), "数值分叉", 31, color=MUTED)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        image.save(stream, format="PNG")


def card_clip(row: dict, duration: float, target: Path, ffmpeg: str,
              work: Path) -> Path:
    if duration <= 1:
        raise ValueError(f"card duration too short: {row['id']}")
    folder = work / "drawings" / row["id"]
    folder.mkdir(parents=True, exist_ok=False)
    images = [folder / f"state-{index}.png" for index in range(3)]
    for index, path in enumerate(images):
        card_image(row, path, index)
    fade = min(.45, duration / 12)
    length = (duration + 2 * fade) / 3
    first = length - fade
    second = 2 * first
    filters = [
        f"[{i}:v]trim=duration={length:.6f},settb=AVTB,setpts=PTS-STARTPTS,format=yuv420p[s{i}]"
        for i in range(3)
    ]
    filters.extend([
        f"[s0][s1]xfade=transition=fade:duration={fade:.6f}:offset={first:.6f}[ab]",
        f"[ab][s2]xfade=transition=fade:duration={fade:.6f}:offset={second:.6f},format=yuv420p[v]",
    ])
    target.parent.mkdir(parents=True, exist_ok=True)
    argv = [ffmpeg, "-nostdin", "-n", "-hide_banner", "-loglevel", "warning"]
    for image in images:
        argv.extend(["-loop", "1", "-framerate", "30", "-i", str(image)])
    argv.extend([
        "-filter_complex_threads", "1", "-filter_complex", ";".join(filters),
        "-map", "[v]", "-an", "-t", f"{duration:.6f}", "-r", "30",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
        "-threads", "4", str(target),
    ])
    run_command(CommandSpec.create(argv, label=f"observation-card-{row['id']}",
                                   partial_artifacts=[target]),
                audit_directory=work / "audit" / "cards" / row["id"])
    return target


def gameplay_clip(source: Path, overlay: Path, row: dict, duration: float,
                  target: Path, ffmpeg: str, work: Path) -> Path:
    start = float(row["gameplay_start_seconds"])
    target.parent.mkdir(parents=True, exist_ok=True)
    # Preserve the native 4:3 gameplay content in full; the side bars carry the
    # provenance label instead of cropping the battle banner or UI.
    filtergraph = (
        "[0:v]fps=30,scale=1920:1440:flags=lanczos,"
        "pad=2560:1440:320:0:color=0x1E1510,format=yuv420p[base];"
        "[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    )
    argv = [
        ffmpeg, "-nostdin", "-n", "-hide_banner", "-loglevel", "warning",
        "-ss", f"{start:.6f}", "-i", str(source), "-loop", "1", "-i", str(overlay),
        "-filter_complex", filtergraph, "-map", "[v]", "-an",
        "-t", f"{duration:.6f}", "-r", "30", "-c:v", "libx264",
        "-preset", "veryfast", "-crf", "21", "-threads", "4", str(target),
    ]
    run_command(CommandSpec.create(argv, label=f"observation-gameplay-{row['id']}",
                                   partial_artifacts=[target]),
                audit_directory=work / "audit" / "gameplay" / row["id"])
    return target


def resolve_visual_file(source: Path, overlay: Path, row: dict, target: Path,
                        ffmpeg: str, work: Path) -> Path:
    duration = float(row["duration_seconds"])
    if not math.isfinite(duration) or duration <= float(row["speech_duration_seconds"]):
        raise ValueError(f"bad cue duration: {row['id']}")
    if row["visual_kind"] == "card":
        result = card_clip(row, duration, target, ffmpeg, work)
    else:
        gameplay_seconds = min(float(row["gameplay_seconds"]), duration - 5)
        if gameplay_seconds <= 0:
            raise ValueError(f"no gameplay interval: {row['id']}")
        part_dir = work / "visual-parts" / row["id"]
        part_dir.mkdir(parents=True, exist_ok=False)
        live = gameplay_clip(source, overlay, row, gameplay_seconds,
                             part_dir / "gameplay.mp4", ffmpeg, work)
        card = card_clip(row, duration - gameplay_seconds,
                         part_dir / "card.mp4", ffmpeg, work)
        concat = part_dir / "concat-inputs.txt"
        concat.write_text(
            f"file '{live.as_posix()}'\nfile '{card.as_posix()}'\n",
            encoding="utf-8", newline="\n")
        target.parent.mkdir(parents=True, exist_ok=True)
        run_command(CommandSpec.create([
            ffmpeg, "-nostdin", "-n", "-hide_banner", "-loglevel", "warning",
            "-f", "concat", "-safe", "0", "-i", str(concat),
            "-c", "copy", "-movflags", "+faststart", str(target),
        ], label=f"observation-hybrid-{row['id']}", partial_artifacts=[target]),
            audit_directory=work / "audit" / "hybrid" / row["id"])
        result = target
    (work / "drawings" / row["id"] / "visual-plan.json").write_text(
        json.dumps({
            "cue_id": row["id"], "kind": row["visual_kind"],
            "duration_seconds": duration, "evidence": row["evidence"],
            "gameplay_source": str(source) if row["visual_kind"] == "gameplay" else None,
            "gameplay_start_seconds": row.get("gameplay_start_seconds"),
            "gameplay_seconds": row.get("gameplay_seconds"),
            "camera_scope": "independent same-checkpoint replay; diverges from original receipts after day 6",
            "human_signoff": "not-provided",
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def compose(config, run, *, config_path, run_path, workdir,
            adapter_factory, preset_factory, validate_only):
    del config_path, validate_only
    adapter, preset = adapter_factory(), preset_factory()
    if config.adapter != adapter["id"] or config.preset != preset["id"]:
        raise ValueError("observation film components mismatch")
    if config.project_id != "ck3-native-war-ai-episode-01-full":
        raise ValueError("wrong observation-film ProjectConfig")
    inputs = load(artifact(run, run_path, "observation-production-inputs"))
    rows = inputs["cues"]
    if len(rows) != 25 or [row["id"] for row in rows] != [
        f"E1-F{index:02d}" for index in range(1, 26)
    ]:
        raise ValueError("observation film requires 25 ordered cues")
    if inputs["provider"] != "edge" or inputs["human_signoff"] != "not-provided":
        raise ValueError("expected unsigned EdgeTTS narration")
    if not 1200 <= sum(row["duration_seconds"] for row in rows) <= 2400:
        raise ValueError("observation film falls outside the authorized 20–40 minutes")
    gameplay = artifact(run, run_path, "messina-full-battle-clean-footage")
    artifact(run, run_path, "messina-camera-visibility-audit")
    work = Path(workdir)
    ffmpeg = os.environ.get("WAR_PROMO_FFMPEG", "ffmpeg")
    ffprobe = os.environ.get("WAR_PROMO_FFPROBE", "ffprobe")
    overlay = artifact(run, run_path, "gameplay-provenance-overlay")
    by_id = {row["id"]: row for row in rows}
    segments = []
    for row in rows:
        segments.append(SegmentDraft(
            segment_id=row["id"],
            visual_source=VisualSource(row["id"], VIDEO,
                                       Path("visuals") / f"{row['id']}.mp4",
                                       "labelled-ck3-gameplay-plus-explainer"
                                       if row["visual_kind"] == "gameplay"
                                       else "sourced-algorithm-card",
                                       requires_resolution=True),
            render_options=RenderOptions(2560, 1440, 30,
                                         row["duration_seconds"],
                                         preset="veryfast", crf=21),
            subtitles={"zh-CN": row["zh"], "en": row["en"]},
            prepared_narration=artifact(run, run_path, row["audio_artifact_id"]),
        ))

    def resolve_visual(source, *, workdir):
        return resolve_visual_file(gameplay, overlay,
                                   by_id[source.source_id],
                                   Path(workdir) / source.path,
                                   ffmpeg, Path(workdir))

    def visual_probe(path):
        result = probe_media(ffprobe, path,
                             audit_directory=work / "audit" / "probe" / path.stem)
        stream = result.video_streams[0]
        return VisualProbeResult("video/mp4", stream.width, stream.height)

    def subtitle_renderer(segment, narration, *, workdir):
        del narration, workdir
        return subtitle_document(by_id[segment.segment_id])

    return PipelineInvocation(
        PipelineDraft(config, tuple(segments),
                      Path("episode-01-observation-unmixed.mp4"),
                      "episode-01-observation-unmixed-v1", "video/mp4"),
        PipelineDependencies(ffmpeg, subtitle_renderer, run_command,
                             visual_probe, visual_resolver=resolve_visual), work)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--make-overlay", type=Path, required=True)
    arguments = parser.parse_args()
    gameplay_overlay(arguments.make_overlay)
