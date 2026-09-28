"""Fail-closed checks for the H2743 read-only runner's external gates."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SCRIPT = (Path(__file__).resolve().parents[2] / "native_bridge" / "research"
          / "run_h2743_dejure_readonly_v3.py")
spec = importlib.util.spec_from_file_location("run_h2743_dejure_readonly_v3", SCRIPT)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def clean_receipt() -> dict[str, object]:
    return {
        "returncode": 0,
        "ck3_pids_after": [],
        "stdout_reader_alive_after": False,
        "source_sha256_after": runner.SOURCE_HASHES.copy(),
        "candidate_dll_sha256_after": runner.DLL_SHA,
        "injector_sha256_after": runner.INJECTOR_SHA,
        "prepared_save_sha256_after": runner.SOURCE_HASHES["xar_checkpoint.ck3"],
        "prepared_sidecar_sha256_after": runner.SOURCE_HASHES["first-heir-marriage-formal-v1.json"],
    }


class H2743RunnerGateTests(unittest.TestCase):
    def test_final_result_requires_clean_managed_exit_and_unchanged_inputs(self) -> None:
        runner.require_clean_session_exit(clean_receipt())
        failures = (
            ("returncode", 1),
            ("ck3_pids_after", [1234]),
            ("stdout_reader_alive_after", True),
            ("candidate_dll_sha256_after", "0" * 64),
            ("prepared_save_sha256_after", "0" * 64),
            ("prepared_sidecar_sha256_after", "0" * 64),
        )
        for field, bad_value in failures:
            with self.subTest(field=field):
                receipt = clean_receipt()
                receipt[field] = bad_value
                with self.assertRaises(RuntimeError):
                    runner.require_clean_session_exit(receipt)
        receipt = clean_receipt()
        receipt["source_sha256_after"]["driver-state.json"] = "0" * 64
        with self.assertRaises(RuntimeError):
            runner.require_clean_session_exit(receipt)

    def test_renewed_lease_rechecks_owner_after_heartbeat(self) -> None:
        heartbeat = SimpleNamespace(stdout=(
            b'{"ok":true,"task":{"task_id":"h2743-review","state":"running",'
            b'"resources":["ck3-screen:acquired"]}}'
        ))
        with (patch.object(runner, "screen_lease") as check,
              patch.object(runner.subprocess, "run", return_value=heartbeat) as call):
            runner.renew_screen_lease("h2743-review")
        self.assertEqual(check.call_count, 2)
        self.assertEqual(call.call_args.args[0][-3:], ["heartbeat", "--task", "h2743-review"])

    def test_rejected_heartbeat_cannot_validate_exclusive_screen(self) -> None:
        heartbeat = SimpleNamespace(stdout=(
            b'{"ok":true,"task":{"task_id":"h2743-review","state":"done",'
            b'"resources":[]}}'
        ))
        with (patch.object(runner, "screen_lease") as check,
              patch.object(runner.subprocess, "run", return_value=heartbeat)):
            with self.assertRaises(RuntimeError):
                runner.renew_screen_lease("h2743-review")
        self.assertEqual(check.call_count, 1)

    def test_screen_lease_routes_through_legacy_non_utf8_summary(self) -> None:
        listed = SimpleNamespace(stdout=(
            b'{"ok":true,"tasks":[{"task_id":"h2743-review","state":"running",'
            b'"stale":false,"resources":["ck3-screen:acquired"],'
            b'"summary":"legacy-\xff"}]}'
        ))
        with patch.object(runner.subprocess, "run", return_value=listed):
            runner.screen_lease("h2743-review")


if __name__ == "__main__":
    unittest.main()
