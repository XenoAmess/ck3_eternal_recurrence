#!/usr/bin/env python3
"""Tests for council claim-fabrication result interrupt contracts."""

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


class ManagerRecoveryCouncilClaimInterruptTests(unittest.TestCase):
    def test_duchy_claim_notice_acknowledges_exact_result_frame(self) -> None:
        event_key = "court_chaplain_task.0313"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=214,
            date_raw=53227008,
            player=32904,
            scopes=[
                _scope("councillor", "character", 56719),
                _scope("councillor_liege", "character", 28679),
                _scope("province", "province"),
                _scope("county", "landed_title"),
                _scope("county_holder", "character", 30599),
                _scope("duchy", "landed_title"),
                _scope("duchy_holder", "character", 32904),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53227008,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 214},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["character_scopes"], {"duchy_holder": 32904})
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][1] = _scope(
            "councillor_liege", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53227008,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 214},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:councillor_liege:unique_third_party"]
        )

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][5] = _scope("duchy", "province")
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53227008,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 214},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:duchy:type"])


if __name__ == "__main__":
    unittest.main()
