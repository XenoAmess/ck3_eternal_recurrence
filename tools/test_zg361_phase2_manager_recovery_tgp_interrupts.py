#!/usr/bin/env python3
"""Purpose split for additional TGP manager-recovery interrupt contracts."""

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


class ManagerRecoveryTgpInterruptTests(unittest.TestCase):
    def test_house_member_province_petition_uses_terminal_refusal(self) -> None:
        event_key = "tgp_decision_events.0101"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=23,
            date_raw=53158008,
            player=32904,
            scopes=[
                _scope("petitioner", "character", 28080),
                _scope("actors_movement", "situation_participant_group"),
                _scope("hegemon", "character", 32904),
                _scope("petition_recipient", "character", 32904),
                _scope("province_metropolitan", "boolean"),
                _scope("house_movement_member", "character", 28087),
                _scope("other_movement_member", "character", 26378),
                _scope("province_change_recipient", "character", 28087),
            ],
            native_option_indices=(0, 1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53158008,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 23},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][-1] = _scope(
            "province_change_recipient", "character", 28088
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53158008,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 23},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:province_change_recipient:matches_any"]
        )

    def test_elder_invitation_uses_terminal_study_route(self) -> None:
        event_key = "tgp_movement_events.0050"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=14,
            date_raw=53150712,
            player=32904,
            scopes=[
                _scope("my_movement", "situation_participant_group"),
                _scope("new_elder", "character", 27275),
            ],
            native_option_indices=(0, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150712,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 14},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(
            contract["scope_types"]["my_movement"],
            "situation_participant_group",
        )
        self.assertEqual(contract["scope_types"]["new_elder"], "character")
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(contract["saved_scope_count"], 2)

        drifted = copy.deepcopy(context)
        drifted["options"][1]["native_option_index"] = 1
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150712,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 14},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])


if __name__ == "__main__":
    unittest.main()
