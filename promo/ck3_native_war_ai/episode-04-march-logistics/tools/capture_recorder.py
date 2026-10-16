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


CAPTURE_SOURCE = "gdigrab-desktop-client-region"
CAPTURE_GUARD_INTERVAL_SECONDS = 0.25


def validate_client_region(source):
    """Validate physical screen coordinates, without touching a desktop."""
    require(type(source) is dict, "Capture source must be an object")
    width, height = source["desktop"]
    left, top, right, bottom = source["client_screen_rect"]
    require(all(type(value) is int for value in (width, height, left, top, right, bottom)),
            "Capture coordinates must be physical integer pixels")
    require(0 <= left < right <= width and 0 <= top < bottom <= height,
            "CK3 client area must be wholly inside the captured primary desktop")
    client = (right - left, bottom - top)
    require(client[0] >= 640 and client[1] >= 360 and all(value % 2 == 0 for value in client),
            "CK3 client capture requires even dimensions at least640x360; no implicit crop or scale")
    require(source["hwnd"] == source["foreground_hwnd"], "Owned CK3 window must be foreground")
    require(not source.get("occluding_windows"), "Another visible window overlaps the CK3 client area")
    return client


def require_same_source(expected, actual):
    validate_client_region(actual)
    for key in ("owned_ck3_pid", "owned_ck3_create_time", "hwnd", "desktop", "client_screen_rect"):
        require(actual[key] == expected[key], "Capture source changed: " + key)


def inspect_owned_client(target_pid, expected_create_time=None):
    """Read the actual Win32 client bounds; never move, focus or capture a window.

    The temporary thread DPI context makes ClientToScreen/GetWindowRect physical
    pixels. It does not alter the application's process-wide DPI settings.
    """
    import ctypes
    from ctypes import wintypes
    import psutil

    ck3 = [p for p in psutil.process_iter(["name"])
           if (p.info["name"] or "").lower() == "ck3.exe"]
    require(len(ck3) == 1 and ck3[0].pid == target_pid, "Exactly one actual owned CK3 PID required")
    created = ck3[0].create_time()
    if expected_create_time is not None:
        require(created == expected_create_time, "Owned CK3 PID was reused")
    user = ctypes.WinDLL("user32", use_last_error=True)

    def api(name, result, *arguments):
        call = getattr(user, name)
        call.restype, call.argtypes = result, list(arguments)
        return call

    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    enum = api("EnumWindows", wintypes.BOOL, callback_type, wintypes.LPARAM)
    visible = api("IsWindowVisible", wintypes.BOOL, wintypes.HWND)
    iconic = api("IsIconic", wintypes.BOOL, wintypes.HWND)
    pid_of = api("GetWindowThreadProcessId", wintypes.DWORD, wintypes.HWND,
                 ctypes.POINTER(wintypes.DWORD))
    owner = api("GetWindow", wintypes.HWND, wintypes.HWND, wintypes.UINT)
    foreground = api("GetForegroundWindow", wintypes.HWND)
    client_rect = api("GetClientRect", wintypes.BOOL, wintypes.HWND, ctypes.POINTER(wintypes.RECT))
    window_rect = api("GetWindowRect", wintypes.BOOL, wintypes.HWND, ctypes.POINTER(wintypes.RECT))
    to_screen = api("ClientToScreen", wintypes.BOOL, wintypes.HWND, ctypes.POINTER(wintypes.POINT))
    metrics = api("GetSystemMetrics", ctypes.c_int, ctypes.c_int)
    set_dpi = api("SetThreadDpiAwarenessContext", ctypes.c_void_p, ctypes.c_void_p)
    prior_dpi = set_dpi(ctypes.c_void_p(-4))  # PER_MONITOR_AWARE_V2, thread-local.
    require(prior_dpi, "Physical-pixel thread DPI context could not be established")
    try:
        windows = []

        @callback_type
        def collect(hwnd, _):
            if visible(hwnd) and not iconic(hwnd):
                pid = wintypes.DWORD()
                pid_of(hwnd, ctypes.byref(pid))
                windows.append((int(hwnd), int(pid.value), bool(owner(hwnd, 4))))
            return True

        require(enum(collect, 0), "EnumWindows failed")
        owned = [hwnd for hwnd, pid, has_owner in windows if pid == target_pid and not has_owner]
        require(len(owned) == 1, "Exactly one visible unowned CK3 top-level window required")
        hwnd = owned[0]
        require(int(foreground() or 0) == hwnd, "Owned CK3 window must be foreground")
        rect = wintypes.RECT()
        require(client_rect(hwnd, ctypes.byref(rect)), "GetClientRect failed")
        start, end = wintypes.POINT(rect.left, rect.top), wintypes.POINT(rect.right, rect.bottom)
        require(to_screen(hwnd, ctypes.byref(start)) and to_screen(hwnd, ctypes.byref(end)),
                "ClientToScreen failed")
        bounds = [int(start.x), int(start.y), int(end.x), int(end.y)]
        occluding = []
        # Inspect the explicit Z-order chain: an overlay can cover the client
        # without taking keyboard focus. Do not rely on EnumWindows ordering.
        above, cursor = set(), int(owner(hwnd, 3) or 0)  # GW_HWNDPREV.
        while cursor:
            require(cursor not in above and len(above) < 4096, "Window Z order changed during inspection")
            above.add(cursor)
            cursor = int(owner(cursor, 3) or 0)
        for other, pid, _ in windows:
            if other not in above:
                continue
            if pid == target_pid:
                continue
            cover = wintypes.RECT()
            require(window_rect(other, ctypes.byref(cover)), "Occlusion window bounds unavailable")
            if max(cover.left, bounds[0]) < min(cover.right, bounds[2]) and max(
                    cover.top, bounds[1]) < min(cover.bottom, bounds[3]):
                occluding.append({"hwnd": other, "pid": pid,
                                  "screen_rect": [cover.left, cover.top, cover.right, cover.bottom]})
        result = {"kind": CAPTURE_SOURCE, "owned_ck3_pid": target_pid,
                  "owned_ck3_create_time": created, "hwnd": hwnd, "foreground_hwnd": hwnd,
                  "desktop": [metrics(0), metrics(1)], "client_screen_rect": bounds,
                  "occluding_windows": occluding, "coordinates": "physical-primary-screen-pixels",
                  "direct_hwnd_capture": False, "window_border_included": False,
                  "observed_at_utc": now()}
        result["output_size"] = list(validate_client_region(result))
        return result
    finally:
        require(set_dpi(prior_dpi), "Could not restore thread DPI context")


def ffmpeg_command(ffmpeg, source, seconds, output):
    width, height = validate_client_region(source)
    left, top, _, _ = source["client_screen_rect"]
    return [ffmpeg, "-hide_banner", "-nostats", "-n", "-thread_queue_size", "512",
            "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "1",
            "-offset_x", str(left), "-offset_y", str(top), "-video_size", f"{width}x{height}",
            "-i", "desktop", "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-fps_mode", "cfr", "-t", str(seconds), str(output)]



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
    def __init__(self, run, keeper, offline, prepared, *, start_admission=None):
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
        self.capture_source = None
        self.capture_guard_error = None
        self.capture_guard_stop = threading.Event()
        self.capture_guard_thread = None
        self.result = None
        self.start_admission = start_admission
        self.deadline_admission_at_request = None
        self.deadline_admission_at_spawn = None

    def _admit_start(self, seconds):
        require(callable(self.start_admission), "Recorder start requires a session/capacity deadline admission guard")
        admission = self.start_admission(seconds)
        require(type(admission) is dict, "Deadline admission must return explicit deadline facts")
        return admission

    def require_healthy(self):
        require(self.capture_guard_error is None, "Recorder capture guard failed: " + str(self.capture_guard_error))
        if self.job is not None and self.terminal is None:
            self.keeper.require_live()

    def _check_capture_source(self):
        actual = inspect_owned_client(self.capture_source["owned_ck3_pid"],
                                      self.capture_source["owned_ck3_create_time"])
        require_same_source(self.capture_source, actual)
        return actual

    def _watch_capture_source(self):
        while not self.capture_guard_stop.wait(CAPTURE_GUARD_INTERVAL_SECONDS):
            try:
                if self.job.poll() is not None:
                    return
                self._check_capture_source()
            except BaseException as error:
                with self._end_lock:
                    if self.capture_guard_stop.is_set():
                        return
                    self.capture_guard_error = repr(error)
                    try:
                        write(self.directory / "capture-guard-failure.json", {
                            "machine_id": self.prepared["machine_id"], "at_utc": now(),
                            "state": "RED_CAPTURE_SOURCE_CHANGED", "error": self.capture_guard_error,
                            "capture_source": self.capture_source, "clean_spans_certified": False,
                            "guard_interval_seconds": CAPTURE_GUARD_INTERVAL_SECONDS})
                    finally:
                        # Finish the container so the retained prefix is readable.
                        # Sampling cannot certify every frame preceding detection.
                        try:
                            self.finish()
                        except BaseException as cleanup:
                            self.cleanup_error = repr(cleanup)
                return

    def handle(self, arguments, snapshot):
        require(type(arguments) is dict, "Recorder arguments must be an object")
        operation = arguments.get("operation")
        if operation in ("status", "finish"):
            require(set(arguments) == {"operation"}, "status/finish accept only operation")
            require(self.job is not None, "No owned recorder exists")
            if operation == "finish" or self.job.poll() is not None:
                return self.finish()
            return {"state": "RECORDING", "pid": self.job.pid, "started_at_utc": self.start_at,
                    "machine_id": self.prepared["machine_id"], "capture_source": self.capture_source,
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
        # A denied request does not consume the one recorder attempt or create
        # its workdir. The supervisor owns both actual deadlines and reserve.
        self.deadline_admission_at_request = self._admit_start(arguments["seconds"])
        directory = Path(arguments["workdir"]).resolve()
        require(directory.is_relative_to(self.assets_root) and directory != self.assets_root, "Recorder output must be inside new episode04 assets root")
        require(not directory.exists() and not any(path.is_symlink() for path in directory.parents), "Fresh recorder workdir required")
        # Mark attempted before validating or spawning, so failure cannot be retried in this session.
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=False)
        try:
            import pyautogui
            from PIL import Image
            from recorder_job import spawn
            source = pin(arguments["source_image"])
            with Image.open(source["path"]) as image:
                size = tuple(image.size)
            desktop = tuple(pyautogui.size())
            require(size == desktop, "Reviewed source image and actual desktop dimensions differ")
            self.capture_source = inspect_owned_client(arguments["target_pid"])
            require(tuple(self.capture_source["desktop"]) == desktop,
                    "Physical Win32 desktop and screenshot dimensions differ")
            current = pyautogui.screenshot()
            require(current.size == desktop == tuple(pyautogui.size()), "Capture dimensions changed")
            current.save(directory / "preflight-desktop.png")
            ffmpeg = pin(arguments["ffmpeg"])
            require(ffmpeg["sha256"] == arguments["ffmpeg_sha256"].lower(), "Reviewed FFmpeg SHA differs")
            command = ffmpeg_command(ffmpeg["path"], self.capture_source, arguments["seconds"], directory / "raw.mkv")
            write(directory / "intent.json", {"machine_id": self.prepared["machine_id"],
                "at_utc": now(), "argv": command, "source_image": source,
                "preflight_desktop": pin(directory / "preflight-desktop.png"), "desktop": list(desktop),
                "snapshot": snapshot, "capture_source": self.capture_source,
                "owned_ck3_pid": self.capture_source["owned_ck3_pid"],
                "owned_ck3_create_time": self.capture_source["owned_ck3_create_time"],
                "capture_guard_interval_seconds": CAPTURE_GUARD_INTERVAL_SECONDS,
                "deadline_admission_at_request": self.deadline_admission_at_request,
                "ffmpeg": ffmpeg, "steam_offline_receipt": pin(self.offline), "source_prepared": self.prepared,
                "one_recorder_per_session": True, "screen_lease_owner": self.keeper.task_id,
                "clean_spans_certified": False, "human_approval": False})
            self.streams = [(directory / "stdout.bin").open("xb"), (directory / "stderr.bin").open("xb")]
            self.start_ns, self.start_at = time.monotonic_ns(), now()
            with self.keeper.process_create_gate():
                self._check_capture_source()
                self.deadline_admission_at_spawn = self._admit_start(arguments["seconds"])
                write(directory / "deadline-admission-at-spawn.json", {
                    "machine_id": self.prepared["machine_id"], "at_utc": now(),
                    "admission": self.deadline_admission_at_spawn})
                self.job = spawn(command, stdin=subprocess.PIPE, stdout=self.streams[0], stderr=self.streams[1],
                    unsafe_marker=directory / "unsafe-recorder-cleanup.json", start_receipt=directory / "job-start.json",
                    failure_receipt=directory / "job-spawn-failure.json")
            ready = {"state": "RECORDING", "machine_id": self.prepared["machine_id"],
                     "pid": self.job.pid, "started_at_utc": self.start_at, "capture_source": self.capture_source,
                     "deadline_admission_at_spawn": self.deadline_admission_at_spawn,
                     "monotonic_ns": self.start_ns, "argv": command, "managed_job_start": pin(directory / "job-start.json")}
            write(directory / "process-ready.json", ready)
            self.capture_guard_thread = threading.Thread(target=self._watch_capture_source,
                name="episode04-client-capture-guard", daemon=True)
            self.capture_guard_thread.start()
            return ready
        except BaseException as error:
            secondary = []
            try:
                write(directory / "start-failure.json", {"machine_id": self.prepared["machine_id"],
                    "state": "RED_RETAINED", "error": repr(error), "at_utc": now()})
            except BaseException as receipt_error:
                secondary.append("start-failure receipt: " + repr(receipt_error))
            finally:
                # Disk/receipt failure must never bypass process cleanup. Keep
                # the first business exception even if cleanup reporting fails.
                try:
                    if self.job is not None:
                        self.abort()
                except BaseException as cleanup_error:
                    secondary.append("recorder abort: " + repr(cleanup_error))
                finally:
                    try:
                        self._close_streams()
                    except BaseException as stream_error:
                        secondary.append("stream close: " + repr(stream_error))
            if secondary:
                self.cleanup_error = "; ".join(secondary)
                error.add_note(self.cleanup_error)
            raise

    def _close_streams(self):
        errors = []
        for stream in reversed(self.streams):
            try:
                stream.close()
            except BaseException as error:
                errors.append(repr(error))
        self.streams.clear()
        if errors:
            raise RuntimeError("Could not close recorder streams: " + "; ".join(errors))

    def _end(self, terminal):
        with self._end_lock:
            if self.terminal is not None:
                return self.report()
            self.capture_guard_stop.set()
            require(terminal.get("job_active_processes") == 0, "Owned recorder Job not proven empty")
            self._close_streams()
            raw = self.directory / "raw.mkv"
            result = {"machine_id": self.prepared["machine_id"],
                      "state": "RED_CAPTURE_SOURCE_CHANGED" if self.capture_guard_error else terminal["state"],
                      "job": terminal, "raw": pin(raw) if raw.is_file() else None,
                      "capture_source": self.capture_source, "capture_guard_error": self.capture_guard_error,
                      "deadline_admission_at_spawn": self.deadline_admission_at_spawn,
                      "started_at_utc": self.start_at, "completed_at_utc": now(), "start_monotonic_ns": self.start_ns,
                      "end_monotonic_ns": time.monotonic_ns(), "partial_assets_retained": True,
                      "clean_spans_certified": False, "human_approval": False, "media_probe_pending": True}
            # The process tree is already proven empty. Retain that fact in
            # memory even when persisting the terminal result is impossible.
            self.terminal = terminal
            self.result = result
            write(self.directory / "result.json", result)
            return result

    def finish(self):
        with self._end_lock:
            if self.terminal is not None:
                return self.report()
            self.capture_guard_stop.set()
            try:
                terminal = self.job.finish(receipt=self.directory / "job-terminal.json",
                    unsafe_marker=self.directory / "unsafe-recorder-cleanup.json", timeout=30)
                return self._end(terminal)
            except BaseException:
                self.abort()
                raise

    def abort(self):
        with self._end_lock:
            self.capture_guard_stop.set()
            if self.job is None or self.terminal is not None:
                return self.report()
            terminal = self.job.abort(receipt=self.directory / ("job-abort-" + str(time.monotonic_ns()) + ".json"),
                unsafe_marker=self.directory / "unsafe-recorder-cleanup.json")
            return self._end(terminal)

    def close(self):
        try:
            if self.job is not None and self.terminal is None:
                if self.job.poll() is not None:
                    self.finish()
                else:
                    self.abort()
        finally:
            self.capture_guard_stop.set()
            watcher = self.capture_guard_thread
            # finish/abort may run on the watcher itself and under _end_lock;
            # only close joins, after those methods have released their locks.
            if watcher is not None and watcher is not threading.current_thread() and watcher.ident is not None:
                watcher.join(timeout=2)
                if watcher.is_alive():
                    self.cleanup_error = (self.cleanup_error + "; " if self.cleanup_error else "") + "capture guard did not stop within2s"

    def report(self):
        return {"state": (self.result or {}).get("state", "NOT_STARTED" if self.directory is None else "RECORDING_OR_START_FAILED"),
                "machine_id": self.prepared["machine_id"], "capture_source": self.capture_source,
                "capture_guard_error": self.capture_guard_error,
                "capture_guard_thread_alive": bool(self.capture_guard_thread and self.capture_guard_thread.is_alive()),
                "directory": str(self.directory) if self.directory else None, "cleanup_error": self.cleanup_error,
                "clean_spans_certified": False, "human_approval": False}
