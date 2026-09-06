#!/usr/bin/env python3
"""Purpose-split tests for birth manager-recovery interrupts."""

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


class ManagerRecoveryBirthInterruptTests(unittest.TestCase):
    def test_played_father_birth_notice_uses_inert_acknowledgement(self) -> None:
        event_key = "birth.1003"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=79,
            date_raw=53175528,
            player=32904,
            scopes=[
                _scope("child", "character", 66252),
                _scope("father", "character", 32904),
                _scope("real_father", "character", 32904),
                _scope("mother", "character", 32797),
                _scope("is_bastard", "boolean"),
                _scope("is_child_of_concubine", "boolean"),
                _scope("matrilineal", "boolean"),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53175528, "active_event": {"option_count": 2}},
            event={"event_instance_id": 79},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope(
            "real_father", "character", 32798
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53175528, "active_event": {"option_count": 2}},
            event={"event_instance_id": 79},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:real_father"])


if __name__ == "__main__":
    unittest.main()
