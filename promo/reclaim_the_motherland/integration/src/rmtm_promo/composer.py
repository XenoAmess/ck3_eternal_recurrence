"""Native ``xar-promo`` composer for the approved Reclaim trailer."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from xar_promo.audio import AudioMixSpec, AudioStem, DuckWindow
from xar_promo.media import probe_media
from xar_promo.model import RunManifest
from xar_promo.pipeline import (
    PipelineDependencies,
    PipelineDraft,
    PipelineInvocation,
    SegmentDraft,
)
from xar_promo.process import run_command
from xar_promo.project import ProjectConfig
from xar_promo.render import RenderOptions
from xar_promo.sources import VIDEO, VisualProbeResult, VisualSource
from xar_promo.subtitles import (
    AssCue,
    AssDocumentConfig,
    AssStyleConfig,
    SubtitleTrackConfig,
    render_ass_document,
)

EXPECTED_PROJECT = "reclaim-the-motherland-promo"
EXPECTED_ADAPTER = "rmtm-ck3-v1"
EXPECTED_PRESET = "rmtm-96s-zh-v1"
TOTAL_SECONDS = 96.0


def _load_policy(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as source:
        value = json.load(source)
    if not isinstance(value, dict) or value.get("project_id") != EXPECTED_PROJECT:
        raise ValueError(f"invalid Reclaim promo policy: {path}")
    return value


def _artifact_path(
    run: RunManifest | None,
    run_path: Path | None,
    artifact_id: str,
) -> Path:
    if run is None or run_path is None:
        raise ValueError(
            "Reclaim composition requires a native RunManifest with preserved inputs"
        )
    matches = [item for item in run.artifacts if item.artifact_id == artifact_id]
    if len(matches) != 1:
        raise ValueError(f"run must contain exactly one {artifact_id!r} artifact")
    return (run_path.parent / Path(matches[0].path)).resolve()


def _subtitle_document(_segment: object, _narration: object, *, workdir: Path) -> str:
    del _segment, _narration, workdir
    body_style = AssStyleConfig(
        name="Narration",
        font_name="Microsoft YaHei",
        font_size=54,
        outline=3,
        shadow=1,
        alignment=2,
        margin_left=150,
        margin_right=150,
        margin_vertical=72,
    )
    overlay_style = AssStyleConfig(
        name="Overlay",
        font_name="Microsoft YaHei",
        font_size=64,
        primary_colour="&H00E9F0F5",
        outline_colour="&H00201810",
        back_colour="&H70081018",
        outline=4,
        shadow=2,
        alignment=8,
        margin_left=130,
        margin_right=130,
        margin_vertical=84,
    )
    title_style = AssStyleConfig(
        name="Title",
        font_name="Microsoft YaHei",
        font_size=78,
        primary_colour="&H00D5E6F7",
        outline_colour="&H00201810",
        back_colour="&H70081018",
        outline=4,
        shadow=2,
        alignment=5,
        margin_left=120,
        margin_right=120,
        margin_vertical=80,
    )
    tracks = (
        SubtitleTrackConfig("narration", "zh-CN", 2, body_style),
        SubtitleTrackConfig("overlay", "zh-CN", 1, overlay_style),
        SubtitleTrackConfig("title", "zh-CN", 3, title_style),
    )
    narration_rows = (
        ("n01", 0.35, 5.70, "天命可以失去，王朝不必随之湮灭。"),
        ("n02", 6.35, 14.70, "当群雄并起，旧日的天子不再被迫散尽基业。"),
        ("n03", 15.35, 26.70, "他失去中华霸权，却仍守故土；\n尊王诸侯，也仍奉旧朝为主。"),
        ("n04", 27.35, 38.70, "国号改作“后宋”，法统暂寄一隅。\n天下虽裂，复国之志未绝。"),
        ("n05", 39.35, 50.70, "待故土过半重归麾下，失落的天命，\n便有了再度争取的资格。"),
        ("n06", 51.35, 62.65, "后朝不向新主称臣。它所等待的，\n只有一道诏书——宣称复辟。"),
        ("n07", 63.35, 74.70, "昭告天下：故国已复，天命重归。"),
        ("n08", 75.35, 82.70, "旧朝之名归入史册，\n而新的天下，自此重开。"),
        ("n09", 83.10, 87.70, "重整河山——一朝失鹿，尚可再兴。"),
    )
    overlay_rows = (
        ("o01", 0.80, 5.60, "天命既移，社稷未亡"),
        ("o02", 6.50, 14.50, "大宋 · 开封\nSong · Kaifeng"),
        ("o03", 15.50, 20.50, "失天命，不失故土"),
        ("o04", 21.00, 26.50, "尊王诸侯，仍列朝班"),
        ("o05", 27.50, 38.50, "后宋"),
        ("o06", 39.50, 50.50, "故土过半"),
        ("o07", 51.50, 62.50, "宣称复辟\nProclaim the Restoration"),
        ("o08", 63.50, 74.50, "昭告天下"),
        ("o09", 75.50, 82.50, "中华霸权复归\n后朝之号封存"),
    )
    cues = tuple(
        AssCue(cue_id, "narration", start, end, text)
        for cue_id, start, end, text in narration_rows
    ) + tuple(
        AssCue(cue_id, "overlay", start, end, text)
        for cue_id, start, end, text in overlay_rows
    ) + (
        AssCue(
            "title01",
            "title",
            83.0,
            95.25,
            "重整河山\nReclaim the Motherland\n\n现已登陆 Steam Workshop\n需《溥天之下 / All Under Heaven》",
        ),
    )
    return render_ass_document(
        AssDocumentConfig(
            title="Reclaim the Motherland promo",
            play_res_x=1920,
            play_res_y=1080,
            duration_seconds=TOTAL_SECONDS,
        ),
        tracks,
        cues,
        available_font_names={"Microsoft YaHei"},
    )


def _music_ducks() -> tuple[DuckWindow, ...]:
    return (
        DuckWindow(0.35, 5.70, -5.5),
        DuckWindow(6.35, 14.70, -5.5),
        DuckWindow(15.35, 26.70, -5.5),
        DuckWindow(27.35, 38.70, -5.5),
        DuckWindow(39.35, 50.70, -5.5),
        DuckWindow(51.35, 62.65, -5.5),
        DuckWindow(62.80, 63.35, -9.5),
        DuckWindow(63.35, 74.70, -5.5),
        DuckWindow(75.35, 82.70, -5.5),
        DuckWindow(83.10, 87.70, -5.5),
    )


def _assert_project(draft: PipelineDraft) -> None:
    config = draft.config
    if (
        config.project_id != EXPECTED_PROJECT
        or config.adapter != EXPECTED_ADAPTER
        or config.preset != EXPECTED_PRESET
        or config.narration_locale != "zh-CN"
        or config.duration_limit_seconds != 97
    ):
        raise ValueError("Reclaim draft does not match the frozen project contract")
    if len(draft.segments) != 1 or draft.segments[0].render_options.duration_seconds != TOTAL_SECONDS:
        raise ValueError("Reclaim draft must contain one exact 96-second master segment")


def compose(
    config: ProjectConfig,
    run: RunManifest | None,
    *,
    config_path: Path,
    run_path: Path | None,
    workdir: Path,
    adapter_factory: object,
    preset_factory: object,
    validate_only: bool,
) -> PipelineInvocation:
    """Compose a one-master render so A03 and narration remain gapless."""

    del validate_only
    adapter = adapter_factory() if callable(adapter_factory) else adapter_factory
    preset = preset_factory() if callable(preset_factory) else preset_factory
    if not isinstance(adapter, Mapping) or adapter.get("id") != EXPECTED_ADAPTER:
        raise ValueError("resolved adapter does not match rmtm-ck3-v1")
    if not isinstance(preset, Mapping) or preset.get("id") != EXPECTED_PRESET:
        raise ValueError("resolved preset does not match rmtm-96s-zh-v1")

    policy = _load_policy(
        _artifact_path(run, run_path, "promo-policy-approved-v1")
    )
    ids = policy["input_artifact_ids"]
    visual = _artifact_path(run, run_path, ids["visual_master"])
    narration = _artifact_path(run, run_path, ids["narration_master"])
    music = _artifact_path(run, run_path, ids["music"])
    video = policy["video"]
    audio = policy["audio"]
    deliverable = policy["deliverable"]

    audio_mix = AudioMixSpec(
        stems=(
            AudioStem(
                "narration",
                narration,
                trim_duration_seconds=TOTAL_SECONDS,
                gain_db=float(audio["narration_gain_db"]),
            ),
            AudioStem(
                "a03",
                music,
                trim_duration_seconds=TOTAL_SECONDS,
                gain_db=float(audio["music_gain_db"]),
                fade_in_seconds=float(audio["music_fade_in_seconds"]),
                fade_out_seconds=float(audio["music_fade_out_seconds"]),
                duck_windows=_music_ducks(),
            ),
        ),
        duration_seconds=TOTAL_SECONDS,
        sample_rate=int(audio["sample_rate"]),
        channels=int(audio["channels"]),
        normalize=False,
        metadata={
            "music_selection": "A03",
            "music_source_sha256": "0E4ED8EE2AA86BD676862B080707796430C2F8C2B2EF7934BDA053CF68EB92FB",
            "picture_end_seconds": 88,
            "deliverable_end_seconds": 96,
        },
    )
    segment = SegmentDraft(
        segment_id="master",
        visual_source=VisualSource(
            "visual-master",
            VIDEO,
            visual,
            "run-artifact",
            metadata={"artifact_id": ids["visual_master"], "mcp_anchor": "b_kaifeng"},
        ),
        render_options=RenderOptions(
            width=int(video["delivery_width"]),
            height=int(video["delivery_height"]),
            fps=int(video["fps"]),
            duration_seconds=TOTAL_SECONDS,
            video_codec=str(video["video_codec"]),
            pixel_format=str(video["pixel_format"]),
            preset=str(video["preset"]),
            crf=int(video["crf"]),
            audio_sample_rate=int(audio["sample_rate"]),
            audio_channels=int(audio["channels"]),
        ),
        subtitles={"zh-CN": "approved-storyboard-v1"},
        prepared_narration=narration,
        audio_mix=audio_mix,
    )
    draft = PipelineDraft(
        config=config,
        segments=(segment,),
        deliverable_relative_path=Path(deliverable["relative_path"]),
        deliverable_artifact_id=str(deliverable["artifact_id"]),
        deliverable_media_type=str(deliverable["media_type"]),
    )

    ffmpeg = os.environ.get("RMTM_FFMPEG", "ffmpeg")
    ffprobe = os.environ.get("RMTM_FFPROBE", "ffprobe")
    attempt = Path(workdir).expanduser().resolve()

    def visual_probe(path: Path) -> VisualProbeResult:
        probe = probe_media(
            ffprobe,
            path,
            audit_directory=attempt / "audit" / "visual-probe",
        )
        streams = probe.video_streams
        if len(streams) != 1 or streams[0].width is None or streams[0].height is None:
            raise ValueError("visual master must contain exactly one sized video stream")
        return VisualProbeResult("video/mp4", streams[0].width, streams[0].height)

    return PipelineInvocation(
        draft=draft,
        dependencies=PipelineDependencies(
            ffmpeg=ffmpeg,
            subtitle_renderer=_subtitle_document,
            command_runner=run_command,
            visual_probe=visual_probe,
            draft_validator=_assert_project,
        ),
        workdir=attempt,
    )
