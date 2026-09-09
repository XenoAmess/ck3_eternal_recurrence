#!/usr/bin/env python3
"""Tests for the narrow great-holy-war manager interrupt contract."""

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


class ManagerRecoveryHolyWarInterruptTests(unittest.TestCase):
    def test_awakening_notice_only_acknowledges_hostile_projection(self) -> None:
        event_key = "great_holy_war.0011"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=346,
            date_raw=53223552,
            player=32904,
            scopes=[
                _scope("awakening_faith", "faith"),
                _scope("ghw_first_sponsor", "character", 32201),
                _scope("background_temple_scope", "character", 32201),
            ],
            native_option_indices=(3,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53223552,
                "active_event": {"option_count": 5},
            },
            event={"event_instance_id": 346},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)
        self.assertEqual(contract["scope_types"], {
            "awakening_faith": "faith",
            "ghw_first_sponsor": "character",
            "background_temple_scope": "character",
        })

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope(
            "background_temple_scope", "character", 32202
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53223552,
                "active_event": {"option_count": 5},
            },
            event={"event_instance_id": 346},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:ghw_first_sponsor:matches_any"]
        )

        drifted = copy.deepcopy(context)
        drifted["options"][0]["native_option_index"] = 4
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53223552,
                "active_event": {"option_count": 5},
            },
            event={"event_instance_id": 346},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_notice_can_repeat_for_later_faith_unlocks(self) -> None:
        event_key = "great_holy_war.0011"
        contract = production._resolve_timeline_interrupt_contract(
            event_key,
            player=32904,
            starting_date=53390000,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertNotIn("max_occurrences", contract)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        for instance_id, date_raw, sponsor in (
            (606, 53392944, 16840827),
            (670, 53437416, 36145),
        ):
            with self.subTest(instance_id=instance_id):
                context = _context(
                    event_key=event_key,
                    instance_id=instance_id,
                    date_raw=date_raw,
                    player=32904,
                    scopes=[
                        _scope("awakening_faith", "faith"),
                        _scope("ghw_first_sponsor", "character", sponsor),
                        _scope(
                            "background_temple_scope", "character", sponsor
                        ),
                    ],
                    native_option_indices=(3,),
                )
                checks = production._known_interrupt_checks(
                    snapshot={
                        "date_raw": date_raw,
                        "active_event": {"option_count": 5},
                    },
                    event={"event_instance_id": instance_id},
                    context=context,
                    event_key=event_key,
                    contract=contract,
                )
                self.assertTrue(all(checks.values()), checks)


if __name__ == "__main__":
    unittest.main()
