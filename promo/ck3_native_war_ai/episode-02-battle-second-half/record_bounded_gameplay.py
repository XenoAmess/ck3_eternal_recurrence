"""Request one capture-owned raw desktop recorder; never starts CK3.

Run this only after the managed hot service is ready and the ck3-screen lease and
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
import threading
import uuid
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
    if args.seconds != 600:
        raise ValueError("managed gameplay recorder requires exactly 600 seconds")
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
    ffmpeg, ffprobe = str(Path(ffmpeg).resolve()), str(Path(ffprobe).resolve())
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
    request = {"action": "gameplay_recorder", "operation": "start",
               "workdir": str(args.workdir.resolve())}
    try:
        state = managed_request(args.session_output, request, timeout=60)
        if state.get("state") != "RECORDING":
            raise RuntimeError("managed recorder did not start")
        deadline = time.monotonic() + args.seconds + 90
        while state.get("state") == "RECORDING":
            if time.monotonic() >= deadline:
                raise TimeoutError("managed recorder exceeded its bounded duration")
            time.sleep(2)
            state = managed_request(args.session_output,
                {**request, "operation": "status"}, timeout=60)
        if state.get("state") != "NORMAL_TREE_EMPTY":
            raise RuntimeError("managed recorder cleanup is not NORMAL_TREE_EMPTY")
    except BaseException as exc:
        try:
            managed_request(args.session_output, {**request, "operation": "abort"}, timeout=60)
        except BaseException:
            pass  # Capture supervisor still owns the Job and lease-loss cleanup.
        write_new(args.workdir / "recorder-failure.json", {
            "failed_at": utc(), "error": repr(exc),
            "raw_partial": digest(raw) if raw.is_file() else None,
            "managed_request": request})
        raise
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
    job = json.loads((workdir / "recorder-job-terminal.json").read_text(encoding="utf-8"))
    result = "ENCODED_UNREVIEWED" if (job.get("state") == "NORMAL_TREE_EMPTY" and
             not (workdir / "unsafe-recorder-cleanup.json").exists() and end["ffmpeg_exit_code"] == 0 and
             probe_exit == 0 and exact_size and first_frame_size_match
             and pts_complete and raw.is_file()) else "RED_PRESERVED"
    final = {
        "schema": "xar.war-promo.bounded-recorder-final/v1", "created_at": utc(),
        "result": result, "clean_spans_certified": False,
        "human_review_completed": False, "ffmpeg_exit_code": end["ffmpeg_exit_code"],
        "managed_job_terminal": digest(workdir / "recorder-job-terminal.json"),
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


def managed_request(output: Path, request: dict[str, Any], *, timeout: float) -> dict:
    """Submit one immutable request to the capture's sole lease owner."""
    directory = output / "interactive-requests"
    if not directory.is_dir():
        raise RuntimeError("managed capture hot service is not ready")
    name = "recorder-" + uuid.uuid4().hex + ".json"
    target = directory / name
    pending = target.with_suffix(".json.pending")
    response = output / "interactive-requests-responses" / name
    write_new(pending, request)
    pending.rename(target)
    deadline = time.monotonic() + timeout
    while not response.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError(f"managed recorder response missing: {response}")
        time.sleep(0.1)
    row = json.loads(response.read_text(encoding="utf-8"))
    if row.get("result") != "CALL_COMPLETED" or row.get("request") != digest(target):
        raise RuntimeError(f"managed recorder request failed: {row}")
    return row["body"]


class ManagedGameplayRecorder:
    """One bounded raw recorder owned by the capture's existing screen keeper."""

    def __init__(self, output: Path, keeper: Any, *, steam_offline_receipt: Path) -> None:
        self.output, self.keeper = output.resolve(), keeper
        self.offline = digest(steam_offline_receipt)
        self.workdir: Path | None = None
        self.recorder = None
        self.streams: list[Any] = []
        self.start_ns = 0
        self.terminal: dict | None = None
        self.lock = threading.RLock()

    def _validate(self, workdir: Path) -> dict:
        if workdir.parent != self.output.parent or not workdir.is_dir() or \
                any(path.is_symlink() for path in (workdir, *workdir.parents)):
            raise ValueError("recorder workdir must be this capture's new sibling")
        intent = json.loads((workdir / "recorder-intent.json").read_text(encoding="utf-8"))
        preflight = json.loads((self.output / "preflight.json").read_text(encoding="utf-8"))
        loaded = json.loads((self.output / "native-start-readback.json").read_text(encoding="utf-8"))
        source = preflight.get("checkpoint_source") or {}
        if intent.get("schema") != "xar.war-promo.bounded-recorder-intent/v1" or \
                intent.get("max_seconds") != 600 or \
                intent.get("session_output") != str(self.output) or \
                intent.get("session_preflight") != digest(self.output / "preflight.json") or \
                intent.get("managed_load_readback") != digest(self.output / "native-start-readback.json") or \
                loaded.get("postcondition_verified") is not True or \
                loaded.get("source_checkpoint") != source or \
                intent.get("source_save") != source.get("save") or \
                intent.get("source_receipt") != source.get("receipt") or \
                intent.get("steam_offline_receipt") != self.offline or \
                intent.get("recorder_script") != digest(Path(__file__)):
            raise ValueError("recorder intent does not bind this loaded source and capture")
        for name in ("source_save", "source_receipt", "steam_offline_receipt",
                     "ffmpeg_executable", "ffprobe_executable"):
            if intent[name] != digest(Path(intent[name]["path"])):
                raise ValueError(f"recorder input changed: {name}")
        geometry = json.loads((workdir / "geometry-admission.json").read_text(encoding="utf-8"))
        if geometry.get("valid_and_equal") is not True or \
                geometry.get("gdi_width") != intent["desktop_primary_width"] or \
                geometry.get("gdi_height") != intent["desktop_primary_height"]:
            raise ValueError("recorder geometry admission differs")
        raw = Path(intent["raw_path"])
        if raw.parent.resolve() != (workdir / "raw").resolve() or raw.suffix != ".mkv" or raw.exists():
            raise ValueError("raw target must be a new MKV in this recorder workdir")
        expected = [intent["ffmpeg_executable"]["path"], "-nostdin", "-n", "-hide_banner",
                    "-loglevel", "warning", "-f", "gdigrab", "-framerate", "30",
                    "-draw_mouse", "0", "-i", "desktop", "-t", "600", "-c:v", "libx264",
                    "-preset", "ultrafast", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(raw)]
        if intent.get("argv") != expected:
            raise ValueError("recorder argv differs from bounded native desktop capture")
        return intent

    def _close_streams(self) -> None:
        for stream in reversed(self.streams):
            stream.close()
        self.streams.clear()

    def _end(self, row: dict, *, interrupted: bool) -> dict:
        if row.get("job_active_processes") != 0:
            raise RuntimeError("recorder Job is not proven empty; retain open stdio and Job")
        workdir = self.workdir
        end_ns, end_utc = time.monotonic_ns(), utc()
        try:
            self._close_streams()  # Job cleanup completed before stdio closure.
            end = {"schema": "xar.war-promo.bounded-recorder-end/v1", "ended_at": end_utc,
                   "monotonic_ns": end_ns, "elapsed_monotonic_seconds": (end_ns-self.start_ns)/1e9,
                   "ffmpeg_exit_code": self.recorder.returncode, "interrupted": interrupted,
                   "managed_job_state": row["state"],
                   "raw": digest(next((workdir / "raw").glob("*.mkv")))
                          if any((workdir / "raw").glob("*.mkv")) else None,
                   "stderr": digest(workdir / "ffmpeg.stderr.txt")}
            write_new(workdir / "recorder-end.json", end)
            append_mark(workdir, {"kind": "recorder-end", "utc": end_utc,
                                 "monotonic_ns": end_ns, "pid": self.recorder.pid,
                                 "ffmpeg_exit_code": self.recorder.returncode})
        except BaseException as error:
            self.terminal = {**row, "state": "RED_METADATA", "error": repr(error)}
            marker = workdir / "unsafe-recorder-cleanup.json"
            if not marker.exists():
                write_new(marker, {"state": "RED_METADATA", "job_active_processes": 0,
                                   "error": repr(error), "at_utc": utc()})
            raise
        self.terminal = row  # Publish normal state only after end/mark are durable.
        return row

    def handle(self, request: dict) -> dict:
        if set(request) != {"action", "operation", "workdir"} or \
                request.get("action") != "gameplay_recorder":
            raise ValueError("explicit managed recorder operation required")
        operation = request["operation"]
        workdir = Path(request["workdir"]).resolve()
        if operation == "start":
            # The sole keeper holds its CAS gate through Job assignment/resume.
            with self.keeper.process_create_gate():
                with self.lock:
                    if self.workdir is not None:
                        raise RuntimeError("this capture already attempted its one raw recorder")
                    intent = self._validate(workdir)
                    self.workdir = workdir
                    from recorder_job import spawn
                    try:
                        self.streams.append((workdir / "ffmpeg.stdout.bin").open("xb"))
                        self.streams.append((workdir / "ffmpeg.stderr.txt").open("xb"))
                        self.start_ns, started_at = time.monotonic_ns(), utc()
                        self.recorder = spawn(intent["argv"], stdin=subprocess.DEVNULL,
                            stdout=self.streams[0], stderr=self.streams[1],
                            unsafe_marker=workdir / "unsafe-recorder-cleanup.json",
                            start_receipt=workdir / "recorder-job-start.json",
                            failure_receipt=workdir / "recorder-job-spawn-failure.json")
                        write_new(workdir / "recorder-start.json", {
                            "schema": "xar.war-promo.bounded-recorder-start/v1",
                            "started_at": started_at, "monotonic_ns": self.start_ns,
                            "pid": self.recorder.pid, "argv": intent["argv"],
                            "managed_job_start": digest(workdir / "recorder-job-start.json")})
                        append_mark(workdir, {"kind": "recorder-start", "utc": started_at,
                                             "monotonic_ns": self.start_ns, "pid": self.recorder.pid})
                    except BaseException:
                        if self.recorder is not None:
                            self.abort()
                        else:
                            self._close_streams()
                        raise
            return {"state": "RECORDING", "pid": self.recorder.pid}
        with self.lock:
            if self.workdir != workdir or self.recorder is None:
                raise RuntimeError("recorder operation belongs to another or unstarted capture")
            if operation == "abort":
                return self.abort()
            if operation != "status":
                raise ValueError("unknown recorder operation")
            if self.terminal is not None:
                return self.terminal
            if self.recorder.poll() is None:
                return {"state": "RECORDING", "pid": self.recorder.pid}
            try:
                row = self.recorder.finish(receipt=workdir / "recorder-job-terminal.json",
                                          unsafe_marker=workdir / "unsafe-recorder-cleanup.json")
            except BaseException:
                self.abort()  # Receipt failure must still reap the owned Job.
                raise
            if row.get("job_active_processes") != 0:
                # finish has already retained its RED receipt. Reap the Job
                # through a distinct abort receipt before closing any stdio.
                return self.abort()
            return self._end(row, interrupted=False)

    def abort(self) -> dict:
        with self.lock:
            if self.recorder is None or self.terminal is not None:
                return self.terminal or {"state": "NOT_STARTED"}
            receipt = self.workdir / ("recorder-job-abort-" + uuid.uuid4().hex + ".json")
            row = self.recorder.abort(receipt=receipt,
                                      unsafe_marker=self.workdir / "unsafe-recorder-cleanup.json")
            return self._end(row, interrupted=True)

    def close(self) -> None:
        with self.lock:
            if self.recorder is not None and self.terminal is None:
                try:
                    if self.recorder.poll() is not None and not \
                            (self.workdir / "recorder-job-terminal.json").exists():
                        self.handle({"action": "gameplay_recorder", "operation": "status",
                                     "workdir": str(self.workdir)})
                    else:
                        self.abort()
                except BaseException:
                    self.abort()  # Distinct append-only receipt for a final cleanup retry.
                    raise

    def report(self) -> dict:
        with self.lock:
            return {"state": (self.terminal or {}).get("state", "NOT_STARTED"
                              if self.workdir is None else "START_FAILED_OR_UNPROVEN"),
                    "workdir": str(self.workdir) if self.workdir else None,
                    "unsafe_marker_present": bool(self.workdir and
                        (self.workdir / "unsafe-recorder-cleanup.json").exists()),
                    "artifacts": {name: digest(self.workdir / filename)
                        for name, filename in (("intent", "recorder-intent.json"),
                            ("start", "recorder-start.json"),
                            ("job_start", "recorder-job-start.json"),
                            ("job_terminal", "recorder-job-terminal.json"),
                            ("unsafe_marker", "unsafe-recorder-cleanup.json"),
                            ("end", "recorder-end.json"),
                            ("final", "recorder-final.json"))
                        if self.workdir and (self.workdir / filename).is_file()},
                    "abort_attempts": [digest(path) for path in
                        sorted(self.workdir.glob("recorder-job-abort-*.json"))]
                        if self.workdir else []}


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
