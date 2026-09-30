from pathlib import Path
import json
import sys
import tempfile
from types import ModuleType
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.h3937_run_config import main_for_runner


class ExplicitH3937ConfigTests(unittest.TestCase):
    def test_explicit_tuple_reaches_worker_without_state_or_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            configuration = {
                "schema": "xar.h3937.run-config.v1", "round": "R900001",
                "live_run_id": "fixture-only--vanilla--R900001",
                "live_execution_id": "fixture-only", "pipe": "fixture-only-pipe",
                "task_bus_dir": str(root / "bus"), "task_bus_cli_sha256": "A" * 64,
                "screen_task_id": "fixture-only-screen", "no_launch_dir": str(root / "preflight"),
                "output_dir": str(root / "live"), "go_receipt": str(root / "go.json"),
                "screen_attempt_dir": str(root / "screen"), "python_executable": sys.executable,
                "python_version": "fixture-only-version", "game_dir": str(root / "game"),
            }
            path = root / "config.json"
            path.write_text(json.dumps(configuration), encoding="utf-8")
            runner = ModuleType("fixture_only")
            runner.ROUND = "R3948"
            calls = []
            runner.main = lambda nonce: calls.append((nonce, runner.ROUND, runner.LIVE_RUN_ID, runner.STATE)) or 0
            self.assertEqual(main_for_runner(runner, root / "entry.py", ["--config", str(path), "--worker", "nonce"]), 0)
            self.assertEqual(calls, [("nonce", "R900001", configuration["live_run_id"], root / "preflight/state")])
            self.assertEqual(runner.RUN_CONFIG_BYTES, path.read_bytes())
            self.assertEqual(list(root.iterdir()), [path])

    def test_missing_config_never_dispatches_legacy_attempt(self):
        runner = ModuleType("fixture_only")
        runner.supervise_exact_once = lambda entry: self.fail("legacy dispatch reached")
        with self.assertRaises(SystemExit) as stopped:
            main_for_runner(runner, Path("entry.py"), [])
        self.assertEqual(stopped.exception.code, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
