#!/usr/bin/env python3
"""CK3-free contracts for the late-save recovery Default-desktop relay."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SOURCE = Path(__file__).resolve().parent
MODULE_PATH = (
    SOURCE / "recover_zg361_phase2_promotion_source_session_default_desktop.py"
)
SPEC = importlib.util.spec_from_file_location(
    "promotion_recovery_default_desktop", MODULE_PATH
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"could not load relay under test: {MODULE_PATH}")
relay = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = relay
SPEC.loader.exec_module(relay)

import default_desktop_process as desktop_process  # noqa: E402


class PromotionRecoveryDefaultDesktopRelayTest(unittest.TestCase):
    def _arrange(self, root: Path) -> tuple[Path, Path]:
        tools = root / "tools"
        tools.mkdir()
        recovery = tools / "recover_zg361_phase2_promotion_source_session.py"
        recovery.write_text("# exact recovery CLI\n", encoding="utf-8")
        python = root / "python.exe"
        python.write_bytes(b"python-fixture")
        return python, recovery

    @staticmethod
    def _argv(root: Path, python: Path, *extra: str) -> list[str]:
        return [
            "--python",
            str(python),
            "--source-root",
            str(root),
            "--result",
            str(root / "relay.json"),
            "--stdout-log",
            str(root / "stdout.log"),
            "--stderr-log",
            str(root / "stderr.log"),
            *extra,
            "--",
            "--source-save",
            "X:/late/autosave.ck3",
            "--startup-mode",
            "continue-last-save",
        ]

    def test_preflight_fixes_exact_recovery_child_and_reuses_win32_primitive(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            python, recovery = self._arrange(root)
            payload = relay.preflight_payload(
                python,
                root,
                (
                    "--",
                    "--source-save",
                    "X:/late/autosave.ck3",
                    "--startup-mode",
                    "continue-last-save",
                ),
                root / "stdout.log",
                root / "stderr.log",
            )

            self.assertEqual(payload["result"], "READY_TO_RUN")
            self.assertEqual(payload["target_desktop"], r"WinSta0\Default")
            self.assertFalse(payload["child_process_started"])
            self.assertFalse(payload["ck3_launch_attempted"])
            self.assertEqual(payload["command"][0], str(python.resolve()))
            self.assertEqual(payload["command"][1], str(recovery.resolve()))
            self.assertEqual(payload["recovery"]["path"], str(recovery.resolve()))
            self.assertEqual(payload["startup_mode"], "continue-last-save")
            self.assertIs(
                relay.execute_on_default_desktop,
                desktop_process.execute_on_default_desktop,
            )
            self.assertIn("fixed", payload["child_contract"])
            self.assertIn("remain unauthorized", payload["legal_commerce_contract"])

    def test_main_defaults_to_no_launch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            python, _recovery = self._arrange(root)
            with mock.patch.object(
                relay,
                "execute_on_default_desktop",
                side_effect=AssertionError("preflight must not create a child"),
            ):
                self.assertEqual(relay.main(self._argv(root, python)), 0)

            payload = json.loads((root / "relay.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "no-launch-preflight")
            self.assertFalse(payload["child_process_started"])
            self.assertFalse(payload["ck3_launch_attempted"])

    def test_execute_is_the_only_child_creation_path(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            python, recovery = self._arrange(root)
            with mock.patch.object(
                relay,
                "execute_on_default_desktop",
                return_value=(361247, 0),
            ) as execute:
                self.assertEqual(
                    relay.main(self._argv(root, python, "--execute")),
                    0,
                )

            execute.assert_called_once()
            command, working_directory, stdout_log, stderr_log = execute.call_args.args
            self.assertEqual(command[1], str(recovery.resolve()))
            self.assertEqual(working_directory, root)
            self.assertEqual(stdout_log, root / "stdout.log")
            self.assertEqual(stderr_log, root / "stderr.log")
            payload = json.loads((root / "relay.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "execute")
            self.assertTrue(payload["child_process_started"])
            self.assertTrue(payload["ck3_launch_attempted"])
            self.assertEqual(payload["child_pid"], 361247)

    def test_missing_recovery_arguments_fails_before_child_creation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            python, _recovery = self._arrange(root)
            argv = self._argv(root, python)[:-5]
            with mock.patch.object(
                relay,
                "execute_on_default_desktop",
                side_effect=AssertionError("invalid preflight must not create a child"),
            ) as execute:
                self.assertEqual(relay.main(argv), 2)
            execute.assert_not_called()
            payload = json.loads((root / "relay.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["result"], "RED")
            self.assertFalse(payload["child_process_started"])

    def test_bridge_frontend_first_mode_is_allowed_without_child_creation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            python, _recovery = self._arrange(root)
            argv = self._argv(root, python)
            argv[-1] = "bridge-frontend-first"
            with mock.patch.object(
                relay,
                "execute_on_default_desktop",
                side_effect=AssertionError("preflight must not create a child"),
            ) as execute:
                self.assertEqual(relay.main(argv), 0)
            execute.assert_not_called()
            payload = json.loads((root / "relay.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["result"], "READY_TO_RUN")
            self.assertEqual(payload["startup_mode"], "bridge-frontend-first")

    def test_invalid_warmup_pipe_fails_before_child_creation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            python, _recovery = self._arrange(root)
            argv = self._argv(root, python)
            argv[-1] = "bridge-frontend-first"
            argv[-2:-2] = [
                "--warmup-bridge-pipe",
                r"\\.\pipe\xar_ck3_bridge_zg361_w283w283w283w283w283w283w28328",
            ]
            with mock.patch.object(
                relay,
                "execute_on_default_desktop",
                side_effect=AssertionError("invalid pipe must not create a child"),
            ) as execute:
                self.assertEqual(relay.main(argv), 2)
            execute.assert_not_called()
            payload = json.loads((root / "relay.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["result"], "RED")
            self.assertIn("32 lowercase hex", payload["error"])

    def test_plain_frontend_first_mode_fails_before_child_creation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            python, _recovery = self._arrange(root)
            argv = self._argv(root, python)
            argv[-1] = "frontend-first"
            with mock.patch.object(
                relay,
                "execute_on_default_desktop",
                side_effect=AssertionError("wrong startup mode must not create a child"),
            ) as execute:
                self.assertEqual(relay.main(argv), 2)
            execute.assert_not_called()
            payload = json.loads((root / "relay.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["result"], "RED")
            self.assertIn("bridge-frontend-first", payload["error"])


if __name__ == "__main__":
    unittest.main()
