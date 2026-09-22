"""Native xar-promo composition of measured narration and teaching graphics."""
from pathlib import Path
import os

from xar_promo.media import probe_media
from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.process import run_command
from xar_promo.render import RenderOptions
from xar_promo.sources import VIDEO, VisualProbeResult, VisualSource
from xar_promo.subtitles import AssCue, AssDocumentConfig, AssStyleConfig, SubtitleTrackConfig, render_ass_document

from .common import load, lines
from .visuals import render_visual


def artifact(run, run_path, identifier):
    if run is None or run_path is None:
        raise ValueError("Composition requires preserved production inputs in a native run")
    matches = [row for row in run.artifacts if row.artifact_id == identifier]
    if len(matches) != 1:
        raise ValueError(f"Expected one preserved artifact: {identifier}")
    return (run_path.parent / matches[0].path).resolve()


def subtitle_document(row):
    duration = row["duration_seconds"]
    tracks = [
        SubtitleTrackConfig("zh", "zh-CN", 2, AssStyleConfig(
            name="Chinese", font_name="Microsoft YaHei", font_size=49, bold=True,
            margin_left=145, margin_right=145, margin_vertical=178, outline=2.5)),
        SubtitleTrackConfig("en", "en", 1, AssStyleConfig(
            name="English", font_name="Microsoft YaHei", font_size=31, bold=False,
            primary_colour="&H00BBC4C9", margin_left=145, margin_right=145,
            margin_vertical=65, outline=2)),
    ]
    cues = []
    for language, size in [("zh", 49), ("en", 31)]:
        wrapped = lines(row[language], size, 2200, language == "zh")
        groups = [wrapped[i:i + 2] for i in range(0, len(wrapped), 2)]
        weights = [sum(len(value) for value in group) for group in groups]
        total = sum(weights)
        cursor = 0.12
        available = row["speech_duration_seconds"] - cursor
        for index, (group, weight) in enumerate(zip(groups, weights)):
            end = min(duration, cursor + available * weight / total)
            cues.append(AssCue(f"{language}-{index}", language, cursor, end, "\n".join(group)))
            cursor = end
    return render_ass_document(
        AssDocumentConfig(row["shot_title"], 2560, 1440, duration_seconds=duration),
        tracks, cues, available_font_names={"Microsoft YaHei"})


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
        PipelineDraft(config, tuple(segments), Path("war-ai-radio-cut.mp4"), "war-ai-radio-cut-v1", "video/mp4"),
        PipelineDependencies(ffmpeg, subtitle_renderer, run_command, visual_probe,
                             visual_resolver=resolve_visual), Path(workdir))
