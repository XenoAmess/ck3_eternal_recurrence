"""Native xar-promo composition of measured narration and teaching graphics."""
from pathlib import Path
import os

from xar_promo.media import probe_media
from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.process import run_command
from xar_promo.render import RenderOptions
from xar_promo.sources import VIDEO, VisualProbeResult, VisualSource
from .common import load
from .captions import subtitle_document
from .visuals import render_visual


def artifact(run, run_path, identifier):
    if run is None or run_path is None:
        raise ValueError("Composition requires preserved production inputs in a native run")
    matches = [row for row in run.artifacts if row.artifact_id == identifier]
    if len(matches) != 1:
        raise ValueError(f"Expected one preserved artifact: {identifier}")
    return (run_path.parent / matches[0].path).resolve()


def compose(config, run, *, config_path, run_path, workdir, adapter_factory,
            preset_factory, validate_only):
    del config_path, validate_only
    adapter, preset = adapter_factory(), preset_factory()
    if adapter["id"] != config.adapter or preset["id"] != config.preset:
        raise ValueError("Project components do not match the selected film")
    if config.project_id != "ck3-native-war-ai":
        raise ValueError("This composer belongs to the CK3 war AI documentary")
    inputs = load(artifact(run, run_path, "production-inputs-v1"))
    rows = inputs["cues"]
    if not rows or inputs["media_scope"] != "teaching-graphics-radio-cut":
        raise ValueError("Expected a nonempty measured teaching cut")
    if any(row["speech_duration_seconds"] <= 0 or row["duration_seconds"] < row["speech_duration_seconds"] for row in rows):
        raise ValueError("Invalid measured speech/segment duration")
    ffmpeg = os.environ.get("WAR_PROMO_FFMPEG", "ffmpeg")
    ffprobe = os.environ.get("WAR_PROMO_FFPROBE", "ffprobe")
    segments = []
    by_id = {row["id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("Duplicate narration cue")
    for row in rows:
        segments.append(SegmentDraft(
            segment_id=row["id"],
            visual_source=VisualSource(row["id"], VIDEO, Path("visuals") / f"{row['id']}.mp4",
                                       "project-teaching-animation", requires_resolution=True),
            render_options=RenderOptions(2560, 1440, 30, row["duration_seconds"], preset="veryfast", crf=21),
            subtitles={"zh-CN": row["zh"], "en": row["en"]},
            prepared_narration=artifact(run, run_path, row["audio_artifact_id"]),
        ))

    def resolve_visual(source, *, workdir):
        target = workdir / source.path
        return render_visual(by_id[source.source_id], target, ffmpeg, workdir)

    def visual_probe(path):
        result = probe_media(ffprobe, path, audit_directory=Path(workdir) / "audit" / "probe" / path.stem)
        stream = result.video_streams[0]
        return VisualProbeResult("video/mp4", stream.width, stream.height)

    def subtitle_renderer(segment, narration, *, workdir):
        del narration, workdir
        return subtitle_document(by_id[segment.segment_id])

    return PipelineInvocation(
        PipelineDraft(config, tuple(segments),
                      Path("war-ai-full-film.mp4" if inputs.get("full_film") else "war-ai-radio-cut.mp4"),
                      "war-ai-full-film-v1" if inputs.get("full_film") else "war-ai-radio-cut-v1", "video/mp4"),
        PipelineDependencies(ffmpeg, subtitle_renderer, run_command, visual_probe,
                             visual_resolver=resolve_visual), Path(workdir))
