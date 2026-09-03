#!/usr/bin/env python3
"""Focused contracts for the phase-two Default-desktop relay."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SOURCE = Path(__file__).resolve().parent
MODULE_PATH = SOURCE / "run_zg361_phase2_seed_capture_default_desktop.py"
SPEC = importlib.util.spec_from_file_location("phase2_default_desktop", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
relay = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = relay
SPEC.loader.exec_module(relay)


class DefaultDesktopRelayTest(unittest.TestCase):
    def test_preflight_is_no_launch_and_preserves_runner(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            tools = root / "tools"
            tools.mkdir()
            runner = tools / "run_zg361_phase2_seed_capture.py"
            runner.write_text("# exact runner\n", encoding="utf-8")
            python = root / "python.exe"
            python.write_bytes(b"python-fixture")
            payload = relay.preflight_payload(
                python,
                root,
                ("--", "--clean-source", "X:/freeze/source"),
                root / "stdout.log",
                root / "stderr.log",
            )
            self.assertEqual(payload["result"], "READY_TO_RUN")
            self.assertEqual(payload["target_desktop"], r"WinSta0\Default")
            self.assertFalse(payload["child_process_started"])
            self.assertFalse(payload["ck3_launch_attempted"])
            self.assertEqual(payload["command"][1], str(runner.resolve()))
            self.assertNotIn("skip", payload["legal_commerce_contract"].lower())
            self.assertIn("remain unauthorized", payload["legal_commerce_contract"])

    def test_main_defaults_to_preflight_without_executing_child(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            tools = root / "tools"
            tools.mkdir()
            (tools / "run_zg361_phase2_seed_capture.py").write_text(
                "# exact runner\n", encoding="utf-8"
            )
            python = root / "python.exe"
            python.write_bytes(b"python-fixture")
            result = root / "preflight.json"
            argv = [
                "--python",
                str(python),
                "--source-root",
                str(root),
                "--result",
                str(result),
                "--stdout-log",
                str(root / "stdout.log"),
                "--stderr-log",
                str(root / "stderr.log"),
                "--",
                "--clean-source",
                "X:/freeze/source",
            ]
            with mock.patch.object(
                relay,
                "execute_on_default_desktop",
                side_effect=AssertionError("preflight must not create a child"),
            ):
                self.assertEqual(relay.main(argv), 0)
            payload = json.loads(result.read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "no-launch-preflight")
            self.assertFalse(payload["ck3_launch_attempted"])

    def test_execute_flag_is_the_only_child_creation_path(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            tools = root / "tools"
            tools.mkdir()
            (tools / "run_zg361_phase2_seed_capture.py").write_text(
                "# exact runner\n", encoding="utf-8"
            )
            python = root / "python.exe"
            python.write_bytes(b"python-fixture")
            result = root / "execute.json"
            argv = [
                "--python",
                str(python),
                "--source-root",
                str(root),
                "--result",
                str(result),
                "--stdout-log",
                str(root / "stdout.log"),
                "--stderr-log",
                str(root / "stderr.log"),
                "--execute",
                "--",
                "--clean-source",
                "X:/freeze/source",
            ]
            with mock.patch.object(
                relay, "execute_on_default_desktop", return_value=(1234, 0)
            ) as execute:
                self.assertEqual(relay.main(argv), 0)
            execute.assert_called_once()
            payload = json.loads(result.read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "execute")
            self.assertTrue(payload["ck3_launch_attempted"])
            self.assertEqual(payload["child_pid"], 1234)


if __name__ == "__main__":
    unittest.main()
