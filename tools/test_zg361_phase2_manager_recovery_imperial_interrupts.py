#!/usr/bin/env python3
"""Purpose-split contracts for imperial manager-recovery interrupts."""

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


def _capital_manpower_scopes() -> list[dict[str, object]]:
    return [
        _scope("suggestor", "character", 30183),
        _scope("minimum_development", "value"),
        _scope("governor_1", "character", 29060),
        _scope("county_1", "landed_title"),
        _scope("governor_2", "character", 28424),
        _scope("county_2", "landed_title"),
        _scope("governor_3", "character", 28893),
        _scope("county_3", "landed_title"),
    ]


class ManagerRecoveryImperialInterruptTests(unittest.TestCase):
    def test_capital_manpower_request_preserves_player_capital(self) -> None:
        event_key = "ep3_emperor_yearly.8000"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=16,
            date_raw=53150712,
            player=32904,
            scopes=_capital_manpower_scopes(),
            native_option_indices=(0, 1, 2, 3),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150712,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 16},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(contract["saved_scope_count"], 8)
        self.assertEqual(
            contract["unique_character_scope_excludes"]["governor_1"],
            (32904,),
        )

        collapsed = copy.deepcopy(context)
        collapsed["saved_scopes"][4] = _scope(
            "governor_2", "character", 29060
        )
        collapsed_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150712,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 16},
            context=collapsed,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(collapsed_checks["scope:governor_1:differs_from"])
        self.assertFalse(collapsed_checks["scope:governor_2:differs_from"])

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][3]["scope"]["type_key"] = "province"
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150712,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 16},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:county_1:type"])


if __name__ == "__main__":
    unittest.main()
