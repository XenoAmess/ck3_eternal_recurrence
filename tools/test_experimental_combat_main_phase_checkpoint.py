"""Focused offline checks for bounded original-combat main-phase pairing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from experimental_combat_main_phase_checkpoint import run_to_main_phase_checkpoint


DATE = 53192304
COMBAT = 738197508
ARMY = 83886367
ACTOR = 29829
EPISODE = "native-29829-2bc2d599f7f9"
INDEX = {
    "actor": ACTOR,
    "episode": EPISODE,
    "date_raw": DATE,
    "files": {"prepared_save": {"path": "Z:/research/state/profile/save games/xar_checkpoint.ck3"}},
}


class FakeDriver:
    def __init__(self) -> None:
        self.day = 0
        self.running = False
        self.running_reads = 0
        self.actions: list[str] = []
        self.phases = [(0, 1), (0, 2), (0, 3), (1, 0)]
        self.actor_change_day: int | None = None
        self.event_day: int | None = None
        self.event_running = False
        self.overshoot = False
        self.winner_day: int | None = None
        self.forced_winner_day: int | None = None
        self.fighting_zero_day: int | None = None
        self.combat_change_day: int | None = None

    def capabilities(self) -> dict[str, object]:
        return {
            "native_session_control": {
                "driver_state_restored": True,
                "driver_state_restore_kind": "cold_checkpoint",
                "driver_state_error": None,
            }
        }

    def take_snapshot(self) -> dict[str, object]:
        if self.running:
            self.running_reads += 1
            date = DATE + self.day * 24
            if self.running_reads >= 2:
                date += 48 if self.overshoot else 24
            active_event = {"instance_id": 1} if self.event_running else None
            return self._snapshot(date, paused=False, active_event=active_event)
        return self._snapshot(
            DATE + self.day * 24,
            paused=True,
            active_event={"instance_id": 1} if self.event_day == self.day else None,
        )

    def _snapshot(self, date: int, *, paused: bool, active_event: object) -> dict[str, object]:
        actor = ACTOR + (1 if self.actor_change_day == self.day else 0)
        return {
            "revision": 3 + self.day,
            "native_revision": 3 + self.day,
            "date_raw": date,
            "paused": paused,
            "map_ready": True,
            "episode_character_id": actor,
            "episode_run_id": EPISODE,
            "played_character": {"character_id": actor},
            "active_event": active_event,
        }

    def execute_step(self, step: str, **kwargs: object) -> dict[str, object]:
        self.actions.append(step)
        if step.startswith("query-battle-control-snapshot-v1-"):
            phase, phase_day = self.phases[self.day]
            return {
                "accepted": True,
                "status": "available",
                "queried_native_revision": 3 + self.day,
                "battle_control_snapshot": {
                    "status": "available",
                    "battle_control_ready": True,
                    "combat_id": COMBAT + (1 if self.combat_change_day == self.day else 0),
                    "subject_public_cunit_id": ARMY,
                    "observed_date_raw": DATE + self.day * 24,
                    "phase_raw": phase,
                    "phase_day": phase_day,
                    "winner_raw": 0 if self.winner_day == self.day else -1,
                    "forced_winner_raw": 0 if self.forced_winner_day == self.day else -1,
                    "finalized": False,
                    "attacker": {
                        "stored_current_fighting_raw": 0 if self.fighting_zero_day == self.day else 21500000,
                        "stored_current_matches_derived": True,
                    },
                    "defender": {
                        "stored_current_fighting_raw": 232400000,
                        "stored_current_matches_derived": True,
                    },
                },
            }
        if step == "resume-map":
            self.running = True
            self.running_reads = 0
        if step == "pause-map":
            self.running = False
            self.day += 1
        if step == "save-checkpoint":
            return {"step": step, "accepted": True, "checkpoint": {"status": "saved"}}
        return {"step": step, "accepted": True, "status": "submitted"}


class MainPhaseCheckpointTests(unittest.TestCase):
    def run_case(self, driver: FakeDriver) -> tuple[dict[str, object], list[dict[str, object]]]:
        observations: list[dict[str, object]] = []
        with patch(
            "xar_autoplayer.native_auto_run._verify_checkpoint_result",
            return_value={"status": "saved", "sha256": "A" * 64},
        ) as verify:
            result = run_to_main_phase_checkpoint(
                driver,
                official_index=INDEX,
                combat_id=COMBAT,
                subject_army_id=ARMY,
                daily_observation_sink=observations.append,
            )
        verify.assert_called_once()
        return result, observations

    def test_three_exact_days_then_one_official_checkpoint(self) -> None:
        driver = FakeDriver()
        result, observations = self.run_case(driver)
        self.assertEqual(result["status"], "main_phase_checkpoint_saved")
        self.assertEqual(result["days_advanced"], 3)
        self.assertEqual(result["date_raw"], DATE + 72)
        self.assertFalse(result["production_trace_ready"])
        self.assertEqual(len(observations), 3)
        self.assertEqual(
            [(o["battle_control"]["battle_control_snapshot"]["phase_raw"],
              o["battle_control"]["battle_control_snapshot"]["phase_day"])
             for o in observations],
            [(0, 2), (0, 3), (1, 0)],
        )
        self.assertEqual(driver.actions.count("resume-map"), 3)
        self.assertEqual(driver.actions.count("pause-map"), 3)
        self.assertEqual(driver.actions.count("save-checkpoint"), 1)
        self.assertFalse(any("experimental-combat-phase-event-trace" in x for x in driver.actions))

    def test_wrong_phase_after_one_day_stops_before_another_resume(self) -> None:
        driver = FakeDriver()
        driver.phases[1] = (0, 1)
        observations: list[dict[str, object]] = []
        with self.assertRaisesRegex(ValueError, "phase transition"):
            run_to_main_phase_checkpoint(driver, official_index=INDEX,
                                         combat_id=COMBAT, subject_army_id=ARMY,
                                         daily_observation_sink=observations.append)
        self.assertEqual(len(observations), 1)
        self.assertEqual(driver.actions.count("resume-map"), 1)
        self.assertNotIn("save-checkpoint", driver.actions)

    def test_overshoot_stops_without_pause_or_second_resume(self) -> None:
        driver = FakeDriver()
        driver.overshoot = True
        with self.assertRaisesRegex(ValueError, "overshot"):
            run_to_main_phase_checkpoint(driver, official_index=INDEX,
                                         combat_id=COMBAT, subject_army_id=ARMY,
                                         daily_observation_sink=lambda _: None)
        self.assertEqual(driver.actions.count("resume-map"), 1)
        self.assertEqual(driver.actions.count("pause-map"), 0)

    def test_actor_event_and_combat_change_stop(self) -> None:
        for attribute, value, message in (
            ("actor_change_day", 1, "actor"),
            ("event_running", True, "event"),
            ("combat_change_day", 1, "CombatID"),
            ("winner_day", 1, "battle-control"),
            ("forced_winner_day", 1, "battle-control"),
            ("fighting_zero_day", 1, "fighting"),
        ):
            with self.subTest(attribute=attribute):
                driver = FakeDriver()
                setattr(driver, attribute, value)
                with self.assertRaisesRegex(ValueError, message):
                    run_to_main_phase_checkpoint(driver, official_index=INDEX,
                                                 combat_id=COMBAT, subject_army_id=ARMY,
                                                 daily_observation_sink=lambda _: None)
                self.assertEqual(driver.actions.count("resume-map"), 1)
                self.assertNotIn("save-checkpoint", driver.actions)

    def test_cold_restore_or_starting_stage_failure_has_no_action(self) -> None:
        driver = FakeDriver()
        driver.phases[0] = (1, 0)
        with self.assertRaisesRegex(ValueError, "maneuver day 1"):
            run_to_main_phase_checkpoint(driver, official_index=INDEX,
                                         combat_id=COMBAT, subject_army_id=ARMY,
                                         daily_observation_sink=lambda _: None)
        self.assertEqual(driver.actions, [f"query-battle-control-snapshot-v1-{ARMY}"])
        driver = FakeDriver()
        driver.capabilities = lambda: {"native_session_control": {"driver_state_restored": False}}
        with self.assertRaisesRegex(ValueError, "cold checkpoint"):
            run_to_main_phase_checkpoint(driver, official_index=INDEX,
                                         combat_id=COMBAT, subject_army_id=ARMY,
                                         daily_observation_sink=lambda _: None)
        self.assertEqual(driver.actions, [])


if __name__ == "__main__":
    unittest.main()
