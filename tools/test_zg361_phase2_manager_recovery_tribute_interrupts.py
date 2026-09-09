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


def _resource_reward_scopes(resource_type: str) -> list[dict[str, object]]:
    return [
        _scope("actor", "character", 30502),
        _scope("recipient", "character", 32904),
        _scope("secondary_actor", "character", unavailable_character=True),
        _scope("secondary_recipient", "character", unavailable_character=True),
        _scope("intermediary", "character", unavailable_character=True),
        *[
            _scope(f"{size}_{resource_type}_tribute", "boolean")
            for size in ("small", "adequate", "excessive")
        ],
        _scope("tribute_mission_target", "character", 32904),
        _scope("tributary_scope", "character", 30502),
        _scope("overlord_scope", "character", 32904),
        _scope("receiving_character", "character", 32904),
        _scope("opinion_of_tributary", "value"),
        _scope("tribute_reward_type_treasury", "value"),
        _scope("saved_innovation", "culture_innovation"),
        _scope("decided_on_treasury_reward", "flag"),
    ]


class ManagerRecoveryTributeInterruptTests(unittest.TestCase):
    def test_tribute_reward_is_repeatable_without_a_lifecycle_ceiling(self) -> None:
        contract = _manager_contract("tribute_mission.1005", player=32904)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

    def test_resource_reward_routes_use_exact_typed_scope_variants(self) -> None:
        event_key = "tribute_mission.1005"
        contract = _manager_contract(event_key, player=32904)
        for resource_type in ("gold", "herd"):
            with self.subTest(resource_type=resource_type):
                context = _context(
                    event_key=event_key,
                    instance_id=65,
                    date_raw=53168208,
                    player=32904,
                    scopes=_resource_reward_scopes(resource_type),
                    native_option_indices=(0, 1, 2, 3, 5, 6),
                )
                checks = production._known_interrupt_checks(
                    snapshot={
                        "date_raw": 53168208,
                        "active_event": {"option_count": 7},
                    },
                    event={"event_instance_id": 65},
                    context=context,
                    event_key=event_key,
                    contract=contract,
                )
                self.assertTrue(all(checks.values()), checks)

        drifted = _context(
            event_key=event_key,
            instance_id=65,
            date_raw=53168208,
            player=32904,
            scopes=_resource_reward_scopes("gold"),
            native_option_indices=(0, 1, 2, 3, 5, 6),
        )
        drifted["saved_scopes"][3] = _scope(
            "secondary_recipient", "character", 30502
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53168208, "active_event": {"option_count": 7}},
            event={"event_instance_id": 65},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:secondary_recipient:unavailable_character"]
        )

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
