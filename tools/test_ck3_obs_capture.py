"""Offline v2 custody contracts; synthetic OS and OBS boundaries only."""
import ctypes
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
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
        gui = SimpleNamespace(PostMessage=mock.Mock(), GetWindowText=lambda _: "OBS 30.0.2",
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
            GetWindowText=lambda hwnd: "OBS 30.0.2" if hwnd == 77 else "Qt auxiliary",
            GetClassName=lambda _: "Qt5152QWindowIcon")
        gui.EnumWindows = lambda callback, data: [callback(hwnd, data) for hwnd in (77, 88, 99)]
        process = SimpleNamespace(GetWindowThreadProcessId=lambda _: (1, 100))
        with mock.patch.dict(sys.modules, {"win32gui": gui, "win32process": process}):
            self.assertTrue(engine.close()["normal_exit_proven"])
        gui.PostMessage.assert_called_once_with(77, 0x0010, 0, 0)

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
