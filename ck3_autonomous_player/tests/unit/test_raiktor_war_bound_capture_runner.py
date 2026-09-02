from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_raiktor_war_bound_private_capture_v1.py"
)
SPEC = importlib.util.spec_from_file_location("war_bound_capture_runner", RUNNER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RaiktorWarBoundCaptureRunnerTests(unittest.TestCase):
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
