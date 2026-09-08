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


def _capital_manpower_two_governor_scopes() -> list[dict[str, object]]:
    return [
        _scope("suggestor", "character", 29346),
        _scope("minimum_development", "value"),
        _scope("governor_1", "character", 30938),
        _scope("county_1", "landed_title"),
        _scope("governor_2", "character", 29348),
        _scope("county_2", "landed_title"),
    ]


class ManagerRecoveryImperialInterruptTests(unittest.TestCase):
    def test_fake_letter_uses_exact_reward_branch_and_alias(self) -> None:
        event_key = "ep3_emperor_yearly.8010"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=204,
            date_raw=53205336,
            player=32904,
            scopes=[
                _scope("governor", "character", 26936),
                _scope("liar", "character", 16841171),
                _scope("new_target", "character", 16841171),
            ],
            native_option_indices=(0, 1, 2, 3),
        )

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot={
                    "date_raw": 53205336,
                    "active_event": {"option_count": 4},
                },
                event={"event_instance_id": 204},
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        alias_drift = copy.deepcopy(context)
        alias_drift["saved_scopes"][2] = _scope(
            "new_target", "character", 16841172
        )
        alias_checks = checks_for(alias_drift)
        self.assertFalse(alias_checks["scope:liar:matches_any"])
        self.assertFalse(alias_checks["scope:new_target:matches_any"])

        governor_is_liar = copy.deepcopy(context)
        governor_is_liar["saved_scopes"][0] = _scope(
            "governor", "character", 16841171
        )
        differs_checks = checks_for(governor_is_liar)
        self.assertFalse(differs_checks["scope:governor:differs_from"])
        self.assertFalse(differs_checks["scope:liar:differs_from"])

        wrong_projection = copy.deepcopy(context)
        wrong_projection["options"][-1]["native_option_index"] = 4
        self.assertFalse(
            checks_for(wrong_projection)["authored_options_exact"]
        )

    def test_capital_manpower_request_accepts_exact_two_governor_variant(
        self,
    ) -> None:
        event_key = "ep3_emperor_yearly.8000"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=343,
            date_raw=53219640,
            player=32904,
            scopes=_capital_manpower_two_governor_scopes(),
            native_option_indices=(0, 1, 3),
        )

        def checks_for(
            candidate: dict[str, object], *, snapshot_count: int = 4,
        ) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot={
                    "date_raw": 53219640,
                    "active_event": {"option_count": snapshot_count},
                },
                event={"event_instance_id": 343},
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        effective = production._scope_contract_for_context(
            context["saved_scopes"], contract
        )
        self.assertEqual(effective["saved_scope_count"], 6)
        self.assertEqual(effective["native_option_indices"], (0, 1, 3))
        self.assertEqual(effective["selected_native_option_index"], 0)

        collapsed = copy.deepcopy(context)
        collapsed["saved_scopes"][4] = _scope(
            "governor_2", "character", 30938
        )
        collapsed_checks = checks_for(collapsed)
        self.assertFalse(collapsed_checks["scope:governor_1:differs_from"])
        self.assertFalse(collapsed_checks["scope:governor_2:differs_from"])

        governor_three_visible = copy.deepcopy(context)
        governor_three_visible["options"][2]["native_option_index"] = 2
        self.assertFalse(
            checks_for(governor_three_visible)["authored_options_exact"]
        )

        self.assertFalse(checks_for(context, snapshot_count=3)[
            "snapshot_option_count"
        ])

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
