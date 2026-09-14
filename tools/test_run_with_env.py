from __future__ import annotations

import unittest
from unittest import mock

import run_with_env


class RunWithEnvTests(unittest.TestCase):
    def test_runs_exact_argv_without_shell_and_with_override(self) -> None:
        completed = mock.Mock(returncode=7)
        with mock.patch.object(run_with_env.subprocess, "run", return_value=completed) as run:
            result = run_with_env.main(
                ["--env", "FIXTURE=value", "--", "python.exe", "worker.py"]
            )
        self.assertEqual(result, 7)
        self.assertEqual(run.call_args.args[0], ["python.exe", "worker.py"])
        self.assertEqual(run.call_args.kwargs["env"]["FIXTURE"], "value")
        self.assertFalse(run.call_args.kwargs["check"])

    def test_rejects_invalid_environment_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid environment override"):
            run_with_env.parse_environment(["BAD-NAME=value"])

    def test_resolves_explicit_working_directory(self) -> None:
        completed = mock.Mock(returncode=0)
        with mock.patch.object(run_with_env.subprocess, "run", return_value=completed) as run:
            result = run_with_env.main(["--cwd", ".", "--", "python.exe", "worker.py"])
        self.assertEqual(result, 0)
        self.assertTrue(run.call_args.kwargs["cwd"].endswith("ck3_eternal_recurrence"))


if __name__ == "__main__":
    unittest.main()
