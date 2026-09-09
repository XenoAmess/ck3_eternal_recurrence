#!/usr/bin/env python3
"""Tests for trait-specific manager interrupt contracts."""

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


class ManagerRecoveryTraitInterruptTests(unittest.TestCase):
    def test_depressed_criticism_uses_low_impact_insult_reply(self) -> None:
        event_key = "trait_specific_ongoing.3015"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=419,
            date_raw=53313672,
            player=32904,
            scopes=[_scope("unsympathetic", "character", 30938)],
            native_option_indices=(0, 1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53313672,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 419},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][0] = _scope(
            "unsympathetic", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53313672,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 419},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:unsympathetic:unique_third_party"]
        )

    def test_depressed_exhaustion_uses_only_acknowledgement(self) -> None:
        event_key = "trait_specific_ongoing.3009"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=624,
            date_raw=53380728,
            player=32904,
            scopes=[],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53380728,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 624},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

    def test_possessed_vision_uses_terminal_stress_relief(self) -> None:
        event_key = "trait_specific_ongoing.2001"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=211,
            date_raw=53219640,
            player=32904,
            scopes=[_scope("clergy", "character", 28662)],
            native_option_indices=(0, 1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53219640,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 211},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(contract["max_occurrences"], 1)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][0] = _scope(
            "clergy", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53219640,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 211},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:clergy:unique_third_party"])

        drifted = copy.deepcopy(context)
        drifted["options"][2]["native_option_index"] = 1
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53219640,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 211},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])


if __name__ == "__main__":
    unittest.main()
