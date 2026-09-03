#!/usr/bin/env python3
"""Focused contract tests for the phase-two media environment preflight."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


TOOLS = Path(__file__).resolve().parent
REPOSITORY_ROOT = TOOLS.parents[1]
if str(REPOSITORY_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT / "tools"))
from promo_toolchain_loader import ensure_promo_toolchain  # noqa: E402

ensure_promo_toolchain()
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import preflight_phase2_media as media_preflight  # noqa: E402


class Phase2MediaPreflightTests(unittest.TestCase):
    def test_external_command_is_shell_free_and_timeout_bounded(self) -> None:
        completed = subprocess.CompletedProcess(["tool"], 0, "ok\n", "")
        runner = mock.Mock(return_value=completed)
        actual = media_preflight._run(
            ("tool", "--probe"),
            action="probe",
            timeout=17.0,
            runner=runner,
        )
        self.assertIs(actual, completed)
        runner.assert_called_once()
        call = runner.call_args
        self.assertEqual(call.args[0], ["tool", "--probe"])
        self.assertFalse(call.kwargs["shell"])
        self.assertEqual(call.kwargs["timeout"], 17.0)

    def test_source_checkout_must_equal_clean_origin_main(self) -> None:
        source = Path("C:/promo/src")
        responses = iter(
            (
                subprocess.CompletedProcess([], 0, "a" * 40 + "\n", ""),
                subprocess.CompletedProcess([], 0, "b" * 40 + "\n", ""),
            )
        )

        def runner(*_args, **_kwargs):
            return next(responses)

        with mock.patch.object(media_preflight, "PACKAGE_SOURCE", source):
            with self.assertRaisesRegex(
                media_preflight.MediaPreflightError, "HEAD is not local origin/main"
            ):
                media_preflight._toolchain_source_main(runner=runner)

    def test_source_checkout_probes_bind_safe_directory_to_exact_checkout(self) -> None:
        source = Path("C:/promo/src")
        calls: list[list[str]] = []
        responses = iter(
            (
                subprocess.CompletedProcess([], 0, "a" * 40 + "\n", ""),
                subprocess.CompletedProcess([], 0, "a" * 40 + "\n", ""),
                subprocess.CompletedProcess([], 0, "\n", ""),
            )
        )

        def runner(*args, **_kwargs):
            calls.append(list(args[0]))
            return next(responses)

        with mock.patch.object(media_preflight, "PACKAGE_SOURCE", source):
            identity = media_preflight._toolchain_source_main(runner=runner)

        safe_root = str(source.parent.resolve())
        self.assertEqual(identity["head"], "a" * 40)
        self.assertEqual(identity["origin_main"], "a" * 40)
        self.assertTrue(identity["clean"])
        self.assertEqual(len(calls), 3)
        for command in calls:
            self.assertEqual(
                command[:5],
                ["git", "-c", f"safe.directory={safe_root}", "-C", safe_root],
            )

    def test_receipt_is_exclusive_and_keeps_honest_scope(self) -> None:
        payload = {
            "schema_version": 1,
            "kind": "zhongguo-361-phase2-media-environment-preflight",
            "result": "GREEN",
            "scope": "environment-only; no CK3 capture, narration, candidate, review, or release claim",
        }
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "preflight.json"
            media_preflight._write_new(output, payload)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), payload)
            with self.assertRaisesRegex(
                media_preflight.MediaPreflightError, "refusing to overwrite"
            ):
                media_preflight._write_new(output, payload)

    def test_main_does_not_write_a_receipt_when_preflight_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "preflight.json"
            with mock.patch.object(
                media_preflight,
                "run_preflight",
                side_effect=media_preflight.MediaPreflightError("synthetic RED"),
            ):
                self.assertEqual(media_preflight.main(("--output", os.fspath(output))), 2)
            self.assertFalse(output.exists())

    def test_planned_path_check_does_not_create_target(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "future" / "candidate-work"
            report = media_preflight._planned_path(target)
            self.assertTrue(report["ready"])
            self.assertFalse(report["target_exists"])
            self.assertFalse(report["path_created"])
            self.assertFalse(report["write_probe_performed"])
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
