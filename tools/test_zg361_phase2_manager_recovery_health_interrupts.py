#!/usr/bin/env python3
"""Purpose-split contracts for health manager-recovery interrupts."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

import zg361_phase2_promotion_source_production_entry as production
from test_zg361_phase2_manager_recovery_interrupts import (
    _context,
    _manager_contract,
    _scope,
)


class ManagerRecoveryHealthInterruptTests(unittest.TestCase):
    def test_third_party_disease_notice_avoids_physician_search(self) -> None:
        event_key = "health.2201"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=20,
            date_raw=53156832,
            player=32904,
            scopes=[
                _scope("sick_character", "character", 32797),
                _scope("disease_type", "flag"),
                _scope("health_court_owner", "character", 32904),
                _scope("background_terrain_scope", "province"),
            ],
            native_option_indices=(5, 6),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53156832,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 20},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 7)
        self.assertEqual(contract["selected_native_option_index"], 6)
        self.assertEqual(contract["character_scopes"]["health_court_owner"], 32904)

        player_became_patient = copy.deepcopy(context)
        player_became_patient["saved_scopes"][0] = _scope(
            "sick_character", "character", 32904
        )
        patient_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53156832,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 20},
            context=player_became_patient,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(patient_checks["scope:sick_character:unique_third_party"])

        drifted = copy.deepcopy(context)
        drifted["options"][0]["native_option_index"] = 4
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53156832,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 20},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])


if __name__ == "__main__":
    unittest.main()
