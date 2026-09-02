from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_raiktor_war_bound_private_capture_v1.py"
)
MANIFEST = (
    ROOT
    / "native_bridge"
    / "research"
    / "raiktor_war_bound_private_capture_v1_manifest.json"
)
SPEC = importlib.util.spec_from_file_location("war_bound_capture_runner", RUNNER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RaiktorWarBoundCaptureRunnerTests(unittest.TestCase):
    def test_manifest_persists_distinct_300_second_readiness(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        attempt = manifest["attempt_contract"]
        readiness = manifest["readiness_contract"]
        self.assertTrue(attempt["fresh_attempt_required"])
        self.assertFalse(attempt["reuse_previous_attempt"])
        self.assertEqual(readiness["main_menu_timeout_seconds"], 300)
        self.assertEqual(
            readiness["main_menu_stage_capture_seconds"],
            [60, 120, 180, 240, 300],
        )
        self.assertEqual(readiness["capture_process_timeout_ms"], 1200000)
        self.assertEqual(manifest["capture_product"]["timeout_max_ms"], 1200000)
        self.assertEqual(
            manifest["capture_product"]["executable_sha256"],
            MODULE.EXPECTED_CAPTURE_EXE_SHA256,
        )
        self.assertIn("MainMenuReadinessTimeout", readiness["typed_terminals"])

    def test_readiness_cli_must_match_manifest(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        args = SimpleNamespace(
            main_menu_timeout_seconds=300,
            ui_timeout_seconds=520,
            capture_timeout_ms=1200000,
        )
        observed = MODULE.validate_readiness_contract(manifest, args)
        self.assertEqual(observed["main_menu_timeout_seconds"], 300)
        args.main_menu_timeout_seconds = 299
        with self.assertRaisesRegex(RuntimeError, "does not match manifest"):
            MODULE.validate_readiness_contract(manifest, args)

    def test_fresh_attempt_rejects_prior_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            attempt = Path(temporary) / "attempt"
            MODULE.require_fresh_attempt_directory(attempt)
            attempt.mkdir()
            MODULE.require_fresh_attempt_directory(attempt)
            (attempt / "prior-report.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(
                MODULE.TypedTerminalError, "artifact directory is not absent or empty"
            ):
                MODULE.require_fresh_attempt_directory(attempt)

    def test_empty_capture_is_a_typed_report_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "capture.json"
            path.write_bytes(b"")
            capture, error = MODULE.load_capture_artifact(path)
        self.assertIsNone(capture)
        self.assertEqual(error, "capture artifact is empty")

    def test_valid_capture_object_loads(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "capture.json"
            path.write_text('{"result":"RED"}\n', encoding="utf-8")
            capture, error = MODULE.load_capture_artifact(path)
        self.assertEqual(capture, {"result": "RED"})
        self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
