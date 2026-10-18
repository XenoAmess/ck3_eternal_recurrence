"""One real launcher/read_json path regression with a synthetic Popen boundary."""
from __future__ import annotations
import argparse
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ck3_mod_acceptance_launcher as launcher

SCRATCH = None

class HostStartedPublicationTests(unittest.TestCase):
    def test_partial_publication_completes_once_and_failure_bounds_remain(self):
        for mode in ("complete_after_partial", "deadline", "malformed_object", "child_exit"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(dir=SCRATCH) as directory:
                root = Path(directory)
                for name in ("proof.json", "challenge.json", "frozen-argv.json"):
                    (root / name).write_text("{}", encoding="utf8")
                args = SimpleNamespace(run_root=root, keeper_root=root / "keeper",
                    proof=root / "proof.json", challenge=root / "challenge.json",
                    observed_nonce="a" * 32, reviewer="synthetic-reviewer")
                frozen = {"run_id": "synthetic-managed-run", "lease_anchor": str(root), "argv": ["not-executed"]}
                acknowledgment = {"run_id": frozen["run_id"], "pid": 1234,
                    "actual_popen_retained": True, "business_pass": False}
                started = root / "host-started.json"
                clock = SimpleNamespace(elapsed=0.0, sleeps=0)
                def sleep(seconds):
                    clock.elapsed += seconds
                    clock.sleeps += 1
                    if mode == "complete_after_partial":
                        started.write_text(json.dumps(acknowledgment), encoding="utf8")
                child = SimpleNamespace(pid=123, poll=lambda: 7 if mode == "child_exit" else None)
                def popen(*_args, **_kwargs):
                    started.write_text("[]" if mode == "malformed_object" else '{"run_id":', encoding="utf8")
                    return child
                output = io.StringIO()
                with patch.object(launcher, "admission", return_value=(frozen, {}, {"lease": {"synthetic": True}})), \
                        patch.object(launcher.subprocess, "Popen", side_effect=popen) as create, \
                        patch.object(launcher.time, "monotonic", side_effect=lambda: clock.elapsed), \
                        patch.object(launcher.time, "sleep", side_effect=sleep), \
                        contextlib.redirect_stdout(output):
                    if mode == "complete_after_partial":
                        self.assertEqual(launcher.launch(args), 0)
                        emitted = json.loads(output.getvalue())
                        self.assertEqual(emitted["host"], acknowledgment)
                        self.assertEqual(emitted["status"], "ORIGINAL_SHARED_HOST_STARTED")
                        self.assertFalse(emitted["business_pass"])
                        self.assertEqual(clock.sleeps, 1)
                        with self.assertRaisesRegex(ValueError, "never replay"):
                            launcher.launch(args)
                    elif mode == "deadline":
                        with self.assertRaises(TimeoutError) as caught:
                            launcher.launch(args)
                        self.assertIsInstance(caught.exception.__cause__, json.JSONDecodeError)
                        self.assertGreaterEqual(clock.elapsed, 45)
                        self.assertLess(clock.elapsed, 45.1)
                        self.assertEqual(output.getvalue(), "")
                    elif mode == "malformed_object":
                        with self.assertRaisesRegex(ValueError, "JSON object required"):
                            launcher.launch(args)
                        self.assertEqual(clock.sleeps, 0)
                    else:
                        with self.assertRaisesRegex(ValueError, "supervisor failed"):
                            launcher.launch(args)
                        self.assertEqual(clock.sleeps, 0)
                    self.assertEqual(create.call_count, 1)
                    self.assertTrue((root / "launch-intent.json").is_file())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch-root", type=Path)
    args, rest = parser.parse_known_args()
    if args.scratch_root:
        SCRATCH = str(args.scratch_root.resolve())
        if not Path(SCRATCH).is_dir():
            raise ValueError("existing scratch root required")
    unittest.main(argv=[sys.argv[0], *rest])
