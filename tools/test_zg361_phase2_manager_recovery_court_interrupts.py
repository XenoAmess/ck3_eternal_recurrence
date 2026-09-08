#!/usr/bin/env python3
"""Purpose-split contracts for royal-court manager-recovery interrupts."""

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


class ManagerRecoveryCourtInterruptTests(unittest.TestCase):
    def test_court_mockery_binds_only_visible_authored_route(self) -> None:
        event_key = "court_yearly.6030"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=210,
            date_raw=53219640,
            player=32904,
            scopes=[_scope("6030_courtier", "character", 28685)],
            native_option_indices=(0,),
        )

        def checks_for(
            candidate: dict[str, object], *, snapshot_count: int = 6,
        ) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot={
                    "date_raw": 53219640,
                    "active_event": {"option_count": snapshot_count},
                },
                event={"event_instance_id": 210},
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        player_courtier = copy.deepcopy(context)
        player_courtier["saved_scopes"][0] = _scope(
            "6030_courtier", "character", 32904
        )
        self.assertFalse(checks_for(player_courtier)[
            "scope:6030_courtier:unique_third_party"
        ])

        wrong_type = copy.deepcopy(context)
        wrong_type["saved_scopes"][0]["scope"]["type_key"] = "landed_title"
        self.assertFalse(checks_for(wrong_type)["scope:6030_courtier:type"])

        wrong_native = copy.deepcopy(context)
        wrong_native["options"][0]["native_option_index"] = 2
        self.assertFalse(checks_for(wrong_native)["authored_options_exact"])

        self.assertFalse(checks_for(context, snapshot_count=1)[
            "snapshot_option_count"
        ])


if __name__ == "__main__":
    unittest.main()
