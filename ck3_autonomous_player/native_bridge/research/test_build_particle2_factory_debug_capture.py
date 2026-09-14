from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
HELPER = HERE / "build_particle2_factory_debug_capture.py"


class Particle2FactoryBuildHelperTests(unittest.TestCase):
    def test_plan_is_python_only_and_non_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "capture.exe"
            result = subprocess.run(
                [
                    sys.executable,
                    str(HELPER),
                    "--output-path",
                    str(output),
                    "--debug-build",
                    "--plan-only",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "planned")
            self.assertTrue(payload["debug_build"])
            self.assertEqual(payload["compiler_flags"], ["/Od", "/Zi"])
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
