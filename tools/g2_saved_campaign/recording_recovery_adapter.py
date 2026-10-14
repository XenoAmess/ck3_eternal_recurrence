"""Configurable same-Game recording recovery adapter/watchdog. Import has no side effects."""
from __future__ import annotations
import argparse
import ast
import ctypes
from ctypes import wintypes
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from recording_recovery_supervisor import (
    Admission, Attach, Cleanup, Game, Observation, Overlay, Recorder,
    RecoverySupervisor, Resume, SdkGuard, Segment,
)

def utc():
    return datetime.now(timezone.utc)

def shared_bytes(path, limit=1024**2):
    """Close immediately; allow READ|WRITE|DELETE while a producer atomically replaces."""
    path = Path(path)
    if os.name != "nt":
        with path.open("rb") as stream:
            data = stream.read(limit + 1)
    else:
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                 ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        k.CreateFileW.restype = wintypes.HANDLE
        k.ReadFile.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                              ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = k.CreateFileW(str(path), 0x80000000, 7, None, 3, 128, None)
        if handle == ctypes.c_void_p(-1).value:
            error = ctypes.get_last_error()
            if error in (2, 3):
                raise FileNotFoundError(path)
            raise ctypes.WinError(error)
        try:
            buffer = ctypes.create_string_buffer(limit + 1)
            count = wintypes.DWORD()
            if not k.ReadFile(handle, buffer, len(buffer), ctypes.byref(count), None):
                raise ctypes.WinError(ctypes.get_last_error())
            data = buffer.raw[:count.value]
        finally:
            k.CloseHandle(handle)
    if len(data) > limit:
        raise ValueError("bounded shared read exceeded limit: " + str(path))
    return data

def shared_json(path, limit=1024**2):
    return json.loads(shared_bytes(path, limit).decode("utf-8-sig"))

def maybe_json(path, limit=1024**2):
    try:
        return shared_json(path, limit)
    except FileNotFoundError:
        return None

def atomic(path, value, *, new=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=True, indent=2).encode() + b"\n"
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".pending")
    with temporary.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        if new:
            os.link(temporary, path)  # Atomic publish with no occupied-name overwrite.
            temporary.unlink()
        else:
            os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()

def load_source(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

class WindowsPlatform:
    """Only owned helper launches and process identity reads; no Game input or MCP."""
    def __init__(self):
        if os.name != "nt":
            raise RuntimeError("production watchdog requires Windows")
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        k = self.k
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.OpenProcess.restype = wintypes.HANDLE
        k.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(ctypes.c_ulonglong)] * 4
        k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        self.lock_handle = None

    def process(self, pid):
        handle = self.k.OpenProcess(0x1000 | 0x100000, False, int(pid))
        if not handle:
            error = ctypes.get_last_error()
            if error == 87:
                return None
            raise ctypes.WinError(error)
        try:
            stamps = [ctypes.c_ulonglong() for _ in range(4)]
            if not self.k.GetProcessTimes(handle, *[ctypes.byref(x) for x in stamps]):
                raise ctypes.WinError(ctypes.get_last_error())
            alive = self.k.WaitForSingleObject(handle, 0) == 258
            code = wintypes.DWORD()
            if not self.k.GetExitCodeProcess(handle, ctypes.byref(code)):
                raise ctypes.WinError(ctypes.get_last_error())
            return {"pid": int(pid), "creation_filetime": stamps[0].value,
                    "alive": alive, "exit_code": None if alive else code.value}
        finally:
            self.k.CloseHandle(handle)

    def alive(self, pid, stamp):
        row = self.process(pid)
        return bool(row and row["alive"] and row["creation_filetime"] == stamp)

    def lock(self, path):
        k = self.k
        k.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                 ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        k.CreateFileW.restype = wintypes.HANDLE
        self.lock_handle = k.CreateFileW(str(path), 0xC0000000, 0, None, 4, 128, None)
        if self.lock_handle == ctypes.c_void_p(-1).value:
            raise RuntimeError("another recovery watchdog owns this SDK session")
        return self

    def close(self):
        if self.lock_handle is not None:
            self.k.CloseHandle(self.lock_handle)
            self.lock_handle = None

    def scripts(self, paths):
        # Query only Python command lines during recovery; do not invoke a shell.
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        try:
            service = win32com.client.GetObject("winmgmts:")
            rows = service.ExecQuery(
                "SELECT ProcessId,CommandLine FROM Win32_Process WHERE Name='python.exe' OR Name='pythonw.exe'")
            needles = {str(Path(p).resolve()).casefold() for p in paths}
            parse = ctypes.WinDLL("shell32", use_last_error=True).CommandLineToArgvW
            parse.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
            parse.restype = ctypes.POINTER(wintypes.LPWSTR)
            self.k.LocalFree.argtypes = [ctypes.c_void_p]
            self.k.LocalFree.restype = ctypes.c_void_p
            result = []
            for row in rows:
                if int(row.ProcessId) == os.getpid() or not row.CommandLine:
                    continue
                count = ctypes.c_int()
                arguments = parse(str(row.CommandLine), ctypes.byref(count))
                if not arguments:
                    raise ctypes.WinError(ctypes.get_last_error())
                try:
                    script = next((arguments[i] for i in range(1, count.value)
                                   if arguments[i].casefold().endswith(".py")), None)
                    match = script is not None and str(Path(script).resolve()).casefold() in needles
                finally:
                    self.k.LocalFree(arguments)
                if match:
                    actual = self.process(int(row.ProcessId))
                    if actual and actual["alive"]:
                        result.append(actual)
            return result
        finally:
            pythoncom.CoUninitialize()

    def spawn(self, argv, stdout, stderr, *, cwd):
        with Path(stdout).open("xb") as out, Path(stderr).open("xb") as err:
            child = subprocess.Popen(argv, cwd=str(cwd), stdin=subprocess.DEVNULL,
                                     stdout=out, stderr=err,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
        actual = self.process(child.pid)
        if not actual:
            raise RuntimeError("spawn returned but process generation is unknown; no retry")
        return actual

    def launch_recording(self, config, job, overlay_receipt):
        previous_pythonpath = os.environ.get("PYTHONPATH")
        previous_sys_path = list(sys.path)
        try:
            provider = load_source("recording_recovery_provider_" + uuid.uuid4().hex,
                                   config.provider_source)
            return provider.capture.launch_recording(
                Path(job["profile_path"]), config.session / "recordings",
                job["pid"], job["hwnd"], None,
                launch_receipt=Path(job["overlay"]["launch_receipt"]),
                ffprobe=Path(job["ffprobe"]),
                placement_receipt=config.placement_receipt,
                overlay_receipt=Path(overlay_receipt), continuous=True)
        finally:
            sys.path[:] = previous_sys_path
            if previous_pythonpath is None:
                os.environ.pop("PYTHONPATH", None)
            else:
                os.environ["PYTHONPATH"] = previous_pythonpath

class ActualAdapter:
    def __init__(self, config, platform):
        self.c, self.platform = config, platform
        self.n = config.session.resolve()
        self.root = config.state_root.resolve()
        if not self.root.is_relative_to(self.n):
            raise ValueError("watchdog state must be inside its exact session")
        self.root.mkdir(parents=True, exist_ok=True)
        self.journal_path = self.root / "watchdog-state.json"
        self.journal = maybe_json(self.journal_path) or {
            "initial_recording_request": str(config.initial_recording_request.resolve()),
            "current_request": str(config.initial_recording_request.resolve()), "active": None}
        if self.journal["initial_recording_request"] != str(config.initial_recording_request.resolve()):
            raise ValueError("configured initial segment differs from this watchdog journal")
        self.q = self.n / (config.sdk_prefix + "-queue")
        self.inbox = self.n / (config.sdk_prefix + "-requests")
        self.outbox = self.n / (config.sdk_prefix + "-responses")
        self.automatic = load_source("recording_recovery_admission_" + uuid.uuid4().hex,
                                     config.automatic_source)

    def save(self):
        atomic(self.journal_path, self.journal)

    def owned(self, path):
        path = Path(path).resolve()
        if not path.is_relative_to(self.n):
            raise ValueError("recovery path escaped session")
        return path

    def attempt(self, rid):
        active = self.journal.get("active")
        if active is None:
            observation = self.observe()
            state = shared_json(self.q / "ROOT-CUMULATIVE-LOOP-STATE.json", 262144)
            halt = shared_json(self.n / ("ROOT-CURRENT-HALT-" + self.c.sdk_prefix.upper() + ".json"), 16384)
            active = {"id": rid, "old_request": self.journal["current_request"],
                      "halt_fingerprint": hashlib.sha256(json.dumps(halt, sort_keys=True).encode()).hexdigest(),
                      "original_pending": state["pending_cycle"], "phase": "recovering"}
            self.journal["active"] = active
            self.save()
        if active["id"] != rid:
            raise ValueError("another recovery id is active")
        root = self.root / rid
        root.mkdir(exist_ok=True)
        return active, root

    def cleanup(self, root, sid):
        row = maybe_json(Path(root) / "cleanup.json")
        if row is None:
            return None
        close = row.get("engine_close") or {}
        if row.get("unknown_or_global_stop_calls", 0) != 0:
            raise ValueError("old recording cleanup invoked an unowned stop")
        return Cleanup(sid, row.get("inputs_unbound") is True,
                       close.get("actual_exit_code"), close.get("normal_exit_proven") is True,
                       close.get("forced_process_calls", -1))

    def overlay(self, row, receipt):
        return Overlay(row["overlay_pid"], row["overlay_creation_filetime"],
                       row["game_pid"], row["game_creation_filetime"],
                       row["managed_desktop_id"], Path(row["decision_text_file"]),
                       self.owned(receipt))

    def observe(self):
        request_path = (self.journal.get("active") or {}).get("old_request", self.journal["current_request"])
        request = shared_json(self.owned(request_path), 16384)
        root = self.owned(request["receipt_root"])
        if not root.is_relative_to(self.n / "recordings"):
            raise ValueError("configured recording request escaped recordings")
        job = shared_json(root / "job.json")
        launch = job["launch"]
        game = Game(job["pid"], job["game_creation_filetime"], launch["creation_date"], launch["pipe"])
        overlay_row = job["overlay"]
        overlay_path = self.n / ("ROOT-DECISION-OVERLAY-" + str(overlay_row["overlay_pid"]) + "-STARTED.json")
        if shared_json(overlay_path, 16384) != overlay_row:
            raise ValueError("job overlay differs from exact creator STARTED receipt")
        overlay = self.overlay(overlay_row, overlay_path)
        state = maybe_json(self.q / "ROOT-CUMULATIVE-LOOP-STATE.json", 262144) or {}
        halt = maybe_json(self.n / ("ROOT-CURRENT-HALT-" + self.c.sdk_prefix.upper() + ".json"), 16384) or {}
        pending = state.get("pending_cycle") or {}
        fingerprint = hashlib.sha256(json.dumps(halt, sort_keys=True).encode()).hexdigest()
        cause = None if fingerprint == self.journal.get("last_resumed_halt") else halt.get("error_type")
        verified = False
        if pending.get("stage") == "auto_verified" and type(pending.get("auto_sequence")) is int:
            response = self.outbox / f"{pending['auto_sequence']:04d}-1-result.json"
            actual = maybe_json(response, 1024**2)
            if actual:
                body = self.decode(actual)
                verified = bool(body and body.get("status") in {"executed", "observed", "readonly_rejected"})
        sdk = SdkGuard(cause == "RecordingPaused" and halt.get("original_response") is None
                       and fingerprint != self.journal.get("last_recording_attachment_halt"), cause,
                       (halt.get("original_request") or {}).get("command"),
                       pending.get("stage"), verified)
        obs_alive = True
        obs_launch = maybe_json(root / "obs-launch.json", 16384)
        if obs_launch:
            obs_alive = self.platform.alive(obs_launch["pid"], obs_launch["creation_filetime"])
        terminal = any((root / f).exists() for f in ("failed.json", "completed.json", "cleanup.json"))
        overlay_alive = self.platform.alive(overlay.pid, overlay.creation_filetime)
        recorder = Recorder(request["session_id"], game, overlay, root,
                            terminal or not obs_alive or sdk.recording_paused,
                            not terminal and obs_alive, self.cleanup(root, request["session_id"]))
        pins = shared_json(self.n / ("ROOT-ACTUAL-SDK-PROCESSES-PINNED-" + self.c.sdk_prefix.upper() + ".json"), 16384)
        if not all(self.platform.alive(p["pid"], p["creation_filetime"]) for p in pins["processes"]):
            raise ValueError("same SDK process pair is no longer alive")
        if (self.n / "EXIT-SDK").exists() or (self.n / "REQUEST-ADMISSION-CLOSED").exists():
            raise ValueError("SDK admission is closed")
        return Observation(game, self.platform.alive(game.pid, game.creation_filetime),
                           recorder, overlay_alive, sdk)

    @staticmethod
    def decode(row):
        result = row.get("result") or {}
        if result.get("is_error") is True:
            return None
        body = result.get("structured_content") or result.get("structuredContent")
        if isinstance(body, dict):
            return body
        for content in result.get("content", []):
            if content.get("type") == "text":
                try:
                    return json.loads(content["text"])
                except (ValueError, TypeError):
                    pass
        return None

    def exclusive_controls(self):
        scripts = [self.c.feeder_template]
        for path in self.root.glob("*/feeder.py"):
            scripts.append(path)
        if self.platform.scripts(scripts):
            return False
        return not any(path.is_file() and not (self.outbox / path.name).exists()
                       for path in self.inbox.glob("*.json"))

    def cleanup_old(self, old, rid):
        self.attempt(rid)
        proof = self.cleanup(old.receipt_root, old.session_id)
        if proof:
            return proof
        if not self.exclusive_controls():
            return None
        stop = old.receipt_root / "STOP-OWNED-RECORDING"
        if not stop.exists():
            atomic(stop, {"reason": "automatic_recording_recovery", "recovery_id": rid}, new=True)
        return None  # The exact existing worker performs its single normal stop/unbind/exit.

    def ensure_overlay(self, game, old, rid):
        active, root = self.attempt(rid)
        if not self.exclusive_controls():
            return None
        if self.platform.alive(old.pid, old.creation_filetime):
            return old
        intent = root / "overlay-intent.json"
        intent_row = maybe_json(intent, 16384)
        if intent_row is None:
            text = self.n / ("live-decision-auto-" + rid + ".txt")
            argv = [str(self.c.python), "-B", "-X", "utf8", str(self.c.overlay_source),
                    "--session", str(self.n), "--launch-receipt",
                    "pending-launch-receipt"]
            old_job = shared_json(Path(shared_json(active["old_request"])["receipt_root"]) / "job.json")
            argv[-1] = old_job["overlay"]["launch_receipt"]
            argv += ["--desktop-id", old.desktop_id, "--decision-text-file", str(text),
                     "--campaign-label", self.c.campaign_label]
            atomic(intent, {"argv": argv, "decision_text_file": str(text)}, new=True)
            process = self.platform.spawn(argv, root / "overlay.stdout.log", root / "overlay.stderr.log", cwd=self.n)
            atomic(root / "overlay-process.json", process, new=True)
        process = maybe_json(root / "overlay-process.json", 16384)
        if process is None:
            raise RuntimeError("overlay launch outcome unknown; intent retained, launch will not repeat")
        path = self.n / ("ROOT-DECISION-OVERLAY-" + str(process["pid"]) + "-STARTED.json")
        row = maybe_json(path, 16384)
        if row is None:
            return None
        if (row.get("overlay_creation_filetime") != process["creation_filetime"]
                or row.get("decision_text_file") != shared_json(intent)["decision_text_file"]
                or not self.platform.alive(process["pid"], process["creation_filetime"])):
            raise ValueError("new overlay creator receipt or retained generation differs")
        active["overlay_started"] = str(path)
        self.save()
        return self.overlay(row, path)

    def launch_segment(self, game, overlay, rid):
        active, root = self.attempt(rid)
        request_path = root / "recording-request.json"
        requested = maybe_json(request_path, 16384)
        if requested is None:
            intent = root / "recording-launch-intent.json"
            if intent.exists():
                raise RuntimeError("recording launch outcome unknown; no second launch is authorized")
            old = shared_json(Path(shared_json(active["old_request"])["receipt_root"]) / "job.json")
            atomic(intent, {"game": asdict(game), "overlay_started_receipt": str(overlay.started_receipt)}, new=True)
            requested = self.platform.launch_recording(self.c, old, overlay.started_receipt)
            atomic(request_path, requested, new=True)
        receipt_root = self.owned(requested["receipt_root"])
        job = shared_json(receipt_root / "job.json")
        active["new_request"] = str(request_path)
        self.save()
        return Segment(requested["session_id"], game, overlay, receipt_root, request_path,
                       job.get("continuous") is True, job.get("duration_seconds"),
                       job.get("max_output_bytes"), job.get("deadline_utc"))

    def admit_segment(self, game, overlay, segment, rid):
        active, root = self.attempt(rid)
        previous = active.get("admission")
        if previous and (root / "control-attach_recording_segment.json").exists():
            row = shared_json(previous, 16384)
            return Admission(segment.session_id, game, overlay, row["status"], row["admission_method"],
                             Path(previous), row["game_png"]["sha256"], row["scene_png"]["sha256"],
                             row["scene_overlay_diff_fraction"])
        job = shared_json(segment.receipt_root / "job.json")
        started = maybe_json(segment.receipt_root / "started.json", 16384)
        latest = maybe_json(segment.receipt_root / "recording-latest.json")
        if not started or not latest:
            return None
        frame = latest.get("frame") or {}
        assets = {}
        for key in ("game", "scene"):
            item = frame.get(key) or {}
            path = self.owned(item.get("path", ""))
            if not path.is_relative_to(segment.receipt_root):
                raise ValueError("frame PNG escaped exact new recorder")
            data = shared_bytes(path, 32 * 1024**2)
            digest = hashlib.sha256(data).hexdigest()
            if len(data) != item.get("bytes") or digest != item.get("sha256"):
                return None  # Mutable pair changed; observe a new consistent metadata pair.
            frozen = segment.receipt_root / ("continuity-" + rid + "-" + digest + "-" + key + ".png")
            if not frozen.exists():
                with frozen.open("xb") as stream:
                    stream.write(data)
            assets[key] = {"path": str(frozen), "bytes": len(data), "sha256": digest}
        frozen_frame = {"at_utc": frame["at_utc"], "mutable_latest_frame": False, **assets}
        row = self.automatic.automatic_continuity_admission(
            job=job, started=started, overlay_started=shared_json(overlay.started_receipt, 16384),
            overlay_started_path=overlay.started_receipt, frame=frozen_frame,
            session_root=self.n, now_utc=utc())
        tag = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()[:20]
        path = root / ("automatic-admission-" + tag + ".json")
        if not path.exists():
            atomic(path, row, new=True)
        active["admission"] = str(path)
        self.save()
        return Admission(segment.session_id, game, overlay, row["status"],
                         row["admission_method"], path, assets["game"]["sha256"],
                         assets["scene"]["sha256"], row["scene_overlay_diff_fraction"])

    def control(self, name, arguments, rid):
        active, root = self.attempt(rid)
        receipt = root / ("control-" + name + ".json")
        plan = maybe_json(receipt, 16384)
        if plan is None:
            if not self.exclusive_controls():
                return None
            next_path = self.n / ("NEXT-SEQUENCE-" + self.c.sdk_prefix.upper() + ".json")
            sequence = shared_json(next_path, 16384)["next_sequence"]
            if type(sequence) is not int or sequence <= 0:
                raise ValueError("current local queue sequence is malformed")
            request = {"sequence": sequence, "command": name, "arguments": arguments}
            plan = {"request": request, "response": str(self.outbox / f"{sequence:04d}-1-result.json")}
            atomic(receipt, plan, new=True)
        request = plan["request"]
        if request["command"] != name or request["arguments"] != arguments:
            raise ValueError("idempotent local control arguments changed")
        response_path = self.owned(plan["response"])
        if response_path.exists():
            row = shared_json(response_path)
            if row.get("request") != request:
                raise ValueError("original local control response differs")
            body = self.decode(row)
            if body is None or (row.get("result") or {}).get("is_error") is not False:
                raise RuntimeError("local control outcome failed/unknown; never repeat")
            return body
        inbox = self.inbox / response_path.name
        if inbox.exists():
            if shared_json(inbox, 16384) != request:
                raise ValueError("local control number occupied by another request")
            return None
        if not self.exclusive_controls():
            return None
        current = shared_json(self.n / ("NEXT-SEQUENCE-" + self.c.sdk_prefix.upper() + ".json"), 16384)
        if current["next_sequence"] != request["sequence"]:
            raise RuntimeError("control publication outcome unknown; sequence advanced, no replay")
        atomic(inbox, request, new=True)
        return None

    def attach_recording_segment(self, old, segment, admission, rid):
        body = self.control("attach_recording_segment", {
            "recording_job_root": str(segment.receipt_root),
            "first_frame_admission": str(admission.receipt_path),
            "recording_request_receipt": str(segment.request_receipt)}, rid)
        if body is None:
            return None
        if (body.get("old_job") != str(old.receipt_root) or body.get("new_job") != str(segment.receipt_root)
                or body.get("game_pid") != old.game.pid):
            raise ValueError("local attached segment identity differs")
        return Attach(body["status"], old.session_id, segment.session_id, old.game,
                      body.get("rpc_calls"), body.get("replay_allowed") is not False)

    def resume_recording_pause(self, rid):
        body = self.control("resume_recording_pause", {}, rid)
        if body is None:
            return None
        active, root = self.attempt(rid)
        if (body.get("status") != "recording_guard_pause_resumed"
                or body.get("pending_cycle_preserved") is not True
                or body.get("original_AUTO_replayed") is not False):
            raise ValueError("local resume did not preserve the exact pending cycle")
        active["phase"] = "settle"
        self.journal["last_resumed_halt"] = active["halt_fingerprint"]
        self.save()
        return Resume(body.get("status"), body.get("pending_cycle_preserved") is True,
                      body.get("original_AUTO_replayed") is not False)

    def drive_attach_only(self, supervisor):
        """Restore capture independently; retain every gameplay halt/bookkeeping field."""
        obs = self.observe()
        if not obs.game_alive_exact:
            return "blocked_game_identity"
        if not obs.recorder.failed and obs.overlay_alive_exact:
            return "healthy"
        if obs.sdk.halt_cause is None:
            return "waiting_sdk_halt"
        rid = hashlib.sha256(
            f"{obs.game.pid}:{obs.game.creation_filetime}:{obs.recorder.session_id}".encode()).hexdigest()[:32]
        active, root = self.attempt(rid)
        if active.get("mode") not in (None, "attach_only"):
            raise ValueError("recovery mode differs from the retained journal")
        active["mode"] = "attach_only"
        active["phase"] = "capture_only"
        self.save()
        if not self.exclusive_controls():
            return "waiting_feeder_exit"
        proof = obs.recorder.cleanup or self.cleanup_old(obs.recorder, rid)
        if proof is None:
            return "waiting_normal_cleanup"
        if (proof.session_id != obs.recorder.session_id or not proof.inputs_unbound
                or proof.actual_exit_code != 0 or not proof.normal_exit_proven
                or proof.forced_process_calls != 0):
            raise ValueError("capture-only recovery lacks normal old OBS cleanup")
        overlay = self.ensure_overlay(obs.game, obs.recorder.overlay, rid)
        if overlay is None:
            return "waiting_overlay"
        attempt = {"game": obs.game, "old": obs.recorder,
                   "old_overlay_alive": obs.overlay_alive_exact, "overlay": overlay}
        supervisor._check_overlay(overlay, attempt)
        segment = self.launch_segment(obs.game, overlay, rid)
        if segment is None:
            return "waiting_segment"
        supervisor._check_segment(segment, attempt)
        attempt["segment"] = segment
        admission = self.admit_segment(obs.game, overlay, segment, rid)
        if admission is None:
            return "waiting_frame"
        supervisor._check_admission(admission, attempt)
        attached = self.attach_recording_segment(obs.recorder, segment, admission, rid)
        if attached is None:
            return "waiting_attach"
        if (attached.status != "same_game_recording_segment_attached"
                or attached.rpc_calls != 0 or attached.replay_allowed):
            raise ValueError("capture-only local attachment was not verified")
        halt = shared_json(self.n / ("ROOT-CURRENT-HALT-" + self.c.sdk_prefix.upper() + ".json"), 16384)
        fingerprint = hashlib.sha256(json.dumps(halt, sort_keys=True).encode()).hexdigest()
        state = shared_json(self.q / "ROOT-CUMULATIVE-LOOP-STATE.json", 262144)
        if fingerprint != active["halt_fingerprint"] or state.get("pending_cycle") != active["original_pending"]:
            raise ValueError("business halt or original pending cycle changed during capture-only attachment")
        completion = {"recovery_id": rid, "mode": "attach_only",
                      "old_request": active["old_request"], "new_request": active["new_request"],
                      "business_halt_preserved": True, "pending_cycle_preserved": True,
                      "resume_controls_published": False, "settle_controls_published": False,
                      "original_AUTO_replayed": False, "game_restarted": False,
                      "at_utc": utc().isoformat()}
        if not (root / "ATTACH-ONLY-COMPLETE.json").exists():
            atomic(root / "ATTACH-ONLY-COMPLETE.json", completion, new=True)
        self.journal["current_request"] = active["new_request"]
        self.journal["last_recording_attachment_halt"] = fingerprint
        self.journal["active"] = None
        self.save()
        return "capture_restored_business_halt_preserved"

    def render_feeder(self, path, first_sequence):
        source = self.c.feeder_template.read_text(encoding="utf-8-sig")
        tree = ast.parse(source)
        replacements = []
        lines = source.splitlines(keepends=True)
        offsets = [0]
        for line in lines:
            offsets.append(offsets[-1] + len(line))
        for node in tree.body:
            value = None
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id == "N":
                    value = "N = Path(" + repr(str(self.n)) + ")"
                elif node.targets[0].id == "FIRST_CONTROL_SEQUENCE":
                    value = "FIRST_CONTROL_SEQUENCE = " + str(first_sequence)
            if isinstance(node, ast.FunctionDef) and node.name == "read":
                value = "def read(path):\n    return shared_json(path)"
            if value is not None:
                replacements.append((offsets[node.lineno-1], offsets[node.end_lineno], value + "\n"))
        if len(replacements) != 3:
            raise ValueError("configured feeder template lacks exact existing N/first/read bindings")
        for a, b, value in sorted(replacements, reverse=True):
            source = source[:a] + value + source[b:]
        insertion = "\nimport sys\nsys.path.insert(0, " + repr(str(Path(__file__).resolve().parent)) + ")\nfrom recording_recovery_adapter import shared_json\n"
        marker = "from pathlib import Path"
        source = source.replace(marker, marker + insertion, 1)
        old_prefix = self.c.feeder_template.stem.split("_")[1]
        if old_prefix.lower().startswith("p") and old_prefix[1:].isdigit():
            source = source.replace(old_prefix.lower(), self.c.sdk_prefix.lower()).replace(old_prefix.upper(), self.c.sdk_prefix.upper())
        ast.parse(source)
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(source)

    def finish_continuation(self):
        active = self.journal.get("active")
        if not active or active.get("phase") != "settle":
            return None
        rid = active["id"]
        original = active["original_pending"]
        root = self.root / rid
        plan = maybe_json(root / "control-full_loop.json", 16384)
        if plan is None:
            state = shared_json(self.q / "ROOT-CUMULATIVE-LOOP-STATE.json", 262144)
            pending = state.get("pending_cycle") or {}
            if (pending.get("stage") != "auto_verified"
                    or pending.get("auto_sequence") != original["auto_sequence"]
                    or pending.get("global_turn") != original["global_turn"]):
                raise ValueError("original auto_verified cycle changed before settle; never replay")
        result = self.control("full_loop", {"max_turns": 1}, rid)
        if result is None:
            return "waiting_settle"
        state = shared_json(self.q / "ROOT-CUMULATIVE-LOOP-STATE.json", 262144)
        settled = shared_json(self.q / f"CUMULATIVE-TURN-{original['global_turn']:06d}.json", 262144)
        if (result.get("status") != "bounded_loop_finished"
                or state.get("completed_cycles") != original["global_turn"]
                or state.get("pending_cycle") is not None
                or settled.get("auto_sequence") != original["auto_sequence"]
                or not settled.get("after_metrics_response")):
            raise ValueError("settle did not finish exactly the retained original AUTO")
        if result.get("same_SDK_continuation_available") is not True:
            active["continuation_terminal"] = True
        stop = self.n / ("ROOT-CONTINUOUS-FEEDER-STOP-" + self.c.sdk_prefix.upper())
        process_path = root / "feeder-process.json"
        if not active.get("continuation_terminal") and not stop.exists():
            process = maybe_json(process_path, 16384)
            if process is None:
                intent = root / "feeder-launch-intent.json"
                if intent.exists():
                    raise RuntimeError("feeder launch outcome unknown; will not launch twice")
                if not self.exclusive_controls():
                    return "waiting_feeder_exit"
                first = shared_json(root / "control-full_loop.json")["request"]["sequence"]
                feeder = root / "feeder.py"
                self.render_feeder(feeder, first)
                argv = [str(self.c.python), "-B", "-X", "utf8", str(feeder)]
                atomic(intent, {"argv": argv, "first_control_sequence": first}, new=True)
                process = self.platform.spawn(argv, root / "feeder.stdout.log", root / "feeder.stderr.log", cwd=self.n)
                atomic(process_path, process, new=True)
        self.journal["current_request"] = active["new_request"]
        completion = {"recovery_id": rid, "old_request": active["old_request"],
               "new_request": active["new_request"], "original_auto_sequence": original["auto_sequence"],
               "settled_global_turn": original["global_turn"], "original_AUTO_replayed": False,
               "game_restarted": False, "at_utc": utc().isoformat()}
        if not (root / "COMPLETE.json").exists():
            atomic(root / "COMPLETE.json", completion, new=True)
        else:
            prior = shared_json(root / "COMPLETE.json", 16384)
            if prior.get("recovery_id") != rid or prior.get("original_auto_sequence") != original["auto_sequence"]:
                raise ValueError("existing recovery completion identity differs")
        self.journal["active"] = None
        self.save()
        return "complete"

def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--session", type=Path, required=True)
    p.add_argument("--sdk-prefix", required=True)
    p.add_argument("--initial-recording-request", type=Path, required=True)
    p.add_argument("--overlay-source", type=Path, required=True)
    p.add_argument("--provider-source", type=Path, required=True)
    p.add_argument("--feeder-template", type=Path, required=True)
    p.add_argument("--automatic-source", type=Path, default=Path(__file__).with_name("automatic_continuity.py"))
    p.add_argument("--state-root", type=Path)
    p.add_argument("--placement-receipt", type=Path)
    p.add_argument("--python", type=Path, default=Path(sys.executable))
    p.add_argument("--campaign-label", default="Continuous CK3 campaign")
    p.add_argument("--poll-seconds", type=float, default=2)
    p.add_argument("--attach-only", action="store_true",
                   help="Restore capture and attach only; retain a mixed/business halt without resume or settle.")
    p.add_argument("--once", action="store_true", help="One bounded policy poll; real effects are possible.")
    return p

def main():
    c = parser().parse_args()
    c.session = c.session.resolve(strict=True)
    c.sdk_prefix = c.sdk_prefix.lower()
    if not c.sdk_prefix.startswith("p") or not c.sdk_prefix[1:].isdigit() or not 0.1 <= c.poll_seconds <= 60:
        raise ValueError("explicit pNN SDK prefix and finite polling interval required")
    c.state_root = c.state_root or c.session / ("automatic-recording-recovery-" + c.sdk_prefix)
    c.placement_receipt = c.placement_receipt or c.session / "ROOT-GAME-PLACEMENT.json"
    for name in ("overlay_source", "provider_source", "feeder_template", "automatic_source", "initial_recording_request"):
        setattr(c, name, getattr(c, name).resolve(strict=True))
    c.state_root.mkdir(parents=True, exist_ok=True)
    platform = WindowsPlatform().lock(c.state_root / "watchdog.lock")
    try:
        adapter = ActualAdapter(c, platform)
        supervisor = RecoverySupervisor(adapter, session_root=c.session)
        while True:
            try:
                if c.attach_only:
                    result = {"status": adapter.drive_attach_only(supervisor), "stage": "capture_only"}
                elif (adapter.journal.get("active") or {}).get("mode") == "attach_only":
                    raise ValueError("retained capture-only recovery requires --attach-only")
                elif (adapter.journal.get("active") or {}).get("phase") == "settle":
                    result = {"status": adapter.finish_continuation(), "stage": "settle"}
                else:
                    progress = supervisor.drive()
                    result = asdict(progress)
                    if progress.status == "complete":
                        result["continuation"] = adapter.finish_continuation()
                atomic(c.state_root / "STATUS.json", {"at_utc": utc().isoformat(), **result})
            except Exception as error:
                atomic(c.state_root / "STATUS.json", {"status": "blocked", "error_type": type(error).__name__,
                       "reason": str(error)[:2048], "at_utc": utc().isoformat()})
            if c.once:
                return
            time.sleep(c.poll_seconds)
    finally:
        platform.close()

if __name__ == "__main__":
    main()
