"""Compose measured narration with preserved capture clips or teaching graphics."""
from dataclasses import replace
from pathlib import Path
import os

from xar_promo.media import probe_media
from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.process import run_command
from xar_promo.render import RenderOptions, plan_render, seconds
from xar_promo.sources import VIDEO, VisualProbeResult, VisualSource
from .common import binding, load
from .captions import subtitle_document
from .visuals import render_visual


def artifact(run, run_path, identifier):
    if run is None or run_path is None:
        raise ValueError("Composition requires preserved production inputs in a native run")
    matches = [row for row in run.artifacts if row.artifact_id == identifier]
    if len(matches) != 1:
        raise ValueError(f"Expected one preserved artifact: {identifier}")
    return (run_path.parent / matches[0].path).resolve()


def plan_capture_render(**kwargs):
    """Keep the importer's already sampled 30fps timeline without extra padding.

    VFR sources were sampled at original PTS/1x by the capture importer; the
    delivery rate does not describe source sampling quality. Keep the official
    subtitle/audio/output/audit contracts. If the upstream graph no
    longer has the inspected normalization seam, fail rather than guess.
    """
    plan = plan_render(**kwargs)
    options = kwargs["options"]
    removed = (f",fps={options.fps},tpad=stop_mode=clone:"
               f"stop_duration={seconds(options.duration_seconds)}")
    commands = []
    for command in plan.commands:
        argv = list(command.spec.argv)
        index = argv.index("-filter_complex") + 1
        if argv[index].count(removed) != 1:
            raise ValueError("Upstream render graph changed; continuous capture seam needs review")
        argv[index] = argv[index].replace(removed, "", 1)
        argv[-1:-1] = ["-fps_mode", "passthrough"]
        commands.append(replace(command, spec=replace(command.spec, argv=tuple(argv))))
    return replace(plan, commands=tuple(commands))


def capture_visual(row, run, run_path):
    """Resolve only preserved artifacts, never a mutable original bundle path."""
    capture = row["capture_clip"]
    path = artifact(run, run_path, capture["media_artifact_id"])
    receipt = load(artifact(run, run_path, capture["receipt_artifact_id"]))
    actual = binding(path)
    if any(actual[key] != receipt["media"][key] for key in ("bytes", "sha256")):
        raise ValueError(f"Preserved capture bytes differ from receipt: {row['id']}")
    if (receipt["cue_id"] != row["id"] or receipt["claim_ids"] != capture["claim_ids"]
            or receipt["evidence_role"] != capture["evidence_role"]):
        raise ValueError(f"Capture mapping differs from its receipt: {row['id']}")
    if not set(capture["claim_ids"]).issubset(row["claim_ids"]):
        raise ValueError(f"Capture claims are not attached to this cue: {row['id']}")
    if receipt.get("schema") not in {"ck3-war-ai.prepared-capture-clip.v2", "ck3-war-ai.labeled-capture-clip.v1"}:
        raise ValueError("Unknown capture clip receipt schema")
    if receipt.get("schema") == "ck3-war-ai.labeled-capture-clip.v1":
        if (receipt.get("case_id") not in {"CASE-W", "CASE-C"}
                or not receipt.get("label_text") or receipt.get("native_ai_causality_verified") is not False
                or receipt.get("human_1x_review_performed") is not False):
            raise ValueError("V3 context label or evidence limit is missing")
    if receipt.get("schema") in {"ck3-war-ai.prepared-capture-clip.v2", "ck3-war-ai.labeled-capture-clip.v1"}:
        sampling = receipt.get("delivery_sampling", {})
        if (receipt.get("fps") != 30 or sampling.get("output_fps") != 30
                or sampling.get("playback_speed") != 1
                or any(sampling.get(key) is not False for key in ("interpolation", "looping", "tail_padding"))):
            raise ValueError("Prepared VFR delivery must retain its 1x/no-interpolation/no-padding contract")
    duration = receipt["selection"]["expected_frame_count"] / 30
    if abs(duration - row["duration_seconds"]) > 0.000001 or duration < row["speech_duration_seconds"]:
        raise ValueError(f"Capture does not cover this cue's exact measured duration: {row['id']}")
    for identifier in [capture["raw_artifact_id"], *capture["control_artifact_ids"]]:
        artifact(run, run_path, identifier)
    return VisualSource(row["id"], VIDEO, path, "ck3-capture-continuous-clip",
        metadata={"evidence_role":capture["evidence_role"], "claim_ids":capture["claim_ids"],
                  "receipt_artifact_id":capture["receipt_artifact_id"],
                  "source_sampling_quality":receipt.get("source_sampling_quality"),
                  "native_ai_causality_verified":False})


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
    if not rows or inputs["media_scope"] not in {"teaching-graphics-radio-cut", "mixed-footage"}:
        raise ValueError("Expected a nonempty measured teaching or mixed-footage cut")
    capture_count = sum("capture_clip" in row for row in rows)
    if (inputs["media_scope"] == "mixed-footage") != (capture_count > 0):
        raise ValueError("media_scope must match the presence of preserved capture clips")
    if any(row["speech_duration_seconds"] <= 0 or row["duration_seconds"] < row["speech_duration_seconds"] for row in rows):
        raise ValueError("Invalid measured speech/segment duration")
    v3 = all(row["id"] == f"V3-{index:02d}" and row["shot_id"] == f"S3-{index:02d}"
             for index, row in enumerate(rows, 1)) and len(rows) == 45
    if any(str(row["id"]).startswith("V3-") for row in rows) and not v3:
        raise ValueError("V3 composition requires all 45 cues in exact order")
    v3_ledger = None
    v3_assets = None
    if v3:
        config = inputs.get("v3_visuals", {})
        if set(config) != {"ledger_artifact_id", "asset_manifest_artifact_id", "frame_artifact_ids"}:
            raise ValueError("V3 preserved visual inputs are incomplete")
        v3_ledger = artifact(run, run_path, config["ledger_artifact_id"])
        if binding(v3_ledger)["sha256"] != inputs["v3_evidence_ledger"]["sha256"]:
            raise ValueError("Preserved V3 evidence ledger differs from narration binding")
        manifest = load(artifact(run, run_path, config["asset_manifest_artifact_id"]))
        if manifest.get("schema") != "ck3-war-ai.v3-context-frames.v1" or set(manifest["assets"]) != {"CASE-R", "CASE-W"}:
            raise ValueError("V3 original frame manifest is incomplete")
        v3_assets = {}
        for case_id, asset in manifest["assets"].items():
            preserved = artifact(run, run_path, config["frame_artifact_ids"][case_id])
            if asset.get("case_id") != case_id or asset.get("evidence_role") != "context-only-original-frame":
                raise ValueError("V3 source frame has wrong case or role")
            actual = binding(preserved)
            if any(actual[key] != asset[key] for key in ("bytes", "sha256")):
                raise ValueError("Preserved V3 frame differs from source manifest")
            v3_assets[case_id] = {**asset, "path": preserved.as_posix()}
    ffmpeg = os.environ.get("WAR_PROMO_FFMPEG", "ffmpeg")
    ffprobe = os.environ.get("WAR_PROMO_FFPROBE", "ffprobe")
    segments = []
    capture_paths = set()
    by_id = {row["id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("Duplicate narration cue")
    for row in rows:
        if "capture_clip" in row:
            visual = capture_visual(row, run, run_path)
            capture_paths.add(visual.path.resolve())
        else:
            visual = VisualSource(row["id"], VIDEO, Path("visuals") / f"{row['id']}.mp4",
                                  "project-teaching-animation", requires_resolution=True)
        segments.append(SegmentDraft(
            segment_id=row["id"],
            visual_source=visual,
            render_options=RenderOptions(2560, 1440, 30, row["duration_seconds"], preset="veryfast", crf=21),
            subtitles={"zh-CN": row["zh"], "en": row["en"]},
            prepared_narration=artifact(run, run_path, row["audio_artifact_id"]),
        ))

    def resolve_visual(source, *, workdir):
        target = workdir / source.path
        return render_visual(by_id[source.source_id], target, ffmpeg, workdir,
                             v3_ledger=v3_ledger, v3_assets=v3_assets)

    def visual_probe(path):
        result = probe_media(ffprobe, path, audit_directory=Path(workdir) / "audit" / "probe" / path.stem)
        stream = result.video_streams[0]
        return VisualProbeResult("video/mp4", stream.width, stream.height)

    def subtitle_renderer(segment, narration, *, workdir):
        del narration, workdir
        return subtitle_document(by_id[segment.segment_id])

    def render_planner(**kwargs):
        planner = plan_capture_render if Path(kwargs["video_input"]).resolve() in capture_paths else plan_render
        return planner(**kwargs)

    return PipelineInvocation(
        PipelineDraft(config, tuple(segments),
                      Path("war-ai-full-film.mp4" if inputs.get("full_film") else "war-ai-radio-cut.mp4"),
                      "war-ai-full-film-v1" if inputs.get("full_film") else "war-ai-radio-cut-v1", "video/mp4"),
        PipelineDependencies(ffmpeg, subtitle_renderer, run_command, visual_probe,
                             visual_resolver=resolve_visual, render_planner=render_planner), Path(workdir))
