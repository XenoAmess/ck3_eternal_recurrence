"""Pure custody contract tests; no OBS, desktop or personal process access."""
import importlib.util
import ctypes
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import subprocess
from types import SimpleNamespace
import unittest
from unittest import mock


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


with mock.patch.object(subprocess, "Popen", side_effect=AssertionError("external custody import forbidden")), \
     mock.patch.object(ctypes, "WinDLL", create=True, side_effect=AssertionError("external custody import forbidden")):
    capture = load_module("custody_capture_contract", "ck3_obs_capture.py")
    recording = load_module("custody_recording_contract", "g2_saved_campaign/managed_decision_recording.py")
SESSION = "00000000-0000-4000-8000-000000000001"
MIN_BYTES = 192 * 1024**2
MAX_BYTES = 1024**3


class CustodyValidatorTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.now = datetime.now(timezone.utc)
        self.review = self.now + timedelta(hours=2)
        self.job = dict(schema=capture.SCHEMA, capture_mode="game_only", duration_seconds=15, pid=1, hwnd=2,
            session_id=SESSION, recording_root=str(self.root / "record"),
            receipt_root=str(self.root / "record/session"), max_output_bytes=MAX_BYTES)
        name = "ManagedWindowCapture-" + SESSION.replace("-", "")
        obs = self.root / "obs"
        self.profile = dict(schema=capture.SCHEMA, strict_isolation=True, host="127.0.0.1",
            port=4459, obs_root=str(obs), executable=str(obs / "bin/64bit/obs64.exe"),
            config_root=str(obs / "config/obs-studio"), profile_name=name,
            collection_name=name, max_output_bytes=MAX_BYTES)
        self.args = SimpleNamespace(obs_root=obs, profile=self.root / "profile.json",
            output_root=self.root / "record", receipt=self.root / "receipt.json",
            deadline_utc=(self.now + timedelta(hours=1)).isoformat(), seconds=15,
            port=4459, max_output_bytes=MAX_BYTES)
        self.admission = dict(status="ADMITTED", review_at_utc=self.review.isoformat(),
            approved_output_roots=[str(self.root)])
        # A regression that reaches external custody must fail before access.
        for target in ("subprocess.Popen", "ctypes.WinDLL"):
            patcher = mock.patch.object(capture.subprocess if target.startswith("subprocess")
                else capture.ctypes, target.split(".")[1], create=True,
                side_effect=AssertionError("external custody forbidden"))
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(capture, "_control", side_effect=AssertionError("OBS control forbidden"))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_valid_job_boundaries_preserve_input(self):
        for seconds in (1, 1200):
            for cap in (MIN_BYTES, MAX_BYTES):
                job = {**self.job, "duration_seconds": seconds, "max_output_bytes": cap}
                before = dict(job)
                self.assertIsNone(capture.validate_job(job))
                self.assertEqual(job, before)

    def test_job_rejects_wrong_identity_types_and_scope(self):
        changes = [{"schema": "xar.ck3.obs-window-capture.v1"}, {"capture_mode": "legacy"},
            {"capture_mode": "game_decision"}, {"overlay": {}}, {"desktop_id": "other-desktop"},
            {"decision_text_file": "other-text"}, {"game_creation_filetime": 123}, {"pid": True},
            {"pid": 0}, {"hwnd": False}, {"hwnd": -1}, {"session_id": "caller-label"},
            {"receipt_root": str(self.root / "record-sibling/session")},
            {"duration_seconds": True}, {"duration_seconds": 1.0},
            {"duration_seconds": 0}, {"duration_seconds": 1201},
            {"max_output_bytes": True}, {"max_output_bytes": MIN_BYTES - 1},
            {"max_output_bytes": MAX_BYTES + 1}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                capture.validate_job({**self.job, **change})

    def test_profile_identity_and_port_are_closed(self):
        self.assertIsNone(capture.validate_profile(dict(self.profile)))
        changes = [{"schema": "xar.ck3.obs-window-capture.v1"}, {"strict_isolation": 1},
            {"host": "localhost"}, {"port": True}, {"port": 1023}, {"port": 65536},
            {"executable": str(self.root / "personal/obs64.exe")},
            {"config_root": str(self.root / "personal/config")},
            {"profile_name": "ManagedWindowCapture-not-a-uuid"},
            {"collection_name": "ManagedWindowCapture-other"},
            {"max_output_bytes": MIN_BYTES - 1}, {"max_output_bytes": MAX_BYTES + 1}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                capture.validate_profile({**self.profile, **change})
        for port in (1024, 65535):
            self.assertIsNone(capture.validate_profile({**self.profile, "port": port}))

    def test_listener_identity_uses_only_supplied_mock_rows(self):
        for rows in ([], [SimpleNamespace(pid=9)], [SimpleNamespace(pid=1), SimpleNamespace(pid=9)],
                     [SimpleNamespace(pid=None)]):
            with self.subTest(rows=rows), mock.patch.object(capture, "_listeners", return_value=rows) as listen:
                with self.assertRaises(RuntimeError):
                    capture._port_owner(4459, 1)
                listen.assert_called_once_with(4459)
        with mock.patch.object(capture, "_listeners", return_value=[SimpleNamespace(pid=1)]):
            self.assertIsNone(capture._port_owner(4459, 1))

    def test_admission_review_and_deadline_boundaries(self):
        self.assertIsNone(recording.validate_admission(self.args, self.admission))
        boundary = self.review - timedelta(minutes=15)
        self.args.deadline_utc = boundary.isoformat()
        self.assertIsNone(recording.validate_admission(self.args, self.admission))
        for deadline in (boundary + timedelta(microseconds=1), self.now - timedelta(seconds=1)):
            self.args.deadline_utc = deadline.isoformat()
            with self.subTest(deadline=deadline), self.assertRaises(ValueError):
                recording.validate_admission(self.args, self.admission)
        self.args.deadline_utc = (self.now + timedelta(hours=1)).replace(tzinfo=None).isoformat()
        with self.assertRaises(ValueError):
            recording.validate_admission(self.args, self.admission)
        self.args.deadline_utc = (self.now + timedelta(hours=1)).isoformat()
        for change in ({"status": "GREEN"}, {"review_at_utc": self.review.replace(tzinfo=None).isoformat()},
                       {"review_at_utc": (self.now - timedelta(seconds=1)).isoformat()}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                recording.validate_admission(self.args, {**self.admission, **change})

    def test_admission_paths_ports_and_finite_budget(self):
        for key in ("obs_root", "profile", "output_root", "receipt"):
            args = SimpleNamespace(**vars(self.args))
            setattr(args, key, self.root.parent / (self.root.name + "-outside") / key)
            with self.subTest(key=key), self.assertRaises(ValueError):
                recording.validate_admission(args, self.admission)
        for key, values in (("port", (True, 1023, 65536)),
                ("seconds", (True, 1.0, 0, 1201)),
                ("max_output_bytes", (True, MIN_BYTES - 1, MAX_BYTES + 1))):
            for value in values:
                args = SimpleNamespace(**vars(self.args))
                setattr(args, key, value)
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    recording.validate_admission(args, self.admission)


if __name__ == "__main__":
    unittest.main()
