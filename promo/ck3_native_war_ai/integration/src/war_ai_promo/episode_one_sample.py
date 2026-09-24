"""Episode 1 EdgeTTS sample composer: retained CK3 context plus sourced teaching cards.

The CASE-W clip is context from another war. The data cards state only the
evidence claimed in the checked-in episode-one script and director plan.
"""

from pathlib import Path
import json
import math
import os

from PIL import ImageDraw
from xar_promo.media import probe_media
from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.process import CommandSpec, run_command
from xar_promo.render import RenderOptions
from xar_promo.sources import VIDEO, VisualProbeResult, VisualSource

from .captions import subtitle_document
from .common import font, load, lines
from .visuals import BG, PANEL, INK, MUTED, GOLD, RED, BLUE, GREEN, make_canvas, box, heraldic_mark


CARDS = {
    "E1-02": ("战前比较 ≠ 整场概率", "两条原版路径，各自回答不同问题", [
        ("确定性预测", "比较当前双方的相对力量"),
        ("逐日结算", "阶段、日期、伤亡与事件继续推进"),
        ("读数边界", "ratio 不是获胜概率")], "原版 CK3 1.19.0.6 · battle-simulation.md"),
    "E1-03": ("先锁住这场仗的输入", "换参战条件，就换了问题", [
        ("参战身份", "兵团顺序、当前人数、攻守角色"),
        ("战场条件", "地形、渡口、战宽、兵种反制"),
        ("角色与时点", "将领、骑士、增援何时抵达")], "同一玩家军队，对一敌与对两敌是两套条件"),
    "E1-04": ("从接战走向下一日", "原版战斗是状态转移，不是一张静态表", [
        ("当日输入", "当前阶段、人数、优势、将领掷骰"),
        ("当日结算", "双方出伤与逐兵团软／硬伤亡"),
        ("下日回流", "剩余兵力、事件与新参战状态")], "一天的精确算术 ≠ 整场终局分布"),
    "E1-05": ("R0220：一日对拍", "按兵团 ID 比对同一个主阶段 tick", [
        ("54 行", "逐兵团当日伤亡记录"),
        ("零差", "对应输入下与原版当日结果一致"),
        ("证据边界", "一日，不是 54 场，也不是整场终局")], "原版 trace：battle-simulation.md · R0220"),
    "E1-06": ("把一天推到终局", "每个分支都可能改写后面的状态", [
        ("阶段事件", "角色或部队状态发生变化"),
        ("动态参战", "增援、退出、撤退与追击"),
        ("结果落地", "winner、终局 effect 与实际记录")], "主案连续拍摄；另案验证必须明示身份"),
    "E1-07": ("三个数字，三种答案", "别让一个比例替另一种问题作答", [
        ("战前 ratio", "眼前的相对力量比较"),
        ("当日零差", "这一日的原版数值对拍"),
        ("条件胜率", "完整终局校验后的重复模拟分布")], "百分比上屏必须同时写条件、样本数与模型误差"),
}


def artifact(run, run_path, identifier):
    hits = [item for item in run.artifacts if item.artifact_id == identifier]
    if len(hits) != 1:
        raise ValueError(f"Expected one preserved artifact: {identifier}")
    return (run_path.parent / hits[0].path).resolve()


def _draw_text(draw, xy, value, size, *, color=INK, bold=False, width=None):
    rows = lines(value, size, width, bold) if width else [value]
    for index, row in enumerate(rows):
        draw.text((xy[0], xy[1] + index * size * 1.4), row, font=font(size, bold), fill=color)


def _card_image(row, path, active):
    title, kicker, items, foot = CARDS[row["id"]]
    im = make_canvas()
    draw = ImageDraw.Draw(im)
    heraldic_mark(draw, (134, 125), 67, GOLD)
    _draw_text(draw, (202, 74), "十字军之王 III · 原生战争机器", 37, color=GOLD, bold=True)
    _draw_text(draw, (153, 190), title, 84, bold=True)
    _draw_text(draw, (159, 320), kicker, 42, color=MUTED)
    for index, (heading, detail) in enumerate(items):
        x = 146 + index * 765
        bounds = (x, 455, x + 712, 955)
        selected = active == index
        box(draw, bounds, PANEL if selected else "#29211A", GOLD if selected else "#66513A")
        draw.rectangle((x + 28, 489, x + 43, 888), fill=[GOLD, RED, GREEN][index] if selected else "#66513A")
        _draw_text(draw, (x + 77, 503), f"0{index+1}", 39, color=GOLD if selected else MUTED)
        _draw_text(draw, (x + 77, 585), heading, 53, color=INK if selected else MUTED, bold=True)
        _draw_text(draw, (x + 77, 702), detail, 37, color=INK if selected else MUTED, width=585)
    draw.line((146, 1030, 2414, 1030), fill="#66513A", width=2)
    _draw_text(draw, (160, 1062), foot, 31, color=GOLD, width=2200)
    _draw_text(draw, (182, 1194), "规则与证据示意｜非同步战斗实机", 31, color=MUTED)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        im.save(stream, format="PNG")


def _context_clip(source, row, target, ffmpeg, workdir):
    duration = float(row["duration_seconds"])
    measured = probe_media("ffprobe", source, audit_directory=workdir / "audit" / "context-source-probe")
    if measured.require_duration() < duration + .01:
        raise ValueError("Preserved CASE-W context footage is shorter than measured cue")
    target.parent.mkdir(parents=True, exist_ok=True)
    run_command(CommandSpec.create([
        ffmpeg, "-nostdin", "-n", "-hide_banner", "-loglevel", "warning",
        "-i", str(source), "-t", f"{duration:.6f}", "-an",
        "-vf", "fps=30,format=yuv420p", "-r", "30", "-c:v", "libx264",
        "-preset", "veryfast", "-crf", "20", "-threads", "4", str(target)],
        label="episode-one-context-CASE-W", partial_artifacts=[target]),
        audit_directory=workdir / "audit" / "context-trim")
    return target


def _card_clip(row, target, ffmpeg, workdir):
    duration = float(row["duration_seconds"])
    folder = workdir / "drawings" / row["id"]
    folder.mkdir(parents=True, exist_ok=False)
    frames = [folder / f"state-{index}.png" for index in range(3)]
    for index, frame in enumerate(frames):
        _card_image(row, frame, index)
    fade = min(.45, duration / 12)
    length = (duration + 2 * fade) / 3
    first = length - fade
    second = 2 * first
    filters = [f"[{i}:v]trim=duration={length:.6f},settb=AVTB,setpts=PTS-STARTPTS,format=yuv420p[s{i}]" for i in range(3)]
    filters.extend([
        f"[s0][s1]xfade=transition=fade:duration={fade:.6f}:offset={first:.6f}[ab]",
        f"[ab][s2]xfade=transition=fade:duration={fade:.6f}:offset={second:.6f},format=yuv420p[v]",
    ])
    target.parent.mkdir(parents=True, exist_ok=True)
    argv = [ffmpeg, "-nostdin", "-n", "-hide_banner", "-loglevel", "warning"]
    for frame in frames:
        argv.extend(["-loop", "1", "-framerate", "30", "-i", str(frame)])
    argv.extend(["-filter_complex_threads", "1", "-filter_complex", ";".join(filters),
                 "-map", "[v]", "-an", "-t", f"{duration:.6f}", "-r", "30",
                 "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21", "-threads", "4", str(target)])
    run_command(CommandSpec.create(argv, label=f"episode-one-card-{row['id']}", partial_artifacts=[target]),
                audit_directory=workdir / "audit" / "cards" / row["id"])
    (folder / "visual-plan.json").write_text(json.dumps({
        "kind": "project-authored-sourced-teaching-card", "cue_id": row["id"],
        "duration_seconds": duration, "source_frames": [str(frame) for frame in frames],
        "transition": "fade", "evidence_scope": "Rule or trace facts only; no original battle footage or full probability inferred",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def compose(config, run, *, config_path, run_path, workdir, adapter_factory,
            preset_factory, validate_only):
    del config_path, validate_only
    adapter, preset = adapter_factory(), preset_factory()
    if config.adapter != adapter["id"] or config.preset != preset["id"]:
        raise ValueError("Episode-one sample components mismatch")
    if config.project_id != "ck3-native-war-ai-episode-01-sample":
        raise ValueError("Wrong ProjectConfig for episode-one sample")
    inputs = load(artifact(run, run_path, "production-inputs-v1"))
    rows = inputs["cues"]
    if len(rows) != 7 or [row["id"] for row in rows] != [f"E1-{i:02d}" for i in range(1, 8)]:
        raise ValueError("Episode-one sample requires seven exact cues")
    if inputs["provider"] != "edge" or inputs["human_signoff"] != "not-provided":
        raise ValueError("Expected unsigned EdgeTTS sample")
    context = artifact(run, run_path, "ck3-context-clip-CASE-W")
    artifact(run, run_path, "ck3-context-source-receipt")
    ffmpeg = os.environ.get("WAR_PROMO_FFMPEG", "ffmpeg")
    ffprobe = os.environ.get("WAR_PROMO_FFPROBE", "ffprobe")
    work = Path(workdir)
    by_id = {row["id"]: row for row in rows}
    segments = []
    for row in rows:
        if not math.isfinite(row["duration_seconds"]) or row["duration_seconds"] < row["speech_duration_seconds"]:
            raise ValueError("Invalid measured narration duration")
        segments.append(SegmentDraft(
            segment_id=row["id"],
            visual_source=VisualSource(row["id"], VIDEO, Path("visuals") / (row["id"] + ".mp4"),
                                       "ck3-context" if row["id"] == "E1-01" else "sourced-teaching-card",
                                       requires_resolution=True),
            render_options=RenderOptions(2560, 1440, 30, row["duration_seconds"], preset="veryfast", crf=21),
            subtitles={"zh-CN": row["zh"], "en": row["en"]},
            prepared_narration=artifact(run, run_path, row["audio_artifact_id"]),
        ))

    def resolve_visual(source, *, workdir):
        target = Path(workdir) / source.path
        row = by_id[source.source_id]
        if source.source_id == "E1-01":
            return _context_clip(context, row, target, ffmpeg, Path(workdir))
        return _card_clip(row, target, ffmpeg, Path(workdir))

    def visual_probe(path):
        result = probe_media(ffprobe, path, audit_directory=work / "audit" / "probe" / path.stem)
        stream = result.video_streams[0]
        return VisualProbeResult("video/mp4", stream.width, stream.height)

    def subtitle_renderer(segment, narration, *, workdir):
        del narration, workdir
        return subtitle_document(by_id[segment.segment_id])

    return PipelineInvocation(
        PipelineDraft(config, tuple(segments), Path("episode-01-edge-sample-unmixed.mp4"),
                      "episode-01-edge-sample-unmixed-v1", "video/mp4"),
        PipelineDependencies(ffmpeg, subtitle_renderer, run_command, visual_probe,
                             visual_resolver=resolve_visual), work)
