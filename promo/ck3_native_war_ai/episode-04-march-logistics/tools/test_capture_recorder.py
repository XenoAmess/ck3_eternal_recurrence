"""Offline capture geometry/lifecycle regressions; no Win32/SDK/media operation."""
import copy
from contextlib import nullcontext
import importlib.util
import json
from pathlib import Path
import sys
import threading
import types
from unittest import mock

from PIL import Image
import pytest


SPEC = importlib.util.spec_from_file_location(
    "episode04_capture_recorder_test_subject", Path(__file__).with_name("capture_recorder.py"))
recorder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recorder)


def source():
    return {"kind": recorder.CAPTURE_SOURCE, "owned_ck3_pid": 123,
            "owned_ck3_create_time": 123456.0, "hwnd": 321, "foreground_hwnd": 321,
            "desktop": [1920, 1080], "client_screen_rect": [100, 80, 1380, 800],
            "occluding_windows": [], "direct_hwnd_capture": False}


def test_ffmpeg_captures_physical_client_bounds_and_retains_native_resolution():
    command = recorder.ffmpeg_command("ffmpeg.exe", source(), 90, "raw.mkv")
    assert command[command.index("-offset_x") + 1] == "100"
    assert command[command.index("-offset_y") + 1] == "80"
    assert command[command.index("-video_size") + 1] == "1280x720"
    assert command[command.index("-i") + 1] == "desktop"
    assert not any("hwnd=" in part for part in command)
    assert "-vf" not in command  # No silent crop/scale or enlarged full desktop.


@pytest.mark.parametrize("rect", [
    [-1, 0, 1279, 720], [0, -1, 1280, 719], [1000, 0, 2280, 720],
    [0, 500, 1280, 1220], [0, 0, 1279, 720], [0, 0, 1280, 719],
    [0, 0, 638, 360], [0, 0, 640, 358], [100, 0, 100, 720],
])
def test_invalid_client_regions_are_rejected_without_implicit_correction(rect):
    actual = source()
    actual["client_screen_rect"] = rect
    with pytest.raises(ValueError):
        recorder.validate_client_region(actual)


@pytest.mark.parametrize("key,value", [
    ("owned_ck3_pid", 456), ("owned_ck3_create_time", 123457.0), ("hwnd", 999),
    ("desktop", [2560, 1440]), ("client_screen_rect", [102, 80, 1382, 800]),
    ("foreground_hwnd", 999), ("occluding_windows", [{"hwnd": 999, "pid": 456}]),
])
def test_capture_guard_rejects_identity_geometry_focus_and_occlusion_changes(key, value):
    actual = copy.deepcopy(source())
    actual[key] = value
    with pytest.raises(ValueError):
        recorder.require_same_source(source(), actual)


def prepared(tmp_path):
    return {"assets_root": str(tmp_path), "machine_id": "synthetic-recorder-machine"}


@pytest.mark.parametrize("failure_stage", ["none", "deadline", "ready-plus-failure",
    "ready-plus-terminalfailure", "ready-plus-abortfailure"])
def test_start_preserves_client_geometry_and_rechecks_deadline_before_spawn(
        monkeypatch, tmp_path, failure_stage):
    desktop = Image.new("RGB", (1920, 1080))
    original = tmp_path / "reviewed-original.png"
    desktop.save(original)
    executable = tmp_path / "ffmpeg.exe"
    executable.write_bytes(b"synthetic executable: never run")
    offline = tmp_path / "offline.json"
    offline.write_text("{}", encoding="utf-8")
    monkeypatch.setitem(sys.modules, "pyautogui", types.SimpleNamespace(
        size=lambda: desktop.size, screenshot=lambda: desktop.copy()))
    owned_job = mock.Mock(pid=456)
    owned_job.poll.return_value = None
    owned_job.abort.return_value = {"state": "ABORT_TREE_EMPTY", "job_active_processes": 0}
    media_streams = []

    def fake_spawn(command, **kwargs):
        recorder.write(kwargs["start_receipt"], {"synthetic": True})
        media_streams.extend([kwargs["stdout"], kwargs["stderr"]])
        return owned_job

    spawn = mock.Mock(side_effect=fake_spawn)
    monkeypatch.setitem(sys.modules, "recorder_job", types.SimpleNamespace(spawn=spawn))
    monkeypatch.setattr(recorder, "inspect_owned_client", mock.Mock(return_value=source()))
    monkeypatch.setattr(recorder.threading, "Thread", mock.Mock())
    keeper = types.SimpleNamespace(task_id="synthetic-screen-owner", process_create_gate=nullcontext)
    admission = mock.Mock(side_effect=[{"stage": "request", "seconds": 90},
        ValueError("remaining time below recording plus shutdown reserve") if failure_stage == "deadline"
        else {"stage": "spawn", "seconds": 90}])
    subject = recorder.OwnedRecorder(tmp_path, keeper, offline, prepared(tmp_path), start_admission=admission)
    arguments = {"operation": "start", "workdir": str(tmp_path / "capture"),
        "ffmpeg": str(executable), "ffmpeg_sha256": recorder.pin(executable)["sha256"],
        "target_pid": 123, "source_image": str(original), "seconds": 90}
    if failure_stage == "deadline":
        with pytest.raises(ValueError, match="shutdown reserve"):
            subject.handle(arguments, {"map_ready": True, "paused": True})
        assert subject.job is None
        assert subject.streams == []
        assert (tmp_path / "capture" / "start-failure.json").exists()
        assert not (tmp_path / "capture" / "process-ready.json").exists()
        spawn.assert_not_called()
        assert admission.call_args_list == [mock.call(90), mock.call(90)]
        return
    if failure_stage.startswith("ready-plus-"):
        actual_write = recorder.write
        if failure_stage == "ready-plus-abortfailure":
            owned_job.abort.side_effect = RuntimeError("Job tree cleanup unproven")

        def fail_both_receipts(path, body):
            if Path(path).name in {"process-ready.json", "start-failure.json"} or (
                    failure_stage == "ready-plus-terminalfailure" and Path(path).name == "result.json"):
                raise OSError("disk full writing " + Path(path).name)
            return actual_write(path, body)

        monkeypatch.setattr(recorder, "write", fail_both_receipts)
        with pytest.raises(OSError, match="process-ready.json") as first_error:
            subject.handle(arguments, {"map_ready": True, "paused": True})
        owned_job.abort.assert_called_once()
        assert subject.streams == []
        assert len(media_streams) == 2 and all(stream.closed for stream in media_streams)
        assert "start-failure.json" in subject.cleanup_error
        assert "start-failure.json" in " ".join(first_error.value.__notes__)
        if failure_stage == "ready-plus-abortfailure":
            assert subject.terminal is None
            assert "Job tree cleanup unproven" in subject.cleanup_error
        else:
            assert subject.terminal["job_active_processes"] == 0
            assert subject.report()["state"] == "ABORT_TREE_EMPTY"
        if failure_stage == "ready-plus-terminalfailure":
            assert "result.json" in subject.cleanup_error
        return
    result = subject.handle(arguments, {"map_ready": True, "paused": True})
    assert result["capture_source"]["kind"] == "gdigrab-desktop-client-region"
    assert result["capture_source"]["direct_hwnd_capture"] is False
    intent = json.loads((tmp_path / "capture" / "intent.json").read_text(encoding="utf-8"))
    with Image.open(tmp_path / "capture" / "preflight-desktop.png") as full:
        assert full.size == (1920, 1080)
    assert intent["argv"][intent["argv"].index("-video_size") + 1] == "1280x720"
    assert intent["source_image"]["sha256"] == recorder.pin(original)["sha256"]
    assert intent["machine_id"] == "synthetic-recorder-machine"
    assert intent["deadline_admission_at_request"]["stage"] == "request"
    assert result["deadline_admission_at_spawn"]["stage"] == "spawn"
    assert json.loads((tmp_path / "capture" / "deadline-admission-at-spawn.json").read_text(
        encoding="utf-8"))["admission"]["stage"] == "spawn"
    assert admission.call_args_list == [mock.call(90), mock.call(90)]
    assert recorder.inspect_owned_client.call_count == 2  # Recheck inside process-create gate.
    spawn.assert_called_once()
    subject._close_streams()


@pytest.mark.parametrize("admission", [None,
    mock.Mock(side_effect=ValueError("deadline exhausted")), mock.Mock(return_value=[]),
])
def test_missing_or_denied_deadline_does_not_create_workdir_or_consume_attempt(tmp_path, admission):
    subject = recorder.OwnedRecorder(tmp_path, None, None, prepared(tmp_path), start_admission=admission)
    with pytest.raises(ValueError):
        subject.handle({"operation": "start", "workdir": str(tmp_path / "capture"),
            "ffmpeg": "unused.exe", "ffmpeg_sha256": "a" * 64, "target_pid": 123,
            "source_image": "unused.png", "seconds": 90}, {"map_ready": True, "paused": True})
    assert subject.directory is None
    assert not (tmp_path / "capture").exists()


def test_source_change_finishes_readable_container_and_retains_red(monkeypatch, tmp_path):
    keeper = types.SimpleNamespace(require_live=mock.Mock())
    subject = recorder.OwnedRecorder(tmp_path, keeper, tmp_path / "unused-offline", prepared(tmp_path))
    subject.directory = tmp_path / "capture"
    subject.directory.mkdir()
    subject.capture_source = source()
    subject.job = mock.Mock(pid=456)
    subject.job.poll.return_value = None
    subject.job.finish.return_value = {"state": "NORMAL_TREE_EMPTY", "job_active_processes": 0}
    monkeypatch.setattr(recorder, "CAPTURE_GUARD_INTERVAL_SECONDS", 0.001)
    monkeypatch.setattr(recorder, "inspect_owned_client", mock.Mock(side_effect=ValueError("window moved")))
    subject._watch_capture_source()
    subject.job.finish.assert_called_once()
    result = json.loads((subject.directory / "result.json").read_text(encoding="utf-8"))
    assert result["state"] == "RED_CAPTURE_SOURCE_CHANGED"
    assert result["job"]["state"] == "NORMAL_TREE_EMPTY"
    assert result["clean_spans_certified"] is False
    assert result["human_approval"] is False
    assert (subject.directory / "capture-guard-failure.json").exists()
    assert subject.report()["state"] == "RED_CAPTURE_SOURCE_CHANGED"
    with pytest.raises(ValueError, match="capture guard failed"):
        subject.require_healthy()


def test_close_signals_and_joins_guard_without_holding_end_lock(tmp_path):
    subject = recorder.OwnedRecorder(tmp_path, None, None, prepared(tmp_path))
    # Synthetic waiting thread only; no capture or Win32 function is called.
    def watcher():
        subject.capture_guard_stop.wait()
        with subject._end_lock:
            pass

    thread = threading.Thread(target=watcher)
    subject.capture_guard_thread = thread
    thread.start()
    subject.close()
    assert subject.capture_guard_stop.is_set()
    assert not thread.is_alive()


def test_close_never_joins_current_guard_thread(tmp_path):
    subject = recorder.OwnedRecorder(tmp_path, None, None, prepared(tmp_path))
    subject.capture_guard_thread = threading.current_thread()
    subject.close()  # Thread.join would raise if attempted on the current thread.
    assert subject.capture_guard_stop.is_set()


def test_stream_close_failure_does_not_skip_remaining_streams(tmp_path):
    subject = recorder.OwnedRecorder(tmp_path, None, None, prepared(tmp_path))
    good, bad = mock.Mock(), mock.Mock()
    bad.close.side_effect = OSError("synthetic close failure")
    subject.streams = [good, bad]
    with pytest.raises(RuntimeError, match="synthetic close failure"):
        subject._close_streams()
    good.close.assert_called_once()
    bad.close.assert_called_once()
    assert subject.streams == []
