"""Project composition for the approved Superhuman Qiang player trailer.

The public xar-promo CLI owns attempts, phases, retention, and process execution.
This module supplies the approved story, frozen media references, measured Chinese
subtitle layout, camera movement, and a mix of the one supplied music source.
"""
from __future__ import annotations

import hashlib
import json
import math
import mimetypes
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageFont

from xar_promo.layout import FontSpec, WrapPolicy, wrap_text
from xar_promo.model import ProjectConfig, RunManifest
from xar_promo.pipeline import (
    PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft,
)
from xar_promo.process import CommandSpec, run_command
from xar_promo.project import artifact_path
from xar_promo.render import (
    GeneratedTextFile, PlannedCommand, RenderOptions, RenderPlan,
    ass_burn_in_filter, concat_manifest, execute_render_plan, seconds,
)
from xar_promo.sources import STILL, VisualProbeResult, VisualSource
from xar_promo.storyboard import TimelineSpacing, plan_storyboard


HEAD_SECONDS = (1.4, 0.9, 0.8, 0.7, 1.0, 0.9, 0.8, 0.9, 0.75, 0.9)
TAIL_SECONDS = (2.0, 2.2, 2.4, 2.4, 4.0, 3.4, 2.6, 2.8, 2.1, 6.0)
EXPECTED_VOICE = "zh-CN-XiaoxiaoNeural"
INPUT_ARTIFACT_ID = "render.inputs"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def checked_file(row: dict[str, Any], label: str) -> Path:
    path = Path(row["path"]).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"Missing {label}: {path}")
    if digest(path) != row["sha256"].lower():
        raise ValueError(f"SHA-256 changed for {label}: {path}")
    return path


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def ass_time(value: float) -> str:
    centiseconds = round(value * 100)
    hour, rest = divmod(centiseconds, 360000)
    minute, rest = divmod(rest, 6000)
    second, hundredth = divmod(rest, 100)
    return f"{hour}:{minute:02}:{second:02}.{hundredth:02}"


def srt_time(value: float) -> str:
    milliseconds = round(value * 1000)
    hour, rest = divmod(milliseconds, 3600000)
    minute, rest = divmod(rest, 60000)
    second, fraction = divmod(rest, 1000)
    return f"{hour:02}:{minute:02}:{second:02},{fraction:03}"


def ass_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def subtitle_header(family: str, font_size: int) -> str:
    return (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n"
        "WrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Narration,{family},{font_size},&H00F5F4F1,&H00F5F4F1,"
        "&H00120E0C,&H9A120E0C,0,0,0,0,100,100,0,0,1,3,0,2,100,100,60,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, "
        "MarginV, Effect, Text\n"
    )


def subtitle_events(scene: dict[str, Any], lead: float, duration: float,
                    font_path: Path, family: str, font_size: int) -> list[dict[str, Any]]:
    """One unchanged paragraph for the whole scene, with measured line breaks."""
    font = ImageFont.truetype(str(font_path), font_size)
    specification = FontSpec("chinese-subtitle", family, font_size)
    boundaries = [json.loads(line) for line in Path(scene["boundaries_path"]).read_text(
        encoding="utf-8").splitlines() if line.strip()]
    sentences = [row for row in boundaries if row["type"] == "SentenceBoundary"]
    if not sentences:
        raise ValueError(f"No sentence boundaries for {scene['scene_id']}")
    text = scene["narration"]
    lines = [text]
    if font.getlength(text) > 1460:
        candidates = []
        for split_at in range(1, len(text)):
            left, right = text[:split_at], text[split_at:]
            left_width, right_width = font.getlength(left), font.getlength(right)
            if max(left_width, right_width) > 1460:
                continue
            # Prefer a real clause boundary and a balanced two-line paragraph.
            # Opening/closing quotes and doubled dashes stay with their phrase.
            if right[0] in "，。！？；：、”》）" or left[-1] in "“《（":
                continue
            if left[-1] == "—" and right[0] == "—":
                continue
            punctuation_penalty = 0 if left[-1] in "。！？；，：、" else 1
            candidates.append((punctuation_penalty, abs(left_width-right_width), left, right))
        if not candidates:
            raise ValueError(f"Full paragraph cannot fit two readable lines for {scene['scene_id']}")
        _, _, left, right = min(candidates, key=lambda item: (item[0], item[1]))
        lines = [left, right]
    layout = wrap_text(
        "\n".join(lines), font=specification,
        measure=lambda value, spec: font.getlength(value), max_width=1460,
        max_lines=2, policy=WrapPolicy(prefer_break_after=frozenset("，、：；")),
    )
    if "".join(layout.lines) != text:
        raise ValueError("Paragraph wrapping changed approved narration characters")
    widths = [font.getlength(line) for line in layout.lines]
    ascent, descent = font.getmetrics()
    line_height = ascent + descent
    top = 1020 - len(layout.lines) * line_height
    bboxes = []
    for index, (line, width) in enumerate(zip(layout.lines, widths)):
        left = 960 - width / 2
        glyph = font.getbbox(line, anchor="lt")
        box = [left + glyph[0]-3, top+index*line_height+glyph[1]-3,
               left+glyph[2]+3, top+index*line_height+glyph[3]+3]
        if box[0] < 230 or box[1] < 880 or box[2] > 1690 or box[3] > 1020:
            raise ValueError(f"Paragraph glyph box escaped safe area: {box}")
        bboxes.append(box)
    fade_out = 0.65 if scene["scene_id"] == "SQP-10" else 0.20
    end = duration - fade_out
    if end <= lead + scene["duration_seconds"]:
        raise ValueError("Full paragraph must remain through the entire narration")
    return [{
        "scene_id": scene["scene_id"], "cue_count": 1, "narration_text": text,
        "start_seconds": round(lead, 6), "end_seconds": round(end, 6),
        "lines": list(layout.lines), "widths_px": widths,
        "glyph_bboxes_px_with_outline": bboxes,
        "safe_rectangle": [230, 880, 1460, 140],
        "font_metrics_px": {"ascent": ascent, "descent": descent, "line_height": line_height},
        "alignment": "whole-scene-paragraph-continuous",
        "provider_boundaries_retained": len(sentences),
        "approved_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "full_text_unchanged": True,
    }]


def event_line(event: dict[str, Any], offset: float = 0) -> str:
    text = "\\N".join(ass_escape(line) for line in event["lines"])
    return (f"Dialogue: 0,{ass_time(offset + event['start_seconds'])},"
            f"{ass_time(offset + event['end_seconds'])},Narration,,0,0,0,,"
            "{\\fad(70,100)}" + text + "\n")


def image_probe(path: Path) -> VisualProbeResult:
    with Image.open(path) as image:
        width, height = image.size
    return VisualProbeResult(mimetypes.guess_type(path.name)[0] or "image/png", width, height)


def frozen_inputs(run: RunManifest | None, run_path: Path | None) -> dict[str, Any]:
    if run is None or run_path is None:
        raise ValueError("Player-trailer composition requires a native run and preserved render.inputs")
    matches = [row for row in run.artifacts if row.artifact_id == INPUT_ARTIFACT_ID]
    if len(matches) != 1:
        raise ValueError("Preserve exactly one render.inputs JSON before composition")
    path = artifact_path(matches[0], run_path.parent)
    if digest(path).upper() != matches[0].sha256:
        raise ValueError("render.inputs artifact binding changed")
    result = read_json(path)
    if (result.get("format_version"), result.get("kind")) != (1, "superman_qiang_render_inputs"):
        raise ValueError("Unsupported Superhuman Qiang render-input contract")
    return result


def preserved_path(run: RunManifest, run_path: Path, artifact_id: str) -> Path:
    matches = [row for row in run.artifacts if row.artifact_id == artifact_id]
    if len(matches) != 1:
        raise ValueError(f"Expected one preserved input artifact: {artifact_id}")
    path = artifact_path(matches[0], run_path.parent)
    if digest(path).upper() != matches[0].sha256:
        raise ValueError(f"Preserved input binding changed: {artifact_id}")
    return path


def compose(config: ProjectConfig, run: RunManifest | None, *, config_path: Path,
            run_path: Path | None, workdir: Path, adapter_factory: Any,
            preset_factory: Any, validate_only: bool) -> PipelineInvocation:
    """The actual PipelineComposer ABI used by xar-promo plan and build."""
    adapter_policy = adapter_factory(config=config)
    preset_policy = preset_factory(config=config)
    if adapter_policy.launches_game or not adapter_policy.requires_frozen_source_hashes:
        raise ValueError("Only the prepared, frozen-media adapter is valid for this attempt")
    if preset_policy.voice != EXPECTED_VOICE or preset_policy.music_source_count != 1:
        raise ValueError("The selected preset must retain Xiaoxiao and the sole supplied music track")
    head_seconds, tail_seconds = preset_policy.head_seconds, preset_policy.tail_seconds
    inputs = frozen_inputs(run, run_path)
    bindings = inputs.get("source_bindings", [])
    if not bindings:
        raise ValueError("Frozen source_bindings are required for every background and extra layer")
    bound_visual_paths = {str(Path(binding["path"]).resolve()).casefold() for binding in bindings}
    for binding in bindings:
        checked_file(binding, "frozen visual source")
    if config.narration_locale != preset_policy.narration_locale or config.subtitle_locales != preset_policy.subtitle_locales:
        raise ValueError("This approved trailer requires Chinese narration and subtitles")
    width, height, fps = preset_policy.frame
    if inputs["frame"] != {"width": width, "height": height, "fps": fps}:
        raise ValueError("Approved output frame is 1920x1080 at 30 fps")
    summary_path = checked_file(inputs["narration_summary"], "narration summary")
    visual_plan_path = checked_file(inputs["visual_plan"], "visual plan")
    music_path = checked_file(inputs["music"], "sole supplied music source")
    summary = read_json(summary_path)
    if summary["voice"] != EXPECTED_VOICE or summary["successful_scenes"] != 10:
        raise ValueError("Narration must use the specified Xiaoxiao voice for every scene")
    narration = {row["scene_id"]: row for row in summary["scenes"]}
    visual_plan = read_json(visual_plan_path)
    visuals = {row.get("scene_id", row.get("id")): row for row in visual_plan["scenes"]}
    visual_root = Path(inputs["visual_root"]).resolve()
    font_path = Path(inputs["subtitle_font"]["path"]).resolve()
    if not font_path.is_file():
        raise ValueError(f"Subtitle font is missing: {font_path}")
    family = inputs["subtitle_font"]["family"]
    font_size = int(inputs["subtitle_font"].get("size", 46))
    ids = [chapter.chapter_id for chapter in config.chapters]
    if ids != [f"SQP-{index:02}" for index in range(1, 11)]:
        raise ValueError("The selected director consists of the ten approved scenes")
    durations: dict[str, float] = {}
    rows: list[dict[str, Any]] = []
    for index, chapter in enumerate(config.chapters):
        sid = chapter.chapter_id
        scene = narration[sid]
        if scene["narration"] != chapter.cues[0].narration["zh-CN"]:
            raise ValueError(f"Narration text does not match approved cue {sid}")
        checked_file({"path": scene["audio_path"], "sha256": scene["audio_sha256"]}, sid + " audio")
        checked_file({"path": scene["boundaries_path"], "sha256": scene["boundaries_sha256"]}, sid + " boundaries")
        duration = math.ceil((scene["duration_seconds"] + head_seconds[index] + tail_seconds[index]) * 30) / 30
        durations[sid] = duration
        visual = visuals[sid]
        if visual["source_kind"] not in adapter_policy.accepted_source_kinds:
            raise ValueError(f"Unapproved prepared visual source kind: {visual['source_kind']}")
        if (visual["source_kind"] == "genuine-screenshot" and
                adapter_policy.genuine_screenshots_preserve_aspect_ratio and
                not visual.get("preserve_aspect_ratio")):
            raise ValueError("Genuine screenshot geometry must preserve its source aspect ratio")
        used_visual_paths = [visual["background_path"]] + [layer["path"] for layer in visual.get("optional_layers", [])]
        if visual.get("background_source"):
            used_visual_paths.append(visual["background"]["source_path"])
        for used_path in used_visual_paths:
            if str(Path(used_path).resolve()).casefold() not in bound_visual_paths:
                raise ValueError(f"Visual file is missing its frozen source binding: {used_path}")
        overlay = preserved_path(run, run_path, f"visual.overlay.{sid}")
        if not overlay.is_file():
            raise ValueError(f"Missing prepared player overlay: {overlay}")
        with Image.open(overlay) as image:
            if image.size != (1920, 1080) or image.mode != "RGBA":
                raise ValueError(f"Overlay must be RGBA 1920x1080: {overlay}")
        rows.append({"id": sid, "lead_seconds": head_seconds[index],
                     "narration_seconds": scene["duration_seconds"],
                     "duration_seconds": duration, "visual": visuals[sid],
                     "overlay": str(overlay), "overlay_sha256": digest(overlay),
                     "narration_sha256": scene["audio_sha256"],
                     "visual_source_bindings": [{"path": path, "sha256": digest(Path(path))}
                                                for path in used_visual_paths],
                     "boundaries": [json.loads(line) for line in Path(scene["boundaries_path"]).read_text(
                         encoding="utf-8").splitlines() if line.strip()]})
    total = sum(durations.values())
    policy = inputs["duration_policy"]
    if (float(policy["minimum_seconds"]) != preset_policy.minimum_duration_seconds or
            float(policy["maximum_seconds"]) != preset_policy.maximum_duration_seconds):
        raise ValueError("Input duration policy differs from the selected project preset")
    if not float(policy["minimum_seconds"]) <= total <= float(policy["maximum_seconds"]):
        raise ValueError(f"Actual media-derived duration {total:.3f}s violates project range")
    available = tuple(row.artifact_id for row in run.artifacts) if run else ()
    storyboard = plan_storyboard(
        config, narration_duration_resolver=None,
        draft_estimator=lambda project, chapter, cue: durations[chapter.chapter_id],
        spacing=TimelineSpacing(cue_gap_seconds=0, chapter_gap_seconds=0),
        available_artifact_ids=available, validate_only=True,
    )
    cursor = 0.0
    for row in rows:
        row["start_seconds"] = cursor
        row["end_seconds"] = cursor + row["duration_seconds"]
        cursor = row["end_seconds"]
    layout_reports: dict[str, list[dict[str, Any]]] = {}
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise ValueError("Verified FFmpeg must be on PATH")

    def subtitle_renderer(segment: SegmentDraft, narration_artifact: Any, *, workdir: Path) -> str:
        del narration_artifact, workdir
        index = ids.index(segment.segment_id)
        events = subtitle_events(narration[segment.segment_id], head_seconds[index],
                                 durations[segment.segment_id], font_path, family, font_size)
        layout_reports[segment.segment_id] = events
        return subtitle_header(family, font_size) + "".join(event_line(event) for event in events)

    def render_planner(**kwargs: Any) -> RenderPlan:
        return player_segment_plan(kwargs, rows, visual_root)

    def concat_planner(**kwargs: Any) -> RenderPlan:
        return player_concat_plan(kwargs, music_path, inputs["music"], total, rows,
                                  layout_reports, storyboard.to_dict(), family, font_size)

    segments = tuple(SegmentDraft(
        segment_id=row["id"], visual_source=VisualSource(
            source_id=row["id"], kind=STILL, path=Path(row["overlay"]),
            origin="prepared-player-overlay", metadata={"source_sha256": row["overlay_sha256"]}),
        prepared_narration=Path(narration[row["id"]]["audio_path"]),
        render_options=RenderOptions(1920, 1080, 30, row["duration_seconds"], preset="fast", crf=19),
        subtitles={"zh-CN": narration[row["id"]]["narration"]},
    ) for row in rows)
    return PipelineInvocation(
        PipelineDraft(config, segments, Path("deliverables/superman-qiang-player-trailer.mp4"),
                      "deliverable.player-trailer", "video/mp4"),
        PipelineDependencies(ffmpeg=ffmpeg, subtitle_renderer=subtitle_renderer,
                             command_runner=run_command, visual_probe=image_probe,
                             render_planner=render_planner, concat_planner=concat_planner,
                             plan_executor=execute_render_plan),
        workdir,
    )


def player_segment_plan(kwargs: dict[str, Any], rows: list[dict[str, Any]], visual_root: Path) -> RenderPlan:
    """Project-only artwork camera moves and truthful, complete screenshot shots."""
    del visual_root
    row = next(item for item in rows if Path(item["overlay"]).resolve() == Path(kwargs["video_input"]).resolve())
    scene = row["visual"]
    options = kwargs["options"]
    duration = row["duration_seconds"]
    frame_count = round(duration * 30)
    root = Path(kwargs["working_directory"])
    overlay = Path(kwargs["video_input"])
    partial, final = Path(kwargs["partial_output"]), Path(kwargs["final_output"])
    background = Path(scene["background_path"])
    argv = [kwargs["ffmpeg"], "-nostdin", "-hide_banner", "-loglevel", "info", "-n",
            "-loop", "1", "-framerate", "30", "-i", overlay,
            "-i", kwargs["audio_input"],
            "-loop", "1", "-framerate", "30", "-i", background]
    filters = [
        "[2:v]scale=1940:1092:flags=lanczos,crop=1920:1080:x='10+8*sin(t/5)':y=6,setsar=1,format=rgba[canvas]",
        "[0:v]format=rgba[title]",
    ]
    last = "canvas"
    next_input = 3
    if scene.get("background_source"):
        source = Path(scene["background"]["source_path"])
        argv.extend(["-loop", "1", "-framerate", "30", "-i", source])
        crop = scene.get("source_crop")
        crop_filter = ""
        if crop:
            left, top, right, bottom = crop
            crop_filter = f"crop={right-left}:{bottom-top}:{left}:{top},"
        x, y, width, height = scene["fit_rect"]
        if scene["source_kind"] == "art":
            # Render more pixels before zoompan to avoid visible integer steps.
            large_width, large_height = width * 2, height * 2
            # The revised queen shot keeps the complete crown in its source
            # framing. Other artwork receives the ordinary slow push.
            zoom_start, zoom_delta = (1.0, 0.0) if row["id"] == "SQP-05" else (1.02, 0.035)
            filters.append(
                f"[{next_input}:v]{crop_filter}scale={large_width}:{large_height}:"
                "force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={large_width}:{large_height},"
                f"zoompan=z='{zoom_start}+{zoom_delta}*on/{frame_count}':"
                f"x='(iw-iw/zoom)*(0.45+0.08*on/{frame_count})':"
                f"y='(ih-ih/zoom)/2':d=1:s={width}x{height}:fps=30,"
                "setsar=1,format=rgba[framed]"
            )
        else:
            filters.append(
                f"[{next_input}:v]{crop_filter}scale={width}:{height}:"
                "force_original_aspect_ratio=decrease:flags=lanczos,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x100910,"
                "setsar=1,format=rgba[framed]"
            )
        filters.append(f"[{last}][framed]overlay=x={x}:y={y}:format=auto[with-source]")
        last = "with-source"
        next_input += 1

    optional = scene.get("optional_layers", [])
    boundary_rows = row["boundaries"]
    lead = row["lead_seconds"]
    end_of_voice = lead + row["narration_seconds"]
    last_sentence = boundary_rows[-1]
    last_sentence_start = lead + last_sentence["offset"] / 10_000_000
    reveal = lead + row["narration_seconds"] * 0.78
    if row["id"] == "SQP-05":
        reveal = last_sentence_start + (last_sentence["duration"] / 10_000_000) * 0.55
    if row["id"] == "SQP-01":
        reveal = lead + row["narration_seconds"] * 0.80
    base_condition = "1"
    if row["id"] == "SQP-01":
        base_condition = "0"
    elif row["id"] == "SQP-05":
        base_condition = f"gte(t,{reveal:.6f})"
    filters.append(f"[{last}][title]overlay=x=0:y=0:enable='{base_condition}':format=auto[with-title]")
    last = "with-title"
    for index, layer in enumerate(optional):
        path = Path(layer["path"])
        name = path.stem
        start, end = lead, end_of_voice
        if row["id"] == "SQP-01":
            start, end = (0, reveal) if name.endswith("hook") else (reveal, duration)
        elif row["id"] == "SQP-05" and "question" in name:
            start, end = 0, reveal
        elif row["id"] == "SQP-05" and "power" in name:
            start, end = reveal, duration - 0.6
        elif row["id"] == "SQP-08":
            first = boundary_rows[0]
            sentence_start = lead + first["offset"] / 10_000_000
            sentence_duration = first["duration"] / 10_000_000
            start = sentence_start + sentence_duration * index / 7
            end = sentence_start + sentence_duration * (index + 1) / 7
        elif row["id"] == "SQP-03" and "外交" in name:
            start, end = last_sentence_start + 0.2, last_sentence_start + 2.8
        elif row["id"] == "SQP-03" and "勇武" in name:
            start, end = last_sentence_start + 2.8, duration - 0.5
        elif "power" in name:
            start, end = lead + 1.0, duration - 0.5
        elif "timing_fraction" in layer:
            start, end = [duration * float(value) for value in layer["timing_fraction"]]
        start = max(0.0, start)
        end = min(duration, end)
        if end <= start:
            continue
        argv.extend(["-loop", "1", "-framerate", "30", "-i", path])
        label = f"optional{index}"
        fade = min(0.12, (end-start)/4)
        filters.append(f"[{next_input}:v]format=rgba,fade=t=in:st={start:.6f}:d={fade:.6f}:alpha=1[extra{index}]")
        filters.append(f"[{last}][extra{index}]overlay=x=0:y=0:"
                       f"enable='between(t,{start:.6f},{end:.6f})':format=auto[{label}]")
        last = label
        next_input += 1
    fade_out = 0.65 if row["id"] == "SQP-10" else 0.20
    filters.append(f"[{last}]fade=t=in:st=0:d=0.25,"
                   f"fade=t=out:st={duration-fade_out:.6f}:d={fade_out},"
                   f"{ass_burn_in_filter(kwargs['ass_path'])},"
                   f"trim=duration={duration:.6f},setpts=PTS-STARTPTS,fps=30,format=yuv420p[v]")
    filters.append(
        "[1:a]highpass=f=70,loudnorm=I=-17:TP=-2:LRA=6,aresample=48000,"
        "aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"adelay={round(lead*1000)}:all=1,apad,atrim=duration={duration:.6f},"
        "asetpts=N/SR/TB[a]"
    )
    graph = ";".join(filters)
    argv.extend(["-filter_complex_threads", "2", "-filter_complex", graph, "-map", "[v]",
                 "-map", "[a]", "-t", seconds(duration), "-c:v", options.video_codec,
                 "-preset", options.preset, "-crf", str(options.crf), "-pix_fmt", "yuv420p",
                 "-r", "30", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                 "-ac", "2", "-movflags", "+faststart", partial])
    graph_path = root / "filtergraphs" / f"{row['id']}.filter"
    command = CommandSpec.create(argv, label=f"render player scene {row['id']}",
                                 cwd=root, partial_artifacts=(partial,))
    return RenderPlan((PlannedCommand(command, Path(kwargs["audit_directory"]) / "render"),),
                      (GeneratedTextFile(graph_path, graph + "\n"),), partial, final)


def player_concat_plan(kwargs: dict[str, Any], music_path: Path, music: dict[str, Any],
                       total: float, rows: list[dict[str, Any]], layouts: dict[str, Any],
                       storyboard: dict[str, Any], family: str, font_size: int) -> RenderPlan:
    """Join narration scenes, continuously duck one music source, and retain inputs."""
    root = Path(kwargs["working_directory"])
    joined = root / "intermediate" / "joined-narration.mp4"
    joined.parent.mkdir(parents=True, exist_ok=True)
    concat_path = Path(kwargs["concat_path"])
    partial = Path(kwargs["partial_output"])
    final = Path(kwargs["final_output"])
    duration = seconds(total)
    music_start = float(music.get("start_seconds", 0))
    # Preserve the supplied opening and ending. Both spans come from the single
    # original WAV; the join overlaps for two seconds and receives an end fade.
    music_duration = float(music.get("duration_seconds", 180.0))
    ending_seconds = 12.0
    overlap_seconds = 2.0
    body_seconds = total - ending_seconds + overlap_seconds
    ending_start = max(music_start + body_seconds, music_duration - ending_seconds)
    graph = (
        f"[1:a]asplit=2[opening][ending];"
        f"[opening]atrim=start={seconds(music_start)}:duration={seconds(body_seconds)},asetpts=PTS-STARTPTS[body];"
        f"[ending]atrim=start={seconds(ending_start)}:duration=12,asetpts=PTS-STARTPTS[tail];"
        f"[body][tail]acrossfade=d=2:c1=tri:c2=tri,afade=t=in:st=0:d=1.5,"
        f"afade=t=out:st={seconds(total-2.5)}:d=2.5,volume=0.30[music];"
        "[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        "asplit=2[voice][key];"
        "[music][key]sidechaincompress=threshold=0.035:ratio=10:attack=20:release=550[ducked];"
        f"[voice][ducked]amix=inputs=2:normalize=0:duration=first,"
        f"atrim=duration={duration},loudnorm=I=-16:TP=-2:LRA=8:print_format=json,"
        "aresample=48000,alimiter=limit=0.891251:level=false[a]"
    )
    commands = (
        PlannedCommand(CommandSpec.create(
            [kwargs["ffmpeg"], "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
             "-f", "concat", "-safe", "0", "-i", concat_path, "-c", "copy",
             "-movflags", "+faststart", joined],
            label="concatenate approved player scenes", cwd=root, partial_artifacts=(joined,)),
            root / "audit" / "concat" / "join-narration"),
        PlannedCommand(CommandSpec.create(
            [kwargs["ffmpeg"], "-nostdin", "-hide_banner", "-loglevel", "info", "-n",
             "-i", joined, "-i", music_path, "-filter_complex", graph, "-map", "0:v:0",
             "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
             "-ar", "48000", "-ac", "2", "-t", duration, "-movflags", "+faststart", partial],
            label="mix one supplied Suno track with Xiaoxiao narration", cwd=root,
            partial_artifacts=(partial,)), root / "audit" / "concat" / "mix-single-music"),
    )
    timeline = {
        "format_version": 1, "kind": "superman_qiang_player_trailer_timeline",
        "duration_seconds": total, "voice": EXPECTED_VOICE, "width": 1920,
        "height": 1080, "fps": 30, "scenes": rows, "storyboard": storyboard,
        "music": {"path": str(music_path), "sha256": digest(music_path),
                  "source_count": 1, "opening_span": [music_start, music_start + body_seconds],
                  "ending_span": [ending_start, ending_start + ending_seconds],
                  "crossfade_seconds": overlap_seconds, "voice_sidechain_ducking": True,
                  "target_lufs": -16, "mix_target_true_peak_dbfs": -2,
                  "actual_final_loudness": "requires post-encode measurement"},
        "review_state": "pending-human-review",
    }
    global_events = []
    for row in rows:
        global_events.extend((row["id"], row["start_seconds"], event)
                             for event in layouts[row["id"]])
    global_ass = subtitle_header(family, font_size) + "".join(
        event_line(event, offset) for _, offset, event in global_events)
    review_storyboard = {
        "chapters": [{
            "id": row["id"], "start_seconds": round(row["start_seconds"], 6),
            "end_seconds": round(row["end_seconds"], 6),
            "boundary_seconds": sorted(set(
                round(row["start_seconds"] + event["start_seconds"], 6)
                for event in layouts[row["id"]]
                if 0 < event["start_seconds"] < row["duration_seconds"])),
        } for row in rows],
    }
    srt = "\n\n".join(
        f"{index}\n{srt_time(offset+event['start_seconds'])} --> "
        f"{srt_time(offset+event['end_seconds'])}\n" + "\n".join(event["lines"])
        for index, (_, offset, event) in enumerate(global_events, start=1)) + "\n"
    generated = (
        GeneratedTextFile(concat_path, concat_manifest(tuple(kwargs["segment_paths"]), manifest_directory=concat_path.parent)),
        GeneratedTextFile(root / "timeline.json", json.dumps(timeline, ensure_ascii=False, indent=2) + "\n"),
        GeneratedTextFile(root / "storyboard.json", json.dumps(review_storyboard, ensure_ascii=False, indent=2) + "\n"),
        GeneratedTextFile(root / "storyboard-timing.json", json.dumps(storyboard, ensure_ascii=False, indent=2) + "\n"),
        GeneratedTextFile(root / "subtitle-layout-report.json", json.dumps({
            "kind": "superman_qiang_subtitle_layout", "font_path": str(Path("C:/Windows/Fonts/msyh.ttc")),
            "font_family": family, "font_size_px": font_size, "scenes": layouts,
            "cue_count": len(global_events), "scene_count": len(layouts),
            "safe_rectangle": [230, 880, 1460, 140],
            "scene_timing": {row["id"]: {"start_seconds": row["start_seconds"],
                                           "end_seconds": row["end_seconds"]} for row in rows},
            "measured_width_safe_max_px": 1460, "max_lines": 2,
            "provider_boundary_unit": "100-nanosecond ticks",
            "subtitle_policy": "one-complete-paragraph-per-scene",
            "provider_boundaries_usage": "retained for provenance; not sentence replacement",
        }, ensure_ascii=False, indent=2) + "\n"),
        GeneratedTextFile(root / "subtitles" / "complete.ass", global_ass),
        GeneratedTextFile(root / "subtitles" / "complete.srt", srt),
        GeneratedTextFile(root / "concat" / "single-music-mix.filter", graph + "\n"),
    )
    return RenderPlan(commands, generated, partial, final)
