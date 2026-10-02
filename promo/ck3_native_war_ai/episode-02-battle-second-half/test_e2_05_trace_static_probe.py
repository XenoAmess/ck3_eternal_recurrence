"""The static trace probe must never admit target life or unrelated receipts."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("e2_05_trace_static_probe.py")
A02_TRACE = Path(
    r"D:\workspace\ck3_native_war_ai_promo_work"
    r"\episode02-e2-05-d26-live-20260929-a02"
    r"\ck3-output\interactive-requests-responses\e2-05-d26-trace-finish.json"
)


class TraceProbeTest(unittest.TestCase):
    def run_probe(self, receipt: Path) -> dict:
        process = subprocess.run(
            [sys.executable, str(SCRIPT), str(receipt)],
            check=True, capture_output=True, text=True)
        return json.loads(process.stdout)

    def test_unrelated_recorder_receipt_is_explicit_non_admission(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "recorder-final.json"
            source.write_text(json.dumps({"result": "CALL_COMPLETED",
                                          "body": {"step": "recorder-final"}}),
                              encoding="utf-8")
            result = self.run_probe(source)
        self.assertFalse(result["source_shape_supported"])
        self.assertFalse(result["admission"])
        self.assertTrue(result["observation_only"])
        self.assertEqual(result["target_33437_day27_life_status"], "UNKNOWN")

    @unittest.skipUnless(A02_TRACE.is_file(), "Exact external a02 trace is unavailable")
    def test_real_failed_a02_trace_is_still_non_admission(self) -> None:
        result = self.run_probe(A02_TRACE)
        self.assertTrue(result["source_shape_supported"])
        self.assertFalse(result["admission"])
        self.assertEqual(result["target_33437_day27_life_status"], "UNKNOWN")
        self.assertFalse(result["knight_selects_presence"])
        self.assertEqual(result["failure_flags"], 1040)


if __name__ == "__main__":
    unittest.main()
