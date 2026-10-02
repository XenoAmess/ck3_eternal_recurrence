"""Read-only native composer for an Episode03 prepared picture and series theme.

Picture, narration and subtitles are prepared by production.py. Composition
only validates those exact inputs and returns the public xar-promo invocation.
It never starts capture, a TTS provider, or an image provider.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from xar_promo.audio import AudioMixSpec, AudioStem, plan_audio_mix
from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.process import CommandSpec, run_command
from xar_promo.render import PlannedCommand, RenderOptions, RenderPlan, plan_concat
from xar_promo.sources import VIDEO, VisualProbeResult, VisualSource

import production as p


def compose(config, run, *, config_path, run_path, workdir,
            adapter_factory, preset_factory, validate_only):
    p.require(run_path is not None, "Episode03 requires a bound native run")
    root = Path(run_path).parent.parent
    p.require_ready(root)
    dry = p.read(root / "dry-master.json")
    music = p.read(root / "music-policy.json")
    p.exact(dry)
    if dry.get("visual_render_receipts"):
        p.exact(dry["visual_render_receipts"])
        visuals = p.read(dry["visual_render_receipts"]["path"])
        p.require(visuals["total_duration_frames"] == dry["duration_frames_expected"],
                  "Native UI render receipt differs from the prepared integer picture clock")
        p.exact(visuals["timeline"])
        p.exact(visuals["edit"])
    p.exact(music["source"])
    p.require(config.project_id == p.read(root / "sources/project-config.json")["project"]["id"],
              "Project config differs from the prepared Episode03 run")
    adapter_factory()
    preset_factory()
    duration = float(dry["duration_expected"])
    p.require(duration > 0 and duration <= config.duration_limit_seconds,
              "Prepared episode exceeds its frozen project duration limit")
    p.require(music["loop"] and music["normalize"] is False,
              "Episode03 requires the fixed series-theme loop without normalization")
    spec = AudioMixSpec(
        stems=(
            AudioStem(stem_id="episode03-narration", path=Path(dry["path"]),
                      gain_db=music["narration_gain_db"]),
            AudioStem(stem_id="series-theme", path=Path(music["source"]["path"]),
                      gain_db=music["music_gain_db"],
                      fade_in_seconds=music["fade_in_seconds"],
                      fade_out_seconds=music["fade_out_seconds"]),
        ),
        duration_seconds=duration, sample_rate=48000, channels=2,
        normalize=False, metadata={"policy": music["policy"]},
    )

    def render_planner(**kw):
        mix = plan_audio_mix(kw["audio_mix"], input_start_index=1, output_label="mixed")
        argv = [kw["ffmpeg"], "-hide_banner", "-nostdin", "-loglevel", "warning", "-n",
                "-i", str(kw["video_input"]), "-i", str(spec.stems[0].path),
                "-stream_loop", "-1", "-i", str(spec.stems[1].path),
                "-filter_complex", mix.filtergraph, "-map", "0:v:0", "-map", "[mixed]",
                "-map_metadata", "0", "-map_chapters", "0", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                "-t", f"{duration:.6f}", "-movflags", "+faststart", str(kw["partial_output"])]
        command = CommandSpec.create(argv, label="Episode03 exact series-theme mix",
                                     cwd=kw["working_directory"], partial_artifacts=(kw["partial_output"],))
        return RenderPlan((PlannedCommand(command, Path(kw["audit_directory"]) / "theme-mix"),),
                          (), Path(kw["partial_output"]), Path(kw["final_output"]))

    def concat_planner(**kw):
        p.require(len(kw["segment_paths"]) == 1, "One complete Episode03 mix is required")
        plan = plan_concat(**kw)
        # Preserve AAC skip-sample metadata and chapter timestamps, as in a09.
        argv = [kw["ffmpeg"], "-hide_banner", "-nostdin", "-loglevel", "error", "-n",
                "-i", str(kw["segment_paths"][0]), "-map", "0:v:0", "-map", "0:a:0",
                "-map_metadata", "0", "-map_chapters", "0", "-c", "copy",
                "-movflags", "+faststart", str(kw["partial_output"])]
        command = CommandSpec.create(argv, label="Episode03 full-mix remux",
                                     cwd=kw["working_directory"], partial_artifacts=(kw["partial_output"],))
        return replace(plan, commands=(PlannedCommand(command, Path(kw["audit_directory"]) / "remux"),))

    def subtitle_renderer(segment, narration, *, workdir):
        # The prepared dry picture already contains the frozen bilingual ASS.
        return ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n"
                "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")

    observation = p.read(root / "dry-master-probe.json")
    video = next(s for s in observation["streams"] if s["codec_type"] == "video")
    p.require((video["width"], video["height"], video["r_frame_rate"]) == (1920, 1080, "30/1"),
              "Episode03 prepared picture must be 1920x1080 at 30 fps")

    def visual_probe(path):
        p.require(Path(path).resolve() == Path(dry["path"]).resolve(), "Unexpected prepared picture")
        mime = "video/quicktime" if Path(dry["path"]).suffix.lower() == ".mov" else "video/mp4"
        return VisualProbeResult(mime, video["width"], video["height"])

    segment = SegmentDraft("episode03-full-picture",
                           VisualSource("episode03-dry-picture", VIDEO, Path(dry["path"]),
                                        "episode03-bound-existing-media"),
                           RenderOptions(1920, 1080, 30, duration), {},
                           prepared_narration=Path(dry["path"]), audio_mix=spec)
    draft = PipelineDraft(config, (segment,), Path(p.output_name(root)), "e3-deliverable", "video/mp4")
    return PipelineInvocation(draft,
                              PipelineDependencies(p.environment(root)["ffmpeg"], subtitle_renderer,
                                                   run_command, visual_probe,
                                                   render_planner=render_planner,
                                                   concat_planner=concat_planner), Path(workdir))
