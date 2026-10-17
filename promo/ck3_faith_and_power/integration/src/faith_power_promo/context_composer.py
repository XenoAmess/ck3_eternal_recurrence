"""Bounded context-sample composer; it cannot award religious-action credit.

Extracted from the actually rendered episode-01 sample. Font input and media
executables are now explicit. The separate causal composer remains plan-only.
"""
import json
from dataclasses import replace
from pathlib import Path

from PIL import ImageFont
from xar_promo.layout import FontSpec, WrapPolicy, wrap_text
from xar_promo.media import probe_media
from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.process import run_command
from xar_promo.render import RenderOptions, ass_burn_in_filter, escape_filter_value, plan_render
from xar_promo.sources import VIDEO, VisualProbeResult, VisualSource
from xar_promo.subtitles import (
    AssCue, AssDocumentConfig, AssStyleConfig, SubtitleTrackConfig, render_ass_document,
)

from .composer import _artifact

ADAPTER = "ck3-faith-episode01-media-v1"
PRESET = "faith-episode01-opening-zh-v1"


def adapter_factory():
    return {"id": ADAPTER, "starts_game": False, "capture_mode": "existing-context-only"}


def preset_factory():
    return {"id": PRESET, "width": 2560, "height": 1440, "fps": 30}


def registry():
    from xar_promo.registry import ComponentRegistry
    return ComponentRegistry(adapters={ADAPTER: adapter_factory},
                             presets={PRESET: preset_factory}, discover_entry_points=False)


def subtitle_document(row, font_file, font_name):
    """Measure both languages against the exact caller-supplied font bytes."""
    tracks, cues = [], []
    for locale, size, margin, height, top in (
        ("zh", 49, 178, 60, 1120), ("en", 31, 65, 38, 1280),
    ):
        font = ImageFont.truetype(str(font_file), size=size)
        layout = wrap_text(row[locale], font=FontSpec(locale, font_name, size),
                           measure=lambda text, selected: font.getlength(text),
                           max_width=2270, max_lines=2, policy=WrapPolicy())
        if 1440 - margin - height * len(layout.lines) < top:
            raise ValueError("Subtitle leaves its reserved lower rectangle")
        style = AssStyleConfig(locale, font_name, size, primary_colour="&H00CFE5F0",
                               outline_colour="&H00131821", outline=2, shadow=1,
                               bold=True, margin_left=145, margin_right=145,
                               margin_vertical=margin)
        tracks.append(SubtitleTrackConfig(locale, "zh-CN" if locale == "zh" else "en",
                                         2 if locale == "zh" else 1, style))
        cues.append(AssCue(f"{row['id']}.{locale}", locale, 0,
                           row["duration_seconds"], "\n".join(layout.lines)))
    terminal = row["raw_terminal_status"]
    state = "源中断RED" if "ABORT" in terminal else "源已停录"
    cadence = "VFR转30fps派生" if row["source_is_vfr"] else "30fps原时钟派生"
    label = "上下文试拍 · 未采用 · " + state + " · " + cadence
    style = AssStyleConfig("source-label", font_name, 30, primary_colour="&H006AA5CB",
                           outline=2, alignment=8, margin_left=100,
                           margin_right=100, margin_vertical=32)
    tracks.append(SubtitleTrackConfig("source-label", "zh-CN", 3, style))
    cues.append(AssCue(f"{row['id']}.source", "source-label", 0,
                       row["duration_seconds"], label))
    return render_ass_document(
        AssDocumentConfig("Faith and Power: context sample", 2560, 1440,
                          row["duration_seconds"]), tracks, cues,
        available_font_names=[font_name],
    )


def font_render_planner(font_directory):
    """Use the public planner injection seam to give libass preserved fonts."""
    def planner(**kwargs):
        plan = plan_render(**kwargs)
        old = ass_burn_in_filter(kwargs["ass_path"])
        new = old + f":fontsdir='{escape_filter_value(font_directory)}'"
        commands = []
        for command in plan.commands:
            argv = list(command.spec.argv)
            position = argv.index("-filter_complex") + 1
            if argv[position].count(old) != 1:
                raise ValueError("Installed render planner's ASS filter ABI changed")
            argv[position] = argv[position].replace(old, new)
            commands.append(replace(command, spec=replace(command.spec, argv=tuple(argv))))
        return replace(plan, commands=tuple(commands))
    return planner


def compose(config, run, *, config_path, run_path, workdir, adapter_factory,
            preset_factory, validate_only):
    del config_path, validate_only
    if run is None or run_path is None:
        raise ValueError("Context sample requires a preserved native run")
    if adapter_factory()["id"] != config.adapter or preset_factory()["id"] != config.preset:
        raise ValueError("Context components mismatch")
    inputs = json.loads(_artifact(run, run_path, "episode01-context-inputs-v1").read_text("utf-8"))
    if (inputs.get("schema") != "ck3-faith-power-context-sample-inputs-v1"
            or inputs.get("scope") != "context-only-first-opening"
            or inputs.get("business_result_verified") is not False
            or inputs.get("human_1x_review_performed") is not False
            or inputs.get("no_gameplay_credit") is not True):
        raise ValueError("This renderer only accepts unadopted context samples")
    video = _artifact(run, run_path, inputs["video_artifact_id"])
    font = _artifact(run, run_path, inputs["font_artifact_id"])
    rows = inputs["cues"]
    if not rows or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Expected unique measured cue IDs")
    if not 30 <= sum(r["duration_seconds"] for r in rows) <= 60:
        raise ValueError("Context sample must be 30–60 authored seconds")
    segments, cursor = [], 0.0
    for row in rows:
        if not 0 < row["speech_duration_seconds"] <= row["duration_seconds"]:
            raise ValueError("Segment cannot be shorter than measured speech")
        subtitle_document(row, font, inputs["font_name"])
        segments.append(SegmentDraft(
            row["id"], VisualSource(row["id"], VIDEO, video, "ck3-existing-observer-capture",
                                    metadata={"claim_ids": row["claim_ids"],
                                              "shot_ids": row["shot_ids"],
                                              "business_result_verified": False}),
            RenderOptions(2560, 1440, 30, row["duration_seconds"], preset="veryfast", crf=21),
            {"zh-CN": row["zh"], "en": row["en"]},
            prepared_narration=_artifact(run, run_path, row["audio_artifact_id"]),
            start_seconds=cursor,
        ))
        cursor += row["duration_seconds"]
    by_id = {r["id"]: r for r in rows}
    sequence = 0

    def subtitles(segment, narration, *, workdir):
        del narration, workdir
        return subtitle_document(by_id[segment.segment_id], font, inputs["font_name"])

    def probe(path):
        nonlocal sequence
        sequence += 1
        result = probe_media(inputs["ffprobe"], path,
                             audit_directory=Path(workdir) / "audit/probe" / f"{sequence:03d}")
        stream = result.video_streams[0]
        return VisualProbeResult("video/mp4", stream.width, stream.height)

    return PipelineInvocation(
        PipelineDraft(config, tuple(segments), Path("episode01-context-sample.mp4"),
                      "episode01-context-sample", "video/mp4"),
        PipelineDependencies(inputs["ffmpeg"], subtitles, run_command, probe,
                             render_planner=font_render_planner(font.parent)),
        Path(workdir),
    )
