"""E04 eight-theme plans and separately admitted, serial public-API producer.

Default plan-only mode creates no media. Production requires an exact future
phase card; this source-only delivery grants no execution or human approval.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from pathlib import Path
import json
import re

from xar_promo.render import (
    GeneratedTextFile, RenderOptions, RenderPlan, plan_concat, plan_render,
)

FPS = 30
CARD_SECONDS = 6
METHOD_FRAMES = 58406
MACHINE = "desktop-3fevhd2-1c74096080"
ACCEPTED: tuple[tuple[str, int, int], ...] = (
    ("R03", 0, 40), ("R04", 0, 30), ("R06", 0, 33),
    ("R07", 32, 52), ("R09", 0, 15), ("R11", 0, 20),
    ("R12", 0, 34), ("R13", 0, 30),
)


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("string key required")
        result[key] = item
    return result


def sequence(value: object) -> tuple[object, ...]:
    if not isinstance(value, list):
        raise ValueError("array required")
    return tuple(value)


def text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("string required")
    return value


def integer(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("integer required")
    return value


def decimal_string(value: object) -> str:
    result = text(value)
    need(re.fullmatch(r"0|[1-9][0-9]*", result) is not None,
         "canonical unsigned decimal string required")
    return result


@dataclass(frozen=True)
class Identity:
    bytes: int
    mtime_ns: str
    st_dev: str
    st_ino: str

    @classmethod
    def parse(cls, value: object) -> Identity:
        row = mapping(value)
        return cls(integer(row["bytes"]), decimal_string(row["mtime_ns"]),
                   decimal_string(row["st_dev"]), decimal_string(row["st_ino"]))

    def verify(self, path: Path) -> None:
        found = path.stat()
        need((found.st_size, str(found.st_mtime_ns), str(found.st_dev),
              str(found.st_ino)) ==
             (self.bytes, self.mtime_ns, self.st_dev, self.st_ino),
             "input stat identity changed: " + str(path))


@dataclass(frozen=True)
class Asset:
    path: Path
    bytes: int
    retained_sha256: str
    identity: Identity

    @classmethod
    def parse(cls, value: object) -> Asset:
        row = mapping(value)
        digest = text(row["retained_sha256"])
        need(re.fullmatch(r"[0-9a-f]{64}", digest) is not None, "bad source digest")
        asset = cls(Path(text(row["path"])), integer(row["bytes"]),
                    digest, Identity.parse(row["fresh_stat"]))
        need(asset.bytes == asset.identity.bytes, "source size mismatch")
        return asset


@dataclass(frozen=True)
class Clip:
    theme: str
    start: int
    stop: int
    source: Asset
    title: str
    chinese: tuple[str, ...]
    english: str

    @classmethod
    def parse(cls, value: object) -> Clip:
        row = mapping(value)
        bounds = sequence(row["accepted_seconds_half_open"])
        need(len(bounds) == 2, "two bounds required")
        need(row.get("speed") == "1/1", "retiming not admitted")
        need(row.get("root_formal_source_accepted") is True, "Root source missing")
        chinese = tuple(text(item) for item in sequence(row["caption_zh"]))
        need(1 <= len(chinese) <= 3, "one to three caption lines")
        clip = cls(text(row["theme"]), integer(bounds[0]), integer(bounds[1]),
                   Asset.parse(row["source"]), text(row["title_zh"]),
                   chinese, text(row["caption_en"]))
        need(clip.stop > clip.start >= 0, "bad source span")
        for line in (clip.title, *clip.chinese, clip.english):
            need("\n" not in line and "\r" not in line and
                 "{" not in line and "}" not in line and "\\" not in line,
                 "caption must be plain one-line text")
        return clip

    @property
    def source_seconds(self) -> int:
        return self.stop - self.start

    @property
    def render_seconds(self) -> int:
        return self.source_seconds + CARD_SECONDS


@dataclass(frozen=True)
class Timeline:
    method: Asset
    music: Asset
    clips: tuple[Clip, ...]
    existing_r04_render: Asset

    @classmethod
    def parse(cls, value: object) -> Timeline:
        row = mapping(value)
        need(row.get("schema") == "xar.e04.formal8-timeline.v1", "wrong timeline")
        need(row.get("machine_id") == MACHINE, "wrong source machine")
        need(integer(row.get("card_seconds")) == CARD_SECONDS, "card clock changed")
        need(integer(row.get("method_frames")) == METHOD_FRAMES, "method clock changed")
        need(integer(row.get("frame_rate")) == FPS, "frame clock changed")
        clips = tuple(Clip.parse(item) for item in sequence(row["clips"]))
        need(tuple((c.theme, c.start, c.stop) for c in clips) == ACCEPTED,
             "selected Root-approved spans or order changed")
        return cls(Asset.parse(row["method"]), Asset.parse(row["music"]), clips,
                   Asset.parse(row["existing_r04_render"]))

    @property
    def new_frames(self) -> int:
        return sum(c.render_seconds for c in self.clips) * FPS

    def verify_inputs_stat_only(self) -> None:
        for asset in (self.method, self.music, self.existing_r04_render,
                      *(c.source for c in self.clips)):
            asset.identity.verify(asset.path)


@dataclass(frozen=True)
class Composition:
    renders: tuple[RenderPlan, ...]
    concat: RenderPlan
    total_video_frames: int


def ass_time(seconds: int) -> str:
    return f"{seconds // 3600}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}.00"


def captions(clip: Clip) -> str:
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Chinese,Microsoft YaHei,32,&H00F0E3CD,&H00FFFFFF,&H00211813,&H00211813,0,0,0,0,100,100,0,0,1,1,0,7,0,0,0,1
Style: English,Arial,24,&H00E2D7C4,&H00FFFFFF,&H00211813,&H00211813,0,0,0,0,100,100,0,0,1,1,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    end = ass_time(clip.source_seconds)
    card_end = ass_time(clip.render_seconds)

    def event(start: str, stop: str, style: str, x: int, y: int,
              body: str, size: int) -> str:
        override = f"{{\\an7\\pos({x},{y})\\fs{size}}}"
        return f"Dialogue: 0,{start},{stop},{style},,0,0,0,,{override}{body}\n"

    lines.append(event("0:00:00.00", end, "Chinese", 192, 875,
                       clip.title + " | 独立回放 / 源镜头原速", 30))
    for index, line in enumerate(clip.chinese):
        lines.append(event("0:00:00.00", end, "Chinese", 192,
                           916 + index * 35, line, 28))
    lines.append(event("0:00:00.00", end, "English", 192, 1030,
                       clip.english, 22))
    lines.append(event(end, card_end, "Chinese", 150, 220, clip.title, 42))
    for index, line in enumerate(clip.chinese):
        lines.append(event(end, card_end, "Chinese", 150,
                           310 + index * 64, line, 36))
    lines.append(event(end, card_end, "English", 150, 580, clip.english, 28))
    lines.append(event(end, card_end, "Chinese", 150, 720,
                       "本段为独立实证补充；不与相邻回放拼成同一因果。", 30))
    return "".join(lines)


def patch_render(plan: RenderPlan, clip: Clip) -> RenderPlan:
    need(len(plan.commands) == 1, "one public render command expected")
    command = plan.commands[0]
    argv = list(command.spec.argv)
    index = argv.index("-filter_complex") + 1
    graph = str(argv[index])
    total = f"{clip.render_seconds:.6f}"
    raw = f"{clip.source_seconds:.6f}"
    initial = "[0:v]trim=duration=" + total
    tail = "tpad=stop_mode=clone:stop_duration=" + total
    scale = "scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos"
    pad = "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x211813"
    for seam in (initial, tail, scale, pad, "[1:a]"):
        need(graph.count(seam) == 1, "public filtergraph seam changed: " + seam)
    graph = graph.replace(initial, "[0:v]trim=duration=" + raw, 1)
    graph = graph.replace(tail,
        "tpad=stop_mode=add:stop_duration=6.000000:color=0x211813", 1)
    graph = graph.replace(scale,
        "scale=1536:864:force_original_aspect_ratio=decrease:flags=lanczos", 1)
    graph = graph.replace(pad, "pad=1920:1080:192:0:color=0x211813", 1)
    graph = graph.replace("[1:a]",
        "[1:a]volume=-17dB,afade=t=in:st=0:d=1,"
        f"afade=t=out:st={clip.render_seconds - 2}:d=2,", 1)
    argv[index] = graph
    argv[1:1] = ["-threads", "1", "-filter_complex_threads", "1"]
    argv[-1:-1] = [
        "-threads:v", "1", "-frames:v", str(clip.render_seconds * FPS),
        "-profile:v", "high", "-level:v", "4.0",
        "-video_track_timescale", "15360",
        "-maxrate", "4M", "-bufsize", "8M",
    ]
    return replace(plan, commands=(
        replace(command, spec=replace(command.spec, argv=tuple(argv))),))


def compose(timeline: Timeline, *, workdir: Path, ffmpeg: Path,
            evidence_only: bool = False) -> Composition:
    """Return public plans only; no file creation, probe or subprocess."""
    need(workdir.is_absolute(), "future work root must be absolute")
    renders: list[RenderPlan] = []
    segments: list[Path] = [] if evidence_only else [timeline.method.path]
    for clip in timeline.clips:
        if clip.theme == "R04":
            segments.append(timeline.existing_r04_render.path)
            continue
        output = workdir / ("segment-" + clip.theme + ".mp4")
        ass = workdir / ("captions-" + clip.theme + ".ass")
        plan = plan_render(
            ffmpeg=ffmpeg, video_input=clip.source.path,
            audio_input=timeline.music.path,
            partial_output=output.with_suffix(".partial.mp4"),
            final_output=output,
            audit_directory=workdir / "audit" / clip.theme,
            options=RenderOptions(
                1920, 1080, FPS, float(clip.render_seconds),
                preset="veryfast", crf=21, audio_bitrate="192k",
                pad_color="0x211813"),
            ass_path=ass, start_seconds=float(clip.start),
            working_directory=workdir)
        plan = patch_render(plan, clip)
        plan = replace(plan, generated_files=(
            GeneratedTextFile(ass, captions(clip)),))
        renders.append(plan)
        segments.append(plan.final_output)
    concat = plan_concat(
        ffmpeg=ffmpeg,
        segment_paths=tuple(segments),
        concat_path=workdir / "formal8.ffconcat",
        partial_output=workdir / "formal8-review.partial.mp4",
        final_output=workdir / ("E04-FORMAL8-EVIDENCE-270s-REVIEW-a01.mp4"
            if evidence_only else "E04-METHOD69-PLUS-FORMAL8-REVIEW-a01.mp4"),
        audit_directory=workdir / "audit" / "concat",
        working_directory=workdir)
    return Composition(tuple(renders), concat,
                       (0 if evidence_only else METHOD_FRAMES) + timeline.new_frames)


def describe_plan(plan: RenderPlan) -> dict[str, object]:
    return {
        "commands": [
            {"argv": [str(arg) for arg in command.spec.argv],
             "audit_directory": str(command.audit_directory)}
            for command in plan.commands
        ],
        "generated_files": [
            {"path": str(item.path), "content": item.content,
             "encoding": item.encoding} for item in plan.generated_files],
        "partial_output": str(plan.partial_output),
        "final_output": str(plan.final_output),
    }


def describe(composition: Composition) -> dict[str, object]:
    return {
        "status": "PLAN_ONLY_NO_MEDIA_PROCESS_NO_OUTPUT_ROOT",
        "total_video_frames_predicted": composition.total_video_frames,
        "frame_rate": FPS,
        "video_clock_seconds_predicted": composition.total_video_frames / FPS,
        "container_duration_is_not_yet_measured": True,
        "renders": [describe_plan(plan) for plan in composition.renders],
        "concat": describe_plan(composition.concat),
        "existing_method_reencoded": False,
        "existing_R04_36s_render_reencoded": False,
        "newly_rendered_theme_count": len(composition.renders),
        "human_1x": False,
        "signoff": False,
        "new_formal_credit": 0,
        "execution_admission": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--future-workdir", type=Path, required=True)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--plan-only", action="store_true", required=True)
    parser.add_argument("--evidence-only", action="store_true")
    args = parser.parse_args()
    timeline_path: Path = args.timeline
    workdir: Path = args.future_workdir
    ffmpeg: Path = args.ffmpeg
    value: object = json.loads(timeline_path.read_text(encoding="utf-8-sig"))
    timeline = Timeline.parse(value)
    timeline.verify_inputs_stat_only()
    need(not workdir.exists(), "future media work root must remain absent")
    result = describe(compose(timeline, workdir=workdir, ffmpeg=ffmpeg,
                              evidence_only=args.evidence_only))
    print(json.dumps(result, ensure_ascii=False, indent=2))


def produce_phase() -> None:
    """One separately admitted serial step. No media effects in plan-only mode.

    Each completed step returns immutable-payload pins for the capacity owner.
    Evidence-only holds its entire future budget to final closure; no active
    or immutable bytes create credit. Full-review accounting is separate.
    """
    import datetime
    import hashlib
    import os
    import stat
    import subprocess
    from xar_promo.render import execute_render_plan
    from xar_promo.process import CommandSpec, CommandResult, run_command
    from xar_promo.operations import initialize_project, preserve_artifact
    from xar_promo.project import artifact_path
    from xar_promo.runlog import append_phase_record

    parser = argparse.ArgumentParser()
    parser.add_argument("--produce-phase", required=True,
        choices=["R03", "R06", "R07", "R09", "R11", "R12", "R13", "concat", "final-CAS"])
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--admission-sha", required=True)
    parser.add_argument("--evidence-only", action="store_true")
    args = parser.parse_args()
    phase: str = args.produce_phase
    timeline_path: Path = args.timeline
    root: Path = args.output_root
    ffmpeg: Path = args.ffmpeg
    admission_path: Path = args.admission
    admission_sha: str = args.admission_sha
    evidence_only: bool = args.evidence_only

    def pin(path: Path) -> dict[str, object]:
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest}

    def total() -> int:
        return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())

    need(pin(admission_path)["sha256"] == admission_sha, "Admission pin changed")
    cap = mapping(json.loads(admission_path.read_text(encoding="utf-8")))
    need(cap.get("machine_id") == MACHINE and cap.get("budget_status") == "GREEN", "No actual GREEN")
    need(cap.get("media_render_execution_admitted") is True, "Source-only card refuses execution")
    need(cap.get("source_bound_media_execution_admitted") is True, "No source-bound media permission")
    need(cap.get("evidence_only") is evidence_only, "Wrong composition mode")
    if evidence_only:
        need(cap.get("full_192MiB_future_held_until_closed") is True,
             "Evidence chapter requires full future held to closure")
    need(cap.get("phase") == phase and Path(text(cap.get("aggregate_root"))).resolve() == root.resolve(), "Wrong phase/root")
    need(cap.get("timeline_sha256") == pin(timeline_path)["sha256"] and
         cap.get("producer_sha256") == pin(Path(__file__))["sha256"], "Source pins differ")
    deadline = datetime.datetime.fromisoformat(text(cap.get("hard_deadline_utc")).replace("Z", "+00:00"))
    need(datetime.datetime.now(datetime.timezone.utc) < deadline, "Expired media card")
    ceiling = integer(cap.get("aggregate_ceiling_bytes"))
    need(ceiling <= (201326592 if evidence_only else 402653184), "Recipe ceiling exceeded")
    order = ["R03", "R06", "R07", "R09", "R11", "R12", "R13", "concat", "final-CAS"]
    index = order.index(phase)
    if index:
        previous = root / ("CLOSED-" + order[index - 1] + ".json")
        need(previous.is_file(), "Previous original step not closed")
        need(cap.get("previous_closed_receipt_sha256") == pin(previous)["sha256"], "Closed-byte accounting ack missing")
        if evidence_only:
            need(cap.get("full_192MiB_future_held_until_closed") is True,
                 "Evidence chapter requires full future held to closure")
        else:
            need(cap.get("previous_immutable_payloads_accounted") is True,
                 "Full review needs separately acknowledged closed-payload accounting")
    work = root / "work"
    run = root / "native" / "runs" / "review-a01" / "run-manifest.json"
    need(not (root / ("ONCE-" + phase + ".json")).exists(), "Unknown/previous phase; no replay")
    value: object = json.loads(timeline_path.read_text(encoding="utf-8-sig"))
    timeline = Timeline.parse(value)
    timeline.verify_inputs_stat_only()
    root.mkdir(parents=True, exist_ok=True)
    temporary = root / "temp"
    temporary.mkdir(exist_ok=True)
    with (root / ("ONCE-" + phase + ".json")).open("x", encoding="utf-8") as stream:
        json.dump({"phase": phase, "admission": pin(admission_path), "timeline": pin(timeline_path)}, stream)
    if not index:
        need(not work.exists() and not run.exists(), "Stale work/run")
        work.mkdir()
        initialize_project(root / "native", project_id="e04-formal8-review",
            title="E04 method plus eight bounded source chapters", narration_locale="zh-CN",
            subtitle_locales=["zh-CN", "en"], adapter="ck3", preset="e04-formal8-review", run_id="review-a01")
        preserve_artifact(run, timeline_path, artifact_id="formal8.timeline", collection="derived",
            role="timeline-intent", label="Frozen eight-theme intent", media_type="application/json")
    composition = compose(timeline, workdir=work, ffmpeg=ffmpeg,
                          evidence_only=evidence_only)

    def bounded_command(spec: CommandSpec, *, audit_directory: Path) -> CommandResult:
        """Public audit format, with original Popen custody and finite guards."""
        def bounded_run(argv: list[str], *, cwd: str | None,
                        env: dict[str, str] | None, shell: bool, check: bool,
                        stdout: int, stderr: int, text: bool,
                        encoding: str, errors: str) -> subprocess.CompletedProcess[str]:
            need(not shell and not check and text, "Unexpected public runner protocol")
            process = subprocess.Popen(argv, cwd=cwd, env=env, shell=False,
                stdout=stdout, stderr=stderr, text=True, encoding=encoding,
                errors=errors, creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            stopped = False
            try:
                while True:
                    active_segments = sum(path.stat().st_size for path in work.glob("segment-*.mp4"))
                    active_final = next((path.stat().st_size for path in spec.partial_artifacts
                                         if phase == "concat" and path.is_file()), 0)
                    final_bound = ((0 if evidence_only else timeline.method.bytes) +
                        timeline.existing_r04_render.bytes + 41943040 +
                        (3145728 if evidence_only else 8388608))
                    if (datetime.datetime.now(datetime.timezone.utc) >= deadline or
                        total() >= ceiling - 1048576 or active_segments >= 41943040 or
                        active_final > final_bound):
                        stopped = True
                        process.terminate()
                    try:
                        out, err = process.communicate(timeout=0.25 if not stopped else 5)
                        break
                    except subprocess.TimeoutExpired:
                        if stopped:
                            process.kill()
                            out, err = process.communicate()
                            break
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            with (audit_directory / "original-popen.json").open("x", encoding="utf-8") as stream:
                json.dump({"pid": process.pid, "original_wait_returncode": process.wait(),
                           "guard_stopped": stopped, "no_replay": True,
                           "machine_id": MACHINE}, stream)
            return subprocess.CompletedProcess(argv, process.returncode if not stopped else -1, out, err)
        environment = dict(os.environ)
        environment.update(TMP=str(temporary), TEMP=str(temporary), PYTHONDONTWRITEBYTECODE="1")
        return run_command(spec, audit_directory=audit_directory,
                           environment=environment, run=bounded_run)

    immutable: list[dict[str, object]] = []
    if phase in order[:7]:
        plan = next(plan for plan in composition.renders if plan.final_output.name == "segment-" + phase + ".mp4")
        execute_render_plan(plan, command_runner=bounded_command)
        plan.final_output.chmod(stat.S_IREAD)
        immutable.append(pin(plan.final_output))
        segment_bytes = sum(path.stat().st_size for path in work.glob("segment-*.mp4"))
        need(segment_bytes <= 41943040, "Actual new segments exceed40MiB; stop without quality reduction/retry")
        record = preserve_artifact(run, plan.final_output, artifact_id="segment." + phase,
            collection="derived", role="intermediate-segment", label=phase, media_type="video/mp4")
        stored = artifact_path(record, run.parent)
        stored.chmod(stat.S_IREAD)
        immutable.append(pin(stored))
    elif phase == "concat":
        segment_bytes = sum(path.stat().st_size for path in work.glob("segment-*.mp4"))
        need(segment_bytes <= 41943040 and len(list(work.glob("segment-*.mp4"))) == 7, "Seven immutable segments required")
        # Count retained work+segment CAS and allow both active mux and future final CAS.
        upper = ((0 if evidence_only else timeline.method.bytes) +
                 timeline.existing_r04_render.bytes + segment_bytes +
                 (3145728 if evidence_only else 8388608))
        need(total() + 2 * upper + 16777216 <= ceiling, "Concat/CAS/QA complete peak does not fit")
        execute_render_plan(composition.concat, command_runner=bounded_command)
        composition.concat.final_output.chmod(stat.S_IREAD)
        immutable.append(pin(composition.concat.final_output))
    else:
        final = composition.concat.final_output
        need(final.is_file(), "Closed concat missing")
        need(total() + final.stat().st_size + 16777216 <= ceiling, "Native CAS copy plus QA headroom does not fit")
        record = preserve_artifact(run, final, artifact_id="formal8.review.movie", collection="derived",
            role="deliverable", label="Formal8 REVIEW pending QA and human review", media_type="video/mp4")
        stored = artifact_path(record, run.parent)
        stored.chmod(stat.S_IREAD)
        immutable.append(pin(stored))
    need(total() <= ceiling, "Aggregate hard cap")
    append_phase_record(run, phase_id="formal8." + phase, status="succeeded",
        detail="Original public render/preserve returned. Automated AV/PTS QA and human review remain pending.")
    receipt = {"machine_id": MACHINE, "phase": phase, "closed_immutable_payloads": immutable,
        "closed_immutable_bytes_consumption_request": (0 if evidence_only else
            sum(integer(item["bytes"]) for item in immutable)),
        "active_bytes_consumed": 0, "aggregate_actual_bytes": total(), "remaining_owned_media_processes": 0,
        "evidence_only": evidence_only, "full_future_held_until_closed": evidence_only,
        "new_formal_credit": 0, "AV_PTS_QA": "pending", "human1x": False, "signoff": False,
        "capacity_owner_ack_required_before_next_phase": True, "no_retry": True}
    with (root / ("CLOSED-" + phase + ".json")).open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2)
    print(json.dumps(receipt))


if __name__ == "__main__":
    import sys
    if "--produce-phase" in sys.argv:
        produce_phase()
    else:
        main()
