"""No-process proof that native launch gates both helper and CK3 creation."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
from xar_autoplayer import runtime  # noqa: E402


class ProcessCreateGateTests(unittest.TestCase):
    def run_harmless(self, gate, calls: list[str]):
        with tempfile.TemporaryDirectory(prefix="video-runtime-gate-") as temporary:
            root = Path(temporary)
            spec = SimpleNamespace(state_dir=root / "state", game_exe=root / "game" / "ck3.exe")
            (spec.state_dir / "control").mkdir(parents=True)
            spec.game_exe.parent.mkdir()

            def watchdog(*unused):
                calls.append("watchdog-spawn")
                return 1001, "created"

            def ck3(*unused):
                calls.append("ck3-spawn")
                raise RuntimeError("synthetic process creation stop")

            with patch.object(runtime, "native_bridge_launch_config_from_environment", return_value=None), \
                 patch.object(runtime, "ck3_processes", return_value=[]), \
                 patch.object(runtime, "_ck3_launch_command", return_value=["fixture-ck3.exe"]), \
                 patch.object(runtime, "_clear_isolated_runtime_logs", return_value=(1, [])), \
                 patch.object(runtime, "_process_identity", return_value={
                     "name": "python.exe", "executable": sys.executable, "creation_date": "fixture"}), \
                 patch.object(runtime, "_start_process_watchdog", side_effect=watchdog), \
                 patch.object(runtime, "_create_kill_on_close_job", return_value=object()), \
                 patch.object(runtime, "_job_active_processes", return_value=0), \
                 patch.object(runtime, "_stop_authenticated_watchdog"), \
                 patch.object(runtime, "_close_job"), \
                 patch.object(runtime, "_create_suspended_process", side_effect=ck3):
                with self.assertRaises((RuntimeError, runtime.AgentError)):
                    runtime.launch(spec, verify_prepared_profile=False,
                                   before_process_create=gate)

    def test_gate_wraps_both_helper_and_ck3_spawn(self):
        calls = []

        @contextmanager
        def gate():
            calls.append("gate-enter")
            try:
                yield
            finally:
                calls.append("gate-exit")

        self.run_harmless(gate, calls)
        self.assertEqual(calls, ["gate-enter", "watchdog-spawn", "gate-exit",
                                 "gate-enter", "ck3-spawn", "gate-exit"])

    def test_first_gate_rejects_before_any_child(self):
        calls = []

        @contextmanager
        def gate():
            calls.append("gate-rejected")
            raise RuntimeError("lease lost")
            yield

        self.run_harmless(gate, calls)
        self.assertEqual(calls, ["gate-rejected"])

    def test_second_gate_rejects_ck3_and_cleans_helper(self):
        calls = []

        @contextmanager
        def gate():
            calls.append("gate-enter")
            if calls.count("gate-enter") == 2:
                raise RuntimeError("lease lost after watchdog")
            yield
            calls.append("gate-exit")

        self.run_harmless(gate, calls)
        self.assertEqual(calls, ["gate-enter", "watchdog-spawn", "gate-exit",
                                 "gate-enter"])


if __name__ == "__main__":
    unittest.main()
