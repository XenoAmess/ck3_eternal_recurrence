from __future__ import annotations

import unittest
from dataclasses import replace

from xar_autoplayer.simulation.battle_calendar_admission import (
    CombatScheduleInput,
    DailyDateStageInput,
    LoadedScheduleInputs,
    project_daily_battle_schedule,
)


class BattleCalendarAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loaded = LoadedScheduleInputs(
            maneuver_days=3,
            roll_cadence_interval=3,
            source="focused-case caller explicit values; not native slot observation",
        )
        self.day = DailyDateStageInput(
            53250432, True, "caller-declared admitted .3 date stage",
            endpoint_paused=True,
        )
        self.combat = CombatScheduleInput(
            1291845646, 1, 0, 2, -1, 392400000, 222800000,
        )

    def test_admitted_day_endpoint_paused_cadence_wrap_then_due(self) -> None:
        wrapped = project_daily_battle_schedule(self.day, self.combat, self.loaded)
        next_day = replace(self.day, date_raw_before=wrapped["date_raw_after"])
        next_combat = replace(
            self.combat,
            phase_day=wrapped["phase_day_after"],
            roll_cadence_counter=wrapped["roll_cadence_counter_after"],
        )
        due = project_daily_battle_schedule(next_day, next_combat, self.loaded)
        self.assertEqual(wrapped["calendar_raw_hours"], 24)
        self.assertEqual(wrapped["accepted_combat_invocations"], 1)
        self.assertIs(wrapped["roll_helpers_called"], False)
        self.assertEqual(wrapped["roll_cadence_counter_after"], 0)
        self.assertEqual(due["calendar_raw_hours"], 24)
        self.assertIs(due["roll_helpers_called"], True)
        self.assertEqual(due["dispatch_date_raw"], 53250480)

    def test_maneuver_threshold_crossing_then_first_main_day(self) -> None:
        maneuver = replace(
            self.combat, phase_raw=0, phase_day=3, roll_cadence_counter=0,
        )
        crossing = project_daily_battle_schedule(self.day, maneuver, self.loaded)
        first_main = project_daily_battle_schedule(
            replace(self.day, date_raw_before=crossing["date_raw_after"]),
            replace(
                maneuver,
                phase_raw=crossing["phase_raw_after"],
                phase_day=crossing["phase_day_after"],
            ),
            self.loaded,
        )
        self.assertEqual(crossing["calendar_raw_hours"], 24)
        self.assertEqual(crossing["phase_raw_after"], 1)
        self.assertEqual(crossing["phase_day_after"], 0)
        self.assertIs(crossing["main_called"], False)
        self.assertIs(crossing["roll_helpers_called"], False)
        self.assertEqual(first_main["phase_day_after"], 1)
        self.assertIs(first_main["roll_helpers_called"], True)


if __name__ == "__main__":
    unittest.main()
