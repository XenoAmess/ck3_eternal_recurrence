"""Dedicated, bounded OBS Game texture plus independent decision-text source.

Only a fresh portable configuration and newly launched engine are accepted.
No desktop source, input, shared OBS attachment or process termination fallback.
Frame/probe receipts require Root review; they do not infer gameplay success.
"""
from __future__ import annotations
import argparse
import base64
import ctypes
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import logging
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
import uuid

PROVIDER_VERSION = "2.0.0"
SCHEMA = "xar.ck3.obs-window-capture.v2"
ALLOWED_SECONDS = frozenset({15, 30, 45, 60, 90, 120})


def _write_new(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _response_data(value):
    return {key: getattr(value, key) for key in value.attrs()}


def _generation_helpers():
    sys.path.insert(0, str(Path(__file__).resolve().parent / "g2_saved_campaign"))
    from managed_desktop1_placement import ProcessGeneration, game_generation, check_game_window, deadline_check
    return ProcessGeneration, game_generation, check_game_window, deadline_check


def _control(profile):
    root = Path(profile["control_dependencies"]).resolve(strict=True)
    versions = {d.metadata["Name"].lower(): d.version
                for d in importlib.metadata.distributions(path=[str(root)])}
    if versions.get("obsws-python") != "1.8.0" or versions.get("websocket-client") != "1.9.2":
        raise RuntimeError("explicit control root must contain obsws-python1.8.0 and websocket-client1.9.2")
    for name, module in list(sys.modules.items()):
        if name == "obsws_python" or name.startswith("obsws_python.") or name == "websocket" or name.startswith("websocket."):
            origin = getattr(module, "__file__", None)
            if not origin or not Path(origin).resolve().is_relative_to(root):
                raise RuntimeError("OBS dependencies were loaded from an ambient root")
    sys.path.insert(0, str(root))
    import obsws_python as obs
    import websocket
    if any(not Path(module.__file__).resolve().is_relative_to(root) for module in (obs, websocket)):
        raise RuntimeError("OBS control import escaped its explicit root")
    logging.getLogger("obsws_python").setLevel(logging.WARNING)
    return obs


def _listeners(port):
    import psutil
    # Access denial is a failure, never an empty/free port claim.
    return [row for row in psutil.net_connections(kind="tcp")
            if row.status == psutil.CONN_LISTEN and row.laddr.port == port]


def _port_owner(port, pid):
    rows = _listeners(port)
    if not rows or any(row.pid != pid for row in rows):
        raise RuntimeError("listener is absent, unreadable or owned by another process")


def validate_profile(profile):
    if (profile.get("schema") != SCHEMA or profile.get("strict_isolation") is not True
            or profile.get("host") != "127.0.0.1" or type(profile.get("port")) is not int
            or not 1024 <= profile["port"] <= 65535):
        raise ValueError("explicit isolated local OBS profile/port required")
    root = Path(profile["obs_root"]).resolve()
    if (Path(profile["executable"]).resolve() != root / "bin/64bit/obs64.exe"
            or Path(profile["config_root"]).resolve() != root / "config/obs-studio"):
        raise ValueError("OBS executable/config escaped the explicit portable tree")
    name = profile["profile_name"]
    if not isinstance(name, str) or not name.startswith("ManagedWindowCapture-"):
        raise ValueError("owned UUID profile required")
    uuid.UUID(hex=name.removeprefix("ManagedWindowCapture-"))
    if profile["collection_name"] != name:
        raise ValueError("OBS profile and collection must share one owned UUID")
    if (type(profile["max_output_bytes"]) is not int
            or not 192 * 1024**2 <= profile["max_output_bytes"] <= 1024**3):
        raise ValueError("recording allocation must be 192MiB..1GiB, including metadata/stop reserve")


def prepare_profile(obs_root: Path, profile_path: Path, recording_root: Path, *,
                    port: int, control_dependencies: Path, deadline_utc: str,
                    max_output_bytes: int, bitrate_kbps: int = 4800) -> Path:
    _, _, _, deadline_check = _generation_helpers()
    deadline_check(deadline_utc)
    obs_root, profile_path, recording_root = (p.resolve() for p in (obs_root, profile_path, recording_root))
    executable = obs_root / "bin/64bit/obs64.exe"
    if not executable.is_file() or profile_path.exists():
        raise ValueError("explicit OBS executable and new profile receipt required")
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError("explicit dedicated local port required")
    if type(max_output_bytes) is not int or not 192 * 1024**2 <= max_output_bytes <= 1024**3:
        raise ValueError("Root recording allocation must include finite metadata/stop reserve")
    if type(bitrate_kbps) is not int or not 0 < bitrate_kbps <= 5000:
        raise ValueError("recording bitrate may not exceed 5Mbps")
    if _listeners(port):
        raise RuntimeError("dedicated OBS port is already occupied")
    config = obs_root / "config/obs-studio"
    if config.exists() or (obs_root / "portable_mode.txt").exists():
        raise FileExistsError("refusing an existing portable configuration")
    name = "ManagedWindowCapture-" + uuid.uuid4().hex
    profile = {"schema": SCHEMA, "provider_version": PROVIDER_VERSION, "strict_isolation": True,
        "obs_root": str(obs_root), "executable": str(executable), "executable_sha256": _sha(executable),
        "config_root": str(config), "profile_name": name, "collection_name": name,
        "host": "127.0.0.1", "port": port, "password": secrets.token_urlsafe(32),
        "control_dependencies": str(control_dependencies.resolve()), "recording_root": str(recording_root),
        "deadline_utc": deadline_utc, "max_output_bytes": max_output_bytes,
        "bitrate_kbps": bitrate_kbps, "width": 2560, "height": 1440, "fps": 30}
    validate_profile(profile)
    _control(profile)  # Existing explicit dependencies only; installs nothing.
    basic = config / "basic/profiles" / name
    basic.mkdir(parents=True)
    recording_root.mkdir(parents=True, exist_ok=True)
    with (obs_root / "portable_mode.txt").open("x", encoding="utf-8") as stream:
        stream.write("")
    (config / "global.ini").write_text(
        "[General]\nFirstRun=false\nLastVersion=503382018\nEnableAutoUpdates=false\n"
        f"[Basic]\nProfile={name}\nProfileDir={name}\nSceneCollection={name}\nSceneCollectionFile={name}\n"
        "[BasicWindow]\nPreviewEnabled=false\nStudioMode=false\nSysTrayEnabled=true\n"
        f"[OBSWebSocket]\nFirstLoad=false\nServerEnabled=true\nServerPort={port}\nAlertsEnabled=false\nAuthRequired=true\nServerPassword={profile['password']}\n", encoding="utf-8")
    # Record with the CBR stream encoder settings; no stream is started.
    (basic / "basic.ini").write_text(
        f"[General]\nName={name}\n[Output]\nMode=Simple\nFilenameFormatting=managed\n"
        f"[SimpleOutput]\nRecFilePath={recording_root.as_posix()}\nRecFormat=mkv\nRecQuality=Stream\n"
        f"StreamEncoder=nvenc\nVBitrate={bitrate_kbps}\nNVENCPreset2=p5\n"
        "[Video]\nBaseCX=2560\nBaseCY=1440\nOutputCX=2560\nOutputCY=1440\nFPSType=0\nFPSCommon=30\n"
        "ColorFormat=NV12\nColorSpace=709\nColorRange=Partial\n"
        "[Audio]\nSampleRate=48000\nChannelSetup=Stereo\nDesktopDevice1=disabled\nDesktopDevice2=disabled\n"
        "AuxDevice1=disabled\nAuxDevice2=disabled\nAuxDevice3=disabled\n", encoding="utf-8")
    scenes = config / "basic/scenes"
    scenes.mkdir(parents=True)
    _write_new(scenes / (name + ".json"), {
        "name": name, "current_scene": name, "current_program_scene": name,
        "scene_order": [{"name": name}], "groups": [], "transitions": [],
        "sources": [{"name": name, "id": "scene", "versioned_id": "scene", "settings": {"items": []}}]})
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    _write_new(profile_path, profile)
    return profile_path


def validate_job(job):
    if job.get("schema") != SCHEMA or type(job.get("duration_seconds")) is not int or not 1 <= job["duration_seconds"] <= 1200:
        raise ValueError("recording must be finite and at most 20 minutes")
    if any(type(job.get(key)) is not int or job[key] <= 0 for key in ("pid", "hwnd")):
        raise ValueError("exact Game PID/HWND required")
    uuid.UUID(job["session_id"])
    if not Path(job["receipt_root"]).resolve().is_relative_to(Path(job["recording_root"]).resolve()):
        raise ValueError("receipt scope escaped the recording root")
    if type(job.get("max_output_bytes")) is not int or not 192 * 1024**2 <= job["max_output_bytes"] <= 1024**3:
        raise ValueError("bounded recording allocation required")
    signal = job.get("start_signal")
    if signal is not None and (not isinstance(signal, str) or not signal
            or not Path(signal).resolve().is_relative_to(Path(job["recording_root"]).resolve())):
        raise ValueError("recording start signal must remain in this recording root")
    mode = job.get("capture_mode")
    if mode not in ("game_only", "game_decision"):
        raise ValueError("use the fixed Game-only or Game+decision contract")
    if mode == "game_only":
        if any(job.get(key) is not None for key in ("overlay", "desktop_id", "decision_text_file", "game_creation_filetime")):
            raise ValueError("Game-only capture may not contain a partial decision/desktop group")
    elif (not isinstance(job.get("overlay"), dict) or not job.get("decision_text_file")
          or not job.get("desktop_id") or type(job.get("game_creation_filetime")) is not int
          or job["game_creation_filetime"] <= 0):
        raise ValueError("Game+decision capture requires the complete attested group")


def launch_recording(profile_path, recording_root, pid, hwnd, seconds, *,
                     launch_receipt, ffprobe, placement_receipt=None, overlay_receipt=None,
                     start_signal=None):
    """Products may record only Game; fresh-agent calls supply the complete group."""
    if (placement_receipt is None) != (overlay_receipt is None):
        raise ValueError("placement and decision Overlay receipts must be supplied together")
    profile, launch = map(_read, (profile_path, launch_receipt))
    placement, overlay, text = None, None, None
    with_decision = overlay_receipt is not None
    validate_profile(profile)
    if profile.get("schema") != SCHEMA or profile.get("strict_isolation") is not True:
        raise ValueError("legacy/shared OBS profiles are not admitted")
    if Path(profile["recording_root"]).resolve() != Path(recording_root).resolve():
        raise ValueError("profile and recording roots differ")
    if start_signal is not None:
        start_signal = Path(start_signal).resolve()
        if not start_signal.is_relative_to(Path(recording_root).resolve()) or start_signal.exists():
            raise ValueError("recording start signal must be new in this recording root")
    if type(launch.get("pid")) is not int or launch["pid"] != pid:
        raise ValueError("launch receipt differs from the explicit Game PID")
    if with_decision:
        placement, overlay = map(_read, (placement_receipt, overlay_receipt))
        if (placement.get("status") != "GREEN" or placement.get("pid") != pid or placement.get("hwnd") != hwnd
                or overlay.get("game_pid") != pid or overlay.get("game_hwnd") != hwnd
                or overlay.get("game_creation_filetime") != placement.get("creation_filetime")
                or overlay.get("managed_desktop_id") != placement.get("target_desktop_id")):
            raise ValueError("matching actual placement and Overlay generation receipts required")
        text = Path(overlay["decision_text_file"]).resolve(strict=True)
        if not text.is_relative_to(Path(overlay["session"]).resolve()) or text.stat().st_size > 32768:
            raise ValueError("decision text escaped its finite session scope")
    probe = Path(ffprobe).resolve(strict=True)
    if probe.name.casefold() != "ffprobe.exe":
        raise ValueError("explicit existing ffprobe.exe required")
    session = str(uuid.uuid4())
    root = Path(recording_root).resolve() / session
    job = {"schema": SCHEMA, "session_id": session, "provider_version": PROVIDER_VERSION,
        "profile_path": str(Path(profile_path).resolve()), "profile_sha256": _sha(profile_path),
        "recording_root": str(Path(recording_root).resolve()), "receipt_root": str(root),
        "pid": pid, "hwnd": hwnd, "duration_seconds": seconds, "launch": launch,
        "capture_mode": "game_decision" if with_decision else "game_only",
        "game_creation_filetime": placement["creation_filetime"] if with_decision else None,
        "desktop_id": placement["target_desktop_id"] if with_decision else None,
        "overlay": overlay, "decision_text_file": str(text) if text else None, "ffprobe": str(probe),
        "deadline_utc": profile["deadline_utc"], "max_output_bytes": profile["max_output_bytes"]}
    if start_signal is not None:
        job["start_signal"] = str(start_signal)
    validate_job(job)
    _, _, _, deadline_check = _generation_helpers()
    deadline_check(job["deadline_utc"])
    end = datetime.fromisoformat(job["deadline_utc"].replace("Z", "+00:00"))
    if (end - datetime.now(timezone.utc)).total_seconds() < seconds + 90:
        raise ValueError("recording plus cleanup does not fit the original deadline")
    root.mkdir()
    path = root / "job.json"
    _write_new(path, job)
    with (root / "worker.stdout.txt").open("x", encoding="utf-8") as stdout, (root / "worker.stderr.txt").open("x", encoding="utf-8") as stderr:
        worker = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "--job", str(path)],
            stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return {"schema": SCHEMA, "session_id": session, "worker_pid": worker.pid,
            "receipt_root": str(root), "state": "requested", "runtime_qualified": False}


def _window_identity(hwnd, expected_pid):
    import win32gui
    import win32process
    windows = []
    def collect(candidate, _):
        if win32gui.IsWindowVisible(candidate) and win32gui.GetWindowText(candidate) == "Crusader Kings III":
            windows.append((candidate, win32process.GetWindowThreadProcessId(candidate)[1]))
    win32gui.EnumWindows(collect, None)
    if windows != [(hwnd, expected_pid)]:
        raise RuntimeError("OBS title selector is not unique to the owned Game window")
    escape = lambda value: value.replace("#", "#22").replace(":", "#3A")
    return ":".join(map(escape, ("Crusader Kings III", win32gui.GetClassName(hwnd), "ck3.exe")))


class OwnedEngine:
    def __init__(self, profile, job):
        self.profile, self.job = profile, job
        self.client = self.generation = self.process = None
        self.obs = _control(profile)

    def check(self):
        self.generation.check()
        _port_owner(self.profile["port"], self.process.pid)
        if _sha(self.job["profile_path"]) != self.job["profile_sha256"]:
            raise RuntimeError("immutable OBS profile receipt changed")

    def connect(self):
        self.check()
        client = self.obs.ReqClient(host="127.0.0.1", port=self.profile["port"], password=self.profile["password"], timeout=10)
        try:
            if (client.get_profile_list().current_profile_name != self.profile["profile_name"]
                    or client.get_scene_collection_list().current_scene_collection_name != self.profile["collection_name"]):
                raise RuntimeError("OBS profile/collection identity differs")
        except Exception:
            client.disconnect()
            raise
        self.client = client
        return client

    def start(self):
        import psutil
        from obsws_python.error import OBSSDKRequestError
        if _listeners(self.profile["port"]):
            raise RuntimeError("dedicated OBS port became occupied")
        executable = Path(self.profile["executable"]).resolve(strict=True)
        if _sha(executable) != self.profile["executable_sha256"]:
            raise RuntimeError("OBS executable changed after preparation")
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        argv = [str(executable), "--portable", "--multi", "--minimize-to-tray", "--disable-updater",
                "--disable-missing-files-check", "--profile", self.profile["profile_name"],
                "--collection", self.profile["collection_name"]]
        self.process = subprocess.Popen(argv, cwd=str(executable.parent), startupinfo=startup,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ProcessGeneration, _, _, _ = _generation_helpers()
        self.generation = ProcessGeneration(self.process.pid, executable)
        _write_new(Path(self.job["receipt_root"]) / "obs-launch.json", {
            "pid": self.process.pid, "creation_filetime": self.generation.creation_filetime,
            "executable": str(executable), "executable_sha256": self.profile["executable_sha256"],
            "profile_name": self.profile["profile_name"], "collection_name": self.profile["collection_name"],
            "port": self.profile["port"], "argv": argv})
        if psutil.Process(self.process.pid).cmdline() != argv:
            raise RuntimeError("OBS command line differs from its isolated argv")
        for _ in range(40):
            self.generation.check()
            if _listeners(self.profile["port"]):
                try:
                    return self.connect()
                except OBSSDKRequestError as error:
                    if (type(error.code) is not int or error.code != 207
                            or error.req_name not in {"GetProfileList", "GetSceneCollectionList"}):
                        raise
            time.sleep(1)
        raise TimeoutError("owned OBS listener did not become ready")

    def reconnect(self):
        if self.client:
            self.client.disconnect()
        return self.connect()

    def close(self):
        """Only WM_CLOSE on this retained generation; never a kill fallback."""
        if not self.generation:
            return {"requested": False, "reason": "not_launched"}
        import win32gui
        import win32process
        if self.process.poll() is not None:
            result = {"requested": False, "actual_exit_code": self.process.returncode}
        else:
            self.generation.check()
            windows = []
            def collect(hwnd, _):
                if (win32process.GetWindowThreadProcessId(hwnd)[1] == self.process.pid
                        and win32gui.GetWindowText(hwnd).startswith("OBS ")
                        and win32gui.GetClassName(hwnd).startswith("Qt")):
                    windows.append(hwnd)
            win32gui.EnumWindows(collect, None)
            if len(windows) != 1:
                raise RuntimeError("owned OBS main window is not unique")
            hwnd = windows[0]
            self.generation.check()
            if win32process.GetWindowThreadProcessId(hwnd)[1] != self.process.pid:
                raise RuntimeError("OBS close window changed generation")
            win32gui.PostMessage(hwnd, 0x0010, 0, 0)
            try:
                actual = self.process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                actual = None
            result = {"requested": bool(windows), "actual_exit_code": actual,
                      "normal_exit_proven": actual == 0, "forced_process_calls": 0}
        self.generation.close()
        return result


def _output_binding(engine):
    engine.check()
    client, profile, job = engine.client, engine.profile, engine.job
    if (client.get_profile_list().current_profile_name != profile["profile_name"]
            or client.get_scene_collection_list().current_scene_collection_name != profile["collection_name"]
            or client.get_profile_parameter("Output", "FilenameFormatting").parameter_value != job["session_id"]
            or Path(client.get_record_directory().record_directory).resolve() != Path(job["recording_root"]).resolve()
            or client.get_scene_list().current_program_scene_name != profile["profile_name"]):
        raise RuntimeError("dedicated OBS output/profile/scene ownership changed")


def _inactive_engine_binding(engine):
    engine.check()
    client = engine.client
    if (client.get_profile_list().current_profile_name != engine.profile["profile_name"]
            or client.get_scene_collection_list().current_scene_collection_name != engine.profile["collection_name"]
            or client.get_record_status().output_active):
        raise RuntimeError("early cleanup requires the same dedicated inactive engine")


def _unbind_owned_inputs(engine, owned_sources, configured):
    """Remove each owned input once, then observe asynchronous GUI completion."""
    def remaining():
        _inactive_engine_binding(engine)
        if configured:
            _output_binding(engine)
        names = {item["inputName"] for item in engine.client.get_input_list().inputs}
        if names - set(owned_sources):
            raise RuntimeError("unknown OBS inputs remain attached")
        return names

    attached = remaining()
    for name in reversed(owned_sources):
        if name in attached:
            engine.check()
            engine.client.remove_input(name)
    for _ in range(40):
        if not remaining():
            return True
        time.sleep(.25)
    raise TimeoutError("owned OBS input removal was submitted but remains unobserved")


def _job_bytes(job):
    output = Path(job["recording_root"])
    root = Path(job["receipt_root"])
    videos = [p for p in output.iterdir() if p.is_file() and p.stem == job["session_id"]]
    video_bytes = sum(p.stat().st_size for p in videos)
    return video_bytes, video_bytes + sum(p.stat().st_size for p in root.iterdir() if p.is_file())


def _settings_match(actual, expected):
    """OBS may add native defaults; every explicitly owned value must match."""
    if not isinstance(actual, dict):
        return False
    return all(_settings_match(actual.get(key), value) if isinstance(value, dict)
               else actual.get(key) == value for key, value in expected.items())


def _wait_for_start_signal(job, check, screenshots, ready_frame):
    """Keep owned sources reviewable while Root chooses the recording start."""
    if job.get("start_signal") is None:
        return
    root, signal = Path(job["receipt_root"]), Path(job["start_signal"])
    check()
    _write_new(root / "record-armed.json", {
        "state": "awaiting_start_signal", "at_utc": datetime.now(timezone.utc).isoformat(),
        "start_signal": str(signal), "game_pid": job["pid"], "game_hwnd": job["hwnd"],
        "ready_frame": ready_frame, "recording_started": False})
    screenshot_at = time.monotonic() + 15
    while True:
        check()
        if (root / "STOP-OWNED-RECORDING").is_file():
            raise RuntimeError("owned shutdown requested before recording start")
        if signal.is_file():
            _write_new(root / "start-signal-observed.json", {
                "at_utc": datetime.now(timezone.utc).isoformat(), "path": str(signal)})
            return
        if time.monotonic() >= screenshot_at:
            frame = screenshots("armed-latest", replace_latest=True)
            latest = root / "armed-latest.json"
            pending = latest.with_suffix(".json.tmp")
            _write_new(pending, {"state": "awaiting_start_signal", "mutable_latest_frame": True,
                                 "frame": frame, "recording_started": False})
            pending.replace(latest)
            screenshot_at = time.monotonic() + 15
        time.sleep(.5)


class FileGrowthWatch:
    """Independent file polling and one stop attempt on a separate WS socket."""
    def __init__(self, engine, seconds, start_monotonic):
        self.engine, self.seconds, self.start_monotonic = engine, seconds, start_monotonic
        self.requested, self.done = threading.Event(), threading.Event()
        self.reason, self.output, self.error = None, None, None
        self.stop_confirmed = False
        self.samples, self.peak = [], 0
        self.thread = threading.Thread(target=self.run, name="owned-recording-growth", daemon=True)

    def start(self):
        self.thread.start()

    def request_stop(self, reason):
        if self.reason is None:
            self.reason = reason
        self.requested.set()

    def run(self):
        job = self.engine.job
        end = self.start_monotonic + max(.25, self.seconds - min(10, self.seconds * .05))
        previous, changed = 0, time.monotonic()
        try:
            while not self.requested.is_set():
                try:
                    if (Path(job["receipt_root"]) / "STOP-OWNED-RECORDING").is_file():
                        self.request_stop("owned_shutdown_requested")
                        break
                    _, _, _, deadline_check = _generation_helpers()
                    deadline_check(job["deadline_utc"])
                    video, total = _job_bytes(job)
                    self.peak = max(self.peak, total)
                    self.samples.append({"at_utc": datetime.now(timezone.utc).isoformat(),
                                         "file_bytes": video, "output_logical_bytes": total})
                    if total >= job["max_output_bytes"] - 96 * 1024**2:
                        raise RuntimeError("actual output reached the reserved stop margin")
                    if video > previous:
                        previous, changed = video, time.monotonic()
                    elif time.monotonic() - changed > 30:
                        raise RuntimeError("actual video file did not grow for over 30 seconds")
                    if time.monotonic() >= end:
                        self.request_stop("duration_reached")
                        break
                except Exception as error:
                    self.error = str(error)
                    self.request_stop("file_or_deadline_guard")
                    break
                self.requested.wait(.5)
            # Never share a ReqClient socket or change the main engine.client.
            peer = OwnedEngine(self.engine.profile, job)
            peer.process, peer.generation = self.engine.process, self.engine.generation
            try:
                peer.connect()
                self.output = _stop_owned(peer)  # Single original stop, no retry.
                self.stop_confirmed = True
            finally:
                if peer.client:
                    peer.client.disconnect()
        except Exception as error:
            self.error = self.error or ("owned stop outcome unknown: " + str(error))
        finally:
            self.done.set()

    def finish(self, reason):
        self.request_stop(reason)
        self.thread.join(timeout=60)
        if not self.done.is_set():
            raise TimeoutError("owned watcher stop remains pending; do not resend")
        if self.error:
            raise RuntimeError(self.error)
        return self.output


def _stop_owned(engine):
    _output_binding(engine)
    if not engine.client.get_record_status().output_active:
        return None
    output = Path(engine.client.stop_record().output_path).resolve()
    for _ in range(40):
        _output_binding(engine)
        if not engine.client.get_record_status().output_active:
            break
        time.sleep(.25)
    else:
        raise TimeoutError("owned recording did not stop")
    if not output.is_relative_to(Path(engine.job["recording_root"]).resolve()) or output.stem != engine.job["session_id"] or not output.is_file():
        raise RuntimeError("closed OBS output escaped the exact session")
    return output


def run_worker(path):
    job = _read(path)
    validate_job(job)
    profile = _read(job["profile_path"])
    validate_profile(profile)
    if profile.get("schema") != SCHEMA or profile.get("host") != "127.0.0.1" or _sha(job["profile_path"]) != job["profile_sha256"]:
        raise ValueError("unsupported or altered dedicated OBS profile")
    root = Path(job["receipt_root"])
    ProcessGeneration, game_generation, check_game_window, deadline_check = _generation_helpers()
    with_decision = job["capture_mode"] == "game_decision"
    if with_decision:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ck3_autonomous_player/src"))
        from xar_autoplayer.bridge.windows_virtual_desktop import window_virtual_desktop
    import win32gui
    foreground = win32gui.GetForegroundWindow()
    engine = OwnedEngine(profile, job)
    armed = False
    source, decision = "ManagedCK3Window-" + job["session_id"], "ManagedDecision-" + job["session_id"]
    owned_sources = [source, decision] if with_decision else [source]
    primary = None
    configured = False
    watch = None
    cleanup, frames, samples = {}, [], []
    initial_files = {str(p.resolve()) for p in Path(job["recording_root"]).iterdir() if p.is_file()}
    with ExitStack() as custody:
        game = custody.enter_context(game_generation(job["launch"]))
        overlay = custody.enter_context(ProcessGeneration(
            job["overlay"]["overlay_pid"], Path(job["overlay"]["overlay_executable"]),
            creation_filetime=job["overlay"]["overlay_creation_filetime"])) if with_decision else None
        def guard():
            deadline_check(job["deadline_utc"])
            game.check()
            check_game_window(game, job["hwnd"])
            if with_decision:
                overlay.check()
                if game.creation_filetime != job["game_creation_filetime"]:
                    raise RuntimeError("Game generation differs from actual placement")
                if window_virtual_desktop(job["hwnd"])["desktop_id"] != job["desktop_id"]:
                    raise RuntimeError("Game left its fixed managed desktop")
            if _window_identity(job["hwnd"], job["pid"]) != window:
                raise RuntimeError("OBS Game title selector lost uniqueness")
            if watch and watch.error:
                raise RuntimeError(watch.error)
            if with_decision:
                text = Path(job["decision_text_file"])
                if text.stat().st_size > 32768 or not text.read_text(encoding="utf-8").startswith(
                        "进程绑定：PID " + str(job["pid"]) + " · " + job["launch"]["creation_date"]):
                    raise RuntimeError("decision text lost its exact generation binding")

        def screenshots(label, *, replace_latest=False):
            guard()
            _output_binding(engine)
            source_binding()
            item = {"label": label, "at_utc": datetime.now(timezone.utc).isoformat()}
            for name, key in ((source, "game"), (profile["profile_name"], "scene")):
                image = engine.client.get_source_screenshot(name, "png", 1280, 720, -1)
                raw = base64.b64decode(image.image_data.split(",", 1)[1], validate=True)
                if len(raw) > 8 * 1024**2 or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise RuntimeError("source PNG is malformed or exceeds its finite budget")
                dest = root / (label + "-" + key + ".png")
                pending = dest.with_suffix(".png.tmp") if replace_latest else dest
                with pending.open("xb") as stream:
                    stream.write(raw)
                if replace_latest:
                    pending.replace(dest)
                item[key] = {"path": str(dest), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            if replace_latest:
                item["mutable_latest_frame"] = True
            else:
                frames.append(item)
            return item

        def source_binding():
            client = engine.client
            if {row["inputName"] for row in client.get_input_list().inputs} != set(owned_sources):
                raise RuntimeError("recording inputs changed")
            for name, expected in source_settings.items():
                actual = client.get_input_settings(name).input_settings
                if not _settings_match(actual, expected):
                    raise RuntimeError("actual Game/decision source settings changed: " + name)
            items = client.get_scene_item_list(profile["profile_name"]).scene_items
            if (len(items) != len(owned_sources) or {row["sourceName"] for row in items} != set(owned_sources)
                    or any(row["sceneItemEnabled"] is not True for row in items)):
                raise RuntimeError("scene lost either enabled owned source")
            by_name = {row["sourceName"]: row for row in items}
            if with_decision and by_name[decision]["sceneItemIndex"] <= by_name[source]["sceneItemIndex"]:
                raise RuntimeError("decision text is behind the Game source")
            for row in client.get_input_list().inputs:
                expected_kind = "game_capture" if row["inputName"] == source else "text_gdiplus"
                kind = row.get("unversionedInputKind") or row["inputKind"].removesuffix("_v2")
                if kind != expected_kind:
                    raise RuntimeError("owned recording input type changed")
            if with_decision:
                transform = client.get_scene_item_transform(profile["profile_name"], decision_id).scene_item_transform
                if any(transform.get(key) != value for key, value in decision_transform.items()):
                    raise RuntimeError("decision scene placement changed")

        try:
            window = _window_identity(job["hwnd"], job["pid"])
            guard()
            client = engine.start()
            if win32gui.GetForegroundWindow() != foreground:
                raise RuntimeError("OBS startup changed the user foreground; no restoration attempted")
            guard()
            if client.get_record_status().output_active or client.get_input_list().inputs:
                raise RuntimeError("fresh OBS already has inputs or active output")
            scene = profile["profile_name"]
            game_settings = {"capture_mode": "window", "window": window, "priority": 0,
                "capture_cursor": False, "capture_audio": False, "limit_framerate": False}
            source_settings = {source: game_settings}
            if with_decision:
                text_settings = {"read_from_file": True, "file": job["decision_text_file"],
                    "font": {"face": "Microsoft YaHei", "size": 24, "flags": 0},
                    "color": 0xffffff, "opacity": 100, "bk_color": 0x151515, "bk_opacity": 88,
                    "extents": True, "extents_cx": 760, "extents_cy": 1300, "extents_wrap": True}
                source_settings[decision] = text_settings
            client.set_current_program_scene(scene)
            client.set_record_directory(job["recording_root"])
            client.set_profile_parameter("Output", "FilenameFormatting", job["session_id"])
            _output_binding(engine)
            configured = True
            client.create_input(scene, source, "game_capture", game_settings, True)
            if with_decision:
                client.create_input(scene, decision, "text_gdiplus_v2", text_settings, True)
                decision_id = client.get_scene_item_id(scene, decision).scene_item_id
                decision_transform = {"positionX": 1770.0, "positionY": 20.0, "alignment": 5,
                    "scaleX": 1.0, "scaleY": 1.0, "rotation": 0.0, "cropLeft": 0, "cropRight": 0,
                    "cropTop": 0, "cropBottom": 0, "boundsType": "OBS_BOUNDS_NONE"}
                client.set_scene_item_transform(scene, decision_id, decision_transform)
                client.set_scene_item_index(scene, decision_id, 1)
            _output_binding(engine)
            video = client.get_video_settings()
            if (video.base_width, video.base_height, video.output_width, video.output_height, video.fps_numerator, video.fps_denominator) != (2560, 1440, 2560, 1440, 30, 1):
                raise RuntimeError("OBS video settings differ from the dedicated profile")
            time.sleep(2)
            ready_frame = screenshots("before-recording")
            def waiting_check():
                guard()
                _output_binding(engine)
                source_binding()
                if engine.client.get_record_status().output_active:
                    raise RuntimeError("owned output became active before recording start signal")
                if _job_bytes(job)[1] >= job["max_output_bytes"] - 96 * 1024**2:
                    raise RuntimeError("waiting frame receipts reached the reserved stop margin")
            _wait_for_start_signal(job, waiting_check, screenshots, ready_frame)
            remaining = (datetime.fromisoformat(job["deadline_utc"].replace("Z", "+00:00")) - datetime.now(timezone.utc)).total_seconds()
            if remaining < job["duration_seconds"] + 90:
                raise RuntimeError("late OBS setup left insufficient recording/cleanup admission")
            if (client.get_profile_parameter("SimpleOutput", "RecQuality").parameter_value != "Stream"
                    or int(client.get_profile_parameter("SimpleOutput", "VBitrate").parameter_value) != profile["bitrate_kbps"]):
                raise RuntimeError("actual OBS encoder parameters differ from bounded CBR profile")
            armed = True  # A timed-out Start RPC may already have started output.
            start_monotonic = time.monotonic()
            client.start_record()
            for _ in range(40):
                guard()
                if client.get_record_status().output_active:
                    break
                time.sleep(.25)
            else:
                raise RuntimeError("OBS did not enter actual recording state")
            watch = FileGrowthWatch(engine, job["duration_seconds"], start_monotonic)
            watch.start()
            _write_new(root / "started.json", {"state": "recording", "at_utc": datetime.now(timezone.utc).isoformat(),
                "game_pid": job["pid"], "game_creation_filetime": game.creation_filetime,
                "source_settings": client.get_input_settings(source).input_settings,
                "capture_mode": job["capture_mode"], "decision_source": with_decision,
                "decision_settings": client.get_input_settings(decision).input_settings if with_decision else None,
                "video": _response_data(video), "runtime_freshness_qualified": False})
            end = start_monotonic + job["duration_seconds"]
            reconnect_at, screenshot_at = time.monotonic() + 20, time.monotonic() + 30
            last_bytes, last_growth, peak = 0, time.monotonic(), 0
            while time.monotonic() < end:
                time.sleep(min(1, max(0, end - time.monotonic())))
                guard()
                if time.monotonic() >= reconnect_at:
                    client = engine.reconnect()
                    reconnect_at = time.monotonic() + 20
                _output_binding(engine)
                source_binding()
                if watch.requested.is_set():
                    break
                status = client.get_record_status()
                if not status.output_active and watch.reason == "duration_reached":
                    break
                if not status.output_active:
                    raise RuntimeError("owned recording ended before its bound")
                files = [p for p in Path(job["recording_root"]).iterdir() if p.is_file() and p.stem == job["session_id"]]
                current_bytes = sum(p.stat().st_size for p in files)
                unexpected = [p for p in Path(job["recording_root"]).iterdir()
                              if p.is_file() and str(p.resolve()) not in initial_files and p.stem != job["session_id"]]
                if unexpected:
                    raise RuntimeError("unexpected OBS output filename")
                total = current_bytes + sum(p.stat().st_size for p in root.iterdir() if p.is_file())
                peak = max(peak, total)
                if total >= job["max_output_bytes"] - 96 * 1024**2:
                    raise RuntimeError("recording allocation nearing hard byte cap")
                if current_bytes > last_bytes:
                    last_bytes, last_growth = current_bytes, time.monotonic()
                elif time.monotonic() - last_growth > 30:
                    raise RuntimeError("actual recording file did not grow for over 30 seconds")
                samples.append({"elapsed_seconds": job["duration_seconds"] - max(0, end - time.monotonic()),
                                "file_bytes": current_bytes, "output_logical_bytes": total})
                if time.monotonic() >= screenshot_at:
                    screenshots("sample-" + str(len(frames)).zfill(3))
                    screenshot_at = time.monotonic() + 60
            if not watch.requested.is_set():
                screenshots("before-stop")
            output = watch.finish("duration_reached")
            armed = False
            if output is None:
                raise RuntimeError("recording absent at final owned stop")
            probe = subprocess.run([job["ffprobe"], "-v", "error", "-show_entries",
                "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,avg_frame_rate",
                "-of", "json", str(output)], capture_output=True, text=True, encoding="utf-8", timeout=30, check=True)
            observed = json.loads(probe.stdout)
            bitrate = int(observed["format"].get("bit_rate", 0))
            duration = float(observed["format"]["duration"])
            if (not 0 < bitrate <= 5_000_000 or not 0 < duration <= job["duration_seconds"]
                    or _job_bytes(job)[1] + 1024**2 >= job["max_output_bytes"]):
                raise RuntimeError("closed probe violates bitrate/byte allocation")
            _write_new(root / "closed-file-probe.json", observed)
            _write_new(root / "completed.json", {"state": "completed", "path": str(output),
                "bytes": output.stat().st_size, "sha256": _sha(output), "peak_logical_bytes": peak,
                "frame_receipts": frames, "file_growth_samples": samples,
                "configured_video_CBR_target_bits_per_second": profile["bitrate_kbps"] * 1000,
                "closed_average_total_bitrate_limit": 5_000_000, "actual_closed_average_bitrate": bitrate,
                "instantaneous_bitrate_hard_cap_qualified": False,
                "hidden_Game_freshness_qualified": False, "decision_business_success_inferred": False,
                "ended_at_utc": datetime.now(timezone.utc).isoformat()})
        except Exception as error:
            primary = error
            _write_new(root / "failed.json", {"state": "failed", "error": str(error),
                       "frame_receipts": frames, "file_growth_samples": samples})
        finally:
            if armed and watch:
                try:
                    stopped = watch.finish("worker_failure")
                    cleanup["recovered_output"] = str(stopped) if stopped else None
                    armed = False
                except Exception as error:
                    cleanup["stop_error"] = str(error)
                    if watch.stop_confirmed:
                        armed = False  # File/deadline failure remains RED; output is actually closed.
            elif armed and engine.client:
                try:
                    engine.reconnect()
                    stopped = _stop_owned(engine)
                    cleanup["recovered_output"] = str(stopped) if stopped else None
                    armed = False
                except Exception as error:
                    cleanup["stop_error"] = str(error)
            if engine.client and not armed:
                try:
                    # Discard possibly late responses after a timed-out main RPC.
                    engine.reconnect()
                    cleanup["inputs_unbound"] = _unbind_owned_inputs(engine, owned_sources, configured)
                except Exception as error:
                    cleanup["unbind_error"] = str(error)
                engine.client.disconnect()
            if not armed and not cleanup.get("unbind_error"):
                try:
                    cleanup["engine_close"] = engine.close()
                except Exception as error:
                    cleanup["close_error"] = str(error)
            cleanup["unknown_or_global_stop_calls"] = 0
            cleanup["final_output_logical_bytes"] = _job_bytes(job)[1]
            cleanup["within_byte_allocation"] = cleanup["final_output_logical_bytes"] + 1024**2 < job["max_output_bytes"]
            if watch:
                cleanup["independent_file_growth_samples"] = watch.samples
                cleanup["watcher_stop_reason"] = watch.reason
            _write_new(root / "cleanup.json", cleanup)
            if engine.generation:
                engine.generation.close()
    if primary:
        raise primary
    if cleanup.get("stop_error") or cleanup.get("unbind_error") or cleanup.get("close_error") or not cleanup.get("within_byte_allocation") or cleanup.get("engine_close", {}).get("actual_exit_code") != 0:
        raise RuntimeError("recording complete but dedicated OBS cleanup is not GREEN")


def stop_session_recording(receipt_root):
    raise RuntimeError("v2 bounded worker owns its exact engine stop; inspect generation receipts")


def request_engine_close(receipt_root):
    raise RuntimeError("v2 worker owns retained-engine close; no detached unverified close")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", type=Path, required=True)
    run_worker(parser.parse_args().job)
