"""Rebuild Episode 1 R6 from preserved visuals and freshly voiced narration."""

from __future__ import annotations

import math
import os
from pathlib import Path
import shutil

from xar_promo.media import probe_media
from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.process import CommandSpec, run_command
from xar_promo.render import RenderOptions
from xar_promo.sources import VIDEO, VisualProbeResult, VisualSource

from .captions import subtitle_document
from .common import load
from .episode_one_math_sample import _artifact, _card_clip


NEW_CARDS = frozenset({"M03", "C02", "C03", "C04", "C05", "C09", "C11", "E1-F19", "E1-F23", "P01", "P02", "P03"})


def compose(config, run, *, config_path, run_path, workdir,
            adapter_factory, preset_factory, validate_only):
    del config_path, adapter_factory, preset_factory, validate_only
    if config.project_id not in ("ck3-war-ai-episode-01-r6-recut", "ck3-war-ai-episode-01-r61-recut",
                                 "ck3-war-ai-episode-01-r62-contextual"):
        raise ValueError("Wrong Episode 1 recut ProjectConfig")
    inputs = load(_artifact(run, run_path, "r6-production-inputs"))
    rows = inputs["cues"]
    expected = 32 if config.project_id.endswith("r6-recut") else 33
    if len(rows) != expected or len({row["id"] for row in rows}) != expected:
        raise ValueError(f"Recut needs {expected} unique edited cues")
    if inputs["provider"] != "edge" or inputs["human_signoff"] != "not-provided":
        raise ValueError("R6 needs unsigned EdgeTTS inputs")
    total = sum(row["duration_seconds"] for row in rows)
    if not 1200 <= total <= 2400:
        raise ValueError(f"R6 duration {total} outside 20–40 minutes")
    work = Path(workdir)
    ffmpeg = os.environ.get("WAR_PROMO_FFMPEG", "ffmpeg")
    ffprobe = os.environ.get("WAR_PROMO_FFPROBE", "ffprobe")
    by_id = {row["id"]: row for row in rows}
    segments = []
    for row in rows:
        duration = float(row["duration_seconds"])
        if not math.isfinite(duration) or duration < row["speech_duration_seconds"]:
            raise ValueError(f"Invalid narration duration for {row['id']}")
        segments.append(SegmentDraft(
            segment_id=row["id"],
            visual_source=VisualSource(row["id"], VIDEO,
                                       Path("visuals") / (row["id"] + ".mp4"),
                                       "R6-preserved-live-visual-or-new-source-bound-card",
                                       requires_resolution=True),
            render_options=RenderOptions(2560, 1440, 30, duration,
                                         preset="veryfast", crf=21),
            subtitles={"zh-CN": row["zh"], "en": row["en"]},
            prepared_narration=_artifact(run, run_path, "audio." + row["id"]),
        ))

    def resolve_visual(source, *, workdir):
        row = by_id[source.source_id]
        target = Path(workdir) / source.path
        if row["id"] in NEW_CARDS or row.get("redraw_card"):
            row["footer"] = "原版 1.19.0.6 · 数字与范围见 docs/ck3-native-ai/ 战斗专题"
            return _card_clip(row, target, ffmpeg, Path(workdir))
        original = _artifact(run, run_path, "source-visual." + row["id"])
        info = probe_media(ffprobe, original,
                           audit_directory=work / "audit" / "source-probe" / row["id"])
        if info.require_duration() >= row["duration_seconds"] - 0.05:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)
            return target
        # The R6 revoice may be longer than a frozen source visual. Hold its
        # final frame instead of silently letting the picture disappear.
        target.parent.mkdir(parents=True, exist_ok=True)
        argv = [ffmpeg, "-nostdin", "-n", "-hide_banner", "-loglevel", "error",
                "-i", str(original), "-vf", "tpad=stop_mode=clone:stop_duration=120",
                "-t", str(row["duration_seconds"]), "-an", "-r", "30",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21", str(target)]
        run_command(CommandSpec.create(argv, label="R6-extend-visual-" + row["id"],
                                       partial_artifacts=[target]),
                    audit_directory=work / "audit" / "extend-visual" / row["id"])
        return target

    def visual_probe(path):
        measured = probe_media(ffprobe, path,
                               audit_directory=work / "audit" / "visual-probe" / path.stem)
        stream = measured.video_streams[0]
        return VisualProbeResult("video/mp4", stream.width, stream.height)

    def subtitle_renderer(segment, narration, *, workdir):
        del narration, workdir
        return subtitle_document(by_id[segment.segment_id])

    return PipelineInvocation(
        PipelineDraft(config, tuple(segments), Path("episode-01-r6-unmixed.mp4"),
                      "episode-01-r6-unmixed-v1", "video/mp4"),
        PipelineDependencies(ffmpeg, subtitle_renderer, run_command, visual_probe,
                             visual_resolver=resolve_visual), work)
