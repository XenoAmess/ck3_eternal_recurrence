"""One raw desktop recorder per new CK3 capture attempt; never starts CK3.

Run this only after the managed game is loaded and the ck3-screen lease and
fresh Steam offline receipt have been checked by the operator. All files are
append-only or create-exclusive. A successful probe is not a clean span.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(path: Path) -> dict[str, Any]:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return {"path": str(path.resolve()), "bytes": path.stat().st_size,
            "sha256": h.hexdigest().upper()}


def write_new(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def append_mark(workdir: Path, row: dict[str, Any]) -> None:
    target = workdir / "marks.jsonl"
    if not target.is_file():
        raise FileNotFoundError(target)
    data = (json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    fd = os.open(target, os.O_WRONLY | os.O_APPEND)
    try:
        if os.write(fd, data) != len(data):
            raise OSError("short marks write")
        os.fsync(fd)
    finally:
        os.close(fd)


def desktop_primary_size() -> dict[str, int | bool]:
    if sys.platform != "win32":
        raise RuntimeError("gdigrab requires Windows")
    import ctypes
    import pyautogui
    user32 = ctypes.windll.user32
    gdi = (int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1)))
    automation = tuple(int(value) for value in pyautogui.size())
    return {"gdi_width": gdi[0], "gdi_height": gdi[1],
            "pyautogui_width": automation[0], "pyautogui_height": automation[1],
            "valid_and_equal": min(gdi + automation) > 0 and gdi == automation}


def bound_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return digest(path)


def run(args: argparse.Namespace) -> int:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", args.track):
        raise ValueError("track must contain only ASCII letters, digits, _ or -")
    if args.seconds <= 0 or args.seconds > 3600:
        raise ValueError("seconds must be 1..3600")
    if not args.workdir.parent.is_dir() or args.workdir.exists():
        raise FileExistsError("recorder workdir must be a new child of an existing attempt")
    if not args.session_output.is_dir():
        raise FileNotFoundError(args.session_output)
    if args.workdir.parent.resolve() != args.session_output.parent.resolve():
        raise ValueError("recorder workdir must be a child of this managed capture attempt")
    source = bound_file(args.source_save)
    receipt = bound_file(args.source_receipt)
    offline = bound_file(args.steam_offline_receipt)
    preflight_path = args.session_output / "preflight.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    bound = preflight.get("checkpoint_source") or {}
    if preflight.get("result") != "READY_FOR_BOUNDED_LIVE_ATTEMPT" or \
            str((bound.get("save") or {}).get("sha256", "")).upper() != source["sha256"] or \
            str((bound.get("receipt") or {}).get("sha256", "")).upper() != receipt["sha256"]:
        raise ValueError("live session preflight does not bind this source save and receipt")
    readback_path = args.session_output / "native-start-readback.json"
    readback = json.loads(readback_path.read_text(encoding="utf-8"))
    loaded = readback.get("source_checkpoint") or {}
    if readback.get("postcondition_verified") is not True or \
            str((loaded.get("save") or {}).get("sha256", "")).upper() != source["sha256"] or \
            str((loaded.get("receipt") or {}).get("sha256", "")).upper() != receipt["sha256"]:
        raise ValueError("managed map load does not bind this source save and receipt")
    ffmpeg = shutil.which(args.ffmpeg)
    ffprobe = shutil.which(args.ffprobe)
    if not ffmpeg or not ffprobe:
        raise FileNotFoundError("ffmpeg and ffprobe must both be installed")
    desktop = desktop_primary_size()
    args.workdir.mkdir()
    write_new(args.workdir / "geometry-admission.json", {
        "observed_at": utc(), **desktop,
        "source": "GetSystemMetrics primary display and pyautogui.size"})
    if not desktop["valid_and_equal"]:
        write_new(args.workdir / "recorder-failure.json", {
            "failed_at": utc(), "error": "desktop DPI/size mismatch before FFmpeg launch",
            "geometry_admission": digest(args.workdir / "geometry-admission.json")})
        raise RuntimeError("desktop DPI/size mismatch; new workdir and failure receipt preserved")
    raw_dir = args.workdir / "raw"
    raw_dir.mkdir()
    raw = raw_dir / (args.track + ".mkv")
    command = [ffmpeg, "-nostdin", "-n", "-hide_banner", "-loglevel", "warning",
               "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "0",
               "-i", "desktop", "-t", str(args.seconds), "-c:v", "libx264",
               "-preset", "ultrafast", "-crf", "18", "-pix_fmt", "yuv420p",
               "-an", str(raw)]
    # Create the journal before starting FFmpeg. It never gets truncated.
    (args.workdir / "marks.jsonl").open("x", encoding="utf-8").close()
    write_new(args.workdir / "recorder-intent.json", {
        "schema": "xar.war-promo.bounded-recorder-intent/v1", "created_at": utc(),
        "argv": command, "ffprobe_path": ffprobe, "workdir": str(args.workdir.resolve()),
        "session_output": str(args.session_output.resolve()),
        "session_preflight": digest(preflight_path),
        "managed_load_readback": digest(readback_path),
        "source_save": source, "source_receipt": receipt,
        "steam_offline_receipt": offline,
        "recorder_script": digest(Path(__file__)),
        "ffmpeg_executable": digest(Path(ffmpeg)),
        "ffprobe_executable": digest(Path(ffprobe)),
        "desktop_primary_width": desktop["gdi_width"],
        "desktop_primary_height": desktop["gdi_height"],
        "desktop_pyautogui_width": desktop["pyautogui_width"],
        "desktop_pyautogui_height": desktop["pyautogui_height"],
        "raw_path": str(raw.resolve()), "max_seconds": args.seconds,
        "media_policy": "native desktop pixels; no crop, scale, loop or audio"})
    start_ns = time.monotonic_ns()
    start_utc = utc()
    interrupted = False
    process: subprocess.Popen[bytes] | None = None
    with (args.workdir / "ffmpeg.stdout.bin").open("xb") as stdout, \
            (args.workdir / "ffmpeg.stderr.txt").open("xb") as stderr:
        try:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
            write_new(args.workdir / "recorder-start.json", {
                "schema": "xar.war-promo.bounded-recorder-start/v1",
                "started_at": start_utc, "monotonic_ns": start_ns,
                "pid": process.pid, "argv": command})
            append_mark(args.workdir, {"kind": "recorder-start", "utc": start_utc,
                                       "monotonic_ns": start_ns, "pid": process.pid})
            try:
                process.wait()
            except KeyboardInterrupt:
                interrupted = True
                process.terminate()
                process.wait(timeout=30)
        except BaseException as exc:
            if process is not None and process.poll() is None:
                process.terminate()
                process.wait(timeout=30)
            write_new(args.workdir / "recorder-failure.json", {
                "failed_at": utc(), "error": repr(exc),
                "pid": process.pid if process else None,
                "ffmpeg_exit_code": process.returncode if process else None,
                "raw_partial": digest(raw) if raw.is_file() else None,
                "stderr": digest(args.workdir / "ffmpeg.stderr.txt")})
            raise
    end_ns = time.monotonic_ns()
    end_utc = utc()
    ffmpeg_exit = process.returncode if process is not None else None
    append_mark(args.workdir, {"kind": "recorder-end", "utc": end_utc,
                               "monotonic_ns": end_ns, "pid": process.pid if process else None,
                               "ffmpeg_exit_code": ffmpeg_exit})
    write_new(args.workdir / "recorder-end.json", {
        "schema": "xar.war-promo.bounded-recorder-end/v1", "ended_at": end_utc,
        "monotonic_ns": end_ns, "elapsed_monotonic_seconds": (end_ns - start_ns) / 1e9,
        "ffmpeg_exit_code": ffmpeg_exit, "interrupted": interrupted,
        "raw": digest(raw) if raw.is_file() else None,
        "stderr": digest(args.workdir / "ffmpeg.stderr.txt")})
    try:
        return probe(args.workdir, ffprobe)
    except BaseException as exc:
        write_new(args.workdir / "probe-failure.json", {
            "failed_at": utc(), "error": repr(exc),
            "raw_partial": digest(raw) if raw.is_file() else None,
            "stderr": digest(args.workdir / "ffmpeg.stderr.txt")})
        raise


def user_mark(args: argparse.Namespace) -> int:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", args.kind):
        raise ValueError("mark kind must contain only ASCII letters, digits, _ or -")
    start_path = args.workdir / "recorder-start.json"
    if not start_path.is_file():
        raise FileNotFoundError(start_path)
    if (args.workdir / "recorder-end.json").exists():
        raise RuntimeError("recording has ended; use a separate review report")
    start = json.loads(start_path.read_text(encoding="utf-8"))
    now_ns = time.monotonic_ns()
    row: dict[str, Any] = {
        "kind": args.kind, "utc": utc(), "monotonic_ns": now_ns,
        "approx_seconds_from_recorder_start": (now_ns - start["monotonic_ns"]) / 1e9,
        "approx_seconds_are_not_video_pts": True,
        "date_raw": args.date_raw, "combat_id": args.combat_id,
        "war_id": args.war_id, "phase": args.phase, "note": args.note,
        "control": bound_file(args.control) if args.control else None,
        "report": bound_file(args.report) if args.report else None,
        "screenshot": bound_file(args.screenshot) if args.screenshot else None}
    if args.capture_screenshot:
        import pyautogui
        screens = args.workdir / "screens"
        screens.mkdir(exist_ok=True)
        target = screens / f"{now_ns}-{args.kind}.png"
        if target.exists():
            raise FileExistsError(target)
        pyautogui.screenshot().save(target)
        row["screenshot"] = digest(target)
    append_mark(args.workdir, row)
    print(json.dumps(row, ensure_ascii=False))
    return 0


def probe(workdir: Path, ffprobe: str | None = None) -> int:
    intent_path = workdir / "recorder-intent.json"
    end_path = workdir / "recorder-end.json"
    if not intent_path.is_file() or not end_path.is_file():
        raise FileNotFoundError("recorder intent/end receipt missing")
    intent = json.loads(intent_path.read_text(encoding="utf-8"))
    end = json.loads(end_path.read_text(encoding="utf-8"))
    raw = Path(intent["raw_path"])
    if ffprobe is None:
        ffprobe = intent["ffprobe_path"]
    command = [ffprobe, "-v", "error", "-show_streams", "-show_format",
               "-show_frames", "-of", "json", str(raw)]
    write_new(workdir / "ffprobe-command.json", command)
    probe_exit: int | None = None
    probe_error: str | None = None
    if raw.is_file():
        with (workdir / "ffprobe.json").open("xb") as stdout, \
                (workdir / "ffprobe.stderr.txt").open("xb") as stderr:
            try:
                probe_exit = subprocess.run(command, stdout=stdout, stderr=stderr,
                                            stdin=subprocess.DEVNULL, check=False).returncode
            except OSError as exc:
                probe_error = repr(exc)
    streams: list[dict[str, Any]] = []
    duration: str | None = None
    frame_pts: dict[int, dict[str, Any]] = {}
    if probe_exit == 0:
        try:
            data = json.loads((workdir / "ffprobe.json").read_text(encoding="utf-8"))
            duration = data.get("format", {}).get("duration")
            streams = [{k: stream.get(k) for k in ("index", "codec_type", "codec_name",
                        "width", "height", "start_time", "duration", "nb_frames")}
                       for stream in data.get("streams", [])]
            for frame in data.get("frames", []):
                index = frame.get("stream_index")
                if type(index) is not int:
                    continue
                row = frame_pts.setdefault(index, {"count": 0, "first_pts_time": None,
                                                   "last_pts_time": None,
                                                   "first_frame_width": None,
                                                   "first_frame_height": None})
                row["count"] += 1
                pts = frame.get("best_effort_timestamp_time") or frame.get("pts_time")
                if row["first_pts_time"] is None:
                    row["first_pts_time"] = pts
                    row["first_frame_width"] = frame.get("width")
                    row["first_frame_height"] = frame.get("height")
                row["last_pts_time"] = pts
        except (OSError, ValueError, TypeError) as exc:
            probe_error = repr(exc)
            probe_exit = None
    video = [s for s in streams if s["codec_type"] == "video"]
    exact_size = (len(video) == 1 and
                  video[0]["width"] == intent["desktop_primary_width"] and
                  video[0]["height"] == intent["desktop_primary_height"])
    video_frames = frame_pts.get(video[0]["index"], {}) if len(video) == 1 else {}
    first_frame_size_match = (video_frames.get("first_frame_width") == intent["desktop_primary_width"]
                              and video_frames.get("first_frame_height") == intent["desktop_primary_height"])
    try:
        duration_seconds = float(duration) if duration is not None else 0.0
    except ValueError:
        duration_seconds = 0.0
    pts_complete = (video_frames.get("count", 0) > 0 and
                    video_frames.get("first_pts_time") is not None and
                    video_frames.get("last_pts_time") is not None and
                    duration_seconds > 0)
    result = "ENCODED_UNREVIEWED" if (end["ffmpeg_exit_code"] == 0 and
             probe_exit == 0 and exact_size and first_frame_size_match
             and pts_complete and raw.is_file()) else "RED_PRESERVED"
    final = {
        "schema": "xar.war-promo.bounded-recorder-final/v1", "created_at": utc(),
        "result": result, "clean_spans_certified": False,
        "human_review_completed": False, "ffmpeg_exit_code": end["ffmpeg_exit_code"],
        "ffprobe_exit_code": probe_exit, "ffprobe_error": probe_error,
        "raw": digest(raw) if raw.is_file() else None,
        "ffprobe_output": digest(workdir / "ffprobe.json") if (workdir / "ffprobe.json").is_file() else None,
        "ffprobe_stderr": digest(workdir / "ffprobe.stderr.txt") if raw.is_file() else None,
        "format_duration_seconds": duration, "streams": streams,
        "frame_pts_by_stream": frame_pts, "native_desktop_size_match": exact_size,
        "first_frame_size_match": first_frame_size_match,
        "video_pts_complete": pts_complete,
        "marks": digest(workdir / "marks.jsonl")}
    write_new(workdir / "recorder-final.json", final)
    print(json.dumps(final, ensure_ascii=False))
    return 0 if result == "ENCODED_UNREVIEWED" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    record = sub.add_parser("record", help="create a new workdir and run one 600s native desktop recorder")
    record.add_argument("--workdir", type=Path, required=True)
    record.add_argument("--track", required=True)
    record.add_argument("--seconds", type=int, default=600)
    record.add_argument("--session-output", type=Path, required=True)
    record.add_argument("--source-save", type=Path, required=True)
    record.add_argument("--source-receipt", type=Path, required=True)
    record.add_argument("--steam-offline-receipt", type=Path, required=True)
    record.add_argument("--ffmpeg", default="ffmpeg")
    record.add_argument("--ffprobe", default="ffprobe")
    mark = sub.add_parser("mark", help="append a wall-clock anchor and source file hashes")
    mark.add_argument("--workdir", type=Path, required=True)
    mark.add_argument("--kind", required=True)
    mark.add_argument("--date-raw", type=int)
    mark.add_argument("--combat-id", type=int)
    mark.add_argument("--war-id", type=int)
    mark.add_argument("--phase")
    mark.add_argument("--note")
    mark.add_argument("--control", type=Path)
    mark.add_argument("--report", type=Path)
    mark.add_argument("--screenshot", type=Path)
    mark.add_argument("--capture-screenshot", action="store_true")
    args = parser.parse_args()
    if args.command == "record":
        return run(args)
    if args.command == "mark":
        if args.screenshot and args.capture_screenshot:
            parser.error("choose either --screenshot or --capture-screenshot")
        return user_mark(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
