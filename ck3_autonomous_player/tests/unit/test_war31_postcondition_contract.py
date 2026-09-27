"""Focused no-launch checks for WAR31 evidence, gaps, and binding."""

from __future__ import annotations

import sys
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from war31_postcondition_contract import project_war31_postcondition  # noqa: E402


def frame(
    *, active: bool, date: int = 53215920, revision: int = 3,
    snapshot_id: str = "native:3", gold: int | None = 500_000,
    prestige: int | None = -200_000,
) -> dict[str, object]:
    value: dict[str, object] = {
        "snapshot_id": snapshot_id,
        "native_revision": revision,
        "date_raw": date,
        "episode_run_id": "native-29829-2bc2d599f7f9",
        "played_character": {"character_id": 29829, "alive": True},
        "active_wars": [
            {
                "war_id": 16777231,
                "player_side": "defender",
                "player_is_primary_war_leader": True,
                "primary_opponent_character_id": 30097,
                "targeted_title_ids": [2128],
            }
        ] if active else [],
    }
    if gold is not None:
        value["played_character_gold"] = {"raw": gold, "scale": 100_000}
    if prestige is not None:
        value["played_character_prestige"] = {
            "raw": prestige, "scale": 100_000
        }
    return value


def action(*, phase: str, absent: bool) -> dict[str, object]:
    return {
        "step": "surrender-war-16777231",
        "accepted": True,
        "status": "submitted",
        "war_termination_result": {
            "war_id": 16777231,
            "outcome": "attacker_victory",
            "episode_run_id": "native-29829-2bc2d599f7f9",
            "starting_snapshot_id": "native:3",
            "observed_snapshot_id": "native:4",
            "submitted_date_raw": 53215920,
            "observed_date_raw": 53215920,
            "command_acknowledged": True,
            "status": phase,
            "war_id_absent_after_ack": absent,
        },
    }


class War31PostconditionTests(unittest.TestCase):
    def test_absent_is_not_zero_and_signed_delta_remains_signed(self) -> None:
        report = project_war31_postcondition(
            frame(active=True),
            frame(active=False, snapshot_id="native:4", revision=4,
                  gold=0, prestige=-300_000),
            action_result=action(phase="applied", absent=True),
        )
        self.assertEqual(report["after"]["war_active"]["value"], False)
        self.assertEqual(report["signed_resource_deltas"]["gold"]["value"]
                         ["signed_delta_raw"], -500_000)
        self.assertEqual(report["signed_resource_deltas"]["prestige"]["value"]
                         ["signed_delta_raw"], -100_000)
        self.assertEqual(report["after"]["resources"]["gold"]["value"]["raw"], 0)
        self.assertEqual(report["target_title_delta"]["status"], "unavailable")
        self.assertEqual(report["persisted_truce_delta"]["status"], "unavailable")
        self.assertFalse(report["material_outcome_complete"])

    def test_missing_resource_is_not_reported_as_zero_delta(self) -> None:
        report = project_war31_postcondition(
            frame(active=True, gold=None),
            frame(active=True, snapshot_id="native:4", revision=4, gold=0),
            action_result=action(phase="submitted_pending", absent=False),
        )
        self.assertEqual(report["signed_resource_deltas"]["gold"]["status"],
                         "unavailable")
        self.assertTrue(report["gates"]["action_submitted"])
        self.assertFalse(report["gates"]["war_absent_after"])

    def test_pending_ack_can_resolve_in_the_next_native_snapshot(self) -> None:
        result = action(phase="submitted_pending", absent=False)
        termination = result["war_termination_result"]
        termination["starting_snapshot_id"] = "native:4"
        termination["observed_snapshot_id"] = "native:4"
        report = project_war31_postcondition(
            frame(active=True, snapshot_id="native:4", revision=4),
            frame(active=False, snapshot_id="native:5", revision=5),
            action_result=result,
        )
        self.assertTrue(report["gates"]["action_submitted"])
        self.assertTrue(report["gates"]["war_absent_after"])
        self.assertEqual(report["action_submission"]["value"]["phase"],
                         "submitted_pending")

        termination["observed_snapshot_id"] = "native:6"
        with self.assertRaisesRegex(ValueError, "exact frame binding"):
            project_war31_postcondition(
                frame(active=True, snapshot_id="native:4", revision=4),
                frame(active=False, snapshot_id="native:5", revision=5),
                action_result=result,
            )

    def test_ack_conflicting_with_war_readback_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "conflicts"):
            project_war31_postcondition(
                frame(active=True),
                frame(active=True, snapshot_id="native:4", revision=4),
                action_result=action(phase="applied", absent=True),
            )

    def test_next_turn_and_paired_recovery_are_independent(self) -> None:
        after = frame(active=False, snapshot_id="native:4", revision=4)
        report = project_war31_postcondition(
            frame(active=True), after,
            action_result=action(phase="applied", absent=True),
            next_turn_snapshot=frame(
                active=False, snapshot_id="native:5", revision=5,
                date=53215944,
            ),
            recovery_snapshot=frame(
                active=False, snapshot_id="native:reloaded", revision=3,
            ),
            recovery_pair={
                "source_save_sha256": "A" * 64,
                "restored_save_sha256": "A" * 64,
            },
        )
        self.assertTrue(report["gates"]["war_absent_next_turn"])
        self.assertTrue(report["gates"]["paired_recovery_matched"])
        self.assertFalse(report["material_outcome_complete"])

    def test_wrong_actor_or_unpaired_recovery_is_rejected(self) -> None:
        wrong = frame(active=True)
        wrong["played_character"] = {"character_id": 30097, "alive": True}
        with self.assertRaisesRegex(ValueError, "Robert"):
            project_war31_postcondition(wrong, frame(active=False))
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            project_war31_postcondition(
                frame(active=True), frame(active=False, snapshot_id="native:4"),
                recovery_snapshot=frame(active=False, snapshot_id="native:reloaded"),
                recovery_pair={
                    "source_save_sha256": "A" * 64,
                    "restored_save_sha256": "B" * 64,
                },
            )

    def test_cli_hashes_inputs_and_never_overwrites_report(self) -> None:
        tool = Path(__file__).resolve().parents[2] / "tools" / "project_war31_postcondition.py"
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            before = root / "before.json"
            after = root / "after.json"
            report = root / "report.json"
            before.write_text(json.dumps(frame(active=True)), encoding="utf-8")
            after.write_text(
                json.dumps(frame(active=False, snapshot_id="native:4", revision=4)),
                encoding="utf-8",
            )
            argv = [
                sys.executable, str(tool), "--before", str(before), "--after",
                str(after), "--output", str(report),
            ]
            first = subprocess.run(argv, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            value = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(len(value["input_artifacts"]["before"]["sha256"]), 64)
            self.assertFalse(value["material_outcome_complete"])
            second = subprocess.run(argv, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)


if __name__ == "__main__":
    unittest.main()
