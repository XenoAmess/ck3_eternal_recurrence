"""Bounded no-screen tests for recording custody, once-only dispatch and CLI wiring."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from ck3_mod_acceptance_recorder import ScreenCaptureService, file_identity
from ck3_mod_acceptance_allocate import keeper_command


class FakeKeeper:
    def __init__(self): self.abort = threading.Event()
    def require_live(self):
        if self.abort.is_set(): raise RuntimeError("fixture keeper aborted")


class FakeRecorder:
    starts = 0
    def __init__(self, **kwargs): self.terminal, self.kwargs, self.output = None, kwargs, Path(kwargs['output'])
    def start(self):
        type(self).starts += 1
        self.output.mkdir()
        return {"state": "FIXTURE_RECORDING_NO_SCREEN"}
    def status(self): return self.terminal or {"state": "FIXTURE_RECORDING_NO_SCREEN"}
    def mark(self, name, receipt): return {"name": name, "receipt": str(receipt)}
    def finish(self):
        self.terminal = {"state": "FIXTURE_FINISHED_NO_SCREEN", "job": {"job_active_processes": 0}}
        return self.terminal
    def abort(self):
        self.terminal = self.terminal or {"state": "FIXTURE_ABORTED_NO_SCREEN", "job": {"job_active_processes": 0}}
        return self.terminal


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="faith-recorder-unit-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo, self.keeper_root = self.root / "repo", self.root / "keeper"
        self.keeper_root.mkdir()
        job = self.repo / "promo/ck3_native_war_ai/integration/recorder_job.py"
        job.parent.mkdir(parents=True); job.write_text("# fixture; never executed\n", encoding="utf-8")
        encoder = self.root / "fixture-tool.bin"; encoder.write_bytes(b"not executable; no process starts")
        storage = self.root / "reservation.json"; storage.write_text(json.dumps({"machine_id": "unit-fixture-not-an-actual-machine", "reservations": [{"task": "episode01-capture", "peak_bytes": 8*1024**3}]}))
        config = {"schema": "ck3-mod-acceptance-recording-config-v1", "machine_id": "unit-fixture-not-an-actual-machine",
                  "capture_root": str(self.root / "captures"), "ffmpeg": file_identity(encoder), "ffprobe": file_identity(encoder),
                  "recorder_job": file_identity(job), "storage_reservation": file_identity(storage),
                  "reservation_task": "episode01-capture",
                  "max_seconds": 120, "peak_bytes": 512 * 1024**2, "required_size": [2560,1440]}
        self.config = self.root / "configuration.json"
        self.config.write_text(json.dumps(config), encoding="utf-8")
        self.keeper = FakeKeeper()
        self.service = ScreenCaptureService(keeper=self.keeper, keeper_root=self.keeper_root, repo=self.repo,
            config_path=self.config, config_sha256=file_identity(self.config)["sha256"], task_id="unit-fixture",
            recorder_factory=FakeRecorder)
        self.service._live = lambda live: (self.root, {})
        FakeRecorder.starts = 0

    def request(self, operation, **options):
        return {"schema": "ck3-mod-acceptance-recorder-request-v1", "id": operation,
                "operation": operation, "live_root": str(self.root), **options}

    def test_one_keeper_and_sequential_takes_require_empty_job(self):
        self.assertIs(self.service.keeper, self.keeper)
        self.service.handle(self.request("start", capture_name="raw01"))
        self.assertIs(self.service.recorder.kwargs["keeper"], self.keeper)
        with self.assertRaisesRegex(ValueError, "never overlap or replay"):
            self.service.handle(self.request("start", capture_name="raw02"))
        self.assertEqual(FakeRecorder.starts, 1)
        self.service.handle(self.request("finish"))
        self.service.handle(self.request("start", capture_name="raw02"))
        self.assertEqual(FakeRecorder.starts, 2)
        self.service.handle(self.request("finish"))
        with self.assertRaisesRegex(ValueError, "unconsumed capture directory"):
            self.service.handle(self.request("start", capture_name="raw01"))
        self.service.handle(self.request("start", capture_name="raw03"))
        self.assertEqual(self.service.handle(self.request("abort"))["state"], "FIXTURE_ABORTED_NO_SCREEN")
        self.service.handle(self.request("start", capture_name="raw04"))
        self.assertEqual(FakeRecorder.starts, 4)
        self.assertIs(self.service.recorder.kwargs["keeper"], self.keeper)

    def test_request_thread_consumes_a_file_once_then_stops(self):
        self.service.start()
        path = self.service.requests / "one.json"
        path.write_text(json.dumps(self.request("start", capture_name="raw01")), encoding="utf-8")
        deadline = time.monotonic() + 3
        while not (self.service.responses / path.name).exists() and time.monotonic() < deadline:
            time.sleep(.05)
        self.assertTrue((self.service.responses / path.name).is_file())
        time.sleep(.4)
        self.service.stop()
        self.assertEqual(FakeRecorder.starts, 1)
        self.assertTrue(self.service.report()["thread_exited"])
        self.assertEqual(self.service.seen, {"one.json"})

    def test_no_recording_argv_and_optional_exact_pins(self):
        keeper = ROOT / "tools/ck3_mod_acceptance_keeper.py"
        ordinary = keeper_command(Path(sys.executable), keeper, ROOT, self.keeper_root, "fixture", 1, self.root / "bus", "a"*64)
        self.assertNotIn("--recorder-config", ordinary)
        configured = keeper_command(Path(sys.executable), keeper, ROOT, self.keeper_root, "fixture", 1, self.root / "bus", "a"*64,
                                    recording={"config": {"path": str(self.config), "sha256": "b"*64}, "service": {"sha256": "c"*64}})
        self.assertEqual(configured[-6:], ["--recorder-config", str(self.config), "--recorder-config-sha256", "b"*64, "--recorder-service-sha256", "c"*64])

    def test_unproven_job_and_cumulative_reservation_block_new_take(self):
        self.service.handle(self.request("start", capture_name="raw01"))
        self.service.recorder.terminal = {"state": "FIXTURE_UNPROVEN", "job": {"job_active_processes": 1}}
        with self.assertRaisesRegex(ValueError, "never overlap or replay"):
            self.service.handle(self.request("start", capture_name="raw02"))
        self.service.recorder.terminal = {"state": "FIXTURE_FINISHED_NO_SCREEN", "job": {"job_active_processes": 0}}
        self.service.config['peak_bytes'] = 9 * 1024**3
        with self.assertRaisesRegex(ValueError, "root capture reservation"):
            self.service.handle(self.request("start", capture_name="raw02"))


if __name__ == "__main__":
    unittest.main()
