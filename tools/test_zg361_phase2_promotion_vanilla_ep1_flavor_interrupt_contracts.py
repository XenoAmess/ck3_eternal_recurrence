#!/usr/bin/env python3
"""Tests for observed CK3 EP1 flavor interrupt contracts."""

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


class VanillaEp1FlavorInterruptTests(unittest.TestCase):
    def test_visiting_eunuch_declines_exact_offer_frame(self) -> None:
        event_key = "ep1_flavor.1000"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=204,
            date_raw=53205336,
            player=32904,
            scopes=[
                _scope("eunuch_target_culture", "culture"),
                _scope("eunuch_target", "character", 16841156),
                _scope("new_court", "landed_title"),
            ],
            native_option_indices=(0, 1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53205336,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 204},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][1] = _scope(
            "eunuch_target", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53205336,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 204},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:eunuch_target:unique_third_party"]
        )

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope("new_court", "province")
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53205336,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 204},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:new_court:type"])


if __name__ == "__main__":
    unittest.main()
