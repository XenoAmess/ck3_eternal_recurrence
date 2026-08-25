from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from xar_autoplayer.simulation.combat_input import load_live_combat_fixture


PROJECT_ROOT = Path(__file__).parents[2]
REPORT_PATH = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "combat"
    / "research"
    / "rev4_phase_events_disabled_n100000_seed_c0319a06.json"
)
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "combat"


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class CombatResearchReportContractTests(unittest.TestCase):
    def test_report_provenance_and_independent_outputs_are_frozen(self) -> None:
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            report["experiment"],
            {
                "horizon_days": 120,
                "sample_count_per_scenario": 100_000,
                "seed_u64": 3_224_476_166,
                "workers": 24,
            },
        )
        self.assertEqual(report["model_fidelity"], "research-only-bounded-core")
        self.assertFalse(report["planner_usable"])
        self.assertFalse(report["active_attack_allowed"])

        actual_code_files = {
            name: hashlib.sha256((PROJECT_ROOT / name).read_bytes()).hexdigest()
            for name in report["code_files_sha256"]
        }
        self.assertEqual(actual_code_files, report["code_files_sha256"])
        self.assertEqual(_canonical_sha256(actual_code_files), report["code_sha256"])
        self.assertEqual(
            _canonical_sha256(report["transition_manifest"]),
            report["transition_manifest_sha256"],
        )

        expected = {
            "live_rev4_vs_357.json": {
                "counts": (100_000, 0, 0),
                "days": (27, 29, 30),
                "player_hard": (17_784_511, 18_901_640, 20_102_278),
                "enemy_hard": (71_277_206, 71_652_004, 71_991_756),
            },
            "live_rev4_vs_combined.json": {
                "counts": (0, 100_000, 0),
                "days": (36, 36, 37),
                "player_hard": (45_198_897, 45_198_914, 45_198_932),
                "enemy_hard": (50_227_014, 52_817_761, 55_472_596),
            },
            "live_rev4_player_attacks_357.json": {
                "counts": (100_000, 0, 0),
                "days": (36, 38, 41),
                "player_hard": (23_961_250, 25_814_489, 27_840_514),
                "enemy_hard": (68_549_526, 69_324_396, 69_991_234),
            },
            "live_rev4_player_attacks_combined.json": {
                "counts": (0, 100_000, 0),
                "days": (34, 34, 35),
                "player_hard": (45_198_930, 45_198_943, 45_198_958),
                "enemy_hard": (37_825_951, 40_124_121, 42_493_942),
            },
        }
        self.assertEqual(len(report["scenarios"]), 4)
        for row in report["scenarios"]:
            fixture_name = row["fixture"]
            fixture_path = FIXTURE_ROOT / fixture_name
            self.assertEqual(
                hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
                row["fixture_file_sha256"],
            )
            combat_input = load_live_combat_fixture(fixture_path)
            self.assertEqual(combat_input.input_sha256, row["input_sha256"])
            summary = row["summary"]
            frozen = expected[fixture_name]
            self.assertEqual(
                (
                    summary["player_wins"],
                    summary["player_losses"],
                    summary["no_resolution"],
                ),
                frozen["counts"],
            )
            self.assertEqual(
                tuple(summary["battle_days"][key] for key in ("p10", "p50", "p90")),
                frozen["days"],
            )
            self.assertEqual(
                tuple(summary["player_hard_losses_raw"][key] for key in ("p10", "p50", "p90")),
                frozen["player_hard"],
            )
            self.assertEqual(
                tuple(summary["enemy_hard_losses_raw"][key] for key in ("p10", "p50", "p90")),
                frozen["enemy_hard"],
            )
            self.assertFalse(summary["fidelity_gate"])
            self.assertFalse(summary["planner_usable"])


if __name__ == "__main__":
    unittest.main()
