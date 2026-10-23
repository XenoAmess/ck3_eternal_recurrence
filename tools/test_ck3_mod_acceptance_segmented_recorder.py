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
from typing import Literal
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
REAL_SPEC_FROM_FILE_LOCATION = importlib.util.spec_from_file_location
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
        # The owner sets TEMP/TMP before this process imports tempfile.
        temporary = TemporaryDirectory(prefix="segmented-unit-")
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

    def config(self, version: object = 2, **changes: object) -> dict[str, object]:
        value: dict[str, object] = {"schema": "ck3-mod-acceptance-recording-config-v" + str(version),
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

    def _assert_terminal_mark_is_immutable(
        self, *, version: int = 2, terminal_operation: Literal["finish", "abort"] = "finish",
        probe_returncode: int = 0, check_input_contract: bool = False,
    ) -> None:
        # Exercise the real service, recorder lock and mailbox response writer.
        # Only process/desktop/probe leaves remain the authored unit fixtures.
        self.probe_returncode = probe_returncode
        config_path = self.work / "terminal-mark-config.json"
        config_path.write_text(json.dumps(self.config(version=version)), encoding="utf-8")
        service = RECORDER.ScreenCaptureService(
            keeper=self.keeper, keeper_root=self.keeper_root, repo=self.repo,
            config_path=config_path, config_sha256=RECORDER.file_identity(config_path)["sha256"],
            task_id="synthetic-screen-task")
        self.services.append(service)
        request = {"schema": "ck3-mod-acceptance-recorder-request-v1", "id": "active",
                   "live_root": str(self.live)}
        service.handle({**request, "operation": "start", "capture_name": "sealed-take"})
        native = self.live / "native-mark.json"
        native.write_text('{"synthetic_unit_fixture":true}\n', encoding="utf-8")
        active = service.handle({**request, "operation": "mark", "label": "before-terminal",
                                 "native_receipt": str(native)})
        self.assertEqual(active["native_receipt"], RECORDER.file_identity(native))
        self.assertEqual(json.loads(json.dumps(active)), active)
        marks = service.recorder.output / "marks.jsonl"
        rows = [json.loads(line) for line in marks.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([row["name"] for row in rows], ["recorder-start", "before-terminal"])
        self.assertIsNone(rows[0]["native_receipt"])
        if check_input_contract:
            active_bytes = marks.read_bytes()
            for invalid_name in (True, 1, 1.0, None, ""):
                with self.subTest(invalid_name=invalid_name), self.assertRaises(ValueError):
                    service.recorder.mark(invalid_name, native)
            invalid_receipts: tuple[object, ...] = (True, 1, 1.0, {})
            for invalid_receipt in invalid_receipts:
                with self.subTest(invalid_receipt=invalid_receipt), self.assertRaises(ValueError):
                    service.recorder.mark("invalid-receipt", invalid_receipt)
            self.assertEqual(marks.read_bytes(), active_bytes)
        service.handle({**request, "operation": terminal_operation})
        terminal_name = "recorder-final.json" if terminal_operation == "finish" else "recorder-abort.json"
        terminal = service.recorder.output / terminal_name
        raw = service.recorder.output / "raw-gameplay.mkv"
        immutable = {marks: marks.read_bytes(), terminal: terminal.read_bytes(), raw: raw.read_bytes()}
        if terminal_operation == "finish":
            self.assertEqual(json.loads(immutable[terminal])["marks"], RECORDER.file_identity(marks))
        # Actual queue consumption must report rejection, never a successful ACK.
        service.requests.mkdir()
        service.responses.mkdir()
        late_request = {**request, "id": "late", "operation": "mark", "label": "late-mailbox",
                        "native_receipt": str(native)}
        request_path = service.requests / "late.json"
        RECORDER.write(request_path, late_request)
        with patch.object(service.done, "wait", side_effect=(False, True)):
            service._run()
        response = json.loads((service.responses / request_path.name).read_text(encoding="utf-8"))
        self.assertEqual(response["request"], RECORDER.file_identity(request_path))
        self.assertEqual(response["status"], "RED_PRESERVED")
        self.assertIn("terminal recording take", response["error"])
        self.assertNotIn("result", response)
        self.assertIsNone(service.error)
        self.assertEqual({path: path.read_bytes() for path in immutable}, immutable)
        with self.assertRaisesRegex(ValueError, "terminal recording take"):
            service.recorder.mark("late-direct", native)
        self.assertEqual({path: path.read_bytes() for path in immutable}, immutable)

    def test_finished_take_rejects_mark_without_mutating_final_or_marks(self) -> None:
        self._assert_terminal_mark_is_immutable()

    def test_aborted_take_rejects_mark_without_mutating_abort_or_marks(self) -> None:
        self._assert_terminal_mark_is_immutable(terminal_operation="abort")

    def test_failed_probe_terminal_rejects_mark_without_mutating_final_or_marks(self) -> None:
        self._assert_terminal_mark_is_immutable(probe_returncode=7)

    def test_v1_terminal_rejects_mark_without_mutating_final_or_marks(self) -> None:
        self._assert_terminal_mark_is_immutable(version=1)

    def test_active_mark_contract_rejects_wrong_types_without_append(self) -> None:
        self._assert_terminal_mark_is_immutable(check_input_contract=True)

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

    def test_explicit_two_gib_scene_accepts_and_enforces_actual_whole_boundary(self) -> None:
        self.storage_document["this_write_peak_bytes"] = 2048 * MiB
        self.storage.write_text(json.dumps(self.storage_document), encoding="utf-8")
        service = self.service()
        self.assertEqual(service.scene_peak, 2048 * MiB)
        self.assertEqual(service.raw_peak, 512 * MiB)
        self.assertEqual(service.config["max_takes"], 4)
        self.assertEqual(service.config["total_seconds"], 300)
        self.assertIsNone(service.thread)
        self.assertIsNone(service.recorder)
        # Real public service comparison, synthetic numerical filesystem leaves.
        # No video, process or multi-GiB file is created.
        def at_boundary(path: Path) -> int:
            return 1920 * MiB if Path(path).resolve() == self.work.resolve() else 0
        with patch.object(RECORDER, "_tree_bytes", side_effect=at_boundary):
            observed = service._segment_limits(reserve=128 * MiB)
        self.assertEqual(observed["scene_tree_logical_bytes"], 1920 * MiB)
        def beyond_boundary(path: Path) -> int:
            return 1920 * MiB + 1 if Path(path).resolve() == self.work.resolve() else 0
        with patch.object(RECORDER, "_tree_bytes", side_effect=beyond_boundary):
            with self.assertRaisesRegex(ValueError, "aggregate scene ceiling"):
                service._segment_limits(reserve=128 * MiB)
        self.assertEqual(self.spawned, [])
        self.assertEqual(service.report()["capture_names_consumed"], [])

    def test_scene_parent_above_two_gib_is_rejected_before_any_process(self) -> None:
        self.storage_document["this_write_peak_bytes"] = 2048 * MiB + 1
        self.storage.write_text(json.dumps(self.storage_document), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "scene and raw ceilings"):
            self.service()
        self.assertEqual(self.spawned, [])
        self.assertFalse(self.capture_root.exists())

    def full_admission(self, **changes: object) -> None:
        # The exact R45 G43 scene/raw numbers; paths and process leaves remain
        # this portable authored fixture, not claimed live machine evidence.
        self.storage_document.update(
            machine_id=MACHINE, approved_root=str(self.work),
            schema="faith-e02-v7-shared-full-scene-capture-admission-v1",
            active=True, capacity_passed=True, this_write_peak_bytes=2815242240,
            hard_allocated_upper_bytes=2815242240,
            manual_consumption_cap_bytes=2815242240, raw_subcap_bytes=64 * MiB)
        self.storage_document.update(changes)
        self.storage.write_text(json.dumps(self.storage_document), encoding="utf-8")

    def test_g43_admitted_scene_and_two_takes_construct_and_enforce_original_hard_cap(self) -> None:
        self.full_admission()
        config = self.config(max_seconds=25, peak_bytes=32 * MiB, max_takes=2,
                             total_seconds=50, total_raw_bytes=64 * MiB)
        service = self.service(json.loads(json.dumps(config)))
        self.assertEqual(service.scene_peak, 2815242240)
        self.assertEqual(service.raw_peak, 64 * MiB)
        self.assertEqual(service.config["max_takes"], 2)
        self.assertIsNone(service.thread)
        self.assertIsNone(service.recorder)
        def at_boundary(path: Path) -> int:
            return 2815242240 - 32 * MiB if path.resolve() == self.work.resolve() else 0
        with patch.object(RECORDER, "_tree_bytes", side_effect=at_boundary):
            service._segment_limits(reserve=32 * MiB)
        def beyond_boundary(path: Path) -> int:
            return at_boundary(path) + (1 if path.resolve() == self.work.resolve() else 0)
        with patch.object(RECORDER, "_tree_bytes", side_effect=beyond_boundary):
            with self.assertRaisesRegex(ValueError, "aggregate scene ceiling"):
                service._segment_limits(reserve=32 * MiB)
        self.assertEqual(self.spawned, [])
        self.assertFalse(self.capture_root.exists())

    def test_historical_full_admission_without_manual_cap_remains_compatible(self) -> None:
        self.full_admission(this_write_peak_bytes=1024 * MiB,
                            hard_allocated_upper_bytes=1024 * MiB)
        del self.storage_document["manual_consumption_cap_bytes"]
        self.storage_document["raw_subcap_bytes"] = 512 * MiB
        self.storage.write_text(json.dumps(self.storage_document), encoding="utf-8")
        self.assertEqual(self.service().scene_peak, 1024 * MiB)

    def test_full_admission_rejects_wrong_types_identity_and_unadmitted_bounds(self) -> None:
        invalid: list[dict[str, object]] = [
            {"hard_allocated_upper_bytes": value} for value in (True, 2815242240.0, None, 2815242239)]
        invalid += [{"this_write_peak_bytes": value} for value in (True, 2815242240.0)]
        invalid += [{"raw_subcap_bytes": value} for value in (True, float(64 * MiB), 513 * MiB, 63 * MiB)]
        invalid += [{"manual_consumption_cap_bytes": value} for value in (True, 2815242240.0, 2815242239)]
        invalid += [{"machine_id": "another-machine"}, {"active": False}, {"capacity_passed": None}]
        config = self.config(max_seconds=25, peak_bytes=32 * MiB, max_takes=2,
                             total_seconds=50, total_raw_bytes=64 * MiB)
        for changes in invalid:
            with self.subTest(changes=changes):
                self.full_admission(**changes)
                with self.assertRaises(ValueError):
                    self.service({**config, "storage_reservation": RECORDER.file_identity(self.storage)})
        self.full_admission()
        del self.storage_document["hard_allocated_upper_bytes"]
        self.storage.write_text(json.dumps(self.storage_document), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.service({**config, "storage_reservation": RECORDER.file_identity(self.storage)})
        self.full_admission()
        for destination in (self.work, self.work.parent / "outside-admitted-scene"):
            with self.subTest(destination=destination):
                with self.assertRaises(ValueError):
                    self.service({**config, "capture_root": str(destination),
                                  "storage_reservation": RECORDER.file_identity(self.storage)})
        self.assertEqual(self.spawned, [])

    def test_actual_public_preflight_consumes_the_same_recorder_configuration(self) -> None:
        # setUp substitutes only the encoder's dynamic loader. The real public
        # entry must still be loaded by the original importlib implementation.
        with patch.object(importlib.util, "spec_from_file_location", REAL_SPEC_FROM_FILE_LOCATION):
            from test_ck3_mod_acceptance import SharedEntryTests
        entry_fixture = SharedEntryTests("test_three_products_select_one_host_source_and_native")
        entry_fixture.setUp()
        self.addCleanup(entry_fixture.doCleanups)
        self.full_admission()
        config = self.config(max_seconds=25, peak_bytes=32 * MiB, max_takes=2,
                             total_seconds=50, total_raw_bytes=64 * MiB)
        config_path = self.work / "public-recorder.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        selected_service = self.repo / "tools/ck3_mod_acceptance_recorder.py"
        selected_service.parent.mkdir()
        selected_service.write_bytes(Path(RECORDER.__file__).read_bytes())
        entry_fixture.runtime["repo_root"] = str(self.repo)
        entry_fixture.runtime["machine_id"] = MACHINE
        entry_fixture.runtime["allocation"] = {"recording": {
            "config": RECORDER.file_identity(config_path),
            "service": RECORDER.file_identity(selected_service)}}
        entry_fixture.write(entry_fixture.runtime_path, entry_fixture.runtime)
        selected = entry_fixture.select()
        self.assertEqual(selected.preflight()["blockers"], [])
        for machine in ("different-selected-runtime", None, True):
            with self.subTest(machine=machine):
                entry_fixture.runtime["machine_id"] = machine
                entry_fixture.write(entry_fixture.runtime_path, entry_fixture.runtime)
                errors = entry_fixture.select().preflight()["blockers"]
                self.assertTrue(any("Shared recording configuration" in error for error in errors), errors)
        del entry_fixture.runtime["machine_id"]
        entry_fixture.write(entry_fixture.runtime_path, entry_fixture.runtime)
        self.assertTrue(any("Shared recording configuration" in error
                            for error in entry_fixture.select().preflight()["blockers"]))
        entry_fixture.runtime["machine_id"] = MACHINE
        # A current exact config pin cannot hide an internally rejected raw cap.
        config["total_raw_bytes"] = 65 * MiB
        config_path.write_text(json.dumps(config), encoding="utf-8")
        attachment = entry_fixture.runtime["allocation"]["recording"]
        attachment["config"] = RECORDER.file_identity(config_path)
        entry_fixture.write(entry_fixture.runtime_path, entry_fixture.runtime)
        blockers = entry_fixture.select().preflight()["blockers"]
        self.assertTrue(any("Shared recording configuration" in error for error in blockers), blockers)
        self.assertEqual(self.spawned, [])
        self.assertFalse(self.capture_root.exists())

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
