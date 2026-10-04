"""Offline tests for acceptance evidence and layer boundaries; no CK3 calls."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_acceptance as runner


class AcceptanceRunnerTests(unittest.TestCase):
    def make_game(self, root: Path) -> tuple[Path, Path]:
        game = root / "installation/game"
        game.mkdir(parents=True)
        executable = game.parent / "binaries/ck3.exe"
        executable.parent.mkdir()
        executable.write_bytes(b"offline fixture: never executable")
        settings = game.parent / "launcher/launcher-settings.json"
        settings.parent.mkdir()
        settings.write_text(json.dumps({"rawVersion": runner.EXACT_VERSION,
                                        "version": "1.20.0.3 (Crozier)",
                                        "exePath": "../binaries/ck3.exe"}), encoding="utf-8")
        return game, executable

    def make_evidence(self, root: Path, version: str = runner.EXACT_VERSION) -> Path:
        response = root / "tools-response.json"
        response.write_text(json.dumps({"result": {"tools": [{"name": name} for name in runner.REQUIRED_BRIDGE_TOOLS]}}), encoding="utf-8")
        evidence = root / "evidence.json"
        evidence.write_text(json.dumps({"endpoint": "offline-test-not-contacted", "observed_at": runner.utc_now(),
                                        "game_version": version, "ck3_exe_sha256": runner.EXACT_EXE_SHA256,
                                        "tools_response_path": response.name,
                                        "tools_response_sha256": runner.digest(response)}), encoding="utf-8")
        return evidence

    def args(self, root: Path, *, preflight_only: bool = False) -> argparse.Namespace:
        return argparse.Namespace(output=root / "report", source=root / "source", game_dir=None, game_exe=None,
                                  mcp_evidence=None, kaishek_profile=None, kaishek_fixture=None,
                                  preflight_only=preflight_only)

    def test_exact_identity_is_frozen_and_binary_drift_is_environment_red(self):
        with tempfile.TemporaryDirectory(prefix="lyd-runner-test-") as temp:
            root = Path(temp)
            game, executable = self.make_game(root)
            first, second = root / "first", root / "second"
            first.mkdir()
            second.mkdir()
            expected = runner.digest(executable)
            result = runner.inspect_game(game, executable, first, expected_sha=expected)
            self.assertEqual(result["status"], "EXACT_BUILD")
            self.assertEqual(result["launcher_settings_sha256"], runner.digest(first / "launcher-settings.snapshot.json"))
            executable.write_bytes(b"different build")
            drift = runner.inspect_game(game, executable, second, expected_sha=expected)
            self.assertEqual(drift["status"], "ENVIRONMENT_RED")
            self.assertIn("executable-is-not-the-frozen-1.20-build", drift["issues"])

    def test_explicit_paths_and_environment_paths(self):
        with tempfile.TemporaryDirectory(prefix="lyd-runner-test-") as temp:
            root = Path(temp)
            game, executable = self.make_game(root)
            self.assertEqual(runner.resolve_game_paths(None, None, {"XAR_CK3_GAME_DIR": str(game)}), (game.resolve(), executable.resolve()))
            self.assertEqual(runner.resolve_game_paths(game, executable, {"XAR_CK3_GAME_DIR": str(root / "wrong")}), (game.resolve(), executable.resolve()))
            self.assertEqual(runner.resolve_game_paths(None, executable, {}), (game.resolve(), executable.resolve()))

    def test_capture_preserves_stdout_stderr_and_nonzero_return_code(self):
        with tempfile.TemporaryDirectory(prefix="lyd-runner-test-") as temp:
            root = Path(temp)
            result = runner.capture_command([sys.executable, "-c", "import sys; sys.stdout.write('out\\n'); sys.stderr.write('err\\n'); sys.exit(7)"], root, "offline", cwd=root)
            self.assertEqual(result["returncode"], 7)
            for kind, expected in (("stdout", b"out\r\n" if sys.platform == "win32" else b"out\n"),
                                   ("stderr", b"err\r\n" if sys.platform == "win32" else b"err\n")):
                path = root / result[kind]["path"]
                self.assertEqual(path.read_bytes(), expected)
                self.assertEqual(result[kind]["sha256"], hashlib.sha256(expected).hexdigest())
            self.assertEqual(json.loads((root / "offline.command.json").read_text())["argv"], result["argv"])

    def test_old_doctor_or_tampered_receipt_never_proves_current_endpoint(self):
        with tempfile.TemporaryDirectory(prefix="lyd-runner-test-") as temp:
            root = Path(temp)
            old_output, current_output, tampered_output = root / "old", root / "current", root / "tampered"
            for output in (old_output, current_output, tampered_output):
                output.mkdir()
            evidence = self.make_evidence(root, "1.19.0.6")
            old = runner.inspect_mcp(evidence, old_output, config=root / "no-config")
            self.assertEqual(old["status"], "NOT_PROVEN")
            self.assertIn("MCP-evidence-does-not-identify-the-exact-1.20-build", old["issues"])
            evidence = self.make_evidence(root)
            current = runner.inspect_mcp(evidence, current_output, config=root / "no-config")
            self.assertEqual(current["status"], "SUPPLIED_EVIDENCE_VALIDATED")
            self.assertFalse(current["reprobed"])
            self.assertTrue(current["unknown_product_capabilities"])
            (root / "tools-response.json").write_text("{}", encoding="utf-8")
            tampered = runner.inspect_mcp(evidence, tampered_output, config=root / "no-config")
            self.assertEqual(tampered["status"], "NOT_PROVEN")
            self.assertTrue(any("SHA-256 mismatch" in issue for issue in tampered["issues"]))

    def test_l0_green_with_missing_live_has_environment_exit_and_fresh_report(self):
        with tempfile.TemporaryDirectory(prefix="lyd-runner-test-") as temp:
            root = Path(temp)
            args = self.args(root)
            commands = []

            def fake_command(argv, output, name):
                self.assertEqual(Path(argv[0]), Path(sys.executable))
                self.assertTrue(Path(argv[1]).name in {"test_build_release.py", "test_run_acceptance.py", "test_school_consent.py", "test_content_leadership.py", "test_institution_candidate.py", "gen_content.py", "gen_runtime.py", "validate_static.py", "build_release.py"})
                commands.append(name)
                return {"argv": argv, "returncode": 0}

            with patch.object(runner, "inspect_game", return_value={"status": "EXACT_BUILD", "issues": []}), \
                 patch.object(runner, "inspect_processes", return_value={"status": "NOT_RUNNING", "pids": []}), \
                 patch.object(subprocess, "run", side_effect=AssertionError("unexpected subprocess")):
                report = runner.run(args, command_runner=fake_command)
            self.assertEqual(commands, ["tool-tests", "runner-tests", "school-consent-tests", "content-leadership-tests", "institution-tests", "content-generated-check", "runtime-generated-check", "static", "build-check"])
            self.assertEqual(report["l0"]["status"], "GREEN")
            self.assertEqual(report["l0"]["product_source"], "GREEN")
            self.assertEqual(report["result"], "ENVIRONMENT_RED")
            self.assertEqual(report["exit_code"], 2)
            self.assertEqual(report["live"]["status"], "NOT_RUN")
            self.assertEqual(report["product_scope"]["iteration"], 4)
            self.assertIn("no live-flow acceptance", report["product_scope"]["reunion_and_schism"])
            self.assertEqual(report["environment"]["kaishek"]["status"], "NOT_APPLICABLE")
            before = (args.output / "report.json").read_bytes()
            with self.assertRaisesRegex(ValueError, "fresh attempt"):
                runner.run(args)
            self.assertEqual((args.output / "report.json").read_bytes(), before)

    def test_preflight_only_skips_l0_and_code_failure_has_priority_over_missing_live(self):
        with tempfile.TemporaryDirectory(prefix="lyd-runner-test-") as temp:
            root = Path(temp)
            with patch.object(runner, "inspect_game", return_value={"status": "ENVIRONMENT_RED", "issues": ["fixture-build-mismatch"]}), \
                 patch.object(runner, "inspect_processes", return_value={"status": "NOT_RUNNING", "pids": []}), \
                 patch.object(subprocess, "run", side_effect=AssertionError("unexpected subprocess")):
                report = runner.run(self.args(root, preflight_only=True), command_runner=lambda *args: self.fail("preflight invoked L0"))
            self.assertEqual(report["l0"]["status"], "NOT_RUN")
            self.assertEqual(report["exit_code"], 2)
            self.assertEqual(runner.decide_result({"status": "RED"}, {"status": "ENVIRONMENT_RED"}), ("L0_RED", 1))


if __name__ == "__main__":
    unittest.main()
