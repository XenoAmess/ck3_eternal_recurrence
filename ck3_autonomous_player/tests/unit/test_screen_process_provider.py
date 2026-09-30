from __future__ import annotations

from contextlib import contextmanager
import importlib
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer import runtime
from xar_autoplayer.errors import AgentError


class ScreenProcessProviderTests(unittest.TestCase):
    def test_real_injector_gate_and_fresh_resume_gate(self) -> None:
        # Exercise the real evidence writer/validator and resume path. No child
        # process is created: only the immutable contained Job result is supplied.
        from test_native_bridge_runtime import NativeBridgeInjectorTests
        config = runtime.NativeBridgeLaunchConfig(
            mode="native-headless", pipe_name=r"\\.\pipe\test",
            dll_path=Path("C:/native/bridge.dll"),
            injector_path=Path("C:/native/injector.exe"))
        argv = [str(config.injector_path), "4123", str(config.dll_path)]
        for refusal in (None, 1, 2):
            with self.subTest(refusal=refusal), tempfile.TemporaryDirectory() as td:
                events = []
                held = False
                sequence = 0

                @contextmanager
                def gate():
                    nonlocal held, sequence
                    sequence += 1
                    events.append(f"gate{sequence}")
                    if refusal == sequence:
                        raise AgentError("owner changed")
                    held = True
                    try:
                        yield
                    finally:
                        held = False

                def inject(*args, **kwargs):
                    self.assertTrue(held)
                    events.append("inject")
                    return NativeBridgeInjectorTests.outcome(argv)

                def resume():
                    self.assertTrue(held)
                    events.append("resume")

                process = SimpleNamespace(pid=4123, resume=mock.Mock(side_effect=resume))
                evidence = Path(td) / "attempt"
                with mock.patch.object(runtime, "sha256_file", return_value="a" * 64), mock.patch.object(
                    runtime, "run_contained_injector_command", side_effect=inject
                ) as spawn:
                    if refusal is None:
                        runtime._resume_with_native_bridge(process, config,
                            before_process_create=gate, injector_evidence_dir=evidence)
                    else:
                        with self.assertRaisesRegex(AgentError, "owner changed"):
                            runtime._resume_with_native_bridge(process, config,
                                before_process_create=gate, injector_evidence_dir=evidence)
                if refusal == 1:
                    spawn.assert_not_called()
                    self.assertFalse(evidence.exists())
                else:
                    self.assertEqual((evidence / "stdout.bin").read_bytes(), b"PASS\r\n")
                    self.assertTrue((evidence / "job-report.json").is_file())
                if refusal is None:
                    self.assertEqual(events, ["gate1", "inject", "gate2", "resume"])
                    process.resume.assert_called_once_with()
                else:
                    process.resume.assert_not_called()

    def test_provider_checks_real_callbacks_and_job_backend(self) -> None:
        runtime.require_screen_process_provider()
        with mock.patch.object(runtime, "run_contained_injector_command", None):
            with self.assertRaisesRegex(AgentError, "provider is unavailable"):
                runtime.require_screen_process_provider()
        session_module = importlib.import_module("xar_autoplayer.native_session")
        with mock.patch.object(session_module, "native_session", lambda: None):
            with self.assertRaisesRegex(AgentError, "warmup gates are unavailable"):
                runtime.require_screen_process_provider()


class ReadinessDiagnosticHookTests(unittest.TestCase):
    def test_progress_stall_keeps_timeout_type_without_semantic_read(self) -> None:
        from xar_autoplayer import native_auto_run
        capabilities = {"diagnostics": {"status": "cold-load"}}
        driver = SimpleNamespace(capabilities=mock.Mock(return_value=capabilities))
        probe = mock.Mock(return_value="shader progress stalled")
        with mock.patch.object(native_auto_run, "_runner_semantic_snapshot") as snapshot:
            with self.assertRaisesRegex(
                native_auto_run.NativeReadinessTimeoutError, "shader progress stalled"
            ) as failure:
                native_auto_run._wait_for_readiness(driver, session_done=threading.Event(),
                    session_state={}, timeout_seconds=10, stable_seconds=0,
                    poll_interval_seconds=0.01, cold_start_checkpoint=True,
                    allow_terminal=False, progress_stall_probe=probe)
        probe.assert_called_once_with(capabilities)
        snapshot.assert_not_called()
        self.assertIsNotNone(failure.exception.readiness_diagnostics)


if __name__ == "__main__":
    unittest.main()
