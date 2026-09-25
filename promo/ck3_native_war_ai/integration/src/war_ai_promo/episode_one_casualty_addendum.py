"""Build the Episode 1 casualty-chain correction as immutable card segments."""

from __future__ import annotations

import math
import os
from pathlib import Path

from xar_promo.media import probe_media
from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.process import run_command
from xar_promo.render import RenderOptions
from xar_promo.sources import VIDEO, VisualProbeResult, VisualSource

from .captions import subtitle_document
from .common import load
from .episode_one_math_sample import _artifact, _card_clip


def compose(config, run, *, config_path, run_path, workdir,
            adapter_factory, preset_factory, validate_only):
    del config_path, adapter_factory, preset_factory, validate_only
    if config.project_id not in ("ck3-war-ai-casualty-addendum", "ck3-war-ai-pursuit-detail"):
        raise ValueError("Wrong project for casualty addendum")
    inputs = load(_artifact(run, run_path, "casualty-production-inputs"))
    rows = inputs["cues"]
    if inputs["provider"] != "edge" or inputs["human_signoff"] != "not-provided":
        raise ValueError("Expected unsigned EdgeTTS narration")
    detail_only = config.project_id == "ck3-war-ai-pursuit-detail"
    expected = ["C12"] if detail_only else [f"C{index:02d}" for index in range(1, 12)]
    if [row["id"] for row in rows] != expected or any(row["visual_kind"] != "card" for row in rows):
        raise ValueError("Unexpected casualty addendum cue set")
    for row in rows:
        row["footer"] = "原版 1.19.0.6 · 数字来源：docs/ck3-native-ai/combat-casualty-chain-explainer.md"
        row["source_scope"] = "episode-01 casualty chain with explicit live/static provenance"
    duration = sum(row["duration_seconds"] for row in rows)
    if not (30 <= duration <= 240 if detail_only else 180 <= duration <= 900):
        raise ValueError("Casualty addendum duration outside expected range")

    work = Path(workdir)
    ffmpeg = os.environ.get("WAR_PROMO_FFMPEG", "ffmpeg")
    ffprobe = os.environ.get("WAR_PROMO_FFPROBE", "ffprobe")
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
                                       "source-bound-native-casualty-card", requires_resolution=True),
            render_options=RenderOptions(2560, 1440, 30, duration,
                                         preset="veryfast", crf=21),
            subtitles={"zh-CN": row["zh"], "en": row["en"]},
            prepared_narration=_artifact(run, run_path, row["audio_artifact_id"]),
        ))

    def resolve_visual(source, *, workdir):
        return _card_clip(by_id[source.source_id],
                          Path(workdir) / source.path, ffmpeg, Path(workdir))

    def visual_probe(path):
        measured = probe_media(ffprobe, path,
                               audit_directory=work / "audit" / "probe" / path.stem)
        stream = measured.video_streams[0]
        return VisualProbeResult("video/mp4", stream.width, stream.height)

    def subtitle_renderer(segment, narration, *, workdir):
        del narration, workdir
        return subtitle_document(by_id[segment.segment_id])

    return PipelineInvocation(
        PipelineDraft(config, tuple(segments), Path("episode-01-casualty-addendum-unmixed.mp4"),
                      "episode-01-casualty-addendum-unmixed-v1", "video/mp4"),
        PipelineDependencies(ffmpeg, subtitle_renderer, run_command, visual_probe,
                             visual_resolver=resolve_visual), work)
