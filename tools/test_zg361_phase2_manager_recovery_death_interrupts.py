#!/usr/bin/env python3
"""Purpose-split tests for manager-cycle death notification drains."""

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


class ManagerRecoveryDeathInterruptTests(unittest.TestCase):
    def test_neutral_spouse_death_uses_only_visible_authored_option(self) -> None:
        event_key = "death_management.1000"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=25,
            date_raw=53159208,
            player=32904,
            scopes=[
                _scope("new_memory", "character_memory"),
                _scope("surviving_consort", "character", 32904),
                _scope("dead_character", "character", 32797),
                _scope("deceased_character_stress", "value"),
                _scope("realm", "landed_title"),
            ],
            native_option_indices=(1,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53159208,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 25},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope(
            "dead_character", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53159208,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 25},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:dead_character:unique_third_party"])


if __name__ == "__main__":
    unittest.main()
