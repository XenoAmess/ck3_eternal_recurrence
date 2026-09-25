"""Render the R7E Messina visual cut against the user's optimized IndexTTS voice."""

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
from .episode_one_math_sample import _artifact
from .episode_one_r7e_same_battle import _paired_clip


def compose(config, run, *, config_path, run_path, workdir,
            adapter_factory, preset_factory, validate_only):
    del config_path, adapter_factory, preset_factory, validate_only
    if config.project_id != "ck3-war-ai-episode-01-r7f-index-formal":
        raise ValueError("Wrong ProjectConfig for formal IndexTTS Messina film")
    inputs = load(_artifact(run, run_path, "r7f-production-inputs"))
    rows = inputs["cues"]
    if len(rows) != 23 or len({row["id"] for row in rows}) != 23:
        raise ValueError("Expected 23 unique frozen Messina cues")
    profile = inputs["index_voice"]["profile"]
    if (inputs["provider"] != "index" or inputs["human_signoff"] != "not-provided" or
        profile["reference_device"] != "cpu" or profile["reuse_spk_cond_for_emo"] is not False):
        raise ValueError("Expected unsigned IndexTTS speech with PR #795 CPU reference encoding")
    total = sum(row["duration_seconds"] for row in rows)
    if not 1200 <= total <= 2400:
        raise ValueError(f"Episode length {total} outside the 20–40 minute target")
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
            raise ValueError(f"Invalid IndexTTS duration for {row['id']}")
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
        probe = probe_media(ffprobe, path,
                            audit_directory=work / "audit" / "visual-probe" / path.stem)
        stream = probe.video_streams[0]
        return VisualProbeResult("video/mp4", stream.width, stream.height)

    def subtitle_renderer(segment, narration, *, workdir):
        del narration, workdir
        return subtitle_document(by_id[segment.segment_id])

    return PipelineInvocation(
        PipelineDraft(config, tuple(segments), Path("episode-01-r7f-index-unmixed.mp4"),
                      "episode-01-r7f-index-unmixed-v1", "video/mp4"),
        PipelineDependencies(ffmpeg, subtitle_renderer, run_command, visual_probe,
                             visual_resolver=resolve_visual), work)
