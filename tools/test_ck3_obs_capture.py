"""Offline v2 custody contracts; synthetic OS and OBS boundaries only."""
import ctypes
import base64
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock
import uuid

TOOLS = Path(__file__).resolve().parent
# This reviewed candidate is installed at tools/test_ck3_obs_capture.py before running.
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

with mock.patch.object(subprocess, "Popen", side_effect=AssertionError("import launched a process")), \
     mock.patch.object(ctypes, "WinDLL", create=True, side_effect=AssertionError("import accessed Windows")):
    subject = load("ck3_obs_capture", TOOLS / "ck3_obs_capture.py")
    placement = load("custody_generation", TOOLS / "g2_saved_campaign/managed_desktop1_placement.py")



class DecisionBindingRetryTests(unittest.TestCase):
    def test_transient_windows_share_lock_retries_and_keeps_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            text = Path(directory) / "decision.txt"
            text.write_text("bound generation", encoding="utf-8")
            original = Path.read_bytes
            attempts = 0

            def temporarily_locked(path):
                nonlocal attempts
                attempts += 1
                if attempts <= 2:
                    raise PermissionError(13, "sharing violation", str(path))
                return original(path)

            with mock.patch.object(Path, "read_bytes", temporarily_locked),                  mock.patch.object(subject.time, "sleep") as sleep:
                subject._read_decision_binding(text, "bound generation")
            self.assertEqual(attempts, 3)
            self.assertEqual(sleep.call_count, 2)

    def test_wrong_generation_still_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            text = Path(directory) / "decision.txt"
            text.write_text("other generation", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "exact generation binding"):
                subject._read_decision_binding(text, "bound generation")



class WindowSelectorAndForegroundTests(unittest.TestCase):
    def windows(self, second_exe="steamwebhelper.exe"):
        gui = SimpleNamespace(IsWindowVisible=lambda hwnd: True,
            GetWindowText=lambda hwnd: "Crusader Kings III", GetClassName=lambda hwnd: "SDL_app",
            EnumWindows=lambda callback, context: [callback(hwnd, context) for hwnd in (11, 22)])
        process = SimpleNamespace(GetWindowThreadProcessId=lambda hwnd: (1, {11: 100, 22: 200}[hwnd]))
        psutil = SimpleNamespace(Process=lambda pid: SimpleNamespace(
            exe=lambda: "C:/test/" + ("ck3.exe" if pid == 100 else second_exe)))
        return {"win32gui": gui, "win32process": process, "psutil": psutil}

    def test_same_title_steam_window_does_not_conflict_with_full_obs_selector(self):
        with mock.patch.dict(sys.modules, self.windows()):
            self.assertEqual(subject._window_identity(11, 100), "Crusader Kings III:SDL_app:ck3.exe")

    def test_two_actual_games_still_conflict(self):
        with mock.patch.dict(sys.modules, self.windows("ck3.exe")):
            with self.assertRaisesRegex(RuntimeError, "not unique"):
                subject._window_identity(11, 100)

    def test_selector_must_still_bind_the_owned_pid(self):
        with mock.patch.dict(sys.modules, self.windows()):
            with self.assertRaisesRegex(RuntimeError, "not unique"):
                subject._window_identity(11, 999)

    def foreground(self, before, after, pid):
        modules = {"win32gui": SimpleNamespace(GetForegroundWindow=lambda: after),
                   "win32process": SimpleNamespace(GetWindowThreadProcessId=lambda hwnd: (1, pid))}
        with mock.patch.dict(sys.modules, modules):
            return subject._foreground_observation(before, 300)

    def test_user_foreground_change_is_recorded_without_blame_or_restoration(self):
        result = self.foreground(11, 22, 200)
        self.assertTrue(result["foreground_changed"])
        self.assertFalse(result["foreground_after_is_owned_obs"])
        self.assertFalse(result["focus_restoration_attempted"])

    def test_owned_obs_taking_foreground_is_still_identified(self):
        result = self.foreground(11, 22, 300)
        self.assertTrue(result["foreground_changed"])
        self.assertTrue(result["foreground_after_is_owned_obs"])

    def test_unchanged_foreground_needs_no_owner_attribution(self):
        result = self.foreground(11, 11, 200)
        self.assertFalse(result["foreground_changed"])
        self.assertIsNone(result["foreground_after_pid"])


class CaptureContractTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.session = str(uuid.uuid4())
        self.obs_root = self.root / "obs"
        self.exe = self.obs_root / "bin/64bit/obs64.exe"
        self.exe.parent.mkdir(parents=True)
        self.exe.write_bytes(b"synthetic executable identity; never run")
        self.recordings = self.root / "recordings"
        self.recordings.mkdir()
        self.receipts = self.recordings / "session"
        self.receipts.mkdir()
        self.profile_path = self.root / "engine.json"
        name = "ManagedWindowCapture-" + uuid.uuid4().hex
        self.profile = dict(schema=subject.SCHEMA, strict_isolation=True, host="127.0.0.1",
            port=4459, password="synthetic-authentication", obs_root=str(self.obs_root),
            executable=str(self.exe), config_root=str(self.obs_root / "config/obs-studio"),
            profile_name=name, collection_name=name, max_output_bytes=1024**3)
        self.profile_path.write_text(json.dumps(self.profile), encoding="utf-8")
        self.job = dict(schema=subject.SCHEMA, capture_mode="game_only", duration_seconds=45, pid=100, hwnd=456,
            session_id=self.session, recording_root=str(self.recordings), receipt_root=str(self.receipts),
            profile_path=str(self.profile_path), profile_sha256=hashlib.sha256(self.profile_path.read_bytes()).hexdigest(),
            max_output_bytes=1024**3, deadline_utc=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat())
        self.kernel = mock.Mock()
        self.kernel.OpenProcess.return_value = 999
        self.kernel.WaitForSingleObject.return_value = 258
        self.kernel.CloseHandle.return_value = True
        def times(handle, creation, exit_time, kernel_time, user_time):
            creation._obj.value = 123
            return True
        def image(handle, flags, buffer, length):
            buffer.value = str(self.exe.resolve())
            length._obj.value = len(buffer.value)
            return True
        self.kernel.GetProcessTimes.side_effect = times
        self.kernel.QueryFullProcessImageNameW.side_effect = image
        patcher = mock.patch.object(ctypes, "WinDLL", create=True, return_value=self.kernel)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.object(subprocess, "Popen", side_effect=AssertionError("test launched a process"))
        patcher.start()
        self.addCleanup(patcher.stop)

    def client(self):
        client = mock.Mock()
        client.get_profile_list.return_value = SimpleNamespace(current_profile_name=self.profile["profile_name"])
        client.get_scene_collection_list.return_value = SimpleNamespace(current_scene_collection_name=self.profile["collection_name"])
        client.get_profile_parameter.return_value = SimpleNamespace(parameter_value=self.session)
        client.get_record_directory.return_value = SimpleNamespace(record_directory=str(self.recordings))
        client.get_scene_list.return_value = SimpleNamespace(current_program_scene_name=self.profile["profile_name"])
        return client

    def engine(self, client=None):
        client = client or self.client()
        obs = SimpleNamespace(ReqClient=mock.Mock(return_value=client))
        with mock.patch.object(subject, "_control", return_value=obs):
            engine = subject.OwnedEngine(self.profile, self.job)
        engine.process = mock.Mock(pid=100)
        engine.generation = placement.ProcessGeneration(100, self.exe, creation_filetime=123)
        self.addCleanup(engine.generation.close)
        engine.client = client
        return engine, obs, client

    def assert_no_mutation(self, client):
        allowed = {"get_profile_list", "get_scene_collection_list", "get_profile_parameter",
                   "get_record_directory", "get_scene_list", "get_record_status", "disconnect"}
        for call in client.mock_calls:
            self.assertIn(call[0], allowed, "unexpected RPC: " + call[0])

    def assert_single_stop_rpc(self, client):
        allowed = {"get_profile_list", "get_scene_collection_list", "get_profile_parameter",
                   "get_record_directory", "get_scene_list", "get_record_status", "disconnect", "stop_record"}
        for call in client.mock_calls:
            self.assertIn(call[0], allowed, "unexpected RPC: " + call[0])
        client.stop_record.assert_called_once()

    def test_duration_and_binding_rejected_before_capture(self):
        for change in ({"duration_seconds":3600}, {"duration_seconds":45.0}, {"pid":0},
                {"hwnd":None}, {"schema":"other"}, {"session_id":"caller-label"},
                {"receipt_root":str(self.root / "escaped")}):
            with self.subTest(change=change), self.assertRaises((ValueError, TypeError)):
                subject.validate_job({**self.job, **change})
        subject.validate_job(self.job)

    def test_optional_start_signal_stays_in_the_exact_recording_scope(self):
        subject.validate_job({**self.job, "start_signal": str(self.recordings / "fresh.signal")})
        for signal in ("", 12, str(self.root / "other.signal")):
            with self.subTest(signal=signal), self.assertRaises(ValueError):
                subject.validate_job({**self.job, "start_signal": signal})

    def run_start_fixture(self, *, delayed=False, expire_wait=False):
        """Exercise the actual worker start/cleanup with entirely synthetic APIs."""
        self.profile.update(recording_root=str(self.recordings), bitrate_kbps=4800)
        self.profile_path.write_text(json.dumps(self.profile), encoding="utf-8")
        job = {**self.job, "launch": {"creation_date": "synthetic-generation"}, "ffprobe": "synthetic-ffprobe.exe",
               "profile_sha256": subject._sha(self.profile_path)}
        signal = self.recordings / "fresh-start.signal"
        if delayed:
            job["start_signal"] = str(signal)
            text = self.root / "decision.txt"
            text.write_text("进程绑定：PID 100 · synthetic-generation", encoding="utf-8")
            job.update(capture_mode="game_decision", game_creation_filetime=123,
                desktop_id="synthetic-managed-desktop", decision_text_file=str(text),
                overlay={"overlay_pid": 101, "overlay_executable": "synthetic-overlay.exe",
                         "overlay_creation_filetime": 124})
        job_path = self.receipts / "job.json"
        job_path.write_text(json.dumps(job), encoding="utf-8")
        client = self.client()
        inputs = {}
        def create_input(scene, name, kind, settings, enabled):
            inputs[name] = {"inputName": name, "inputKind": kind, "settings": settings}
        client.create_input.side_effect = create_input
        client.remove_input.side_effect = lambda name: inputs.pop(name)
        client.get_input_list.side_effect = lambda: SimpleNamespace(inputs=list(inputs.values()))
        client.get_input_settings.side_effect = lambda name: SimpleNamespace(input_settings=inputs[name]["settings"])
        client.get_scene_item_list.side_effect = lambda scene: SimpleNamespace(scene_items=[
            {"sourceName": name, "sceneItemEnabled": True, "sceneItemIndex": index}
            for index, name in enumerate(inputs)])
        transform = {}
        client.get_scene_item_id.return_value = SimpleNamespace(scene_item_id=1)
        client.set_scene_item_transform.side_effect = lambda scene, item, value: transform.update(value)
        client.get_scene_item_transform.side_effect = lambda scene, item: SimpleNamespace(scene_item_transform=transform)
        client.get_record_status.return_value = SimpleNamespace(output_active=False)
        client.get_video_settings.return_value = SimpleNamespace(base_width=2560, base_height=1440,
            output_width=2560, output_height=1440, fps_numerator=30, fps_denominator=1)
        client.get_profile_parameter.side_effect = lambda category, name: SimpleNamespace(
            parameter_value={"FilenameFormatting": self.session, "RecQuality": "Stream", "VBitrate": "4800"}[name])
        fake_clock = [0.0]
        captures = []
        def screenshot(name, *args):
            captures.append((fake_clock[0], name))
            raw = b"\x89PNG\r\n\x1a\n" + str(fake_clock[0]).encode("ascii")
            return SimpleNamespace(image_data="data:image/png;base64," + base64.b64encode(raw).decode("ascii"))
        client.get_source_screenshot.side_effect = screenshot
        def sleep(seconds):
            fake_clock[0] += seconds
            if delayed and not expire_wait and fake_clock[0] >= 34:
                signal.touch(exist_ok=True)
        def deadline_check(deadline):
            if expire_wait and fake_clock[0] >= 40:
                raise TimeoutError("synthetic unchanged deadline reached")
        def start_once():
            self.assertEqual((self.receipts / "start-signal-observed.json").exists(), delayed)
            self.assertEqual(signal.exists(), delayed)
            raise TimeoutError("synthetic StartRecord outcome unknown")
        client.start_record.side_effect = start_once
        engine = mock.Mock(profile=self.profile, job=job, client=client, process=SimpleNamespace(pid=100))
        engine.start.return_value = client
        engine.reconnect.return_value = client
        engine.close.return_value = {"actual_exit_code": 0}
        game = SimpleNamespace(creation_filetime=123, check=mock.Mock())
        helpers = (lambda *args, **kwargs: nullcontext(SimpleNamespace(check=mock.Mock())),
                   lambda launch: nullcontext(game), mock.Mock(), deadline_check)
        gui = SimpleNamespace(GetForegroundWindow=lambda: 777)
        desktop = SimpleNamespace(window_virtual_desktop=lambda hwnd: {"desktop_id": "synthetic-managed-desktop"})
        with mock.patch.object(subject, "OwnedEngine", return_value=engine), \
             mock.patch.object(subject, "_generation_helpers", return_value=helpers), \
             mock.patch.object(subject, "_window_identity", return_value="synthetic-owned-window"), \
             mock.patch.dict(sys.modules, {"win32gui": gui,
                 "xar_autoplayer.bridge.windows_virtual_desktop": desktop}), \
             mock.patch.object(subject.time, "sleep", side_effect=sleep), \
             mock.patch.object(subject.time, "monotonic", side_effect=lambda: fake_clock[0]):
            expected = "unchanged deadline" if expire_wait else "StartRecord outcome unknown"
            with self.assertRaisesRegex(TimeoutError, expected):
                subject.run_worker(job_path)
        self.assertFalse(inputs)
        engine.close.assert_called_once()
        self.assertTrue((self.receipts / "cleanup.json").is_file())
        self.assertEqual(client.start_record.call_count, 0 if expire_wait else 1)
        client.stop_record.assert_not_called()
        self.assertEqual((self.receipts / "record-armed.json").exists(), delayed)
        if delayed:
            latest = json.loads((self.receipts / "armed-latest.json").read_text(encoding="utf-8"))
            self.assertTrue(latest["mutable_latest_frame"])
            self.assertFalse(latest["recording_started"])
            self.assertEqual(captures[-1][0], 32.0)
            self.assertEqual(len(list(self.receipts.glob("armed-latest-*.png"))), 2)
            self.assertFalse(list(self.receipts.glob("*.tmp")))
            for key in ("game", "scene"):
                observed = latest["frame"][key]
                self.assertEqual(subject._sha(observed["path"]), observed["sha256"])
            failed = json.loads((self.receipts / "failed.json").read_text(encoding="utf-8"))
            self.assertEqual([frame["label"] for frame in failed["frame_receipts"]], ["before-recording"])
            self.assertGreaterEqual(len(captures), 6)
        else:
            self.assertEqual(len(captures), 2)

    def test_default_worker_starts_once_and_does_not_replay_unknown_start(self):
        self.run_start_fixture()

    def test_delayed_worker_keeps_two_latest_frames_then_starts_once(self):
        self.run_start_fixture(delayed=True)

    def test_waiting_deadline_closes_owned_engine_without_starting_output(self):
        self.run_start_fixture(delayed=True, expire_wait=True)

    def run_post_start_fixture(self, *, unexpected_signal=False, continuous=False, reserve_stop=False):
        """Run the real post-StartRecord loop; mock OBS/OS and its file watcher."""
        self.profile.update(recording_root=str(self.recordings), bitrate_kbps=4800)
        storage = {"approved_output_roots": [str(self.root)], "disk_reserve_bytes": 1000}
        if continuous:
            self.profile.update(continuous=True, deadline_utc=None, max_output_bytes=None, storage=storage)
        self.profile_path.write_text(json.dumps(self.profile), encoding="utf-8")
        signal = self.recordings / "fresh-start.signal"
        foreign = self.recordings / "other-unapproved.signal"
        output = self.recordings / (self.session + ".mkv")
        job = {**self.job, "duration_seconds": 2, "launch": {}, "ffprobe": "synthetic-ffprobe.exe",
               "profile_sha256": subject._sha(self.profile_path), "start_signal": str(signal)}
        if continuous:
            job.update(continuous=True, duration_seconds=None, max_output_bytes=None,
                       deadline_utc=None, storage=storage)
        job_path = self.receipts / "job.json"
        job_path.write_text(json.dumps(job), encoding="utf-8")
        client = self.client()
        inputs, clock, active, started_at = {}, [0.0], [False], [None]
        def create_input(scene, name, kind, settings, enabled):
            inputs[name] = {"inputName": name, "inputKind": kind, "settings": settings}
        client.create_input.side_effect = create_input
        client.remove_input.side_effect = lambda name: inputs.pop(name)
        client.get_input_list.side_effect = lambda: SimpleNamespace(inputs=list(inputs.values()))
        client.get_input_settings.side_effect = lambda name: SimpleNamespace(input_settings=inputs[name]["settings"])
        client.get_scene_item_list.side_effect = lambda scene: SimpleNamespace(scene_items=[
            {"sourceName": name, "sceneItemEnabled": True, "sceneItemIndex": 0} for name in inputs])
        client.get_record_status.side_effect = lambda: SimpleNamespace(output_active=active[0], output_path="")
        video = SimpleNamespace(base_width=2560, base_height=1440, output_width=2560,
            output_height=1440, fps_numerator=30, fps_denominator=1)
        video.attrs = lambda: ["base_width", "base_height", "output_width", "output_height", "fps_numerator", "fps_denominator"]
        client.get_video_settings.return_value = video
        client.get_profile_parameter.side_effect = lambda category, name: SimpleNamespace(
            parameter_value={"FilenameFormatting": self.session, "RecQuality": "Stream", "VBitrate": "4800"}[name])
        client.get_source_screenshot.return_value = SimpleNamespace(image_data="data:image/png;base64," +
            base64.b64encode(b"\x89PNG\r\n\x1a\nsynthetic").decode("ascii"))
        def sleep(seconds):
            clock[0] += seconds
            if (self.receipts / "record-armed.json").exists():
                signal.touch(exist_ok=True)
            if active[0]:
                with output.open("ab") as stream:
                    stream.write(b"synthetic growth\n")
                if continuous and not reserve_stop and clock[0] - started_at[0] >= 1300:
                    (self.receipts / "STOP-OWNED-RECORDING").touch()
        def start_record():
            self.assertTrue(signal.is_file())
            active[0] = True
            started_at[0] = clock[0]
            output.write_bytes(b"synthetic video; never decoded\n")
            if unexpected_signal:
                foreign.write_text("unexpected", encoding="utf-8")
        def stop_record():
            active[0] = False
            return SimpleNamespace(output_path=str(output))
        client.start_record.side_effect = start_record
        client.stop_record.side_effect = stop_record
        engine = mock.Mock(profile=self.profile, job=job, client=client, process=SimpleNamespace(pid=100))
        engine.start.return_value = client
        engine.reconnect.return_value = client
        engine.close.return_value = {"actual_exit_code": 0}
        class FakeWatch:
            def __init__(watch, *args):
                watch.requested = mock.Mock()
                watch.requested.is_set.return_value = False
                watch.error, watch.reason, watch.samples, watch.stop_confirmed = None, None, [], False
                watch.sample_summary, watch.last_disk_observation = {}, None
            def start(watch):
                pass
            def request_stop(watch, reason):
                watch.reason = watch.reason or reason
                watch.requested.is_set.return_value = True
            def finish(watch, reason):
                watch.reason = watch.reason or reason
                result = subject._stop_owned(engine)
                watch.stop_confirmed = True
                return result
        game = SimpleNamespace(creation_filetime=123, check=mock.Mock())
        deadline = mock.Mock(side_effect=AssertionError("continuous job consulted a deadline")) if continuous else mock.Mock()
        helpers = (mock.Mock(), lambda launch: nullcontext(game), mock.Mock(), deadline)
        gui = SimpleNamespace(GetForegroundWindow=lambda: 777)
        probe = SimpleNamespace(stdout=json.dumps({"format": {"duration": "1300" if continuous else "1",
                                                "bit_rate": "1000000"}, "streams": []}))
        def disk_observation(job):
            reached = reserve_stop and started_at[0] is not None and clock[0] - started_at[0] >= 1300
            return {"available_bytes": 999 if reached else 2000, "disk_reserve_bytes": 1000,
                    "reserve_reached": reached}
        with mock.patch.object(subject, "OwnedEngine", return_value=engine), \
             mock.patch.object(subject, "FileGrowthWatch", FakeWatch), \
             mock.patch.object(subject, "_generation_helpers", return_value=helpers), \
             mock.patch.object(subject, "_window_identity", return_value="synthetic-owned-window"), \
             mock.patch.dict(sys.modules, {"win32gui": gui}), \
             mock.patch.object(subject.time, "sleep", side_effect=sleep), \
             mock.patch.object(subject.time, "monotonic", side_effect=lambda: clock[0]), \
             mock.patch.object(subject, "_disk_observation", side_effect=disk_observation), \
             mock.patch.object(subject.subprocess, "run", return_value=probe):
            if unexpected_signal:
                with self.assertRaisesRegex(RuntimeError, "unexpected OBS output filename") as caught:
                    subject.run_worker(job_path)
                failed = json.loads((self.receipts / "failed.json").read_text(encoding="utf-8"))
                self.assertEqual(failed["error"], str(caught.exception))
                paths = json.loads(failed["error"].split(": ", 1)[1])
                self.assertEqual(paths, [str(foreign.resolve())])
            else:
                subject.run_worker(job_path)
                completed = json.loads((self.receipts / "completed.json").read_text(encoding="utf-8"))
                self.assertEqual(completed["path"], str(output.resolve()))
                self.assertEqual(len(completed["file_growth_samples"]), subject.RECENT_SAMPLE_COUNT if continuous else 2)
                self.assertFalse((self.receipts / "failed.json").exists())
                if continuous:
                    self.assertGreater(completed["file_growth_summary"]["samples_seen"], 1200)
                    self.assertEqual(completed["stop_reason"], "disk_reserve_reached" if reserve_stop else "owned_shutdown_requested")
                    self.assertEqual([frame["label"] for frame in completed["frame_receipts"]], ["before-recording"])
                    self.assertEqual(len(list(self.receipts.glob("recording-latest-*.png"))), 2)
                    latest = json.loads((self.receipts / "recording-latest.json").read_text(encoding="utf-8"))
                    self.assertTrue(latest["mutable_latest_frame"])
                    for key in ("game", "scene"):
                        frame = latest["frame"][key]
                        self.assertEqual(subject._sha(frame["path"]), frame["sha256"])
                    for receipt in ("started.json", "completed.json"):
                        proof = json.loads((self.receipts / receipt).read_text(encoding="utf-8"))
                        self.assertTrue(proof["continuous"])
                        for key in ("duration_seconds", "max_output_bytes", "deadline_utc"):
                            self.assertIsNone(proof[key])
        self.assertFalse(inputs)
        client.start_record.assert_called_once()
        client.stop_record.assert_called_once()
        engine.close.assert_called_once()

    def test_post_start_file_scan_accepts_the_declared_new_signal(self):
        self.run_post_start_fixture()

    def test_post_start_file_scan_rejects_other_new_signal_with_exact_path(self):
        self.run_post_start_fixture(unexpected_signal=True)

    def test_continuous_worker_runs_past_1200_seconds_until_root_stop_with_recent_proof(self):
        self.run_post_start_fixture(continuous=True)

    def test_continuous_worker_stops_for_actual_disk_reserve_without_game_close(self):
        self.run_post_start_fixture(continuous=True, reserve_stop=True)

    def run_continuous_growth_watch(self, *, disk_stop=False, stalled=False):
        self.job.update(continuous=True, duration_seconds=None, max_output_bytes=None, deadline_utc=None,
            storage={"approved_output_roots": [str(self.root)], "disk_reserve_bytes": 1000})
        engine, _, original = self.engine()
        peer = self.client()
        output = self.recordings / (self.session + ".mkv")
        output.write_bytes(b"synthetic closed output")
        peer.get_record_status.side_effect = [SimpleNamespace(output_active=True), SimpleNamespace(output_active=False)]
        peer.stop_record.return_value = SimpleNamespace(output_path=str(output))
        obs = SimpleNamespace(ReqClient=mock.Mock(return_value=peer))
        clock = [0.0]
        class Request:
            value = False
            def is_set(request):
                return request.value
            def set(request):
                request.value = True
            def wait(request, seconds):
                clock[0] += seconds
                if not disk_stop and clock[0] >= 1300:
                    (self.receipts / "STOP-OWNED-RECORDING").touch()
        watcher = subject.FileGrowthWatch(engine, None, 0)
        watcher.requested = Request()
        def disk(job):
            return {"available_bytes": 999 if disk_stop and clock[0] >= 1300 else 2000,
                    "disk_reserve_bytes": 1000, "reserve_reached": disk_stop and clock[0] >= 1300}
        with mock.patch.object(subject.time, "monotonic", side_effect=lambda: clock[0]), \
             mock.patch.object(subject, "_control", return_value=obs), \
             mock.patch.object(subject, "_listeners", return_value=[SimpleNamespace(pid=100)]), \
             mock.patch.object(subject, "_generation_helpers", side_effect=AssertionError("continuous consulted deadline")), \
             mock.patch.object(subject, "_disk_observation", side_effect=disk), \
             mock.patch.object(subject, "_job_bytes", side_effect=lambda job: (2 * 1024**3 + (0 if stalled else int(clock[0]) * 1000),
                                                                            2 * 1024**3 + (0 if stalled else int(clock[0]) * 1000))):
            watcher.run()
        self.assertTrue(watcher.stop_confirmed)
        if stalled:
            self.assertIn("did not grow for over 30 seconds", watcher.error)
            self.assertEqual(watcher.reason, "file_or_disk_guard")
            self.assertLess(clock[0], 100)
        else:
            self.assertIsNone(watcher.error)
            self.assertEqual(watcher.reason, "disk_reserve_reached" if disk_stop else "owned_shutdown_requested")
            self.assertGreaterEqual(clock[0], 1300)
            self.assertEqual(len(watcher.samples), subject.RECENT_SAMPLE_COUNT)
            self.assertGreater(watcher.sample_summary["samples_seen"], 1200)
        self.assertGreater(watcher.sample_summary["peak_output_logical_bytes"], 1024**3)
        self.assert_single_stop_rpc(peer)
        original.stop_record.assert_not_called()

    def test_continuous_independent_watch_has_no_1200_second_or_1gib_cap(self):
        self.run_continuous_growth_watch()

    def test_continuous_independent_watch_owns_one_stop_at_actual_disk_reserve(self):
        self.run_continuous_growth_watch(disk_stop=True)

    def test_continuous_recording_fault_still_stops_once_and_preserves_failure(self):
        self.run_continuous_growth_watch(stalled=True)

    def test_continuous_prepare_and_launch_preserve_null_limits_and_admitted_paths(self):
        admission = self.root / "admission.json"
        admission.write_text(json.dumps({"status": "ADMITTED", "approved_output_roots": [str(self.root)],
            "disk_reserve_bytes": 1000, "review_at_utc": "2000-01-01T00:00:00+00:00"}), encoding="utf-8")
        profile_path = self.root / "new-profile.json"
        with mock.patch.object(subject, "_listeners", return_value=[]), \
             mock.patch.object(subject, "_control", return_value=SimpleNamespace()), \
             mock.patch.object(subject, "_generation_helpers", side_effect=AssertionError("continuous consulted deadline")), \
             mock.patch.object(subject.shutil, "disk_usage", return_value=SimpleNamespace(free=2000)):
            subject.prepare_profile(self.obs_root, profile_path, self.recordings, port=4459,
                control_dependencies=self.root / "control", deadline_utc=None, max_output_bytes=None,
                continuous=True, storage_admission=admission)
        prepared = json.loads(profile_path.read_text(encoding="utf-8"))
        self.assertTrue(prepared["continuous"])
        self.assertIsNone(prepared["deadline_utc"])
        self.assertIsNone(prepared["max_output_bytes"])
        self.assertEqual(prepared["storage"]["disk_reserve_bytes"], 1000)
        launch = self.root / "launch.json"
        launch.write_text(json.dumps({"pid": 100}), encoding="utf-8")
        ffprobe = self.root / "ffprobe.exe"
        ffprobe.write_bytes(b"synthetic; never execute")
        with mock.patch.object(subject.subprocess, "Popen", return_value=SimpleNamespace(pid=77)) as spawn, \
             mock.patch.object(subject.shutil, "disk_usage", return_value=SimpleNamespace(free=2000)), \
             mock.patch.object(subject, "_generation_helpers", side_effect=AssertionError("continuous consulted deadline")):
            result = subject.launch_recording(profile_path, self.recordings, 100, 456, None,
                launch_receipt=launch, ffprobe=ffprobe, continuous=True)
        job = json.loads((Path(result["receipt_root"]) / "job.json").read_text(encoding="utf-8"))
        for key in ("duration_seconds", "max_output_bytes", "deadline_utc"):
            self.assertIsNone(job[key])
        self.assertEqual(job["storage"], prepared["storage"])
        self.assertIn("--continuous", spawn.call_args.args[0])
        for change in ({"duration_seconds": 5000}, {"max_output_bytes": 10 * 1024**3},
                       {"deadline_utc": "2099-01-01T00:00:00Z"}, {"receipt_root": str(self.root.parent / "outside")}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                subject.validate_job({**job, **change})

    def test_continuous_wrapper_uses_admission_reserve_without_turning_review_into_deadline(self):
        wrapper = load("continuous_recording_wrapper", TOOLS / "g2_saved_campaign/managed_decision_recording.py")
        args = SimpleNamespace(continuous=True, deadline_utc=None, seconds=None, max_output_bytes=None,
            obs_root=self.obs_root, profile=self.profile_path, output_root=self.recordings,
            receipt=self.root / "receipt.json", port=4459, start_signal=None)
        admission = {"status": "ADMITTED", "approved_output_roots": [str(self.root)],
                     "disk_reserve_bytes": 1000, "review_at_utc": "2000-01-01T00:00:00Z"}
        wrapper.validate_admission(args, admission)
        for key, value in (("deadline_utc", "2099-01-01T00:00:00Z"), ("seconds", 5000), ("max_output_bytes", 10 * 1024**3)):
            changed = SimpleNamespace(**{**vars(args), key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                wrapper.validate_admission(changed, admission)
        with self.assertRaises(ValueError):
            wrapper.validate_admission(args, {**admission, "disk_reserve_bytes": None})

    def test_continuous_public_cli_does_not_insert_bounded_defaults(self):
        wrapper = load("continuous_recording_cli", TOOLS / "g2_saved_campaign/managed_decision_recording.py")
        admission = self.root / "admission.json"
        admission.write_text(json.dumps({"status": "ADMITTED", "approved_output_roots": [str(self.root)],
            "disk_reserve_bytes": 1000, "review_at_utc": "2000-01-01T00:00:00Z"}), encoding="utf-8")
        receipt = self.root / "prepared-receipt.json"
        values = {"obs-root": self.obs_root, "profile": self.profile_path, "output-root": self.recordings,
            "control-dependencies": self.root / "control", "launch-receipt": self.root / "launch.json",
            "placement-receipt": self.root / "placement.json", "overlay-receipt": self.root / "overlay.json",
            "ffprobe": self.root / "ffprobe.exe", "receipt": receipt, "storage-admission": admission}
        argv = ["managed_decision_recording.py", "prepare", "--continuous", "--port", "4459"]
        for name, value in values.items():
            argv.extend(["--" + name, str(value)])
        capture = SimpleNamespace(prepare_profile=mock.Mock())
        with mock.patch.object(sys, "argv", argv), mock.patch.dict(sys.modules, {"ck3_obs_capture": capture}), \
             mock.patch.object(sys, "stdout", io.StringIO()):
            wrapper.main()
        kwargs = capture.prepare_profile.call_args.kwargs
        self.assertTrue(kwargs["continuous"])
        self.assertIsNone(kwargs["deadline_utc"])
        self.assertIsNone(kwargs["max_output_bytes"])
        self.assertEqual(kwargs["storage_admission"], admission)

    def test_launch_rejects_a_stale_start_signal_before_starting_a_worker(self):
        self.profile["recording_root"] = str(self.recordings)
        self.profile_path.write_text(json.dumps(self.profile), encoding="utf-8")
        launch = self.root / "launch.json"
        launch.write_text(json.dumps({"pid": self.job["pid"]}), encoding="utf-8")
        signal = self.recordings / "stale.signal"
        signal.touch()
        with self.assertRaisesRegex(ValueError, "signal must be new"):
            subject.launch_recording(self.profile_path, self.recordings, self.job["pid"], self.job["hwnd"],
                45, launch_receipt=launch, ffprobe=self.root / "not-accessed.exe", start_signal=signal)

    def test_profile_is_local_authenticated_and_cannot_replace_user_config(self):
        profile = self.root / "new-profile.json"
        kwargs = dict(port=4459, control_dependencies=self.root / "control",
            deadline_utc=self.job["deadline_utc"], max_output_bytes=1024**3)
        with mock.patch.object(subject, "_listeners", return_value=[]), \
             mock.patch.object(subject, "_control", return_value=SimpleNamespace()):
            subject.prepare_profile(self.obs_root, profile, self.recordings, **kwargs)
            data = json.loads(profile.read_text(encoding="utf-8"))
            self.assertEqual(data["host"], "127.0.0.1")
            self.assertEqual(data["fps"], 30)
            self.assertTrue(data["strict_isolation"])
            self.assertGreaterEqual(len(data["password"]), 32)
            prefix = "ManagedWindowCapture-"
            self.assertTrue(data["profile_name"].startswith(prefix))
            self.assertEqual(uuid.UUID(hex=data["profile_name"][len(prefix):]).version, 4)
            self.assertEqual(data["collection_name"], data["profile_name"])
            second_obs = self.root / "second-obs"
            second_exe = second_obs / "bin/64bit/obs64.exe"
            second_exe.parent.mkdir(parents=True)
            second_exe.write_bytes(b"second synthetic executable; never run")
            second_profile = self.root / "second-profile.json"
            subject.prepare_profile(second_obs, second_profile, self.recordings, **{**kwargs, "port":4460})
            second = json.loads(second_profile.read_text(encoding="utf-8"))
            self.assertEqual(uuid.UUID(hex=second["profile_name"][len(prefix):]).version, 4)
            self.assertEqual(second["collection_name"], second["profile_name"])
            self.assertNotEqual(second["profile_name"], data["profile_name"])
            original = profile.read_bytes()
            with self.assertRaises(ValueError):
                subject.prepare_profile(self.obs_root, profile, self.recordings, **kwargs)
            self.assertEqual(profile.read_bytes(), original)
            with self.assertRaises(FileExistsError):
                subject.prepare_profile(self.obs_root, self.root / "different.json", self.recordings, **kwargs)
            self.assertFalse((self.root / "different.json").exists())

    def test_response_serialization_excludes_sdk_methods(self):
        value = type("Response", (), {"attrs":staticmethod(lambda:["fps_numerator"]),
                                     "fps_numerator":30, "unrelated":object()})
        self.assertEqual(subject._response_data(value), {"fps_numerator":30})

    def test_wrong_listener_pid_blocks_connection_and_mutation(self):
        engine, obs, client = self.engine()
        with mock.patch.object(subject, "_listeners", return_value=[SimpleNamespace(pid=101)]):
            with self.assertRaisesRegex(RuntimeError, "another process"):
                engine.connect()
        obs.ReqClient.assert_not_called()
        self.assert_no_mutation(client)

    def test_wrong_creation_stamp_is_rejected_without_connection(self):
        with self.assertRaisesRegex(RuntimeError, "FILETIME differs"):
            placement.ProcessGeneration(100, self.exe, creation_filetime=124)
        self.kernel.CloseHandle.assert_called_once_with(999)
        self.kernel.QueryFullProcessImageNameW.assert_not_called()

    def test_changed_profile_receipt_blocks_connection_and_mutation(self):
        for changed in ("changed synthetic receipt", json.dumps({**self.profile, "port":4460})):
            with self.subTest(changed=changed):
                engine, obs, client = self.engine()
                self.profile_path.write_text(changed, encoding="utf-8")
                with mock.patch.object(subject, "_listeners", return_value=[SimpleNamespace(pid=100)]):
                    with self.assertRaisesRegex(RuntimeError, "receipt changed"):
                        engine.connect()
                obs.ReqClient.assert_not_called()
                self.assert_no_mutation(client)

    def test_wrong_profile_disconnects_before_mutation(self):
        client = self.client()
        client.get_profile_list.return_value.current_profile_name = "different-profile"
        engine, obs, client = self.engine(client)
        with mock.patch.object(subject, "_listeners", return_value=[SimpleNamespace(pid=100)]):
            with self.assertRaisesRegex(RuntimeError, "identity differs"):
                engine.connect()
        client.disconnect.assert_called_once()
        self.assert_no_mutation(client)

    def test_reconnection_rechecks_engine_and_collection_ownership(self):
        for field in ("profile", "collection"):
            with self.subTest(field=field):
                new = self.client()
                if field == "profile":
                    new.get_profile_list.return_value.current_profile_name = "different-profile"
                else:
                    new.get_scene_collection_list.return_value.current_scene_collection_name = "different-collection"
                engine, obs, _ = self.engine(new)
                old = mock.Mock()
                engine.client = old
                with mock.patch.object(subject, "_listeners", return_value=[SimpleNamespace(pid=100)]):
                    with self.assertRaisesRegex(RuntimeError, "identity differs"):
                        engine.reconnect()
                old.disconnect.assert_called_once()
                new.disconnect.assert_called_once()
                self.assert_no_mutation(old)
                self.assert_no_mutation(new)

    def test_stop_rejects_another_recording_session_before_mutation(self):
        engine, _, client = self.engine()
        client.get_profile_parameter.return_value.parameter_value = "another-session"
        with mock.patch.object(subject, "_listeners", return_value=[SimpleNamespace(pid=100)]):
            with self.assertRaisesRegex(RuntimeError, "ownership changed"):
                subject._stop_owned(engine)
        self.assert_no_mutation(client)

    def test_repeated_stop_requests_issue_one_stop_on_independent_client(self):
        engine, _, original = self.engine()
        peer = self.client()
        output = self.recordings / (self.session + ".mkv")
        output.write_bytes(b"synthetic closed output")
        peer.get_record_status.side_effect = [SimpleNamespace(output_active=True), SimpleNamespace(output_active=False)]
        peer.stop_record.return_value = SimpleNamespace(output_path=str(output))
        obs = SimpleNamespace(ReqClient=mock.Mock(return_value=peer))
        watcher = subject.FileGrowthWatch(engine, 45, time.monotonic())
        watcher.request_stop("first")
        watcher.request_stop("second")
        with mock.patch.object(subject, "_control", return_value=obs), \
             mock.patch.object(subject, "_listeners", return_value=[SimpleNamespace(pid=100)]):
            watcher.start()
            self.assertEqual(watcher.finish("third"), output.resolve())
            self.assertEqual(watcher.finish("fourth"), output.resolve())
        self.assertEqual(watcher.reason, "first")
        self.assertTrue(watcher.stop_confirmed)
        peer.stop_record.assert_called_once()
        self.assert_single_stop_rpc(peer)
        peer.disconnect.assert_called_once()
        original.stop_record.assert_not_called()
        self.assertIs(engine.client, original)

    def test_owned_stop_file_uses_the_existing_single_stop_owner(self):
        engine, _, original = self.engine()
        peer = self.client()
        output = self.recordings / (self.session + ".mkv")
        output.write_bytes(b"synthetic closed output")
        peer.get_record_status.side_effect = [SimpleNamespace(output_active=True),
                                             SimpleNamespace(output_active=False)]
        peer.stop_record.return_value = SimpleNamespace(output_path=str(output))
        obs = SimpleNamespace(ReqClient=mock.Mock(return_value=peer))
        (self.receipts / "STOP-OWNED-RECORDING").write_text("owned shutdown", encoding="utf-8")
        watcher = subject.FileGrowthWatch(engine, 45, time.monotonic())
        with mock.patch.object(subject, "_control", return_value=obs), \
             mock.patch.object(subject, "_listeners", return_value=[SimpleNamespace(pid=100)]):
            watcher.start()
            self.assertTrue(watcher.done.wait(2))
            self.assertEqual(watcher.finish("later_request"), output.resolve())
        self.assertEqual(watcher.reason, "owned_shutdown_requested")
        self.assertTrue(watcher.stop_confirmed)
        self.assert_single_stop_rpc(peer)
        original.stop_record.assert_not_called()

    def test_uncertain_stop_is_not_repeated_or_reported_closed(self):
        engine, _, original = self.engine()
        peer = self.client()
        peer.get_record_status.return_value = SimpleNamespace(output_active=True)
        peer.stop_record.side_effect = TimeoutError("synthetic stop outcome unknown")
        obs = SimpleNamespace(ReqClient=mock.Mock(return_value=peer))
        watcher = subject.FileGrowthWatch(engine, 45, time.monotonic())
        watcher.request_stop("first")
        with mock.patch.object(subject, "_control", return_value=obs), \
             mock.patch.object(subject, "_listeners", return_value=[SimpleNamespace(pid=100)]):
            watcher.start()
            for reason in ("second", "third"):
                with self.assertRaisesRegex(RuntimeError, "stop outcome unknown"):
                    watcher.finish(reason)
        self.assertFalse(watcher.stop_confirmed)
        self.assertIsNone(watcher.output)
        peer.stop_record.assert_called_once()
        self.assert_single_stop_rpc(peer)
        peer.disconnect.assert_called_once()
        original.stop_record.assert_not_called()

    def test_wm_close_timeout_preserves_unknown_exit_without_force(self):
        engine, _, _ = self.engine()
        engine.process.poll.return_value = None
        engine.process.wait.side_effect = subprocess.TimeoutExpired(["synthetic-obs"], 30)
        gui = SimpleNamespace(PostMessage=mock.Mock(), GetParent=lambda _: 0,
                              GetWindowText=lambda _: "OBS 30.0.2",
                              GetClassName=lambda _: "Qt5152QWindowIcon")
        gui.EnumWindows = lambda callback, data: callback(77, data)
        process = SimpleNamespace(GetWindowThreadProcessId=mock.Mock(return_value=(1,100)))
        with mock.patch.dict(sys.modules, {"win32gui":gui, "win32process":process}):
            result = engine.close()
        gui.PostMessage.assert_called_once_with(77, 0x0010, 0, 0)
        self.assertIsNone(result["actual_exit_code"])
        self.assertFalse(result["normal_exit_proven"])
        self.assertEqual(result["forced_process_calls"], 0)
        engine.process.kill.assert_not_called()
        engine.process.terminate.assert_not_called()

    def test_main_close_does_not_post_to_auxiliary_windows(self):
        engine, _, _ = self.engine()
        engine.process.poll.return_value = None
        engine.process.wait.return_value = 0
        gui = SimpleNamespace(PostMessage=mock.Mock(),
            GetParent=lambda hwnd: 0 if hwnd == 77 else 77,
            GetWindowText=lambda hwnd: "OBS 30.0.2",
            GetClassName=lambda _: "Qt5152QWindowIcon")
        gui.EnumWindows = lambda callback, data: [callback(hwnd, data) for hwnd in (77, 88, 99)]
        process = SimpleNamespace(GetWindowThreadProcessId=lambda _: (1, 100))
        with mock.patch.dict(sys.modules, {"win32gui": gui, "win32process": process}):
            self.assertTrue(engine.close()["normal_exit_proven"])
        gui.PostMessage.assert_called_once_with(77, 0x0010, 0, 0)

    def test_two_owned_obs_root_windows_still_reject_close(self):
        engine, _, _ = self.engine()
        engine.process.poll.return_value = None
        gui = SimpleNamespace(PostMessage=mock.Mock(), GetParent=lambda _: 0,
            GetWindowText=lambda _: "OBS 30.0.2", GetClassName=lambda _: "Qt5152QWindowIcon")
        gui.EnumWindows = lambda callback, data: [callback(hwnd, data) for hwnd in (77, 88)]
        process = SimpleNamespace(GetWindowThreadProcessId=lambda _: (1, 100))
        with mock.patch.dict(sys.modules, {"win32gui": gui, "win32process": process}), \
                self.assertRaisesRegex(RuntimeError, "not unique"):
            engine.close()
        gui.PostMessage.assert_not_called()
        engine.process.wait.assert_not_called()

    def test_obs_root_parent_change_rejects_close_without_post(self):
        engine, _, _ = self.engine()
        engine.process.poll.return_value = None
        gui = SimpleNamespace(PostMessage=mock.Mock(), GetParent=mock.Mock(side_effect=[0, 88]),
            GetWindowText=lambda _: "OBS 30.0.2", GetClassName=lambda _: "Qt5152QWindowIcon")
        gui.EnumWindows = lambda callback, data: callback(77, data)
        process = SimpleNamespace(GetWindowThreadProcessId=lambda _: (1, 100))
        with mock.patch.dict(sys.modules, {"win32gui": gui, "win32process": process}), \
                self.assertRaisesRegex(RuntimeError, "changed generation"):
            engine.close()
        gui.PostMessage.assert_not_called()

    def test_late_input_removal_is_observed_without_resending(self):
        engine, _, client = self.engine()
        client.get_record_status.return_value = SimpleNamespace(output_active=False)
        attached = SimpleNamespace(inputs=[{"inputName": "owned"}])
        client.get_input_list.side_effect = [attached, attached, SimpleNamespace(inputs=[])]
        with mock.patch.object(subject, "_listeners", return_value=[SimpleNamespace(pid=100)]), \
             mock.patch.object(subject.time, "sleep"):
            self.assertTrue(subject._unbind_owned_inputs(engine, ["owned"], True))
        client.remove_input.assert_called_once_with("owned")

    def test_unobserved_removal_is_not_resubmitted(self):
        engine, _, client = self.engine()
        client.get_record_status.return_value = SimpleNamespace(output_active=False)
        client.get_input_list.return_value = SimpleNamespace(inputs=[{"inputName": "owned"}])
        with mock.patch.object(subject, "_listeners", return_value=[SimpleNamespace(pid=100)]), \
             mock.patch.object(subject.time, "sleep"), self.assertRaises(TimeoutError):
            subject._unbind_owned_inputs(engine, ["owned"], True)
        client.remove_input.assert_called_once_with("owned")

    def test_unknown_input_rejects_removal_before_mutation(self):
        engine, _, client = self.engine()
        client.get_record_status.return_value = SimpleNamespace(output_active=False)
        client.get_input_list.return_value = SimpleNamespace(inputs=[{"inputName": "foreign"}])
        with mock.patch.object(subject, "_listeners", return_value=[SimpleNamespace(pid=100)]), \
             self.assertRaisesRegex(RuntimeError, "unknown OBS inputs"):
            subject._unbind_owned_inputs(engine, ["owned"], True)
        client.remove_input.assert_not_called()


if __name__ == "__main__":
    unittest.main()
