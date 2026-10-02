from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.simulation.hard_conversion_diagnostic import (
    assess_precontact_hard_conversion,
)


def _normalized_two_defender_v3() -> dict:
    phase_sides = [
        {"encounter_role": "attacker", "ordered_army_ids": [11],
         "commander_character_id": 101},
        {"encounter_role": "defender", "ordered_army_ids": [22, 33],
         "commander_character_id": 202},
    ]
    hard_sides = [
        {"side_index": 0, **phase_sides[0], "own_modifier_raw": 10_000,
         "enemy_modifier_raw": 25_000},
        {"side_index": 1, **phase_sides[1], "own_modifier_raw": -5_000,
         "enemy_modifier_raw": 20_000},
    ]
    return {
        "schema_version": 3,
        "contract_stage": "production_exact_132_refs",
        "completeness": {"input_observation_ready": True},
        "base_inputs": {
            "target_province_id": 2629,
            "scenario": {
                "attacker_entry_province_id": 2630,
                "attacker_army_ids": [11],
                "defender_army_ids": [22, 33],
                "actual_route_dependency": False,
            },
        },
        "phase_event_inputs": {
            "status": "available",
            "raw": {"sides": phase_sides},
            "hard_casualty_sides": {
                "status": "available", "source_target_province_id": 2629,
                "scale": 100_000, "sides": hard_sides,
            },
            "hard_casualty_winter": {
                "status": "available", "source_target_province_id": 2629,
                "scale": 100_000, "first_original_guard": False,
                "second_original_guard": None, "raw": None,
            },
        },
    }


def assess(payload: dict) -> dict:
    return assess_precontact_hard_conversion(
        payload, target_province_id=2629, attacker_entry_province_id=2630,
        attacker_army_ids=(11,), defender_army_ids=(22, 33),
    )


class HardConversionDiagnosticTests(unittest.TestCase):
    def test_defender_uses_opposite_enemy_modifier_with_native_rounding(self) -> None:
        result = assess(_normalized_two_defender_v3())
        self.assertEqual(result["status"], "observed_precontact_research_only")
        self.assertEqual(
            [row["conversion_raw"] for row in result["conversion_by_defending_role"]],
            [39_000, 36_000],
        )
        self.assertFalse(result["planner_usable"])
        self.assertFalse(result["active_attack_allowed"])
        self.assertFalse(result["actual_combat_parity"])

    def test_guarded_winter_only_adds_when_native_read_guarded(self) -> None:
        payload = _normalized_two_defender_v3()
        winter = payload["phase_event_inputs"]["hard_casualty_winter"]
        winter.update(first_original_guard=True, second_original_guard=True, raw=10_000)
        result = assess(payload)
        self.assertEqual(
            [row["conversion_raw"] for row in result["conversion_by_defending_role"]],
            [42_000, 39_000],
        )
        winter.update(second_original_guard=False, raw=None)
        self.assertEqual(assess(payload)["conversion_by_defending_role"][0]["conversion_raw"], 39_000)

    def test_stale_target_order_commander_or_missing_operand_rejects(self) -> None:
        base = _normalized_two_defender_v3()
        mutations = []
        changed = copy.deepcopy(base)
        changed["base_inputs"]["scenario"]["defender_army_ids"] = [33, 22]
        mutations.append(changed)
        changed = copy.deepcopy(base)
        changed["phase_event_inputs"]["hard_casualty_sides"]["sides"][1]["ordered_army_ids"] = [33, 22]
        mutations.append(changed)
        changed = copy.deepcopy(base)
        changed["phase_event_inputs"]["hard_casualty_sides"]["sides"][1]["commander_character_id"] = 999
        mutations.append(changed)
        changed = copy.deepcopy(base)
        changed["phase_event_inputs"]["hard_casualty_sides"]["status"] = "unavailable"
        mutations.append(changed)
        changed = copy.deepcopy(base)
        changed["phase_event_inputs"]["hard_casualty_winter"]["first_original_guard"] = True
        mutations.append(changed)
        changed = copy.deepcopy(base)
        changed["phase_event_inputs"]["hard_casualty_sides"]["sides"][0]["own_modifier_raw"] = True
        mutations.append(changed)
        for payload in mutations:
            with self.subTest(payload=payload):
                result = assess(payload)
                self.assertEqual(result["status"], "unavailable")
                self.assertIsNone(result["conversion_by_defending_role"])
                self.assertFalse(result["planner_usable"])


if __name__ == "__main__":
    unittest.main()
