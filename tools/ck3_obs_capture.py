"""Typed, bounded OBS game-window recording provider (contract v1).

Caller adapters supply their attested HWND/PID and recording directory. No
project paths, mod identities, arbitrary OBS requests or desktop input are
part of this provider. A worker owns the timed stop and its immutable receipts.
"""
from __future__ import annotations

import argparse
import base64
import ctypes
from ctypes import wintypes
import hashlib
import json
import logging
from pathlib import Path
import secrets
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

PROVIDER_VERSION = "1.0.0"
SCHEMA = "xar.ck3.obs-window-capture.v1"
ALLOWED_SECONDS = frozenset({15, 30, 45, 60, 90, 120})


def _response_data(value: object) -> dict:
    return {key: getattr(value, key) for key in value.attrs()}


def _reconnect_owned_output(profile: dict, job: dict, previous: object):
    import obsws_python as obs
    previous.disconnect()
    client = obs.ReqClient(host='127.0.0.1', port=profile['port'], password=profile['password'], timeout=10)
    if client.get_profile_parameter('Output', 'FilenameFormatting').parameter_value != job['session_id']:
        client.disconnect()
        raise RuntimeError('OBS recording ownership changed during capture')
    return client


def _write_new(path: Path, data: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def prepare_profile(obs_root: Path, profile_path: Path, recording_root: Path) -> Path:
    obs_root, profile_path, recording_root = (p.resolve() for p in (obs_root, profile_path, recording_root))
    executable = obs_root / "bin/64bit/obs64.exe"
    if not executable.is_file():
        raise FileNotFoundError(executable)
    if profile_path.exists():
        return profile_path
    config = obs_root / "config/obs-studio"
    if (config / "global.ini").exists():
        raise FileExistsError("refusing to replace an existing OBS configuration")
    recording_root.mkdir(parents=True, exist_ok=True)
    basic = config / "basic/profiles/ManagedWindowCapture"
    basic.mkdir(parents=True)
    (obs_root / "portable_mode.txt").write_text("", encoding="utf-8")
    password = secrets.token_urlsafe(32)
    (config / "global.ini").write_text(
        "[General]\nFirstRun=false\nLastVersion=503382018\nEnableAutoUpdates=false\n"
        "[Basic]\nProfile=ManagedWindowCapture\nProfileDir=ManagedWindowCapture\n"
        "SceneCollection=ManagedWindowCapture\nSceneCollectionFile=ManagedWindowCapture\n"
        "[BasicWindow]\nPreviewEnabled=false\nStudioMode=false\nSysTrayEnabled=true\n"
        f"[OBSWebSocket]\nFirstLoad=false\nServerEnabled=true\nServerPort=4459\nAlertsEnabled=false\nAuthRequired=true\nServerPassword={password}\n", encoding="utf-8")
    (basic / "basic.ini").write_text(
        "[General]\nName=ManagedWindowCapture\n[Output]\nMode=Simple\nFilenameFormatting=managed\n"
        f"[SimpleOutput]\nRecFilePath={recording_root.as_posix()}\nRecFormat=mkv\nRecEncoder=nvenc\nRecQuality=HQ\n"
        "[Video]\nBaseCX=1920\nBaseCY=1080\nOutputCX=1920\nOutputCY=1080\nFPSType=0\nFPSCommon=60\n"
        "ColorFormat=NV12\nColorSpace=709\nColorRange=Partial\n"
        "[Audio]\nSampleRate=48000\nChannelSetup=Stereo\nDesktopDevice1=disabled\nDesktopDevice2=disabled\n"
        "AuxDevice1=disabled\nAuxDevice2=disabled\nAuxDevice3=disabled\n", encoding="utf-8")
    scenes = config / "basic/scenes"
    scenes.mkdir(parents=True)
    _write_new(scenes / "ManagedWindowCapture.json", {
        "name": "ManagedWindowCapture", "current_scene": "ManagedWindowCapture",
        "current_program_scene": "ManagedWindowCapture", "scene_order": [{"name": "ManagedWindowCapture"}],
        "sources": [{"name": "ManagedWindowCapture", "id": "scene", "versioned_id": "scene",
                     "settings": {"items": []}}], "groups": [], "transitions": [],
    })
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    _write_new(profile_path, {"schema": SCHEMA, "provider_version": PROVIDER_VERSION,
        "obs_root": str(obs_root), "executable": str(executable), "host": "127.0.0.1", "port": 4459,
        "password": password, "recording_root": str(recording_root), "fps": 60})
    return profile_path


def validate_job(job: dict) -> None:
    if job.get("schema") != SCHEMA or job.get("duration_seconds") not in ALLOWED_SECONDS:
        raise ValueError("unsupported capture contract or duration")
    if type(job["duration_seconds"]) is not int:
        raise ValueError("duration must be an integer")
    if any(type(job.get(key)) is not int or job[key] <= 0 for key in ("pid", "hwnd")):
        raise ValueError("capture requires an attested process and window")
    uuid.UUID(job["session_id"])
    root = Path(job["recording_root"]).resolve()
    if not Path(job["receipt_root"]).resolve().is_relative_to(root):
        raise ValueError("receipt path escaped the recording root")


def launch_recording(profile_path: Path, recording_root: Path, pid: int, hwnd: int, seconds: int) -> dict:
    session = str(uuid.uuid4())
    receipt_root = recording_root.resolve() / session
    job = {"schema": SCHEMA, "provider_version": PROVIDER_VERSION, "session_id": session,
           "profile_path": str(profile_path.resolve()), "recording_root": str(recording_root.resolve()),
           "receipt_root": str(receipt_root), "pid": pid, "hwnd": hwnd, "duration_seconds": seconds}
    validate_job(job)
    receipt_root.mkdir()
    path = receipt_root / "job.json"
    _write_new(path, job)
    with (receipt_root / "worker.stdout.txt").open("x", encoding="utf-8") as stdout, (receipt_root / "worker.stderr.txt").open("x", encoding="utf-8") as stderr:
        worker = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--job", str(path)],
            stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return {"schema": SCHEMA, "session_id": session, "worker_pid": worker.pid,
            "receipt_root": str(receipt_root), "state": "requested"}


def _window_identity(hwnd: int, expected_pid: int) -> str:
    user32 = ctypes.windll.user32
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value != expected_pid or not user32.IsWindowVisible(hwnd):
        raise RuntimeError("capture window no longer belongs to the expected process")
    title, classname = ctypes.create_unicode_buffer(512), ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, title, len(title))
    user32.GetClassNameW(hwnd, classname, len(classname))
    if title.value != "Crusader Kings III":
        raise RuntimeError("capture window is not CK3")
    escape = lambda text: text.replace("#", "#22").replace(":", "#3A")
    return ":".join(map(escape, (title.value, classname.value, "ck3.exe")))


def engine_windows(receipt_root: Path) -> list[int]:
    return [item['hwnd'] for item in engine_window_inventory(receipt_root)
            if (item['title'].startswith('OBS ') and 'ManagedWindowCapture' in item['title'])
            or item['title'] in {'OBS 已在运行', 'OBS is already running'}]


def engine_window_inventory(receipt_root: Path) -> list[dict]:
    job = json.loads((receipt_root / "job.json").read_text(encoding="utf-8"))
    validate_job(job)
    launch = receipt_root / "obs-launch.json"
    if not launch.is_file():
        return []
    expected_pid = json.loads(launch.read_text(encoding="utf-8"))["pid"]
    user32 = ctypes.windll.user32
    handles = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def visit(hwnd, _):
        pid = wintypes.DWORD()
        name = ctypes.create_unicode_buffer(128)
        title = ctypes.create_unicode_buffer(512)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        user32.GetClassNameW(hwnd, name, len(name))
        user32.GetWindowTextW(hwnd, title, len(title))
        if pid.value == expected_pid:
            handles.append({'hwnd': int(hwnd), 'title': title.value, 'class': name.value,
                            'visible': bool(user32.IsWindowVisible(hwnd))})
        return True
    callback = callback_type(visit)
    user32.EnumWindows(callback, 0)
    return handles


def request_engine_close(receipt_root: Path) -> dict:
    # Only this provider's launched OBS window; never accepts caller HWND/PID.
    if not (receipt_root / "failed.json").is_file() and not (receipt_root / "completed.json").is_file():
        raise RuntimeError("capture worker must finish before its engine is closed")
    handles = engine_windows(receipt_root)
    if handles:
        import obsws_python as obs
        logging.getLogger('obsws_python').setLevel(logging.WARNING)
        job = json.loads((receipt_root / 'job.json').read_text(encoding='utf-8'))
        profile = json.loads(Path(job['profile_path']).read_text(encoding='utf-8'))
        try:
            client = obs.ReqClient(host='127.0.0.1', port=profile['port'], password=profile['password'], timeout=2)
        except Exception:
            client = None
        if client:
            try:
                if client.get_record_status().output_active:
                    raise RuntimeError('refusing to close an OBS engine with active output')
            finally:
                client.disconnect()
    for hwnd in handles:
        if not ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0):
            raise RuntimeError("owned OBS close request failed")
    return {"close_requested": bool(handles), "owned_windows": handles}


def stop_session_recording(receipt_root: Path) -> dict:
    import obsws_python as obs
    logging.getLogger('obsws_python').setLevel(logging.WARNING)
    job = json.loads((receipt_root / 'job.json').read_text(encoding='utf-8'))
    validate_job(job)
    profile = json.loads(Path(job['profile_path']).read_text(encoding='utf-8'))
    if profile.get('host') != '127.0.0.1':
        raise ValueError('capture control must remain local')
    client = obs.ReqClient(host=profile['host'], port=profile['port'], password=profile['password'], timeout=10)
    try:
        if client.get_profile_parameter('Output', 'FilenameFormatting').parameter_value != job['session_id']:
            raise RuntimeError('active OBS output belongs to another session')
        if not client.get_record_status().output_active:
            return {'stop_requested': False, 'output_active': False}
        output = Path(client.stop_record().output_path).resolve()
        for _ in range(20):
            status = client.get_record_status()
            if not status.output_active:
                break
            time.sleep(0.5)
        if status.output_active:
            raise RuntimeError('OBS stop has not completed')
        if not output.is_relative_to(Path(job['recording_root']).resolve()) or output.stem != job['session_id']:
            raise RuntimeError('stopped OBS output escaped its session')
        data = {'stop_requested': True, 'output_active': client.get_record_status().output_active,
                'path': str(output), 'bytes': output.stat().st_size,
                'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                'stats_after': _response_data(client.get_stats())}
        _write_new(receipt_root / 'recovered-stop.json', data)
        return data
    finally:
        client.disconnect()


def run_worker(path: Path) -> None:
    import obsws_python as obs
    logging.getLogger('obsws_python').setLevel(logging.WARNING)
    job = json.loads(path.read_text(encoding="utf-8"))
    validate_job(job)
    root = Path(job["receipt_root"])
    profile = json.loads(Path(job["profile_path"]).read_text(encoding="utf-8"))
    if profile.get("schema") != SCHEMA or profile.get("host") != "127.0.0.1" or profile.get("fps") != 60:
        raise ValueError("unsupported server profile")
    window = _window_identity(job["hwnd"], job["pid"])
    client = None
    recording = False
    try:
        try:
            client = obs.ReqClient(host=profile["host"], port=profile["port"], password=profile["password"], timeout=10)
        except Exception:
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 0
            process = subprocess.Popen([profile["executable"], "--portable", "--minimize-to-tray", "--disable-updater",
                "--disable-missing-files-check", "--profile", "ManagedWindowCapture", "--collection", "ManagedWindowCapture"],
                cwd=str(Path(profile["executable"]).parent), startupinfo=startup,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            _write_new(root / "obs-launch.json", {"pid": process.pid})
            for _ in range(40):
                time.sleep(1)
                if process.poll() is not None:
                    raise RuntimeError(f"owned OBS process exited before control readiness (code {process.returncode})")
                try:
                    client = obs.ReqClient(host=profile["host"], port=profile["port"], password=profile["password"], timeout=10)
                    break
                except Exception:
                    pass
        if client is None:
            raise RuntimeError("OBS control service did not become ready")
        if client.get_record_status().output_active:
            raise RuntimeError("another OBS recording is active")
        scene = "ManagedWindowCapture"
        source = "ManagedCK3Window"
        names = {x["inputName"] for x in client.get_input_list().inputs}
        settings = {"capture_mode": "window", "window": window, "priority": 0,
                    "capture_cursor": False, "capture_audio": False, "limit_framerate": False}
        if source in names:
            client.set_input_settings(source, settings, True)
        else:
            client.create_input(scene, source, "game_capture", settings, True)
        client.set_current_program_scene(scene)
        client.set_record_directory(job["recording_root"])
        client.set_profile_parameter("Output", "FilenameFormatting", job["session_id"])
        video = client.get_video_settings()
        if (video.base_width, video.base_height, video.output_width, video.output_height, video.fps_numerator, video.fps_denominator) != (1920, 1080, 1920, 1080, 60, 1):
            raise RuntimeError("OBS video settings do not match the capture profile")
        time.sleep(3)
        image = client.get_source_screenshot(source, "png", 1920, 1080, -1)
        (root / "source-before.png").write_bytes(base64.b64decode(image.image_data.split(",", 1)[1]))
        client.start_record()
        for _ in range(20):
            status = client.get_record_status()
            if status.output_active:
                break
            time.sleep(0.5)
        if not status.output_active:
            raise RuntimeError("OBS did not start recording")
        recording = True
        _write_new(root / "started.json", {"state": "recording", "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "window": window, "source_settings": client.get_input_settings(source).input_settings,
            "video": _response_data(video), "stats_before": _response_data(client.get_stats())})
        deadline = time.monotonic() + job['duration_seconds']
        reconnect_at = time.monotonic() + 20
        while time.monotonic() < deadline:
            time.sleep(min(3, max(0, deadline - time.monotonic())))
            if time.monotonic() >= reconnect_at:
                client = _reconnect_owned_output(profile, job, client)
                reconnect_at = time.monotonic() + 20
            if not client.get_record_status().output_active:
                raise RuntimeError('OBS output stopped before its bounded duration')
        stopped = client.stop_record()
        for _ in range(20):
            if not client.get_record_status().output_active:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError('OBS stop has not completed')
        recording = False
        output = Path(stopped.output_path).resolve()
        if not output.is_relative_to(Path(job["recording_root"]).resolve()) or not output.is_file():
            raise RuntimeError("OBS output path escaped its recording scope")
        _write_new(root / "completed.json", {"state": "completed", "path": str(output), "bytes": output.stat().st_size,
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "stats_after": _response_data(client.get_stats()),
            "ended_at_utc": datetime.now(timezone.utc).isoformat()})
    except Exception as exc:
        if recording and client:
            try:
                client.stop_record()
            except Exception:
                pass
        _write_new(root / "failed.json", {"state": "failed", "error": str(exc)})
        raise
    finally:
        if client:
            client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", type=Path, required=True)
    run_worker(parser.parse_args().job)
