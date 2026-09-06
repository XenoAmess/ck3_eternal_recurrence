#!/usr/bin/env python3
"""Purpose-split contracts for tribute manager-recovery interrupts."""

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


def _nonhuman_reward_scopes() -> list[dict[str, object]]:
    return [
        _scope("actor", "character", 34077),
        _scope("recipient", "character", 32904),
        _scope("secondary_actor", "character", unavailable_character=True),
        _scope("secondary_recipient", "character", 54393),
        _scope("intermediary", "character", unavailable_character=True),
        _scope("tribute_mission_target", "character", 32904),
        _scope("tributary_scope", "character", 34077),
        _scope("overlord_scope", "character", 32904),
        _scope("receiving_character", "character", 32904),
        _scope("opinion_of_tributary", "value"),
        _scope("tribute_reward_type_treasury", "value"),
        _scope("saved_innovation", "culture_innovation"),
        _scope("decided_on_treasury_reward", "flag"),
    ]


class ManagerRecoveryTributeInterruptTests(unittest.TestCase):
    def test_nonhuman_reward_uses_exact_direct_scope_variant(self) -> None:
        event_key = "tribute_mission.1005"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=14,
            date_raw=53150352,
            player=32904,
            scopes=_nonhuman_reward_scopes(),
            native_option_indices=(0, 1, 2, 3, 5, 6),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150352,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 14},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 6)
        self.assertEqual(contract["selected_native_option_index"], 5)
        self.assertEqual(
            contract["scope_variants"][0][
                "unique_character_scope_excludes"
            ]["actor"],
            (32904,),
        )

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"].append(
            _scope("unexpected_scope", "character", 54393)
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150352,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 14},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["saved_scope_names_exact"])


if __name__ == "__main__":
    unittest.main()
