"""Public service checks with synthetic process and desktop leaves only.

No game, FFmpeg, WinDLL, screen capture, or large file is started/created.
These authored unit fixtures do not qualify a native runtime or a clean span.
"""
from contextlib import ExitStack, contextmanager
import ctypes
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "segmented_recorder_public_under_test", HERE / "ck3_mod_acceptance_recorder.py")
RECORDER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RECORDER
SPEC.loader.exec_module(RECORDER)
MiB = 1024 ** 2
MACHINE = "synthetic-segmented-unit-machine"


class SyntheticJob:
    """RecorderJob leaf: explicit original wait and tree query observations."""
    def __init__(self, owner, pid):
        self.owner, self.pid = owner, pid
        self.returncode = None
        self.finish_calls = self.abort_calls = 0
        self.active = 0

    def poll(self):
        return self.returncode

    def _terminal(self, state, code, receipt):
        self.returncode = code
        row = {"schema": "synthetic-recorder-job-unit-v1", "state": state,
               "pid": self.pid, "returncode": code,
               "job_active_processes": self.active, "error": None,
               "original_wait_observed": True, "synthetic_unit_fixture": True}
        RECORDER.write(receipt, row)
        self.owner.original_job_terminals.append(row)
        return row

    def finish(self, *, receipt, unsafe_marker):
        self.finish_calls += 1
        return self._terminal("NORMAL_TREE_EMPTY", 0, receipt)

    def abort(self, *, receipt, unsafe_marker):
        self.abort_calls += 1
        return self._terminal("ABORT_TREE_EMPTY", 1, receipt)


class SyntheticLoader:
    def __init__(self, owner):
        self.owner = owner

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        module.spawn = self.owner.spawn_job


class SegmentedRecorderPublicService(unittest.TestCase):
    def setUp(self):
        # Source-candidate runs keep all scratch in their allocated lane.
        temporary = TemporaryDirectory(prefix="segmented-unit-", dir=HERE.parent)
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.repo, self.live = self.work / "repo", self.work / "live"
        self.keeper_root, self.capture_root = self.work / "keeper", self.work / "captures"
        self.job_source = self.repo / "promo/ck3_native_war_ai/integration/recorder_job.py"
        self.job_source.parent.mkdir(parents=True)
        self.job_source.write_text("# Synthetic source pin; loader supplies process leaf.\n", encoding="utf-8")
        self.live.mkdir(); self.keeper_root.mkdir()
        (self.live / "launch-intent.json").write_text("{}\n", encoding="utf-8")
        self.ffmpeg, self.ffprobe = self.work / "ffmpeg.exe", self.work / "ffprobe.exe"
        self.ffmpeg.write_bytes(b"synthetic ffmpeg identity\n")
        self.ffprobe.write_bytes(b"synthetic ffprobe identity\n")
        self.storage = self.work / "storage.json"
        self.storage_document = {"machine_id": MACHINE, "approved_root": str(self.work),
            "this_write_peak_bytes": 896 * MiB, "raw_subcap_bytes": 512 * MiB,
            "reservations": [{"task": "synthetic-capture", "peak_bytes": 896 * MiB}]}
        self.storage.write_text(json.dumps(self.storage_document), encoding="utf-8")
        self.services, self.jobs, self.spawned, self.original_job_terminals = [], [], [], []
        self.live_checks = self.gate_entries = self.lease_checks = 0
        self.probe_duration, self.probe_returncode, self.spawn_error = "20.0", 0, None
        self.keeper = SimpleNamespace(process_create_gate=self.process_gate,
                                      require_live=self.require_live)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.addCleanup(self.close_streams)
        self.stack.enter_context(patch.object(RECORDER.subprocess, "Popen",
            side_effect=AssertionError("No real child process allowed")))
        self.stack.enter_context(patch.object(ctypes, "WinDLL", create=True,
            side_effect=AssertionError("No real WinDLL allowed")))
        self.stack.enter_context(patch.object(ctypes, "windll", create=True,
            new=SimpleNamespace(user32=SimpleNamespace(GetSystemMetrics=lambda index: (2560, 1440)[index]))))
        self.stack.enter_context(patch.dict(sys.modules, {"pyautogui": SimpleNamespace(size=lambda: (2560, 1440))}))
        self.stack.enter_context(patch.object(RECORDER.subprocess, "check_output", return_value=MACHINE + "\n"))
        self.stack.enter_context(patch.object(RECORDER.subprocess, "run", side_effect=self.probe))
        self.stack.enter_context(patch.object(RECORDER, "require_no_legacy_blue_overlay", return_value={
            "legacy_blue_overlay_retired": True, "synthetic_unit_fixture": True}))
        self.stack.enter_context(patch.object(RECORDER.importlib.util, "spec_from_file_location",
                                              side_effect=self.job_spec))
        self.stack.enter_context(patch.object(RECORDER.ScreenCaptureService, "_live", autospec=True,
            side_effect=lambda service, live: self.live_guard(service, live)))

    def close_streams(self):
        for service in self.services:
            if service.recorder is not None:
                service.recorder._close()

    @contextmanager
    def process_gate(self):
        self.gate_entries += 1
        yield

    def require_live(self):
        self.lease_checks += 1

    def live_guard(self, service, live):
        self.assertEqual(Path(live).resolve(), self.live.resolve())
        self.assertIs(service.keeper, self.keeper)
        self.live_checks += 1
        self.keeper.require_live()
        return self.live, {"synthetic_live_guard": True}

    def job_spec(self, name, path):
        self.assertEqual(Path(path).resolve(), self.job_source.resolve())
        return importlib.machinery.ModuleSpec(name, SyntheticLoader(self))

    def spawn_job(self, argv, *, stdout, stderr, unsafe_marker, start_receipt, failure_receipt):
        self.spawned.append(list(argv))
        if self.spawn_error is not None:
            RECORDER.write(failure_receipt, {"state": "RED_UNPROVEN", "job_active_processes": None,
                                           "synthetic_unit_fixture": True})
            raise self.spawn_error
        raw = Path(argv[-1])
        raw.write_bytes(b"synthetic encoded bytes; no actual video\n")
        job = SyntheticJob(self, 7000 + len(self.jobs))
        self.jobs.append(job)
        RECORDER.write(start_receipt, {"state": "SYNTHETIC_ASSIGNED", "pid": job.pid,
                                      "synthetic_unit_fixture": True})
        return job

    def probe(self, argv, **kwargs):
        self.assertEqual(Path(argv[0]).resolve(), self.ffprobe.resolve())
        self.assertEqual(argv[1:7], ["-v", "error", "-show_streams", "-show_format", "-of", "json"])
        stdout = json.dumps({"format": {"duration": self.probe_duration}}).encode("utf-8")
        return SimpleNamespace(returncode=self.probe_returncode, stdout=stdout, stderr=b"")

    def config(self, version=2, **changes):
        value = {"schema": "ck3-mod-acceptance-recording-config-v" + str(version),
                 "machine_id": MACHINE, "capture_root": str(self.capture_root),
                 "ffmpeg": RECORDER.file_identity(self.ffmpeg),
                 "ffprobe": RECORDER.file_identity(self.ffprobe),
                 "recorder_job": RECORDER.file_identity(self.job_source),
                 "storage_reservation": RECORDER.file_identity(self.storage),
                 "reservation_task": "synthetic-capture", "max_seconds": 75,
                 "peak_bytes": (128 if version == 2 else 512) * MiB,
                 "required_size": [2560, 1440]}
        if version == 2:
            value.update(max_takes=4, total_seconds=300, total_raw_bytes=512 * MiB)
        value.update(changes)
        return value

    def service(self, config=None):
        config = config if config is not None else self.config()
        path = self.work / ("config-" + str(len(self.services)) + ".json")
        path.write_text(json.dumps(config), encoding="utf-8")
        service = RECORDER.ScreenCaptureService(keeper=self.keeper, keeper_root=self.keeper_root,
            repo=self.repo, config_path=path, config_sha256=RECORDER.file_identity(path)["sha256"],
            task_id="synthetic-screen-task")
        self.services.append(service)
        return service

    def handle(self, service, operation, name=None, **fields):
        request = {"schema": "ck3-mod-acceptance-recorder-request-v1", "id": "synthetic-" + operation,
                   "operation": operation, "live_root": str(self.live)}
        if name is not None:
            request["capture_name"] = name
        request.update(fields)
        return service.handle(request)

    def argument(self, argv, name):
        return argv[argv.index(name) + 1]

    def test_v1_argv_and_512_mib_minimum_remain_compatible(self):
        service = self.service(self.config(version=1, max_seconds=120))
        self.handle(service, "start", "legacy-one")
        argv = self.spawned[-1]
        self.assertEqual(self.argument(argv, "-maxrate"), "18M")
        self.assertEqual(self.argument(argv, "-bufsize"), "36M")
        self.assertEqual(float(self.argument(argv, "-t")), 120)
        self.assertNotIn("-fs", argv)
        self.probe_duration = "19.75"
        terminal = self.handle(service, "finish")
        self.assertEqual(terminal["job"], self.original_job_terminals[-1])
        self.assertEqual(self.jobs[-1].finish_calls, 1)
        self.assertEqual(terminal["result"], "ENCODED_UNREVIEWED")
        with self.assertRaises(ValueError):
            RECORDER.BoundedScreenRecorder(root=self.repo, output=self.capture_root / "too-small",
                keeper=self.keeper, ffmpeg=self.ffmpeg, ffprobe=self.ffprobe, machine_id=MACHINE,
                admission_receipt=self.live / "launch-intent.json", peak_bytes=511 * MiB)

    def test_v2_argv_uses_decimal_byte_ceiling_and_exact_duration(self):
        service = self.service()
        self.handle(service, "start", "segmented-one")
        argv = self.spawned[-1]
        self.assertEqual(self.argument(argv, "-maxrate"), "8M")
        self.assertEqual(self.argument(argv, "-bufsize"), "16M")
        self.assertEqual(self.argument(argv, "-fs"), str(120 * MiB))
        self.assertEqual(float(self.argument(argv, "-t")), 75)
        self.probe_duration = "19.125"
        terminal = self.handle(service, "finish")
        self.assertEqual(terminal["duration_seconds"], 19.125)
        self.assertIs(terminal["duration_known"], True)
        self.assertEqual(terminal["duration_charge_seconds"], 19.125)
        self.assertIs(terminal["budget_qualified"], True)
        self.assertEqual(terminal["job"], self.original_job_terminals[-1])

    def test_four_sequential_takes_then_fifth_rejected_without_new_process(self):
        service = self.service()
        self.probe_duration = "50.0"
        for index in range(4):
            self.handle(service, "start", "take-" + str(index))
            terminal = self.handle(service, "finish")
            self.assertEqual(terminal["job"]["job_active_processes"], 0)
        with self.assertRaises(ValueError):
            self.handle(service, "start", "take-five")
        self.assertEqual(len(self.spawned), 4)
        self.assertFalse((self.capture_root / "take-five").exists())
        self.assertEqual(service.report()["capture_names_consumed"], ["take-0", "take-1", "take-2", "take-3"])
        self.assertEqual(self.gate_entries, 4)

    def test_active_previous_take_blocks_next_without_consuming_name(self):
        service = self.service()
        self.handle(service, "start", "active-one")
        with self.assertRaises(ValueError):
            self.handle(service, "start", "blocked-next")
        self.assertEqual(len(self.spawned), 1)
        self.assertNotIn("blocked-next", service.report()["capture_names_consumed"])
        self.assertFalse((self.capture_root / "blocked-next").exists())

    def test_unproven_previous_job_never_becomes_tree_empty(self):
        service = self.service()
        self.handle(service, "start", "unknown-tree")
        self.jobs[-1].active = None
        with self.assertRaises(RuntimeError):
            self.handle(service, "finish")
        with self.assertRaises(ValueError):
            self.handle(service, "start", "must-not-start")
        self.assertEqual(len(self.spawned), 1)
        self.assertIsNone(self.original_job_terminals[-1]["job_active_processes"])
        self.assertNotIn("must-not-start", service.report()["capture_names_consumed"])

    def test_request_fields_cannot_override_segmented_budget(self):
        service = self.service()
        for field in ("segmented", "seconds", "max_takes", "total_seconds", "total_raw_bytes", "peak_bytes"):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    self.handle(service, "start", "unconsumed", **{field: 1})
        self.assertEqual(self.spawned, [])
        self.assertEqual(service.report()["capture_names_consumed"], [])

    def test_segmented_config_rejects_unbounded_or_ambiguous_values(self):
        invalid = [("max_takes", 0), ("max_takes", 5), ("max_takes", True),
                   ("max_takes", 1.5), ("total_seconds", 9), ("total_seconds", 301),
                   ("total_seconds", float("nan")), ("max_seconds", 121),
                   ("max_seconds", 9), ("max_seconds", True),
                   ("total_raw_bytes", 513 * MiB), ("peak_bytes", 8 * MiB),
                   ("peak_bytes", 513 * MiB)]
        for field, value in invalid:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    self.service(self.config(**{field: value}))
        self.assertEqual(self.spawned, [])

    def test_actual_fractional_duration_floors_next_take_and_exhausts_remaining_time(self):
        service = self.service(self.config(total_seconds=100))
        self.handle(service, "start", "first-time")
        self.probe_duration = "70.5"
        first = self.handle(service, "finish")
        self.assertEqual(first["duration_charge_seconds"], 70.5)
        self.handle(service, "start", "remaining-time")
        self.assertEqual(float(self.argument(self.spawned[-1], "-t")), 29)
        self.probe_duration = "20.0"
        self.handle(service, "finish")
        self.assertEqual(service.report()["total_duration_charge_seconds"], 90.5)
        with self.assertRaises(ValueError):
            self.handle(service, "start", "less-than-ten-left")
        self.assertEqual(len(self.spawned), 2)
        self.assertNotIn("less-than-ten-left", service.report()["capture_names_consumed"])

    def test_nan_duration_is_unknown_and_charges_full_reserved_take(self):
        service = self.service(self.config(total_seconds=100))
        self.handle(service, "start", "unknown-duration")
        self.probe_duration = "NaN"
        terminal = self.handle(service, "finish")
        self.assertIsNone(terminal["duration_seconds"])
        self.assertIs(terminal["duration_known"], False)
        self.assertEqual(terminal["duration_charge_seconds"], 75)
        self.assertIs(terminal["budget_qualified"], False)
        self.assertEqual(terminal["job"], self.original_job_terminals[-1])
        self.assertEqual(service.report()["total_duration_charge_seconds"], 75)
        with self.assertRaises(ValueError):
            self.handle(service, "start", "cannot-follow-unknown")
        self.assertEqual(len(self.spawned), 1)
        self.assertIsNotNone(service.report()["segment_blocked"])

    def test_failed_spawn_consumes_durable_attempt_and_restart_cannot_replay(self):
        service = self.service()
        self.spawn_error = RuntimeError("synthetic spawn result unknown")
        with self.assertRaisesRegex(RuntimeError, "synthetic spawn result unknown"):
            self.handle(service, "start", "failed-consumed")
        report = service.report()
        self.assertEqual(report["capture_names_consumed"], ["failed-consumed"])
        self.assertEqual(len(report["take_ledger"]), 1)
        self.assertEqual(report["total_duration_charge_seconds"], 75)
        ledger = self.capture_root / "segmented-ledger.jsonl"
        rows = [json.loads(row) for row in ledger.read_text(encoding="utf-8").splitlines()]
        self.assertGreaterEqual(len(rows), 1)
        self.assertIn("failed-consumed", ledger.read_text(encoding="utf-8"))
        self.spawn_error = None
        with self.assertRaises(ValueError):
            self.handle(service, "start", "failed-consumed")
        with self.assertRaises(ValueError):
            self.handle(service, "start", "another-while-unknown")
        with self.assertRaises(ValueError):
            self.service(self.config())
        self.assertEqual(len(self.spawned), 1)

    def test_nonempty_capture_root_cannot_reset_durable_segmented_budget(self):
        self.capture_root.mkdir()
        (self.capture_root / "prior-small-evidence.json").write_text("{}\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.service()
        self.assertEqual(self.spawned, [])

    def test_scene_usage_plus_next_reservation_cannot_exceed_896_mib(self):
        service = self.service()
        # Numerical filesystem observation only; no large file is created.
        def observed(path):
            return 769 * MiB if Path(path).resolve() == self.work.resolve() else 0
        with patch.object(RECORDER, "_tree_bytes", side_effect=observed):
            with self.assertRaises(ValueError):
                self.handle(service, "start", "scene-too-full")
        self.assertEqual(self.spawned, [])
        self.assertEqual(service.report()["capture_names_consumed"], [])
        self.assertFalse((self.capture_root / "scene-too-full").exists())

    def test_failed_ffprobe_charges_reserved_time_and_preserves_original_job(self):
        service = self.service()
        self.handle(service, "start", "probe-failed")
        self.probe_returncode = 7
        terminal = self.handle(service, "finish")
        self.assertEqual(terminal["result"], "RED_PRESERVED")
        self.assertEqual(terminal["probe_exit_code"], 7)
        self.assertIsNone(terminal["duration_seconds"])
        self.assertIs(terminal["duration_known"], False)
        self.assertEqual(terminal["duration_charge_seconds"], 75)
        self.assertIs(terminal["budget_qualified"], False)
        self.assertEqual(terminal["job"], self.original_job_terminals[-1])
        self.assertEqual(terminal["job"]["returncode"], 0)
        self.assertEqual(self.jobs[-1].finish_calls, 1)

    def test_prior_capture_bytes_plus_next_take_cannot_exceed_512_mib(self):
        service = self.service()
        for index in range(3):
            self.handle(service, "start", "raw-prior-" + str(index))
            self.handle(service, "finish")
        real_tree_bytes = RECORDER._tree_bytes
        def observed(path):
            if Path(path).resolve() in {self.capture_root.resolve(), self.work.resolve()}:
                return 385 * MiB
            return real_tree_bytes(path)
        with patch.object(RECORDER, "_tree_bytes", side_effect=observed):
            with self.assertRaises(ValueError):
                self.handle(service, "start", "raw-total-would-be-513")
        self.assertEqual(len(self.spawned), 3)
        self.assertEqual(len(service.report()["take_ledger"]), 3)
        self.assertNotIn("raw-total-would-be-513", service.report()["capture_names_consumed"])

    def test_final_aggregate_overrun_is_red_and_preserves_original_finish_wait(self):
        service = self.service()
        self.handle(service, "start", "final-raw-overrun")
        real_tree_bytes = RECORDER._tree_bytes
        def observed(path):
            if self.jobs[-1].finish_calls:
                if Path(path).resolve() == self.capture_root.resolve():
                    return 513 * MiB
                if Path(path).resolve() == self.work.resolve():
                    return 600 * MiB
            return real_tree_bytes(path)
        with patch.object(RECORDER, "_tree_bytes", side_effect=observed):
            terminal = self.handle(service, "finish")
        self.assertEqual(terminal.get("result", terminal.get("state")), "RED_PRESERVED")
        self.assertIs(terminal["budget_qualified"], False)
        self.assertEqual(terminal["job"], self.original_job_terminals[-1])
        self.assertIs(terminal["job"]["original_wait_observed"], True)
        self.assertEqual(terminal["job"]["returncode"], 0)
        self.assertEqual(self.jobs[-1].finish_calls, 1)
        self.assertEqual(self.jobs[-1].abort_calls, 0)
        self.assertIsNotNone(service.report()["segment_blocked"])
        self.assertEqual(service.report()["take_ledger"][-1]["state"], "TERMINAL_UNPROVEN")

    def test_observed_duration_overrun_charges_actual_seconds_and_blocks_next_take(self):
        service = self.service()
        self.handle(service, "start", "duration-overrun")
        self.probe_duration = "76.5"
        terminal = self.handle(service, "finish")
        self.assertEqual(terminal["result"], "RED_PRESERVED")
        self.assertIs(terminal["duration_known"], True)
        self.assertEqual(terminal["duration_seconds"], 76.5)
        self.assertGreaterEqual(terminal["duration_charge_seconds"], 76.5)
        self.assertGreaterEqual(service.report()["total_duration_charge_seconds"], 76.5)
        self.assertEqual(terminal["job"], self.original_job_terminals[-1])
        with self.assertRaises(ValueError):
            self.handle(service, "start", "cannot-follow-duration-overrun")
        self.assertEqual(len(self.spawned), 1)

    def test_tree_usage_observer_sums_real_small_files_without_large_allocations(self):
        self.capture_root.mkdir()
        (self.capture_root / "small-a.bin").write_bytes(b"abc")
        child = self.capture_root / "child"
        child.mkdir()
        (child / "small-b.bin").write_bytes(b"12345")
        self.assertEqual(RECORDER._tree_bytes(self.capture_root), 8)


if __name__ == "__main__":
    unittest.main()
