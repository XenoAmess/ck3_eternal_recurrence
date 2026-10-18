"""Bounded capture and mailbox owned by the existing shared screen keeper.

No CLI starts a recorder. The owner must supply its existing keeper and wire
abort() into that keeper's on_abort path. This module never acquires a lease,
starts CK3/Steam, takes screenshots, presses keys, or certifies a clean span.
"""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import threading
import time


def utc():
    return datetime.now(timezone.utc).isoformat()


def file_identity(path):
    path = Path(path).resolve()
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": value.hexdigest()}


def write(path, document):
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


# Fingerprint of the retired renderer, not a title/OCR or generic decision-UI rule.
# See tools/g2_saved_campaign/decision_overlay_window.py and the migration note.
LEGACY_BLUE_OVERLAY_CLASS_PREFIX = "XARG2DecisionOverlay_"


def legacy_blue_overlay_windows(window_api=None):
    """Read only current-desktop window classes, including hidden legacy owners."""
    if window_api is None:
        import win32gui as window_api
    found = []

    def collect(hwnd, _):
        class_name = window_api.GetClassName(hwnd)
        suffix = class_name.removeprefix(LEGACY_BLUE_OVERLAY_CLASS_PREFIX)
        if (class_name.startswith(LEGACY_BLUE_OVERLAY_CLASS_PREFIX)
                and suffix.isascii() and suffix.isdecimal() and int(suffix) > 0):
            found.append({"hwnd": int(hwnd), "class_name": class_name})
        return True

    window_api.EnumWindows(collect, None)
    return found


def require_no_legacy_blue_overlay():
    legacy = legacy_blue_overlay_windows()
    if legacy:
        raise RuntimeError(
            "Retired legacy blue decision panel is still present; its owner must "
            "close it before a new take. New decision UIs are not disabled: " + repr(legacy))
    return {"legacy_blue_overlay_retired": True,
            "legacy_window_class_prefix": LEGACY_BLUE_OVERLAY_CLASS_PREFIX,
            "legacy_window_count_at_start": 0, "starts_or_mounts_decision_overlay": False}


class BoundedScreenRecorder:
    def __init__(self, *, root, output, keeper, ffmpeg, ffprobe, machine_id,
                 admission_receipt, seconds=120, peak_bytes=512 * 1024**2,
                 required_size=(2560, 1440)):
        if not 10 <= seconds <= 300 or peak_bytes < 512 * 1024**2:
            raise ValueError("Recorder requires 10–300 seconds and at least a 512 MiB raw reservation")
        self.root, self.output = Path(root).resolve(), Path(output).resolve()
        self.keeper, self.ffmpeg, self.ffprobe = keeper, Path(ffmpeg).resolve(), Path(ffprobe).resolve()
        self.machine_id, self.admission = machine_id, Path(admission_receipt).resolve()
        self.seconds, self.peak_bytes = seconds, peak_bytes
        self.required_size = tuple(required_size)
        self.recorder = None
        self.lock = threading.RLock()
        self.streams, self.terminal, self.start_ns = [], None, 0

    def start(self):
        # Keeper verifies fresh unique owner, unchanged source/checkout, and CAS.
        with self.keeper.process_create_gate(), self.lock:
            if self.output.exists() or self.recorder is not None:
                raise FileExistsError("Each capture attempt needs a new output path")
            actual_machine = subprocess.check_output([sys.executable, "-B", self.root / "tools/ck3_live_run_id.py", "machine"], text=True).strip()
            if actual_machine != self.machine_id:
                raise RuntimeError("Recorder machine identity changed")
            overlay_policy = require_no_legacy_blue_overlay()
            import ctypes
            import pyautogui
            native_size = (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
            automation_size = tuple(map(int, pyautogui.size()))
            if native_size != automation_size or native_size != self.required_size or min(native_size) <= 0:
                raise RuntimeError("Desktop native/automation geometry must both match the explicitly requested capture size")
            self.output.mkdir()
            source = self.root / "promo/ck3_native_war_ai/integration/recorder_job.py"
            spec = importlib.util.spec_from_file_location("faith_bound_recorder_job", source)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            raw = self.output / "raw-gameplay.mkv"
            argv = [str(self.ffmpeg), "-n", "-hide_banner", "-loglevel", "info", "-f", "gdigrab",
                    "-framerate", "30", "-draw_mouse", "0", "-i", "desktop", "-t", str(self.seconds),
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-maxrate", "18M",
                    "-bufsize", "36M", "-pix_fmt", "yuv420p", "-an", str(raw)]
            self.start_ns = time.monotonic_ns()
            intent = {"schema": "ck3-mod-acceptance-recorder-intent-v1", "machine_id": self.machine_id,
                      "observed_at_utc": utc(), "evidence_source": "BoundedScreenRecorder.start; actual keeper process-create gate and source bindings",
                      "argv": argv, "max_seconds": self.seconds, "peak_bytes": self.peak_bytes,
                      "geometry": {"gdi": native_size, "pyautogui": automation_size},
                      "decision_display_policy": overlay_policy,
                      "admission": file_identity(self.admission), "recorder_job_source": file_identity(source),
                      "project_source": file_identity(Path(__file__)), "ffmpeg": file_identity(self.ffmpeg),
                      "ffprobe": file_identity(self.ffprobe), "clean_spans_certified": False}
            write(self.output / "recorder-intent.json", intent)
            (self.output / "marks.jsonl").open("x", encoding="utf-8").close()
            self.streams = [(self.output / "ffmpeg.stdout.bin").open("xb"), (self.output / "ffmpeg.stderr.txt").open("xb")]
            try:
                self.recorder = module.spawn(argv, stdout=self.streams[0], stderr=self.streams[1],
                                             unsafe_marker=self.output / "unsafe-recorder-cleanup.json",
                                             start_receipt=self.output / "job-start.json",
                                             failure_receipt=self.output / "job-start-failure.json")
            except BaseException:
                self._close()
                raise
            self.mark("recorder-start")
            return {"state": "RECORDING_UNREVIEWED", "pid": self.recorder.pid, "output": str(self.output)}

    def mark(self, name, native_receipt=None):
        with self.lock:
            row = {"name": name, "machine_id": self.machine_id, "observed_at_utc": utc(),
                   "monotonic_ns": time.monotonic_ns(), "seconds_since_spawn_intent": (time.monotonic_ns() - self.start_ns) / 1e9,
                   "evidence_source": "operator mark; offset is not an exact first-frame PTS calibration",
                   "native_receipt": None if native_receipt is None else file_identity(native_receipt)}
            with (self.output / "marks.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            return row

    def status(self):
        with self.lock:
            if self.terminal:
                return self.terminal
            if self.recorder is None:
                return {"state": "NOT_STARTED"}
            raw = self.output / "raw-gameplay.mkv"
            if raw.is_file() and raw.stat().st_size > self.peak_bytes:
                return self.abort("reserved raw byte ceiling exceeded")
            if self.recorder.poll() is None:
                return {"state": "RECORDING_UNREVIEWED", "pid": self.recorder.pid}
            return self.finish()

    def _close(self):
        for stream in self.streams:
            stream.close()
        self.streams = []

    def finish(self):
        with self.lock:
            if self.terminal:
                return self.terminal
            if self.recorder is None:
                return {"state": "NOT_STARTED"}
            job = self.recorder.finish(receipt=self.output / "job-terminal.json", unsafe_marker=self.output / "unsafe-recorder-cleanup.json")
            if job.get("job_active_processes") != 0:
                raise RuntimeError("Recorder process tree remains unproven")
            self._close()
            raw = self.output / "raw-gameplay.mkv"
            command = [str(self.ffprobe), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(raw)]
            result = subprocess.run(command, capture_output=True, timeout=60)
            (self.output / "ffprobe.stdout.json").write_bytes(result.stdout)
            (self.output / "ffprobe.stderr.txt").write_bytes(result.stderr)
            self.terminal = {"schema": "ck3-mod-acceptance-recorder-final-v1", "machine_id": self.machine_id,
                             "observed_at_utc": utc(), "evidence_source": "actual contained FFmpeg termination and ffprobe",
                             "result": "ENCODED_UNREVIEWED" if job["state"] == "NORMAL_TREE_EMPTY" and result.returncode == 0 else "RED_PRESERVED",
                             "raw": file_identity(raw) if raw.is_file() else None, "job": job,
                             "probe_argv": command, "probe_exit_code": result.returncode,
                             "marks": file_identity(self.output / "marks.jsonl"), "clean_spans_certified": False,
                             "native_business_verified": False, "human_review_performed": False}
            write(self.output / "recorder-final.json", self.terminal)
            return self.terminal

    def abort(self, reason="screen keeper aborted"):
        with self.lock:
            if self.terminal or self.recorder is None:
                return self.terminal or {"state": "NOT_STARTED"}
            job = self.recorder.abort(receipt=self.output / "job-abort.json", unsafe_marker=self.output / "unsafe-recorder-cleanup.json")
            if job.get("job_active_processes") != 0:
                raise RuntimeError("Aborted recorder process tree remains unproven")
            self._close()
            self.terminal = {"schema": "ck3-mod-acceptance-recorder-abort-v1", "machine_id": self.machine_id,
                             "observed_at_utc": utc(), "evidence_source": "BoundedScreenRecorder.abort actual Job tree-empty result",
                             "state": "RED_PRESERVED", "reason": reason, "job": job,
                             "clean_spans_certified": False, "human_review_performed": False}
            write(self.output / "recorder-abort.json", self.terminal)
            return self.terminal


# Common helper body. Project content, native actions and Steam launch are absent.
import re
from datetime import timedelta


def _object(path):
    result = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(result, dict):
        raise ValueError("JSON object required")
    return result


def _pin(reference):
    observed = file_identity(reference["path"])
    if observed["bytes"] != reference["bytes"] or observed["sha256"] != reference["sha256"].lower():
        raise ValueError("Pinned recorder input changed: " + reference["path"])
    return Path(reference["path"]).resolve()


class ScreenCaptureService:
    """One request thread inside the original keeper process and instance."""
    def __init__(self, *, keeper, keeper_root, repo, config_path, config_sha256, task_id, recorder_factory=BoundedScreenRecorder):
        self.keeper, self.keeper_root, self.repo = keeper, Path(keeper_root).resolve(), Path(repo).resolve()
        self.config_path, self.config_sha256, self.task_id = Path(config_path).resolve(), config_sha256.lower(), task_id
        if file_identity(self.config_path)["sha256"] != self.config_sha256:
            raise ValueError("Recording config changed")
        self.config = _object(self.config_path)
        required = {"schema", "machine_id", "capture_root", "ffmpeg", "ffprobe", "recorder_job", "storage_reservation", "reservation_task", "max_seconds", "peak_bytes", "required_size"}
        if set(self.config) != required or self.config["schema"] != "ck3-mod-acceptance-recording-config-v1":
            raise ValueError("Unknown shared recorder configuration")
        if not 10 <= self.config["max_seconds"] <= 300 or self.config["peak_bytes"] < 512 * 1024**2:
            raise ValueError("Invalid bounded recording allocation")
        self.ffmpeg, self.ffprobe = _pin(self.config["ffmpeg"]), _pin(self.config["ffprobe"])
        job = _pin(self.config["recorder_job"])
        if job != self.repo / "promo/ck3_native_war_ai/integration/recorder_job.py":
            raise ValueError("Only the existing shared RecorderJob is supported")
        self.storage = _pin(self.config["storage_reservation"])
        if _object(self.storage).get("machine_id") != self.config["machine_id"]:
            raise ValueError("Recording reservation crossed machine")
        self.capture_root = Path(self.config["capture_root"]).resolve()
        if any(path.is_symlink() for path in (self.capture_root, *self.capture_root.parents)):
            raise ValueError("Capture output must not cross symlinks")
        self.requests, self.responses = self.keeper_root / "recorder-requests", self.keeper_root / "recorder-responses"
        self.done, self.thread, self.recorder, self.error = threading.Event(), None, None, None
        self.seen, self.recorder_factory = set(), recorder_factory
        self.capture_names, self.completed_takes = set(), []
        self.started_at = utc()

    def start(self):
        if self.thread is not None:
            raise ValueError("Recorder service already started")
        self.requests.mkdir(); self.responses.mkdir()
        write(self.keeper_root / "recording-service-ready.json", {
            "schema": "ck3-mod-acceptance-recording-service-ready-v1", "machine_id": self.config["machine_id"],
            "observed_at_utc": utc(), "evidence_source": "same existing keeper instance; passive recorder request service",
            "pid": __import__('os').getpid(), "screen_task": self.task_id,
            "configuration": file_identity(self.config_path), "service_source": file_identity(Path(__file__)),
            "requests": str(self.requests), "responses": str(self.responses),
            "screen_owner_acquired": False, "recorder_started": False})
        self.thread = threading.Thread(target=self._run, name="shared-screen-recorder-requests", daemon=True)
        self.thread.start()

    def _live(self, live):
        from ck3_mod_acceptance_launcher import frozen_run
        from ck3_mod_acceptance_keeper import live_lease
        live = Path(live).resolve()
        frozen, context = frozen_run(live, all_pins=True, input_phase="running")
        if (Path(context["keeper_root"]).resolve() != self.keeper_root
                or frozen["screen_task"] != self.task_id
                or frozen["identity_allocation"]["machine_id"] != self.config["machine_id"]):
            raise ValueError("Recorder request belongs to another actual allocation/keeper")
        for reference in (file_identity(self.config_path), file_identity(Path(__file__)), self.config["recorder_job"]):
            current = frozen["files"].get(str(Path(reference["path"]).resolve()))
            if not current or current["sha256"].lower() != reference["sha256"].lower():
                raise ValueError("Recording config/service/Job source absent from actual allocation pins")
        live_lease(self.keeper_root, frozen)
        self.keeper.require_live()
        report = _object(live / "native-report.json")
        if report.get("phase") != "hold" or report.get("finished_at") or report.get("hold_finished_by_control_plan"):
            raise ValueError("Actual common host is not in its live hold phase")
        if report.get("state_dir") != frozen["state_dir"] or report.get("agent_source_root") != frozen["source_root"]:
            raise ValueError("Common host report crossed frozen state/source")
        started = _object(live / "host-started.json")
        import psutil
        if abs(psutil.Process(started["pid"]).create_time() - started["create_time"]) > 0.000001:
            raise ValueError("Actual original common host is no longer alive")
        return live, frozen

    def handle(self, request):
        if set(request) - {"schema", "id", "operation", "live_root", "capture_name", "label", "native_receipt"}:
            raise ValueError("Unknown recorder request field")
        if request.get("schema") != "ck3-mod-acceptance-recorder-request-v1":
            raise ValueError("Unknown recorder request schema")
        operation = request.get("operation")
        if operation not in {"start", "status", "mark", "finish", "abort"}:
            raise ValueError("Recorder only supports start/status/mark/finish/abort")
        if operation == "abort":
            return self.abort_for_lease()
        live, frozen = self._live(request["live_root"])
        if operation == "start":
            # Reject before consuming a take name or creating a recorder object.
            require_no_legacy_blue_overlay()
            if self.recorder is not None:
                terminal = self.recorder.terminal
                job = terminal.get('job', {}) if isinstance(terminal, dict) else {}
                if type(job.get('job_active_processes')) is not int or job['job_active_processes'] != 0:
                    raise ValueError("Previous take is active or its Job tree is unproven; never overlap or replay")
            name = request.get("capture_name", "")
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,100}", name):
                raise ValueError("Explicit portable capture basename required")
            output = self.capture_root / name
            if name in self.capture_names or output.exists() or not output.is_relative_to(self.capture_root):
                raise ValueError("Use an unconsumed capture directory inside configured root")
            reservation = _object(self.storage)
            capture_limits = [row['peak_bytes'] for row in reservation.get('reservations', [])
                              if row.get('task') == self.config['reservation_task']]
            if len(capture_limits) != 1:
                raise ValueError("One explicit root capture reservation is required")
            used = sum(path.stat().st_size for path in self.capture_root.rglob('*') if path.is_file()) if self.capture_root.is_dir() else 0
            if used + self.config['peak_bytes'] > capture_limits[0]:
                raise ValueError("New take would exceed the actual root capture reservation")
            self.capture_root.mkdir(parents=True, exist_ok=True)
            _pin(self.config["recorder_job"])
            _pin(self.config["ffmpeg"]); _pin(self.config["ffprobe"])
            if self.recorder is not None:
                self.completed_takes.append({'output': str(self.recorder.output), 'terminal': self.recorder.terminal})
            self.capture_names.add(name)
            self.recorder = self.recorder_factory(root=self.repo, output=output, keeper=self.keeper,
                ffmpeg=self.ffmpeg, ffprobe=self.ffprobe, machine_id=self.config["machine_id"],
                admission_receipt=live / "launch-intent.json", seconds=self.config["max_seconds"],
                peak_bytes=self.config["peak_bytes"], required_size=self.config["required_size"])
            return self.recorder.start()
        if self.recorder is None:
            raise ValueError("Recorder has not started")
        if operation == "status": return self.recorder.status()
        if operation == "finish": return self.recorder.finish()
        label = request.get("label", "")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,160}", label):
            raise ValueError("A native phase mark label is required")
        receipt = Path(request["native_receipt"]).resolve() if request.get("native_receipt") else None
        if receipt and not any(receipt.is_relative_to(root) for root in (live, self.capture_root)):
            raise ValueError("Native mark receipt must be in this live run or capture root")
        return self.recorder.mark(label, receipt)

    def _run(self):
        try:
            while not self.done.wait(.25):
                self.keeper.require_live()
                for path in sorted(self.requests.glob("*.json")):
                    if path.name in self.seen:
                        continue
                    self.seen.add(path.name)  # Mark before action: unknown results are never replayed.
                    response = {"schema": "ck3-mod-acceptance-recorder-response-v1", "machine_id": self.config["machine_id"],
                                "observed_at_utc": utc(), "evidence_source": "actual same-keeper recording request execution",
                                "request": file_identity(path), "business_pass": False}
                    try:
                        if path.stat().st_size > 64 * 1024:
                            raise ValueError("Recorder request exceeds 64 KiB")
                        response["result"] = self.handle(_object(path))
                        response["status"] = "CALL_COMPLETED_ACK_NOT_CLEAN"
                    except BaseException as error:
                        response.update(status="RED_PRESERVED", error=repr(error))
                    write(self.responses / path.name, response)
                if self.recorder is not None and self.recorder.terminal is None:
                    self.recorder.status()  # Enforce byte cap and actual normal completion.
        except BaseException as error:
            self.error = repr(error)
            self.abort_for_lease()
            self.keeper.abort.set()
            write(self.keeper_root / "recording-service-failure.json", self.report())

    def abort_for_lease(self):
        return self.recorder.abort() if self.recorder is not None else {"state": "NOT_STARTED"}

    def stop(self):
        self.done.set()
        if self.thread is not None:
            self.thread.join(timeout=65)
            if self.thread.is_alive():
                raise RuntimeError("Recording service did not exit before keeper stop")
        self.abort_for_lease()
        write(self.keeper_root / "recording-service-final.json", self.report())

    def report(self):
        return {"schema": "ck3-mod-acceptance-recording-service-report-v1", "machine_id": self.config["machine_id"],
                "observed_at_utc": utc(), "evidence_source": "same keeper request thread and recorder terminal state",
                "screen_task": self.task_id, "thread_exited": self.thread is not None and not self.thread.is_alive(),
                "failure": self.error, "requests_consumed": sorted(self.seen),
                "capture_names_consumed": sorted(self.capture_names), "completed_takes": self.completed_takes,
                "recorder_terminal": None if self.recorder is None else self.recorder.terminal,
                "no_additional_screen_owner": True, "business_pass": False, "clean_spans_certified": False}
