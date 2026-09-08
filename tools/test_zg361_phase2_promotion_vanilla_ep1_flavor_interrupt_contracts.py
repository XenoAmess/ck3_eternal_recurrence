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

    def test_exotic_arms_accepts_r350_armor_branch_and_refuses(self) -> None:
        event_key = "ep1_flavor.2040"
        contract = _manager_contract(event_key, player=32904)
        armor_context = _context(
            event_key=event_key,
            instance_id=324,
            date_raw=53233416,
            player=32904,
            scopes=[
                _scope("exotic_blade_holder", "character", 36439),
                _scope("exotic_arms_target", "character", 32904),
                _scope("exotic_blade_quality", "boolean"),
                _scope("owner", "character", 36439),
                _scope("armor_type", "flag"),
                _scope("random_quality_bonus", "value"),
                _scope("quality", "value"),
                _scope("wealth", "value"),
                _scope("newly_created_artifact", "artifact"),
                _scope("merchant_county", "landed_title"),
                _scope("foreign_merchant", "character", 16817492),
                _scope("exotic_blade", "artifact"),
            ],
            native_option_indices=(1, 2),
        )

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot={
                    "date_raw": 53233416,
                    "active_event": {"option_count": 3},
                },
                event={"event_instance_id": 324},
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(armor_context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

        normal_quality_armor = copy.deepcopy(armor_context)
        normal_quality_armor["saved_scopes"] = [
            item for item in normal_quality_armor["saved_scopes"]
            if item["name"] != "exotic_blade_quality"
        ]
        self.assertTrue(all(checks_for(normal_quality_armor).values()))

        weapon_context = copy.deepcopy(armor_context)
        weapon_context["saved_scopes"][4] = _scope("weapon_type", "flag")
        self.assertTrue(all(checks_for(weapon_context).values()))

        wrong_armor_type = copy.deepcopy(armor_context)
        wrong_armor_type["saved_scopes"][4] = _scope("armor_type", "value")
        self.assertFalse(
            checks_for(wrong_armor_type)["scope:armor_type:optional_type"]
        )

        ambiguous_artifact_kind = copy.deepcopy(armor_context)
        ambiguous_artifact_kind["saved_scopes"].append(
            _scope("weapon_type", "flag")
        )
        self.assertFalse(
            checks_for(ambiguous_artifact_kind)["saved_scope_names_exact"]
        )


if __name__ == "__main__":
    unittest.main()
