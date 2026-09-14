from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RECORDER = ROOT / "tools" / "record_native_capability_segment.py"


class NativeCapabilityRecorderTests(unittest.TestCase):
    def test_plan_is_python_only_and_does_not_create_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recorder-plan-") as temporary:
            output = Path(temporary) / "not-created"
            result = subprocess.run(
                [
                    sys.executable,
                    str(RECORDER),
                    "--segment-id",
                    "fixture",
                    "--english-title",
                    "Fixture",
                    "--chinese-title",
                    "夹具",
                    "--status-badge",
                    "STATIC",
                    "--boundary-text",
                    "NO LIVE RUN",
                    "--runner",
                    sys.executable,
                    "--runner-argument=--version",
                    "--environment",
                    "XAR_FIXTURE=1",
                    "--output-directory",
                    str(output),
                    "--plan-only",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            plan = json.loads(result.stdout)
            self.assertEqual(plan["kind"], "ck3_native_capability_segment_recording_plan")
            self.assertEqual(plan["runner_arguments"], ["--version"])
            self.assertEqual(plan["environment_keys"], ["XAR_FIXTURE"])
            self.assertFalse(output.exists())

    def test_output_argument_injection_cannot_be_overridden(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(RECORDER),
                "--segment-id",
                "fixture",
                "--english-title",
                "Fixture",
                "--chinese-title",
                "夹具",
                "--status-badge",
                "STATIC",
                "--boundary-text",
                "NO LIVE RUN",
                "--runner",
                sys.executable,
                "--runner-argument=--output=elsewhere.json",
                "--output-directory",
                str(ROOT / "artifacts" / "forbidden"),
                "--plan-only",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not contain --output", result.stderr)


if __name__ == "__main__":
    unittest.main()
