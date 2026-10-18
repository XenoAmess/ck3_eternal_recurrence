#!/usr/bin/env python3
"""Render an existing campaign score JSON as a silent PNG and/or 60-second MP4."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
from xar_autoplayer import campaign_score_presentation_v1 as presentation

MIB = 1024**2
PNG_CAP = 6 * MIB
VIDEO_CAP = 256 * MIB
PIPE_LOG_CAP = MIB


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def identity(path: Path) -> dict:
    st = path.stat()
    return {"bytes": st.st_size, "mtime_ns": st.st_mtime_ns,
            "device": st.st_dev, "inode": st.st_ino}


def new_path(path: Path | None, suffix: str) -> Path | None:
    if path is None:
        return None
    result = path.resolve()
    need(result.suffix.lower() == suffix, f"Expected {suffix} output")
    need(not result.exists() and result.parent.is_dir(), "Output must be new, with an existing parent")
    return result


def command(ffmpeg: str, output: Path) -> list[str]:
    return [ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-nostats", "-n",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-video_size", "2560x1440",
            "-framerate", "30", "-i", "pipe:0", "-an", "-sn", "-dn", "-map_metadata", "-1",
            "-vf", "scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-threads:v", "2",
            "-maxrate", "16M", "-bufsize", "32M", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
            "-video_track_timescale", "15360", "-avoid_negative_ts", "disabled",
            "-movflags", "+faststart", "-frames:v", str(presentation.FRAMES),
            "-progress", "pipe:1", "-fs", str(VIDEO_CAP), str(output)]


def render_video(report: dict, args, output: Path) -> dict:
    executable = shutil.which(args.ffmpeg)
    need(executable is not None, "FFmpeg executable was not found")
    argv = command(executable, output)
    flags = (subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS) if os.name == "nt" else 0
    child = None
    threads: list[threading.Thread] = []
    errors: list[str] = []
    stdout, stderr = bytearray(), bytearray()
    sent_frames = 0
    forced = False
    started = time.monotonic()

    def feed() -> None:
        nonlocal sent_frames
        try:
            for frame in range(presentation.FRAMES):
                image = presentation.draw_score_frame(report, frame, args.font, args.bold_font,
                                                     campaign_title=args.title)
                rgb = image.tobytes()
                image.close()
                need(len(rgb) == 2560 * 1440 * 3, "A complete native RGB frame is required")
                remaining = memoryview(rgb)
                while remaining:
                    n = child.stdin.write(remaining)
                    need(n is not None and n > 0, "RGB pipe made no progress")
                    remaining = remaining[n:]
                sent_frames += 1
            child.stdin.close()
        except BaseException as exc:
            errors.append("frame pipe: " + str(exc))

    def drain(stream, target) -> None:
        try:
            while chunk := stream.read(65536):
                target.extend(chunk)
                need(len(target) <= PIPE_LOG_CAP, "FFmpeg log exceeded its bounded pipe")
        except BaseException as exc:
            errors.append("output pipe: " + str(exc))

    try:
        child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, bufsize=0, creationflags=flags)
        threads = [threading.Thread(target=feed, daemon=True),
                   threading.Thread(target=drain, args=(child.stdout, stdout), daemon=True),
                   threading.Thread(target=drain, args=(child.stderr, stderr), daemon=True)]
        for thread in threads:
            thread.start()
        while child.poll() is None:
            need(time.monotonic() - started <= args.timeout, "Score render exceeded the timeout")
            need(not errors, "; ".join(errors))
            if output.exists():
                need(output.stat().st_size <= VIDEO_CAP, "Score video exceeded 256 MiB")
            time.sleep(.1)
        child.wait(timeout=5)
    finally:
        if child is not None:
            if child.poll() is None:
                forced = True
                child.kill()
            child.wait(timeout=5)
            for thread in threads:
                thread.join(timeout=5)
    need(child is not None and child.returncode == 0 and not forced and not errors
         and not any(thread.is_alive() for thread in threads),
         "Score video did not finish normally: " + stderr.decode("utf-8", "replace")[-2000:])
    progress = dict(line.split("=", 1) for line in stdout.decode("utf-8").splitlines() if "=" in line)
    need(sent_frames == presentation.FRAMES and progress.get("progress") == "end"
         and int(progress.get("frame", -1)) == presentation.FRAMES,
         "FFmpeg did not acknowledge all 1800 frames")
    need(output.stat().st_size <= VIDEO_CAP, "Score video exceeded its final cap")
    return {"argv": argv, "actual_exit_code": child.returncode, "forced_own_child": forced,
            "frames_sent": sent_frames, "progress": progress,
            "ffmpeg_stderr": stderr.decode("utf-8", "replace"),
            "CPU_priority": "BELOW_NORMAL_PRIORITY_CLASS" if os.name == "nt" else "inherited",
            "audio_tracks_requested": 0, "production_film_qualification_claimed": False}


def check() -> None:
    report = presentation.synthetic_report()
    presentation.validate_report(report)
    need(presentation.storyboard(report)[-1]["end_frame"] == 1800, "Finite storyboard")
    need(presentation.format_interval({"lower": "1.234", "upper": "9.876", "value": None}) == "1.2–9.9",
         "Intervals must round outward")
    need(presentation.format_number("1.25") == "≈1.3", "Rounded exact values must be marked")
    report["scores"]["L"]["value"] = "50"
    try:
        presentation.validate_report(report)
    except ValueError:
        pass
    else:
        raise AssertionError("An invented midpoint was accepted")
    print(json.dumps({"status": "PASS_PURE_PRESENTATION_CHECK", "media_or_output_calls": 0}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="Existing campaign-development-score/v1 JSON")
    parser.add_argument("--image", type=Path, help="New PNG, 2560x1440")
    parser.add_argument("--video", type=Path, help="New silent MP4, 60 seconds, 30 fps")
    parser.add_argument("--ffmpeg", help="FFmpeg executable; required with --video")
    parser.add_argument("--font", type=Path, help="Regular font containing the report's Chinese glyphs")
    parser.add_argument("--bold-font", type=Path, help="Bold Chinese font")
    parser.add_argument("--title", default="战役发展报告")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--receipt", type=Path, help="Optional new JSON render receipt")
    parser.add_argument("--check", action="store_true", help="Pure contract/rounding check; no Pillow or media")
    args = parser.parse_args()
    if args.check:
        check()
        return
    need(args.report is not None and (args.image or args.video), "Provide --report and --image and/or --video")
    need(args.font is not None and args.bold_font is not None, "Provide both Chinese font paths")
    need(not args.video or args.ffmpeg, "Provide --ffmpeg for a video")
    need(1 <= args.timeout <= 7200, "Timeout must be between 1 and 7200 seconds")
    image_path, video_path = new_path(args.image, ".png"), new_path(args.video, ".mp4")
    receipt_path = new_path(args.receipt, ".json")
    report_path = args.report.resolve()
    need(report_path not in (image_path, video_path, receipt_path), "Input report cannot be an output")
    with report_path.open("rb") as stream:
        payload = stream.read(4 * MIB + 1)
    need(len(payload) <= 4 * MIB, "Report exceeds 4 MiB")
    report = presentation.validate_report(json.loads(payload))
    inputs = {str(path.resolve()): identity(path.resolve()) for path in (args.font, args.bold_font)}
    # This helper reads the execution machine identity without allocating a game/run identity.
    from ck3_live_run_id import current_machine_id
    machine_id = current_machine_id()
    result = {"schema": "xar.ck3.campaign-score-presentation-render/v1", "machine_id": machine_id,
              "observed_at_utc": datetime.now(timezone.utc).isoformat(),
              "input_report": {"path": str(report_path), "bytes": len(payload),
                               "sha256": hashlib.sha256(payload).hexdigest()},
              "font_inputs": inputs, "qualification": report["qualification"],
              "silent_graphics_only": True, "production_film_qualification_claimed": False}
    if image_path:
        try:
            from PIL.PngImagePlugin import PngInfo
        except ImportError as exc:
            raise RuntimeError("Pillow is required for score images; install it in the selected Python environment") from exc
        image = presentation.draw_score_frame(report, 1799, args.font, args.bold_font,
                                             summary=True, campaign_title=args.title)
        metadata = PngInfo()
        metadata.add_text("machine_id", machine_id)
        metadata.add_text("score_report_sha256", result["input_report"]["sha256"])
        output = BytesIO()
        image.save(output, format="PNG", pnginfo=metadata, compress_level=6)
        image.close()
        data = output.getvalue()
        need(len(data) <= PNG_CAP, "Score PNG exceeded 6 MiB")
        with image_path.open("xb") as stream:
            stream.write(data)
        result["image"] = {"path": str(image_path), "bytes": len(data),
                           "sha256": hashlib.sha256(data).hexdigest()}
    if video_path:
        result["video_render"] = render_video(report, args, video_path)
        result["video"] = {"path": str(video_path), **identity(video_path)}
    need(all(identity(Path(path)) == stat for path, stat in inputs.items()), "A font input changed during rendering")
    result.update(status="PRESENTATION_RENDERED_NOT_FILM_QUALIFIED",
                  completed_at_utc=datetime.now(timezone.utc).isoformat())
    if receipt_path:
        with receipt_path.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
