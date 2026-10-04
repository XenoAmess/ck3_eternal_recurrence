"""One explicit raw recorder owned by the episode04 bootstrap's existing keeper.

Import performs no process, SDK, screen, window, or game operation. Recorder
start is admitted only by a root-published gameplay_recorder request.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import threading
import time



def now():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pin(path):
    path = Path(path).resolve(strict=True)
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest}


def write(path, body):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(body, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


class OwnedRecorder:
    def __init__(self, run, keeper, offline, prepared):
        self.run, self.keeper, self.offline, self.prepared = run, keeper, offline, prepared
        self.assets_root = Path(prepared["assets_root"]).resolve()
        self.directory = None
        self.job = None
        self.streams = []
        self.terminal = None
        self.start_ns = None
        self.start_at = None
        self.cleanup_error = None
        self._end_lock = threading.RLock()

    def require_healthy(self):
        if self.job is not None and self.terminal is None:
            self.keeper.require_live()

    def handle(self, arguments, snapshot):
        require(type(arguments) is dict, "Recorder arguments must be an object")
        operation = arguments.get("operation")
        if operation in ("status", "finish"):
            require(set(arguments) == {"operation"}, "status/finish accept only operation")
            require(self.job is not None, "No owned recorder exists")
            if operation == "finish" or self.job.poll() is not None:
                return self.finish()
            return {"state": "RECORDING", "pid": self.job.pid, "started_at_utc": self.start_at,
                    "monotonic_ns": self.start_ns, "clean_spans_certified": False}
        require(operation == "start", "Unknown recorder operation")
        require(self.directory is None, "This session has already attempted its one recorder")
        required = {"operation", "workdir", "ffmpeg", "ffmpeg_sha256", "target_pid", "source_image", "seconds"}
        require(set(arguments) == required, "Explicit workdir/ffmpeg/SHA/owned PID/current original image/seconds required")
        require(type(snapshot) is dict and snapshot.get("map_ready") is True and snapshot.get("paused") is True,
                "Recorder start requires actual paused native map")
        checkpoint = (self.prepared.get("checkpoint") or {}).get("source")
        if checkpoint:
            actor = (snapshot.get("played_character") or {}).get("character_id")
            require(actor == checkpoint["actor_id"], "Recorder actor differs from checkpoint source")
        require(type(arguments["seconds"]) is int and 1 <= arguments["seconds"] <= 3600, "Recorder seconds must be1..3600")
        require(type(arguments["target_pid"]) is int and arguments["target_pid"] > 0, "Owned positive PID required")
        directory = Path(arguments["workdir"]).resolve()
        require(directory.is_relative_to(self.assets_root) and directory != self.assets_root, "Recorder output must be inside new episode04 assets root")
        require(not directory.exists() and not any(path.is_symlink() for path in directory.parents), "Fresh recorder workdir required")
        # Mark attempted before validating or spawning, so failure cannot be retried in this session.
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=False)
        try:
            import pyautogui
            import psutil
            from PIL import Image
            from recorder_job import spawn
            source = pin(arguments["source_image"])
            with Image.open(source["path"]) as image:
                size = tuple(image.size)
            desktop = tuple(pyautogui.size())
            require(size == desktop, "Reviewed source image and actual desktop dimensions differ")
            require(desktop[0] >= 1920 and desktop[1] >= 1080 and desktop[0] % 2 == 0 and desktop[1] % 2 == 0,
                    "Full native capture requires even dimensions at least1920x1080")
            current = pyautogui.screenshot()
            require(current.size == desktop == tuple(pyautogui.size()), "Capture dimensions changed")
            current.save(directory / "preflight-desktop.png")
            ck3 = [p for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower() == "ck3.exe"]
            require(len(ck3) == 1 and ck3[0].pid == arguments["target_pid"], "Exactly one actual owned CK3 PID required")
            ffmpeg = pin(arguments["ffmpeg"])
            require(ffmpeg["sha256"] == arguments["ffmpeg_sha256"].lower(), "Reviewed FFmpeg SHA differs")
            command = [ffmpeg["path"], "-hide_banner", "-nostats", "-n", "-thread_queue_size", "512",
                       "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "1", "-video_size",
                       f"{desktop[0]}x{desktop[1]}", "-i", "desktop", "-an", "-c:v", "libx264",
                       "-preset", "ultrafast", "-crf", "18", "-pix_fmt", "yuv420p", "-fps_mode", "cfr",
                       "-t", str(arguments["seconds"]), str(directory / "raw.mkv")]
            write(directory / "intent.json", {"at_utc": now(), "argv": command, "source_image": source,
                "preflight_desktop": pin(directory / "preflight-desktop.png"), "desktop": list(desktop),
                "snapshot": snapshot, "owned_ck3_pid": ck3[0].pid, "owned_ck3_create_time": ck3[0].create_time(),
                "ffmpeg": ffmpeg, "steam_offline_receipt": pin(self.offline), "source_prepared": self.prepared,
                "one_recorder_per_session": True, "screen_lease_owner": self.keeper.task_id,
                "clean_spans_certified": False, "human_approval": False})
            self.streams = [(directory / "stdout.bin").open("xb"), (directory / "stderr.bin").open("xb")]
            self.start_ns, self.start_at = time.monotonic_ns(), now()
            with self.keeper.process_create_gate():
                self.job = spawn(command, stdin=subprocess.PIPE, stdout=self.streams[0], stderr=self.streams[1],
                    unsafe_marker=directory / "unsafe-recorder-cleanup.json", start_receipt=directory / "job-start.json",
                    failure_receipt=directory / "job-spawn-failure.json")
            ready = {"state": "RECORDING", "pid": self.job.pid, "started_at_utc": self.start_at,
                     "monotonic_ns": self.start_ns, "argv": command, "managed_job_start": pin(directory / "job-start.json")}
            write(directory / "process-ready.json", ready)
            return ready
        except BaseException as error:
            write(directory / "start-failure.json", {"state": "RED_RETAINED", "error": repr(error), "at_utc": now()})
            if self.job is not None:
                self.abort()
            else:
                self._close_streams()
            raise

    def _close_streams(self):
        for stream in reversed(self.streams):
            stream.close()
        self.streams.clear()

    def _end(self, terminal):
        with self._end_lock:
            if self.terminal is not None:
                return self.report()
            require(terminal.get("job_active_processes") == 0, "Owned recorder Job not proven empty")
            self._close_streams()
            raw = self.directory / "raw.mkv"
            result = {"state": terminal["state"], "job": terminal, "raw": pin(raw) if raw.is_file() else None,
                      "started_at_utc": self.start_at, "completed_at_utc": now(), "start_monotonic_ns": self.start_ns,
                      "end_monotonic_ns": time.monotonic_ns(), "partial_assets_retained": True,
                      "clean_spans_certified": False, "human_approval": False, "media_probe_pending": True}
            write(self.directory / "result.json", result)
            self.terminal = terminal
            return result

    def finish(self):
        if self.terminal is not None:
            return self.report()
        try:
            terminal = self.job.finish(receipt=self.directory / "job-terminal.json",
                unsafe_marker=self.directory / "unsafe-recorder-cleanup.json", timeout=30)
            return self._end(terminal)
        except BaseException:
            self.abort()
            raise

    def abort(self):
        if self.job is None or self.terminal is not None:
            return self.report()
        terminal = self.job.abort(receipt=self.directory / ("job-abort-" + str(time.monotonic_ns()) + ".json"),
            unsafe_marker=self.directory / "unsafe-recorder-cleanup.json")
        return self._end(terminal)

    def close(self):
        if self.job is not None and self.terminal is None:
            if self.job.poll() is not None:
                self.finish()
            else:
                self.abort()

    def report(self):
        return {"state": (self.terminal or {}).get("state", "NOT_STARTED" if self.directory is None else "RECORDING_OR_START_FAILED"),
                "directory": str(self.directory) if self.directory else None, "cleanup_error": self.cleanup_error,
                "clean_spans_certified": False, "human_approval": False}
