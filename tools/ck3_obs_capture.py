"""Dedicated OBS Game texture plus independent decision-text source.

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
import importlib.util
import json
import logging
import math
from pathlib import Path
import secrets
import stat
import shutil
import subprocess
import sys
import threading
import time
import uuid

PROVIDER_VERSION = "3.0.0"
SCHEMA = "xar.ck3.obs-window-capture.v3"
ALLOWED_SECONDS = frozenset({15, 30, 45, 60, 90, 120})
RECENT_SAMPLE_COUNT = 120

def require_no_retired_decision_window():
    """Use the current recorder's exact class check, including hidden old windows."""
    path = Path(__file__).with_name('ck3_mod_acceptance_recorder.py')
    spec = importlib.util.spec_from_file_location('obs_retired_decision_guard', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.require_no_legacy_blue_overlay()

def decision_publisher_api():
    path = (Path(__file__).resolve().parent / 'g2_saved_campaign/decision_text_publisher.py').resolve(strict=True)
    name = 'decision_text_publisher'
    existing = sys.modules.get(name)
    if existing is not None:
        if Path(getattr(existing, '__file__', '')).resolve() != path:
            raise RuntimeError('Foreign cached decision text publisher; exact provider sibling source required')
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(name) is module: sys.modules.pop(name)
        raise
    return module


def _write_new(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def _read_decision_binding(path, expected, *, retry_seconds=2.0):
    """OBS and the overlay can briefly hold a Windows replace/share lock."""
    deadline = time.monotonic() + retry_seconds
    while True:
        try:
            raw = Path(path).read_bytes()
            if len(raw) > 32768 or not raw.decode("utf-8").startswith(expected):
                raise RuntimeError("decision text lost its exact generation binding")
            return
        except PermissionError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(.05)



def _replace_mutable_latest(pending, destination):
    """Retry this already-written temp only; never capture or serialize again."""
    deadline = time.monotonic() + 2.0
    delays = (.02, .04, .08, .16, .24, .32, .4)
    last_error = None
    for attempt in range(8):
        if last_error is not None and time.monotonic() >= deadline:
            last_error.add_note("mutable latest replace retry deadline exhausted")
            raise last_error
        try:
            return pending.replace(destination)
        except OSError as error:
            if getattr(error, "winerror", None) not in (5, 32, 33):
                raise
            last_error = error
            remaining = deadline - time.monotonic()
            if attempt == 7 or remaining <= 0:
                error.add_note(f"mutable latest replace failed after {attempt + 1} attempts")
                raise
            time.sleep(min(delays[attempt], remaining))


def _replace_json(path, value):
    """Mutable latest state; old paths are never presented as immutable evidence."""
    path = Path(path)
    pending = path.with_suffix(path.suffix + ".tmp")
    _write_new(pending, value)
    _replace_mutable_latest(pending, path)


def _validate_storage(storage, paths):
    roots = storage.get("approved_output_roots") if isinstance(storage, dict) else None
    if (not isinstance(roots, list) or not roots or any(not isinstance(p, str) or not p for p in roots)
            or type(storage.get("disk_reserve_bytes")) is not int or storage["disk_reserve_bytes"] <= 0):
        raise ValueError("continuous recording requires admitted roots and an actual disk reserve")
    roots = [Path(p).resolve() for p in roots]
    if any(not any(Path(p).resolve().is_relative_to(root) for root in roots) for p in paths):
        raise ValueError("continuous recording output escaped its admitted roots")


def _continuous_storage(admission_path, paths):
    if admission_path is None:
        raise ValueError("continuous recording requires an explicit storage admission")
    admission_path = Path(admission_path).resolve(strict=True)
    admission = _read(admission_path)
    if admission.get("status") != "ADMITTED":
        raise ValueError("continuous recording storage must be ADMITTED")
    storage = {"approved_output_roots": admission["approved_output_roots"],
               "disk_reserve_bytes": admission["disk_reserve_bytes"],
               "admission_path": str(admission_path), "admission_sha256": _sha(admission_path)}
    _validate_storage(storage, paths)
    return storage


def _disk_observation(job):
    path = Path(job["recording_root"]).resolve()
    # Preparation may precede creation of the new recording directory.
    probe = path
    while not probe.exists():
        if probe.parent == probe:
            raise FileNotFoundError("recording volume is unavailable: " + str(path))
        probe = probe.parent
    free = shutil.disk_usage(probe).free
    reserve = job["storage"]["disk_reserve_bytes"]
    return {"at_utc": datetime.now(timezone.utc).isoformat(), "recording_root": str(path),
            "available_bytes": free, "disk_reserve_bytes": reserve, "reserve_reached": free <= reserve}


def _append_sample(samples, summary, sample, continuous):
    samples.append(sample)
    summary["samples_seen"] = summary.get("samples_seen", 0) + 1
    summary["peak_output_logical_bytes"] = max(summary.get("peak_output_logical_bytes", 0), sample["output_logical_bytes"])
    if continuous and len(samples) > RECENT_SAMPLE_COUNT:
        del samples[:-RECENT_SAMPLE_COUNT]


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
    if profile.get("continuous") is True:
        if profile.get("max_output_bytes") is not None or profile.get("deadline_utc") is not None:
            raise ValueError("continuous recording has no byte cap or deadline")
        _validate_storage(profile.get("storage"), (root, profile["config_root"], profile["recording_root"]))
    elif (type(profile["max_output_bytes"]) is not int
            or not 192 * 1024**2 <= profile["max_output_bytes"] <= 1024**3):
        raise ValueError("recording allocation must be 192MiB..1GiB, including metadata/stop reserve")


def prepare_profile(obs_root: Path, profile_path: Path, recording_root: Path, *,
                    port: int, control_dependencies: Path, deadline_utc: str | None,
                    max_output_bytes: int | None, bitrate_kbps: int = 4800,
                    continuous: bool = False, storage_admission=None) -> Path:
    if continuous:
        if deadline_utc is not None or max_output_bytes is not None:
            raise ValueError("continuous recording does not accept a deadline or byte cap")
    else:
        _, _, _, deadline_check = _generation_helpers()
        deadline_check(deadline_utc)
    obs_root, profile_path, recording_root = (p.resolve() for p in (obs_root, profile_path, recording_root))
    executable = obs_root / "bin/64bit/obs64.exe"
    if not executable.is_file() or profile_path.exists():
        raise ValueError("explicit OBS executable and new profile receipt required")
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError("explicit dedicated local port required")
    if not continuous and (type(max_output_bytes) is not int or not 192 * 1024**2 <= max_output_bytes <= 1024**3):
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
    if continuous:
        profile["continuous"] = True
        profile["storage"] = _continuous_storage(storage_admission, (obs_root, profile_path, recording_root))
    validate_profile(profile)
    if continuous and _disk_observation(profile)["reserve_reached"]:
        raise RuntimeError("actual recording volume has reached its disk reserve")
    _control(profile)  # Existing explicit dependencies only; installs nothing.
    basic = config / "basic/profiles" / name
    basic.mkdir(parents=True)
    recording_root.mkdir(parents=True, exist_ok=True)
    with (obs_root / "portable_mode.txt").open("x", encoding="utf-8") as stream:
        stream.write("")
    (config / "global.ini").write_text(
        "[General]\nFirstRun=true\nLastVersion=503382018\nEnableAutoUpdates=false\n"
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
    continuous = job.get("continuous") is True
    if job.get("schema") != SCHEMA:
        raise ValueError("unsupported recording job schema")
    if continuous:
        if any(job.get(key) is not None for key in ("duration_seconds", "max_output_bytes", "deadline_utc")):
            raise ValueError("continuous recording has no duration, byte cap or deadline")
        _validate_storage(job.get("storage"), (job["profile_path"], job["recording_root"], job["receipt_root"]))
    elif type(job.get("duration_seconds")) is not int or not 1 <= job["duration_seconds"] <= 1200:
        raise ValueError("recording must be finite and at most 20 minutes")
    if any(type(job.get(key)) is not int or job[key] <= 0 for key in ("pid", "hwnd")):
        raise ValueError("exact Game PID/HWND required")
    uuid.UUID(job["session_id"])
    if not Path(job["receipt_root"]).resolve().is_relative_to(Path(job["recording_root"]).resolve()):
        raise ValueError("receipt scope escaped the recording root")
    if not continuous and (type(job.get("max_output_bytes")) is not int or not 192 * 1024**2 <= job["max_output_bytes"] <= 1024**3):
        raise ValueError("bounded recording allocation required")
    signal = job.get("start_signal")
    if signal is not None and (not isinstance(signal, str) or not signal
            or not Path(signal).resolve().is_relative_to(Path(job["recording_root"]).resolve())):
        raise ValueError("recording start signal must remain in this recording root")
    mode = job.get("capture_mode")
    if mode not in ("game_only", "game_decision", "game_decision_text"):
        raise ValueError("use the fixed Game-only or Game+decision contract")
    if mode == "game_only":
        if any(job.get(key) is not None for key in ("overlay", "desktop_id", "decision_text_file", "game_creation_filetime", 'decision_text_publisher', 'decision_text_publisher_receipt')):
            raise ValueError("Game-only capture may not contain a partial decision/desktop group")
    elif mode == 'game_decision_text':
        if (job.get('overlay') is not None or not isinstance(job.get('decision_text_publisher'), dict)
                or not isinstance(job.get('decision_text_publisher_receipt'), dict)
                or not job.get('decision_text_file') or not job.get('desktop_id')
                or type(job.get('game_creation_filetime')) is not int):
            raise ValueError('Independent text publisher group required; old overlay identity is forbidden')
    elif (not isinstance(job.get("overlay"), dict) or not job.get("decision_text_file")
          or not job.get("desktop_id") or type(job.get("game_creation_filetime")) is not int
          or job["game_creation_filetime"] <= 0):
        raise ValueError("Game+decision capture requires the complete attested group")


def launch_recording(profile_path, recording_root, pid, hwnd, seconds, *,
                     launch_receipt, ffprobe, placement_receipt=None, overlay_receipt=None,
                      decision_publisher_receipt=None, start_signal=None, continuous=False):
    """Products may record only Game; fresh-agent calls supply the complete group."""
    display_policy = require_no_retired_decision_window()
    if overlay_receipt is not None:
        raise ValueError('Legacy blue overlay launch is retired; use a real independent decision text publisher')
    if (placement_receipt is None) != (decision_publisher_receipt is None):
        raise ValueError('Placement and actual text publisher receipts must be supplied together')
    profile, launch = map(_read, (profile_path, launch_receipt))
    placement, overlay, publisher, publisher_pin, text = None, None, None, None, None
    with_decision = decision_publisher_receipt is not None
    validate_profile(profile)
    if continuous != (profile.get("continuous") is True):
        raise ValueError("recording mode differs from the prepared profile")
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
        placement = _read(placement_receipt)
        if placement.get('status') != 'GREEN' or placement.get('pid') != pid or placement.get('hwnd') != hwnd:
            raise ValueError('Actual matching Game placement required')
        api = decision_publisher_api(); publisher_pin = api.pin(decision_publisher_receipt)
        publisher = api.read_text_binding(publisher_pin, game={'pid': pid, 'creation_filetime': placement['creation_filetime'],
                    'hwnd': hwnd, 'desktop_id': placement['target_desktop_id']})
        text = Path(publisher['decision_text_file']).resolve(strict=True)
        if not text.is_relative_to(Path(publisher['session']).resolve()) or text.stat().st_size > 32768:
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
        "capture_mode": "game_decision_text" if with_decision else "game_only",
        "game_creation_filetime": placement["creation_filetime"] if with_decision else None,
        "desktop_id": placement["target_desktop_id"] if with_decision else None,
        "overlay": None, 'decision_text_publisher': publisher, 'decision_text_publisher_receipt': publisher_pin,
        'decision_display_policy': display_policy, "decision_text_file": str(text) if text else None, "ffprobe": str(probe),
        "deadline_utc": profile["deadline_utc"], "max_output_bytes": profile["max_output_bytes"]}
    if continuous:
        job.update(continuous=True, storage=profile["storage"])
    if start_signal is not None:
        job["start_signal"] = str(start_signal)
    validate_job(job)
    if continuous:
        if _disk_observation(job)["reserve_reached"]:
            raise RuntimeError("actual recording volume has reached its disk reserve")
    else:
        _, _, _, deadline_check = _generation_helpers()
        deadline_check(job["deadline_utc"])
        end = datetime.fromisoformat(job["deadline_utc"].replace("Z", "+00:00"))
        if (end - datetime.now(timezone.utc)).total_seconds() < seconds + 90:
            raise ValueError("recording plus cleanup does not fit the original deadline")
    root.mkdir()
    path = root / "job.json"
    _write_new(path, job)
    with (root / "worker.stdout.txt").open("x", encoding="utf-8") as stdout, (root / "worker.stderr.txt").open("x", encoding="utf-8") as stderr:
        argv = [sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()), "--job", str(path)]
        if continuous:
            argv.append("--continuous")
        worker = subprocess.Popen(argv,
            stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    ProcessGeneration, _, _, _ = _generation_helpers()
    with ProcessGeneration(worker.pid, Path(sys.executable)) as actual_worker:
        actual_worker.check()
        worker_birth = actual_worker.creation_filetime
        worker_executable = str(actual_worker.executable)
    return {"schema": SCHEMA, "session_id": session, "worker_pid": worker.pid,
            "worker_creation_filetime": worker_birth, "worker_executable": worker_executable,
            "receipt_root": str(root), "state": "requested", "runtime_qualified": False}


def _window_identity(hwnd, expected_pid):
    import win32gui
    import win32process
    import psutil
    windows = []
    owned_class = win32gui.GetClassName(hwnd)
    def collect(candidate, _):
        if (win32gui.IsWindowVisible(candidate)
                and win32gui.GetWindowText(candidate) == "Crusader Kings III"
                and win32gui.GetClassName(candidate) == owned_class):
            pid = win32process.GetWindowThreadProcessId(candidate)[1]
            if Path(psutil.Process(pid).exe()).name.casefold() == "ck3.exe":
                windows.append((candidate, pid))
    win32gui.EnumWindows(collect, None)
    if windows != [(hwnd, expected_pid)]:
        raise RuntimeError("OBS title selector is not unique to the owned Game window")
    escape = lambda value: value.replace("#", "#22").replace(":", "#3A")
    return ":".join(map(escape, ("Crusader Kings III", win32gui.GetClassName(hwnd), "ck3.exe")))


def _foreground_observation(before, owned_obs_pid):
    import win32gui
    import win32process
    after = win32gui.GetForegroundWindow()
    changed = after != before
    pid = win32process.GetWindowThreadProcessId(after)[1] if changed and after else None
    return {"foreground_before": before, "foreground_after": after,
            "foreground_changed": changed, "foreground_after_pid": pid,
            "owned_obs_pid": owned_obs_pid, "foreground_after_is_owned_obs": pid == owned_obs_pid,
            "focus_restoration_attempted": False}


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
        for _ in range(120):
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
                        and win32gui.GetParent(hwnd) == 0
                        and win32gui.GetWindowText(hwnd).startswith("OBS ")
                        and win32gui.GetClassName(hwnd).startswith("Qt")):
                    windows.append(hwnd)
            win32gui.EnumWindows(collect, None)
            if len(windows) != 1:
                raise RuntimeError("owned OBS main window is not unique")
            hwnd = windows[0]
            self.generation.check()
            if (win32process.GetWindowThreadProcessId(hwnd)[1] != self.process.pid
                    or win32gui.GetParent(hwnd) != 0):
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


MUTABLE_LATEST_RECEIPT_NAMES = frozenset(
    label + suffix + temporary
    for label in ("armed-latest", "recording-latest")
    for suffix in ("-game.png", "-scene.png", ".json")
    for temporary in ("", ".tmp"))


def _receipt_bytes(root):
    """Atomic latest replacement may remove only these exact receipt names."""
    total = 0
    for path in Path(root).iterdir():
        try:
            observed = path.stat()
        except FileNotFoundError:
            if path.name in MUTABLE_LATEST_RECEIPT_NAMES:
                continue
            raise
        if stat.S_ISREG(observed.st_mode):
            total += observed.st_size
    return total


def _job_bytes(job):
    output = Path(job["recording_root"])
    root = Path(job["receipt_root"])
    videos = [p for p in output.iterdir() if p.is_file() and p.stem == job["session_id"]]
    video_bytes = sum(p.stat().st_size for p in videos)
    return video_bytes, video_bytes + _receipt_bytes(root)


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
            _replace_mutable_latest(pending, latest)
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
        self.sample_summary = {}
        self.last_disk_observation = None
        self.thread = threading.Thread(target=self.run, name="owned-recording-growth", daemon=True)

    def start(self):
        self.thread.start()

    def request_stop(self, reason):
        if self.reason is None:
            self.reason = reason
        self.requested.set()

    def run(self):
        job = self.engine.job
        continuous = job.get("continuous") is True
        end = None if continuous else self.start_monotonic + max(.25, self.seconds - min(10, self.seconds * .05))
        previous, changed = 0, time.monotonic()
        try:
            while not self.requested.is_set():
                try:
                    if (Path(job["receipt_root"]) / "STOP-OWNED-RECORDING").is_file():
                        self.request_stop("owned_shutdown_requested")
                        break
                    if continuous:
                        self.last_disk_observation = _disk_observation(job)
                        if self.last_disk_observation["reserve_reached"]:
                            self.request_stop("disk_reserve_reached")
                            break
                    else:
                        _, _, _, deadline_check = _generation_helpers()
                        deadline_check(job["deadline_utc"])
                    video, total = _job_bytes(job)
                    self.peak = max(self.peak, total)
                    _append_sample(self.samples, self.sample_summary,
                        {"at_utc": datetime.now(timezone.utc).isoformat(),
                         "file_bytes": video, "output_logical_bytes": total}, continuous)
                    if not continuous and total >= job["max_output_bytes"] - 96 * 1024**2:
                        raise RuntimeError("actual output reached the reserved stop margin")
                    if video > previous:
                        previous, changed = video, time.monotonic()
                    elif time.monotonic() - changed > 30:
                        raise RuntimeError("actual video file did not grow for over 30 seconds")
                    if end is not None and time.monotonic() >= end:
                        self.request_stop("duration_reached")
                        break
                except Exception as error:
                    self.error = str(error)
                    self.request_stop("file_or_disk_guard" if continuous else "file_or_deadline_guard")
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


def _publish_closed_receipt(path, value):
    path = Path(path)
    pending = path.with_name(path.name + "." + uuid.uuid4().hex + ".pending")
    try:
        _write_new(pending, value)
        if path.exists():
            raise FileExistsError(path)
        pending.rename(path)  # On the required Windows runtime this refuses an existing target.
    finally:
        try:
            pending.unlink()
        except FileNotFoundError:
            pass


def _lower_media_finalizer_priority():
    """Change only this capture worker after all capture custody has closed."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.GetPriorityClass.argtypes = [ctypes.c_void_p]
    kernel.GetPriorityClass.restype = ctypes.c_ulong
    kernel.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    kernel.SetPriorityClass.restype = ctypes.c_int
    handle = kernel.GetCurrentProcess()
    before = kernel.GetPriorityClass(handle)
    applied = bool(kernel.SetPriorityClass(handle, 0x4000))
    after = kernel.GetPriorityClass(handle)
    return {"scope": "current_post_capture_worker_only", "requested": 0x4000,
            "before": before, "after": after, "applied": applied and after == 0x4000}


def _finalize_closed_media(root, completed_payload):
    """Background finalization preserves the existing full-file SHA receipt."""
    try:
        try:
            priority = _lower_media_finalizer_priority()
        except Exception as error:
            priority = {"scope": "current_post_capture_worker_only", "applied": False,
                        "error": str(error)[:2048]}
        _write_new(root / "media-finalization-started.json", {
            "at_utc": datetime.now(timezone.utc).isoformat(), "priority": priority,
            "capture_resources_already_closed": True})
        output = Path(completed_payload["path"])
        before = output.stat()
        if before.st_size != completed_payload["bytes"]:
            raise RuntimeError("closed media size changed before final hashing")
        digest = _sha(output)
        after = output.stat()
        if after.st_size != before.st_size or after.st_mtime_ns != before.st_mtime_ns:
            raise RuntimeError("closed media changed during final hashing")
        _publish_closed_receipt(root / "completed.json", {**completed_payload, "sha256": digest,
            "media_finalization": {"mode": "background_thread_after_capture_close",
                "priority": priority, "completed_at_utc": datetime.now(timezone.utc).isoformat()}})
    except Exception as error:
        # Capture cleanup remains authoritative.  Missing full-file integrity is
        # a separate RED artifact, never a fabricated completed/failed capture.
        _publish_closed_receipt(root / "media-finalization-failed.json", {
            "at_utc": datetime.now(timezone.utc).isoformat(),
            "path": completed_payload.get("path"), "error": str(error)[:2048],
            "capture_resources_already_closed": True, "completed_sha256_claimed": False})


def _publish_capture_closed_and_finalize(root, job, completed_payload, cleanup):
    close = cleanup.get("engine_close") or {}
    if (cleanup.get("inputs_unbound") is not True
            or close.get("actual_exit_code") != 0 or close.get("normal_exit_proven") is not True
            or close.get("forced_process_calls") != 0
            or any(cleanup.get(key) for key in ("stop_error", "unbind_error", "close_error", "disk_read_error"))):
        raise RuntimeError("capture_closed requires actual normal owned OBS cleanup")
    root = Path(root)
    output = Path(completed_payload["path"]).resolve()
    if (root.name != job["session_id"]
            or output != (Path(job["recording_root"]) / (job["session_id"] + ".mkv")).resolve()
            or output.stat().st_size != completed_payload["bytes"]):
        raise RuntimeError("capture_closed output differs from the immutable job")
    obs = _read(root / "obs-launch.json")
    if type(obs.get("pid")) is not int or obs["pid"] <= 0 or type(obs.get("creation_filetime")) is not int or obs["creation_filetime"] <= 0:
        raise RuntimeError("capture_closed requires the original owned OBS generation")
    started = _read(root / "started.json")
    game_birth = started.get("game_creation_filetime")
    if (started.get("game_pid") != job["pid"] or type(game_birth) is not int or game_birth <= 0
            or job.get("game_creation_filetime") is not None
            and job["game_creation_filetime"] != game_birth):
        raise RuntimeError("capture_closed requires the actual captured Game generation")
    capture_closed = {"schema": "xar.ck3.capture-closed-before-media-hash/v1",
        "at_utc": datetime.now(timezone.utc).isoformat(), "session_id": job["session_id"],
        "game_pid": job["pid"], "game_creation_filetime": game_birth,
        "obs_pid": obs["pid"], "obs_creation_filetime": obs["creation_filetime"],
        "output_path": str(output), "output_bytes": completed_payload["bytes"],
        "closed_file_probe": {"path": str(root / "closed-file-probe.json"), "sha256": _sha(root / "closed-file-probe.json")},
        "cleanup": {"path": str(root / "cleanup.json"), "sha256": _sha(root / "cleanup.json")},
        "inputs_unbound": True, "engine_close": close,
        "media_sha256_pending": True, "final_completed_path": str(root / "completed.json"),
        "postprocessing_worker_pid": __import__("os").getpid(),
        "capture_custody_released_before_publication": True}
    _publish_closed_receipt(root / "capture_closed.json", capture_closed)
    # The caller and Root may proceed after capture_closed.  This non-daemon
    # thread keeps only the closed file finalizer alive until its SHA is saved.
    finalizer = threading.Thread(target=_finalize_closed_media,
        args=(root, completed_payload), name="owned-closed-media-sha256", daemon=False)
    finalizer.start()


def _start_stall_edl_metadata(job, root):
    try:
        if __package__:
            from .ck3_recording_stall_hook import start_collector
        else:
            from ck3_recording_stall_hook import start_collector
        return start_collector(job, _read(root / "started.json"))
    except Exception as metadata_error:
        _write_new(root / "stall-edl-start-failed.json", {
            "metadata_only_failure": True, "error": str(metadata_error)[:2048],
            "recording_stop_requested_by_metadata_failure": False})
        return None


def _stop_stall_edl_metadata(job, root):
    try:
        if __package__:
            from .ck3_recording_stall_hook import request_stop
        else:
            from ck3_recording_stall_hook import request_stop
        request_stop(job)
    except Exception as metadata_error:
        _write_new(root / "stall-edl-stop-failed.json", {"error": str(metadata_error)[:2048]})


def run_worker(path):
    worker_display_policy = require_no_retired_decision_window()
    job = _read(path)
    validate_job(job)
    profile = _read(job["profile_path"])
    validate_profile(profile)
    continuous = job.get("continuous") is True
    if continuous != (profile.get("continuous") is True) or (continuous and job["storage"] != profile["storage"]):
        raise ValueError("recording mode/storage differs from the immutable prepared profile")
    if profile.get("schema") != SCHEMA or profile.get("host") != "127.0.0.1" or _sha(job["profile_path"]) != job["profile_sha256"]:
        raise ValueError("unsupported or altered dedicated OBS profile")
    root = Path(job["receipt_root"])
    ProcessGeneration, game_generation, check_game_window, deadline_check = _generation_helpers()
    if job['capture_mode'] == 'game_decision':
        raise ValueError('New worker cannot launch retired legacy decision overlay configuration')
    with_decision = job["capture_mode"] == "game_decision_text"
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
    completed_payload = None
    sample_summary = {}
    initial_files = {str(p.resolve()) for p in Path(job["recording_root"]).iterdir() if p.is_file()}
    if job.get("start_signal") is not None:
        initial_files.add(str(Path(job["start_signal"]).resolve()))
    with ExitStack() as custody:
        game = custody.enter_context(game_generation(job["launch"]))
        publisher = job.get('decision_text_publisher')
        text_process = custody.enter_context(ProcessGeneration(
            publisher['publisher']['pid'], Path(publisher['publisher']['executable']),
            creation_filetime=publisher['publisher']['creation_filetime'])) if with_decision else None
        def guard():
            if continuous:
                disk = _disk_observation(job)
                reason = ("owned_shutdown_requested" if (root / "STOP-OWNED-RECORDING").is_file()
                          else "disk_reserve_reached" if disk["reserve_reached"] else None)
                if reason:
                    if watch:
                        watch.request_stop(reason)
                    else:
                        raise RuntimeError("continuous recording not started: " + reason)
            else:
                deadline_check(job["deadline_utc"])
            game.check()
            check_game_window(game, job["hwnd"])
            if with_decision:
                text_process.check()
                if game.creation_filetime != job["game_creation_filetime"]:
                    raise RuntimeError("Game generation differs from actual placement")
                desktop_query_deadline = time.monotonic() + 30.0
                while True:
                    try:
                        actual_desktop = window_virtual_desktop(job["hwnd"])["desktop_id"]
                        break
                    except OSError as error:
                        if "IsWindowOnCurrentVirtualDesktop HRESULT" not in str(error):
                            raise
                        if time.monotonic() >= desktop_query_deadline:
                            raise RuntimeError("Game desktop identity unavailable for 30 seconds") from error
                        time.sleep(.25)
                if actual_desktop != job["desktop_id"]:
                    raise RuntimeError("Game left its fixed managed desktop")
            if _window_identity(job["hwnd"], job["pid"]) != window:
                raise RuntimeError("OBS Game title selector lost uniqueness")
            if watch and watch.error:
                raise RuntimeError(watch.error)
            if with_decision:
                decision_publisher_api().read_text_binding(job['decision_text_publisher_receipt'], game={
                    'pid': job['pid'], 'creation_filetime': job['game_creation_filetime'], 'hwnd': job['hwnd'], 'desktop_id': job['desktop_id']})

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
                    _replace_mutable_latest(pending, dest)
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
            foreground_observation = _foreground_observation(foreground, engine.process.pid)
            _write_new(root / "foreground-observation.json", foreground_observation)
            if foreground_observation["foreground_changed"] and foreground_observation["foreground_after_is_owned_obs"]:
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
                if not continuous and _job_bytes(job)[1] >= job["max_output_bytes"] - 96 * 1024**2:
                    raise RuntimeError("waiting frame receipts reached the reserved stop margin")
            _wait_for_start_signal(job, waiting_check, screenshots, ready_frame)
            if not continuous:
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
                'decision_text_publisher': publisher if with_decision else None,
                'decision_display_policy': worker_display_policy,
                "decision_settings": client.get_input_settings(decision).input_settings if with_decision else None,
                "video": _response_data(video), "runtime_freshness_qualified": False,
                "continuous": continuous, "duration_seconds": job["duration_seconds"],
                "max_output_bytes": job["max_output_bytes"], "deadline_utc": job["deadline_utc"]})
            _start_stall_edl_metadata(job, root)
            end = None if continuous else start_monotonic + job["duration_seconds"]
            reconnect_at, screenshot_at = time.monotonic() + 20, time.monotonic() + 30
            last_bytes, last_growth, peak = 0, time.monotonic(), 0
            while end is None or time.monotonic() < end:
                time.sleep(1 if end is None else min(1, max(0, end - time.monotonic())))
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
                    raise RuntimeError("unexpected OBS output filename: " + json.dumps(
                        [str(p.resolve()) for p in unexpected], ensure_ascii=False))
                total = current_bytes + _receipt_bytes(root)
                peak = max(peak, total)
                if not continuous and total >= job["max_output_bytes"] - 96 * 1024**2:
                    raise RuntimeError("recording allocation nearing hard byte cap")
                if current_bytes > last_bytes:
                    last_bytes, last_growth = current_bytes, time.monotonic()
                elif time.monotonic() - last_growth > 30:
                    raise RuntimeError("actual recording file did not grow for over 30 seconds")
                _append_sample(samples, sample_summary,
                    {"elapsed_seconds": time.monotonic() - start_monotonic,
                     "file_bytes": current_bytes, "output_logical_bytes": total}, continuous)
                if time.monotonic() >= screenshot_at:
                    if continuous:
                        latest = screenshots("recording-latest", replace_latest=True)
                        _replace_json(root / "recording-latest.json",
                                      {"state": "recording", "mutable_latest_frame": True, "frame": latest,
                                       "file_growth_summary": sample_summary, "recent_file_growth_samples": samples})
                    else:
                        screenshots("sample-" + str(len(frames)).zfill(3))
                    screenshot_at = time.monotonic() + 60
            if not watch.requested.is_set():
                screenshots("before-stop")
            output = watch.finish("worker_finished" if continuous else "duration_reached")
            armed = False
            if output is None:
                raise RuntimeError("recording absent at final owned stop")
            probe = subprocess.run([job["ffprobe"], "-v", "error", "-show_entries",
                "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,avg_frame_rate",
                "-of", "json", str(output)], capture_output=True, text=True, encoding="utf-8", timeout=30, check=True)
            observed = json.loads(probe.stdout)
            bitrate = int(observed["format"].get("bit_rate", 0))
            duration = float(observed["format"]["duration"])
            if (not 0 < bitrate <= 5_000_000 or not math.isfinite(duration) or not duration > 0
                    or (not continuous and (duration > job["duration_seconds"]
                        or _job_bytes(job)[1] + 1024**2 >= job["max_output_bytes"]))):
                raise RuntimeError("closed probe violates bitrate/byte allocation")
            _write_new(root / "closed-file-probe.json", observed)
            completed_payload = {"state": "completed", "path": str(output),
                "bytes": output.stat().st_size, "peak_logical_bytes": peak,
                "frame_receipts": frames, "file_growth_samples": samples,
                "file_growth_summary": sample_summary, "continuous": continuous,
                "stop_reason": watch.reason, "duration_seconds": job["duration_seconds"],
                "max_output_bytes": job["max_output_bytes"], "deadline_utc": job["deadline_utc"],
                "configured_video_CBR_target_bits_per_second": profile["bitrate_kbps"] * 1000,
                "closed_average_total_bitrate_limit": 5_000_000, "actual_closed_average_bitrate": bitrate,
                "instantaneous_bitrate_hard_cap_qualified": False,
                "hidden_Game_freshness_qualified": False, "decision_business_success_inferred": False,
                "ended_at_utc": datetime.now(timezone.utc).isoformat()}
        except Exception as error:
            primary = error
            _write_new(root / "failed.json", {"state": "failed", "error": str(error),
                       "frame_receipts": frames, "file_growth_samples": samples,
                       "file_growth_summary": sample_summary})
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
            cleanup["within_byte_allocation"] = (None if continuous else
                cleanup["final_output_logical_bytes"] + 1024**2 < job["max_output_bytes"])
            if continuous:
                cleanup["continuous"] = True
                try:
                    cleanup["disk_at_close"] = _disk_observation(job)
                except Exception as error:
                    cleanup["disk_read_error"] = str(error)
            if watch:
                cleanup["independent_file_growth_samples"] = watch.samples
                cleanup["watcher_stop_reason"] = watch.reason
                if continuous:
                    cleanup["independent_file_growth_summary"] = watch.sample_summary
                    cleanup["watcher_last_disk_observation"] = watch.last_disk_observation
            _write_new(root / "cleanup.json", cleanup)
            _stop_stall_edl_metadata(job, root)
            if engine.generation:
                engine.generation.close()
    if primary:
        raise primary
    if cleanup.get("stop_error") or cleanup.get("unbind_error") or cleanup.get("close_error") or cleanup.get("disk_read_error") or (not continuous and not cleanup.get("within_byte_allocation")) or cleanup.get("engine_close", {}).get("actual_exit_code") != 0:
        raise RuntimeError("recording complete but dedicated OBS cleanup is not GREEN")

    if completed_payload is None:
        raise RuntimeError("normal capture closed without a final media payload")
    _publish_capture_closed_and_finalize(root, job, completed_payload, cleanup)


def read_capture_closed_receipt(receipt_root, *, session_id, game_pid,
                                game_creation_filetime, recording_worker_pid, recording_root):
    """Read only the admitted capture closure; final media SHA stays separate."""
    if __package__:
        from .ck3_capture_closed_receipt import validate_capture_closed_receipt
    else:
        from ck3_capture_closed_receipt import validate_capture_closed_receipt
    return validate_capture_closed_receipt(
        receipt_root, session_id=session_id, game_pid=game_pid,
        game_creation_filetime=game_creation_filetime,
        recording_worker_pid=recording_worker_pid, recording_root=recording_root,
    )


def stop_session_recording(receipt_root):
    raise RuntimeError("v2 worker owns its exact engine stop; inspect generation receipts")


def request_engine_close(receipt_root):
    raise RuntimeError("v2 worker owns retained-engine close; no detached unverified close")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--continuous", action="store_true", help="require an explicit continuous job")
    args = parser.parse_args()
    if args.continuous and _read(args.job).get("continuous") is not True:
        parser.error("--continuous requires a continuous job with null limits")
    run_worker(args.job)
