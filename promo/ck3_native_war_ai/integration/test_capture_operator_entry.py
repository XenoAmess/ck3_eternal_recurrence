"""Exercise the capture/600s recorder wiring without launching any process."""
from __future__ import annotations

import argparse
import asyncio
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
import importlib
import json
from pathlib import Path
import sys
import tempfile
import threading
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
INTEGRATION = Path(__file__).resolve().parent
EPISODE = INTEGRATION.parent / "episode-02-battle-second-half"
sys.path[:0] = [str(INTEGRATION), str(EPISODE),
                str(ROOT / "ck3_autonomous_player" / "src"), str(ROOT / "tools")]
capture = importlib.import_module("capture_session")
bounded = importlib.import_module("record_bounded_gameplay")
jobs = importlib.import_module("recorder_job")
runtime = importlib.import_module("xar_autoplayer.runtime")
native = importlib.import_module("xar_autoplayer.native_session")
environment = importlib.import_module("xar_autoplayer.environment")
live_ids = importlib.import_module("ck3_live_run_id")
for _module in (capture, bounded, jobs, runtime, native, environment, live_ids):
    if not Path(_module.__file__).resolve().is_relative_to(ROOT):
        raise RuntimeError(f"test must import this checkout: {_module.__file__}")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


class FakeKeeper:
    def __init__(self, events: list[str], **kwargs):
        self.events = events
        self.abort = kwargs.get("abort", threading.Event())
        self.on_abort = kwargs.get("on_abort")
        self.failure = None
        self.gate_depth = 0

    def start(self):
        self.events.append("keeper-start")

    def refresh(self):
        self.require_live()

    def require_live(self):
        if self.failure is not None:
            raise RuntimeError(self.failure)

    @contextmanager
    def process_create_gate(self):
        self.require_live()
        self.gate_depth += 1
        self.events.append("gate-enter")
        try:
            yield
        finally:
            self.events.append("gate-exit")
            self.gate_depth -= 1

    def lose(self, *, report_failure=True):
        self.failure = "synthetic lease loss" if report_failure else None
        self.abort.set()
        self.events.append("lease-abort")
        self.on_abort()

    def stop(self):
        self.events.append("keeper-stop")

    def report(self):
        return {"failure": self.failure}


class FakeThread:
    """Model a completed observer without creating its desktop/MCP worker."""
    ident = None

    def __init__(self, **kwargs):
        self.target = kwargs["target"]

    def start(self):
        cells = dict(zip(self.target.__code__.co_freevars,
                         (cell.cell_contents for cell in self.target.__closure__)))
        cells["worker"]["ok"] = True

    def is_alive(self):
        return False


class FakeJob:
    def __init__(self, case, events, streams, *, natural_on_poll=None, red=False):
        self.case, self.events, self.streams = case, events, streams
        self.natural_on_poll, self.red = natural_on_poll, red
        self.poll_count = 0
        self.abort_unproven = False
        self.pid = 4242
        self.returncode = None

    def poll(self):
        self.poll_count += 1
        if self.natural_on_poll is not None and self.poll_count >= self.natural_on_poll:
            if self.returncode is None:
                self.events.append("natural-exit")
            self.returncode = 0
        return self.returncode

    def _open_stdio(self):
        for stream in self.streams:
            self.case.assertFalse(stream.closed, "stdio closed before Job cleanup")

    def finish(self, *, receipt, unsafe_marker, timeout=30):
        self._open_stdio()
        self.case.assertEqual(self.returncode, 0, "finish called before natural exit")
        self.events.append("finish")
        row = {"state": "RED_UNPROVEN" if self.red == "unproven" else
                        "RED_TREE_EMPTY" if self.red else "NORMAL_TREE_EMPTY",
               "job_active_processes": 1 if self.red == "unproven" else 0}
        bounded.write_new(receipt, row)
        if self.red:
            if not unsafe_marker.exists():
                write_json(unsafe_marker, {"reason": "synthetic descendant cleanup failure"})
        return row

    def abort(self, *, receipt, unsafe_marker):
        self._open_stdio()
        self.events.append("abort")
        if not self.abort_unproven:
            self.returncode = 1
        if not unsafe_marker.exists():
            write_json(unsafe_marker, {"reason": "synthetic abort; remains RED"})
        row = {"state": "RED_UNPROVEN" if self.abort_unproven else "ABORT_TREE_EMPTY",
               "job_active_processes": 1 if self.abort_unproven else 0}
        bounded.write_new(receipt, row)
        if self.abort_unproven:
            raise RuntimeError("recorder descendant cleanup is unproven")
        return row


class CaptureOperatorEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="capture-entry-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.output = self.base / "ck3-output"
        self.output.mkdir()
        self.workdir = self.base / "raw600"
        self.profile = self.base / "profile"
        self.profile.mkdir()
        self.events = []
        self.keepers = []
        self.managers = []
        self.fake_jobs = []
        self.source_save = self.base / "fixture.ck3"
        self.source_save.write_bytes(b"synthetic checkpoint, not a playable save")
        self.source_receipt = self.base / "source.json"
        write_json(self.source_receipt, {"fixture": True})
        self.screenshot = self.base / "offline.fixture"
        self.screenshot.write_bytes(b"synthetic receipt pixels, not desktop evidence")
        self.offline = self.base / "offline.json"
        write_json(self.offline, {
            "current_offline_ui_observed": True,
            "screenshot": capture.identity(self.screenshot),
            "observed_at": datetime.now(timezone.utc).isoformat(),
        })
        self.ffmpeg = self.base / "ffmpeg.fixture"
        self.ffprobe = self.base / "ffprobe.fixture"
        self.ffmpeg.write_bytes(b"not executable: mocked FFmpeg")
        self.ffprobe.write_bytes(b"not executable: mocked FFprobe")
        self.checkpoint = {"save": bounded.digest(self.source_save),
                           "receipt": bounded.digest(self.source_receipt)}
        write_json(self.output / "preflight.json", {
            "result": "READY_FOR_BOUNDED_LIVE_ATTEMPT", "checkpoint_source": self.checkpoint,
        })
        write_json(self.output / "native-start-readback.json", {
            "postcondition_verified": True, "source_checkpoint": self.checkpoint,
        })
        self.args = argparse.Namespace(
            workdir=self.workdir, track="fixture", seconds=600,
            session_output=self.output, source_save=self.source_save,
            source_receipt=self.source_receipt, steam_offline_receipt=self.offline,
            ffmpeg=str(self.ffmpeg), ffprobe=str(self.ffprobe), output_dir=self.output,
            checkpoint_save=self.source_save, checkpoint_receipt=self.source_receipt,
            battle_control_pair_manifest=None, bridge_dll=self.base / "bridge.fixture",
            bridge_injector=self.base / "injector.fixture", gui_scale="1.0",
            state_dir=self.base / "state", pipe_name="mock-only",
            screen_cli_sha256="A" * 64, screen_task_id="mock-only",
            frontend_timeout=1, hold_seconds=0, recovery_seconds=0,
            interactive_seconds=0, record_debug_desktop=False, native_session_invoked=False,
        )
        # Any accidental process launcher fails this suite immediately.
        self.launch = self.enterContext(mock.patch("subprocess.Popen", side_effect=
            AssertionError("test attempted a real subprocess")))
        self.process_run = self.enterContext(mock.patch("subprocess.run", side_effect=
            AssertionError("test attempted a real subprocess")))

    def keeper_factory(self, **kwargs):
        keeper = FakeKeeper(self.events, **kwargs)
        self.keepers.append(keeper)
        return keeper

    def spawn_factory(self, keeper, *, natural_on_poll=None, red=False):
        def spawn(command, **kwargs):
            self.assertGreater(keeper.gate_depth, 0, "spawn outside the CAS lease gate")
            self.assertEqual(command[command.index("-t") + 1], "600")
            self.assertEqual(kwargs["stdin"], bounded.subprocess.DEVNULL)
            streams = [kwargs["stdout"], kwargs["stderr"]]
            self.assertTrue(all(not stream.closed for stream in streams))
            self.events.append("spawn")
            write_json(kwargs["start_receipt"], {"state": "STARTED"})
            Path(command[-1]).write_bytes(b"synthetic raw, not a video")
            job = FakeJob(self, self.events, streams,
                          natural_on_poll=natural_on_poll, red=red)
            self.fake_jobs.append(job)
            return job
        return spawn

    def geometry(self):
        return {"valid_and_equal": True, "gdi_width": 800, "gdi_height": 600,
                "pyautogui_width": 800, "pyautogui_height": 600}

    def cli_context(self, keeper, *, natural_on_poll=1, red=False):
        stack = ExitStack()
        manager = bounded.ManagedGameplayRecorder(self.output, keeper,
                                                  steam_offline_receipt=self.offline)
        stack.enter_context(mock.patch.object(bounded.shutil, "which", side_effect=lambda value: value))
        stack.enter_context(mock.patch.object(bounded, "desktop_primary_size", side_effect=self.geometry))
        stack.enter_context(mock.patch.object(bounded.time, "sleep"))
        stack.enter_context(mock.patch.object(jobs, "spawn", side_effect=
            self.spawn_factory(keeper, natural_on_poll=natural_on_poll, red=red)))
        stack.enter_context(mock.patch.object(bounded, "managed_request", side_effect=
            lambda output, request, timeout: manager.handle(request)))
        return stack, manager

    def prepare_intent(self):
        # Let the real CLI generate its exact frozen intent before capture starts.
        with mock.patch.object(bounded.shutil, "which", side_effect=lambda value: value), \
                mock.patch.object(bounded, "desktop_primary_size", side_effect=self.geometry), \
                mock.patch.object(bounded.time, "sleep"), \
                mock.patch.object(bounded, "managed_request", side_effect=[
                    {"state": "RECORDING"}, {"state": "NORMAL_TREE_EMPTY"}]), \
                mock.patch.object(bounded, "probe", return_value=0):
            self.assertEqual(bounded.run(self.args), 0)

    def service(self, manager, operations):
        directory = self.output / "interactive-requests"
        original_write = capture.write_new

        def write_with_requests(path, value):
            if path.suffix == ".pending":
                self.assertFalse(path.with_suffix("").exists())
                self.events.append("response-pending")
            original_write(path, value)
            if path.name == "service.json":
                for index, operation in enumerate(operations):
                    original_write(directory / f"{index:02}.json", {
                        "action": "gameplay_recorder", "operation": operation,
                        "workdir": str(self.workdir),
                    })
                original_write(directory / "99.json", {"action": "finish"})

        call = mock.AsyncMock(side_effect=AssertionError("gameplay request dispatched to MCP"))
        with mock.patch.object(capture, "write_new", side_effect=write_with_requests):
            asyncio.run(capture.service_requests(directory, call=call,
                stopped=self.keepers[-1].abort, seconds=1, state_reader=lambda: {"fixture": True},
                gameplay_recorder_call=manager.handle))
        call.assert_not_called()
        response = json.loads((self.output / "interactive-requests-responses" / "00.json").read_text())
        self.assertEqual(response["result"], "CALL_COMPLETED")
        self.assertEqual(response["body"]["state"], "RECORDING")
        self.assertEqual(response["request"], capture.identity(directory / "00.json"))
        self.assertIn("response-pending", self.events)
        self.assertFalse(list((self.output / "interactive-requests-responses").glob("*.pending")))

    def capture_context(self, native_hook):
        stack = ExitStack()
        stack.enter_context(mock.patch.object(runtime, "require_screen_process_provider"))
        stack.enter_context(mock.patch.object(live_ids, "allocate_live_run_id",
                                              return_value=SimpleNamespace(run_id="mock-only")))
        stack.enter_context(mock.patch.object(live_ids, "write_identity_receipt"))
        stack.enter_context(mock.patch.object(live_ids, "record_live_run_status"))
        stack.enter_context(mock.patch.object(capture, "checkpoint_source", return_value=self.checkpoint))
        stack.enter_context(mock.patch.object(capture, "validate_a04_ui_gui_source_binding", return_value=None))
        stack.enter_context(mock.patch.object(capture, "validate_d11_battle_control_pair", return_value=None))
        stack.enter_context(mock.patch.object(capture, "prepare_profile",
            return_value=(SimpleNamespace(profile_dir=self.profile), None)))
        stack.enter_context(mock.patch.object(capture, "require_gui_scale_disk_gate"))
        stack.enter_context(mock.patch.object(capture, "reseed_gui_scale_after_warmup",
                                              side_effect=lambda *a, **kw: self.events.append("settings-gate")))
        stack.enter_context(mock.patch.object(capture, "ScreenLeaseKeeper", side_effect=self.keeper_factory))
        stack.enter_context(mock.patch.object(capture.threading, "Thread", FakeThread))
        stack.enter_context(mock.patch.object(environment, "ck3_process_inventory", return_value={"processes": []}))
        original_manager = bounded.ManagedGameplayRecorder

        def manager_factory(*args, **kwargs):
            manager = original_manager(*args, **kwargs)
            original_close = manager.close

            def close():
                self.events.append("managed-close")
                original_close()

            manager.close = close
            self.managers.append(manager)
            return manager

        stack.enter_context(mock.patch.object(bounded, "ManagedGameplayRecorder", side_effect=manager_factory))

        def native_session(spec, **kwargs):
            keeper = self.keepers[-1]
            self.assertEqual(kwargs["before_process_create"], keeper.process_create_gate)
            self.assertIs(kwargs["stop_event"], keeper.abort)
            kwargs["frontend_first_before_final_launch"](spec)
            with kwargs["before_process_create"]():
                self.events.append("native-spawn")
            native_hook(keeper, self.managers[-1])
            self.events.append("native-tree-empty")
            return {"ok": True, "shutdown": {"cleanup_proven": True}}

        stack.enter_context(mock.patch.object(native, "native_session", side_effect=native_session))
        return stack

    def invoke_capture(self):
        return capture.capture(self.args, {"checkpoint_source": self.checkpoint,
            "launch_mode": "mock-only"}, {"sequence": 1})

    def test_missing_provider_stops_capture_before_any_spawn_or_run_id(self):
        missing = ModuleType("xar_autoplayer.runtime")
        with mock.patch.dict(sys.modules, {"xar_autoplayer.runtime": missing}), \
                mock.patch.object(capture, "spawn_recorder") as debug_spawn, \
                mock.patch.object(jobs, "spawn") as bounded_spawn, \
                mock.patch.object(capture, "ScreenLeaseKeeper") as keeper, \
                mock.patch.object(native, "native_session") as session, \
                mock.patch.object(live_ids, "allocate_live_run_id") as allocate:
            with self.assertRaises(ImportError):
                self.invoke_capture()
            for operation in (debug_spawn, bounded_spawn, keeper, session, allocate,
                              self.launch, self.process_run):
                operation.assert_not_called()
        self.assertFalse(self.args.native_session_invoked)

    def test_capture_binds_one_keeper_and_hot_dispatch_then_closes_before_keeper(self):
        self.prepare_intent()

        def hook(keeper, manager):
            with mock.patch.object(jobs, "spawn", side_effect=self.spawn_factory(keeper, natural_on_poll=1)):
                self.service(manager, ["start", "status"])

        with self.capture_context(hook):
            result = self.invoke_capture()
        self.assertTrue(self.args.native_session_invoked)
        self.assertEqual(len(self.keepers), 1)
        self.assertEqual(self.managers[0].terminal["state"], "NORMAL_TREE_EMPTY")
        self.assertLess(self.events.index("native-tree-empty"), self.events.index("managed-close"))
        self.assertLess(self.events.index("managed-close"), self.events.index("keeper-stop"))
        self.assertIn("settings-gate", self.events)
        self.assertEqual(result["result"], "ENVIRONMENT_SESSION_COMPLETE_WITH_UNREVIEWED_GAMEPLAY")
        self.assertEqual(result["classification"], "managed-gameplay-raw-pending-human-review")
        self.assertFalse(result["human_1x_review_performed"])

    def test_capture_keeper_abort_stops_owned_raw_and_preserves_red(self):
        self.prepare_intent()

        def hook(keeper, manager):
            with mock.patch.object(jobs, "spawn", side_effect=self.spawn_factory(keeper)):
                self.service(manager, ["start"])
                # Keep other completion predicates valid: owned raw abort must
                # independently prevent a synthetic successful session result.
                keeper.lose(report_failure=False)

        with self.capture_context(hook):
            result = self.invoke_capture()
        self.assertEqual(result["result"], "RED")
        self.assertTrue(self.keepers[0].abort.is_set())
        self.assertEqual(self.managers[0].terminal["state"], "ABORT_TREE_EMPTY")
        self.assertTrue((self.workdir / "unsafe-recorder-cleanup.json").is_file())
        end = json.loads((self.workdir / "recorder-end.json").read_text())
        self.assertTrue(end["interrupted"])
        self.assertLess(self.events.index("abort"), self.events.index("keeper-stop"))
        self.assertTrue(all(stream.closed for stream in self.fake_jobs[0].streams))

    def test_second_stdio_open_failure_closes_first_stream_without_spawn(self):
        self.prepare_intent()
        keeper = FakeKeeper(self.events)
        manager = bounded.ManagedGameplayRecorder(self.output, keeper,
                                                  steam_offline_receipt=self.offline)
        original_open = Path.open
        streams = []

        def open_with_failure(path, *args, **kwargs):
            if path.name == "ffmpeg.stderr.txt" and args and args[0] == "xb":
                raise OSError("synthetic second stdio open failure")
            stream = original_open(path, *args, **kwargs)
            if path.name == "ffmpeg.stdout.bin" and args and args[0] == "xb":
                streams.append(stream)
            return stream

        with mock.patch.object(Path, "open", autospec=True, side_effect=open_with_failure), \
                mock.patch.object(jobs, "spawn") as spawn:
            with self.assertRaisesRegex(OSError, "second stdio"):
                manager.handle({"action": "gameplay_recorder", "operation": "start",
                                "workdir": str(self.workdir)})
            spawn.assert_not_called()
        self.assertEqual(len(streams), 1)
        self.assertTrue(streams[0].closed)
        self.assertEqual(manager.streams, [])

    def test_unproven_tree_retains_stdio_until_distinct_abort_retry_proves_empty(self):
        self.prepare_intent()
        keeper = FakeKeeper(self.events)
        manager = bounded.ManagedGameplayRecorder(self.output, keeper,
                                                  steam_offline_receipt=self.offline)
        self.addCleanup(manager._close_streams)
        request = {"action": "gameplay_recorder", "operation": "start",
                   "workdir": str(self.workdir)}
        with mock.patch.object(jobs, "spawn", side_effect=
                self.spawn_factory(keeper, natural_on_poll=1, red="unproven")):
            manager.handle(request)
            job = self.fake_jobs[-1]
            job.abort_unproven = True
            with self.assertRaisesRegex(RuntimeError, "cleanup is unproven"):
                manager.handle({**request, "operation": "status"})
        self.assertIsNone(manager.terminal)
        self.assertTrue(all(not stream.closed for stream in job.streams))
        terminal = self.workdir / "recorder-job-terminal.json"
        before = bounded.digest(terminal)
        self.assertEqual(json.loads(terminal.read_text())["state"], "RED_UNPROVEN")
        self.assertFalse((self.workdir / "recorder-end.json").exists())
        job.abort_unproven = False
        manager.close()
        self.assertEqual(bounded.digest(terminal), before)
        self.assertEqual(manager.terminal["state"], "ABORT_TREE_EMPTY")
        self.assertEqual(len(list(self.workdir.glob("recorder-job-abort-*.json"))), 2)
        self.assertTrue(all(stream.closed for stream in job.streams))
        self.assertTrue(manager.report()["unsafe_marker_present"])
        end = json.loads((self.workdir / "recorder-end.json").read_text())
        self.assertTrue(end["interrupted"])

    def test_600s_cli_waits_for_natural_exit_and_normal_tree_before_probe(self):
        keeper = FakeKeeper(self.events)
        stack, manager = self.cli_context(keeper, natural_on_poll=2)

        def probe(workdir, ffprobe):
            self.events.append("probe")
            self.assertEqual(manager.terminal["state"], "NORMAL_TREE_EMPTY")
            self.assertTrue(all(stream.closed for stream in self.fake_jobs[0].streams))
            end = json.loads((workdir / "recorder-end.json").read_text())
            self.assertFalse(end["interrupted"])
            self.assertEqual(end["managed_job_state"], "NORMAL_TREE_EMPTY")
            self.assertFalse((workdir / "unsafe-recorder-cleanup.json").exists())
            return 0

        with stack, mock.patch.object(bounded, "probe", side_effect=probe) as probe_call:
            self.assertEqual(bounded.run(self.args), 0)
            probe_call.assert_called_once()
        self.assertLess(self.events.index("natural-exit"), self.events.index("finish"))
        self.assertLess(self.events.index("finish"), self.events.index("probe"))
        self.assertNotIn("abort", self.events)

    def test_red_finish_skips_probe_and_keeps_failure_and_unsafe_marker(self):
        keeper = FakeKeeper(self.events)
        stack, manager = self.cli_context(keeper, red=True)
        with stack, mock.patch.object(bounded, "probe") as probe_call:
            with self.assertRaisesRegex(RuntimeError, "not NORMAL_TREE_EMPTY"):
                bounded.run(self.args)
            probe_call.assert_not_called()
        self.assertNotIn("abort", self.events)
        self.assertTrue((self.workdir / "recorder-failure.json").is_file())
        self.assertTrue((self.workdir / "unsafe-recorder-cleanup.json").is_file())
        self.assertEqual(manager.terminal["state"], "RED_TREE_EMPTY")
        terminal = json.loads((self.workdir / "recorder-job-terminal.json").read_text())
        self.assertEqual(terminal["state"], "RED_TREE_EMPTY")
        self.assertTrue(all(stream.closed for stream in self.fake_jobs[0].streams))

    def test_start_receipt_failure_aborts_job_before_closing_stdio(self):
        keeper = FakeKeeper(self.events)
        stack, manager = self.cli_context(keeper, natural_on_poll=None)
        original_write = bounded.write_new

        def failed_start_receipt(path, value):
            if path.name == "recorder-start.json":
                raise OSError("synthetic start receipt write failure")
            original_write(path, value)

        with stack, mock.patch.object(bounded, "write_new", side_effect=failed_start_receipt), \
                mock.patch.object(bounded, "probe") as probe_call:
            with self.assertRaisesRegex(OSError, "start receipt"):
                bounded.run(self.args)
            probe_call.assert_not_called()
        self.assertEqual(manager.terminal["state"], "ABORT_TREE_EMPTY")
        self.assertLess(self.events.index("spawn"), self.events.index("abort"))
        self.assertNotIn("finish", self.events)
        self.assertTrue(all(stream.closed for stream in self.fake_jobs[0].streams))
        self.assertTrue((self.workdir / "recorder-failure.json").is_file())
        self.assertTrue((self.workdir / "unsafe-recorder-cleanup.json").is_file())

    def test_legacy_end_write_failure_is_red_and_never_reaches_probe(self):
        keeper = FakeKeeper(self.events)
        stack, manager = self.cli_context(keeper)
        original_write = bounded.write_new

        def failed_end_receipt(path, value):
            if path.name == "recorder-end.json":
                raise OSError("synthetic legacy end write failure")
            original_write(path, value)

        with stack, mock.patch.object(bounded, "write_new", side_effect=failed_end_receipt), \
                mock.patch.object(bounded, "probe") as probe_call:
            with self.assertRaisesRegex(OSError, "legacy end"):
                bounded.run(self.args)
            probe_call.assert_not_called()
        self.assertEqual(manager.report()["state"], "RED_METADATA")
        self.assertTrue(manager.report()["unsafe_marker_present"])
        self.assertEqual(manager.terminal["job_active_processes"], 0)
        self.assertTrue(all(stream.closed for stream in self.fake_jobs[0].streams))
        self.assertFalse((self.workdir / "recorder-end.json").exists())
        terminal = json.loads((self.workdir / "recorder-job-terminal.json").read_text())
        self.assertEqual(terminal["state"], "NORMAL_TREE_EMPTY")
        self.assertTrue((self.workdir / "recorder-failure.json").is_file())

    def test_terminal_receipt_write_failure_close_retries_abort_before_releasing_stdio(self):
        self.prepare_intent()
        keeper = FakeKeeper(self.events)
        manager = bounded.ManagedGameplayRecorder(self.output, keeper,
                                                  steam_offline_receipt=self.offline)
        self.addCleanup(manager._close_streams)
        with mock.patch.object(jobs, "spawn", side_effect=
                self.spawn_factory(keeper, natural_on_poll=1)):
            manager.handle({"action": "gameplay_recorder", "operation": "start",
                            "workdir": str(self.workdir)})
        job = self.fake_jobs[-1]
        original_write, original_abort = bounded.write_new, job.abort
        abort_calls = 0

        def failed_terminal_receipt(path, value):
            if path.name == "recorder-job-terminal.json":
                raise OSError("synthetic terminal receipt write failure")
            original_write(path, value)

        def abort_then_retry(**kwargs):
            nonlocal abort_calls
            abort_calls += 1
            job.abort_unproven = abort_calls == 1
            return original_abort(**kwargs)

        with mock.patch.object(bounded, "write_new", side_effect=failed_terminal_receipt), \
                mock.patch.object(job, "abort", side_effect=abort_then_retry):
            with self.assertRaisesRegex(RuntimeError, "cleanup is unproven"):
                manager.close()
        self.assertEqual(abort_calls, 2)
        self.assertEqual(self.events.count("finish"), 1)
        self.assertEqual(manager.report()["state"], "ABORT_TREE_EMPTY")
        self.assertTrue(manager.report()["unsafe_marker_present"])
        self.assertTrue(all(stream.closed for stream in job.streams))
        self.assertFalse((self.workdir / "recorder-job-terminal.json").exists())
        receipts = sorted(self.workdir.glob("recorder-job-abort-*.json"))
        self.assertEqual(len(receipts), 2)
        self.assertEqual({json.loads(path.read_text())["state"] for path in receipts},
                         {"RED_UNPROVEN", "ABORT_TREE_EMPTY"})
        self.assertTrue(json.loads((self.workdir / "recorder-end.json").read_text())["interrupted"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
