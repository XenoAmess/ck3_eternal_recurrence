from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.throughput_report import (  # noqa: E402
    analyze_one_generation_throughput,
    main,
)


def _report() -> dict[str, object]:
    return {
        "run_id": "fixture-one-generation",
        "status": "blocked",
        "started_at": "2026-08-28T00:00:00+00:00",
        "finished_at": "2026-08-28T00:00:21.100000+00:00",
        "elapsed_seconds": 21.1,
        "auto_run": {
            "turns": [
                {
                    "index": 1,
                    "class": "query",
                    "started_at": "2026-08-28T00:00:10+00:00",
                    "finished_at": "2026-08-28T00:00:11+00:00",
                    "before": {"date_raw": 1_000},
                    "after": {"date_raw": 1_000},
                    "result": {"step": "query-war"},
                },
                {
                    "index": 2,
                    "class": "gameplay",
                    "started_at": "2026-08-28T00:00:11.100000+00:00",
                    "finished_at": "2026-08-28T00:00:15.100000+00:00",
                    "before": {"date_raw": 1_000},
                    "after": {"date_raw": 1_168},
                    "result": {
                        "elapsed_days": 7,
                        "timeline_speed": 5,
                        "requested_horizon_days": 7,
                        "timeline_policy": "bounded_non_tactical",
                    },
                },
                {
                    "index": 3,
                    "class": "gameplay",
                    "started_at": "2026-08-28T00:00:17.100000+00:00",
                    "finished_at": "2026-08-28T00:00:19.100000+00:00",
                    "before": {"date_raw": 1_168},
                    "after": {"date_raw": 1_192},
                    "result": {
                        "timeline_speed": 3,
                        "requested_horizon_days": 1,
                        "timeline_policy": "remote_enemy_route",
                    },
                },
            ]
        },
        "checkpoints": [{"turn_index": 2, "status": "saved"}],
        "cleanup": {"elapsed_seconds": 1.0, "ok": True},
    }


class ThroughputReportTests(unittest.TestCase):
    def test_decomposes_full_run_without_claiming_checkpoint_io(self) -> None:
        result = analyze_one_generation_throughput(_report())

        self.assertEqual(result["game_days"], 8.0)
        self.assertEqual(result["wall_seconds"], 21.1)
        self.assertAlmostEqual(result["actual_days_per_minute"], 22.749, places=3)
        self.assertAlmostEqual(
            result["turn_loop_steady_state_days_per_minute"],
            52.747,
            places=3,
        )
        decomposition = result["decomposition"]
        self.assertEqual(decomposition["startup_seconds"], 10.0)
        self.assertEqual(decomposition["turn_loop_steady_state_seconds"], 9.1)
        self.assertEqual(
            decomposition["post_last_turn_to_report_finish_seconds"],
            2.0,
        )
        self.assertEqual(decomposition["query"], {"count": 1, "seconds": 1.0})
        self.assertEqual(decomposition["advance"]["seconds"], 6.0)
        self.assertEqual(
            decomposition["checkpoint_interturn"]["seconds"], 2.0
        )
        self.assertEqual(
            decomposition["checkpoint_interturn"]["precision"],
            "inferred_from_post_turn_gap",
        )
        self.assertEqual(decomposition["ordinary_interturn"]["seconds"], 0.1)
        self.assertEqual(decomposition["cleanup_seconds"], 1.0)
        self.assertEqual(decomposition["residual_seconds"], 1.0)
        self.assertFalse(result["targets"]["hard"]["target_met"])
        self.assertEqual(result["targets"]["hard"]["days_per_minute"], 60.0)
        self.assertEqual(
            result["targets"]["hard"]["measurement_scope"],
            "turn_loop_steady_state",
        )
        self.assertTrue(result["policy_neutrality"]["read_only_report_analysis"])
        self.assertFalse(
            result["policy_neutrality"]["changes_gameplay_decisions"]
        )
        self.assertEqual(
            result["policy_neutrality"]["war_contracts_unchanged"],
            [
                "entry",
                "participation",
                "continuation",
                "surrender",
                "peace",
                "termination",
            ],
        )
        self.assertEqual(
            result["targets"]["stretch"]["days_per_minute"], 120.0
        )
        self.assertFalse(
            result["measurement_quality"][
                "report_is_sufficient_for_pure_checkpoint_io"
            ]
        )

    def test_hard_gate_uses_complete_turn_loop_not_full_run(self) -> None:
        report = _report()
        report["finished_at"] = "2026-08-28T00:01:40+00:00"
        report["elapsed_seconds"] = 100.0
        turns = report["auto_run"]["turns"]
        turns[2]["started_at"] = "2026-08-28T00:00:16+00:00"
        turns[2]["finished_at"] = "2026-08-28T00:00:18+00:00"

        result = analyze_one_generation_throughput(report)

        self.assertEqual(result["turn_loop_steady_state_days_per_minute"], 60.0)
        self.assertTrue(result["targets"]["hard"]["target_met"])
        self.assertFalse(
            result["targets"]["hard"]["full_run_diagnostic"]["target_met"]
        )
        self.assertFalse(result["targets"]["stretch"]["target_met"])

    def test_groups_advance_cost_by_speed_horizon_and_policy(self) -> None:
        result = analyze_one_generation_throughput(_report())
        rows = {
            (row["timeline_speed"], row["timeline_policy"]): row
            for row in result["timeline_breakdown"]
        }

        self.assertEqual(rows[(5, "bounded_non_tactical")]["game_days"], 7.0)
        self.assertEqual(rows[(5, "bounded_non_tactical")]["wall_seconds"], 4.0)
        self.assertEqual(rows[(3, "remote_enemy_route")]["game_days"], 1.0)
        self.assertEqual(rows[(3, "remote_enemy_route")]["wall_seconds"], 2.0)

    def test_rejects_missing_turn_timestamps(self) -> None:
        report = _report()
        report["auto_run"]["turns"][0].pop("started_at")
        with self.assertRaisesRegex(ValueError, "started_at"):
            analyze_one_generation_throughput(report)

    def test_cli_reads_report_and_emits_json(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-throughput-report-") as temp:
            path = Path(temp) / "report.json"
            path.write_text(json.dumps(_report()), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(
                    [
                        str(path),
                        "--hard-target-days-per-minute",
                        "60",
                        "--stretch-target-days-per-minute",
                        "90",
                    ]
                )

        self.assertEqual(status, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["targets"]["hard"]["days_per_minute"], 60.0)
        self.assertEqual(payload["targets"]["stretch"]["days_per_minute"], 90.0)

    def test_rejects_stretch_target_below_hard_target(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least the hard target"):
            analyze_one_generation_throughput(
                _report(),
                hard_target_days_per_minute=100,
                stretch_target_days_per_minute=90,
            )


if __name__ == "__main__":
    unittest.main()
