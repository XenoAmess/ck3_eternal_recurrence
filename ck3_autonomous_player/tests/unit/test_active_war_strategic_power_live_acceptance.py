"""Focused checks for the active-war strategic-power live harness."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_active_war_strategic_power_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_active_war_strategic_power_live_acceptance", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError(f"cannot load harness: {SCRIPT}")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


class ActiveWarStrategicPowerHistoryChecksTests(unittest.TestCase):
    def test_uses_native_command_history_and_allows_only_two_queries(self) -> None:
        step = "query-war-entry-assessments-v1-1-28551"
        prefix = [{"index": 4, "command": "restore-checkpoint", "ok": True}]
        first = {"index": 5, "command": step, "ok": True}
        second = {"index": 6, "command": step, "ok": True}
        checks = HARNESS._query_history_checks(
            before={"native_command_history": prefix},
            between={"native_command_history": [*prefix, first]},
            after={"native_command_history": [*prefix, first, second]},
            step=step,
        )
        self.assertEqual(
            checks,
            {
                "history_first_query_only": True,
                "history_two_queries_only": True,
            },
        )

        extra = {"index": 7, "command": "resume-map", "ok": True}
        rejected = HARNESS._query_history_checks(
            before={"native_command_history": prefix},
            between={"native_command_history": [*prefix, first]},
            after={"native_command_history": [*prefix, first, second, extra]},
            step=step,
        )
        self.assertFalse(rejected["history_two_queries_only"])


if __name__ == "__main__":
    unittest.main()
