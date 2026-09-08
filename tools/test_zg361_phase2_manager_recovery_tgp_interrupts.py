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
    def test_military_aid_request_uses_saved_governor_resolution(self) -> None:
        event_key = "tgp_interaction_event.0010"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=276,
            date_raw=53245584,
            player=32904,
            scopes=[
                _scope("actor", "character", 29253),
                _scope("recipient", "character", 32904),
                _scope("secondary_actor", "character", unavailable_character=True),
                _scope(
                    "secondary_recipient", "character", unavailable_character=True
                ),
                _scope("intermediary", "character", unavailable_character=True),
                _scope("hook", "boolean"),
                _scope("dominant_family", "boolean"),
                _scope("joining_governor", "character", 32536),
            ],
            native_option_indices=(1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53245584,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 276},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(contract["snapshot_option_count"], 3)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

        all_routes_context = _context(
            event_key=event_key,
            instance_id=509,
            date_raw=53262744,
            player=32904,
            scopes=[
                _scope("actor", "character", 32350),
                _scope("recipient", "character", 32904),
                _scope("secondary_actor", "character", unavailable_character=True),
                _scope(
                    "secondary_recipient", "character", unavailable_character=True
                ),
                _scope("intermediary", "character", unavailable_character=True),
                _scope("hook", "boolean"),
                _scope("dominant_family", "boolean"),
                _scope("joining_governor", "character", 32536),
            ],
            native_option_indices=(0, 1, 2),
        )
        all_routes_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53262744,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 509},
            context=all_routes_context,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(all_routes_checks.values()), all_routes_checks)

        wrong_order = copy.deepcopy(all_routes_context)
        wrong_order["options"][1]["native_option_index"] = 2
        wrong_order_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53262744,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 509},
            context=wrong_order,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(wrong_order_checks["authored_options_exact"])

    def test_military_budget_renewal_keeps_current_allocation(self) -> None:
        event_key = "tgp_china_ministry.0100"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=31,
            date_raw=53163168,
            player=32904,
            scopes=[
                _scope("treasury_ruler", "character", 32904),
                _scope("steward", "character", 28080),
                _scope("military_budget", "character", 32904),
            ],
            native_option_indices=(0, 1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53163168,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 31},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        military_variant = next(
            variant
            for variant in contract["scope_variants"]
            if "military_budget" in variant["saved_scope_names"]
        )
        self.assertEqual(
            military_variant["character_scopes"],
            {"treasury_ruler": 32904, "military_budget": 32904},
        )

    def test_repeatable_military_aid_notice_uses_only_acknowledgement(self) -> None:
        event_key = "tgp_interaction_event.0015"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=27,
            date_raw=53159976,
            player=32904,
            scopes=[
                _scope("actor", "character", 34077),
                _scope("recipient", "character", 32904),
                _scope("secondary_actor", "character", unavailable_character=True),
                _scope("secondary_recipient", "character", 54393),
                _scope("intermediary", "character", unavailable_character=True),
                _scope("governor_at_war", "character", 32904),
                _scope("governor_joining", "character", 54393),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53159976,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 27},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(contract["max_occurrences"], 2)

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

    def test_all_source_authored_province_types_use_exact_scope_variants(self) -> None:
        event_key = "tgp_decision_events.0101"
        contract = _manager_contract(event_key, player=32904)
        for province_scope in (
            "province_metropolitan",
            "province_industrial",
            "province_military",
            "province_protectorate",
        ):
            with self.subTest(province_scope=province_scope):
                context = _context(
                    event_key=event_key,
                    instance_id=24,
                    date_raw=53161896,
                    player=32904,
                    scopes=[
                        _scope("petitioner", "character", 29346),
                        _scope("actors_movement", "situation_participant_group"),
                        _scope("hegemon", "character", 32904),
                        _scope("petition_recipient", "character", 32904),
                        _scope(province_scope, "boolean"),
                        _scope("other_movement_member", "character", 26378),
                        _scope(
                            "province_change_recipient", "character", 26378
                        ),
                    ],
                    native_option_indices=(0, 1, 2),
                )
                checks = production._known_interrupt_checks(
                    snapshot={
                        "date_raw": 53161896,
                        "active_event": {"option_count": 3},
                    },
                    event={"event_instance_id": 24},
                    context=context,
                    event_key=event_key,
                    contract=contract,
                )
                self.assertTrue(all(checks.values()), checks)

    def test_examination_petition_uses_compact_boolean_scope_variant(self) -> None:
        event_key = "tgp_decision_events.0101"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=220,
            date_raw=53229288,
            player=32904,
            scopes=[
                _scope("petitioner", "character", 27275),
                _scope("actors_movement", "situation_participant_group"),
                _scope("hegemon", "character", 32904),
                _scope("petition_recipient", "character", 32904),
                _scope("hold_examinations", "boolean"),
            ],
            native_option_indices=(0, 1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53229288,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 220},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

        wrong_branch = copy.deepcopy(context)
        wrong_branch["saved_scopes"][4] = _scope(
            "hold_examinations", "flag"
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53229288,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 220},
            context=wrong_branch,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:hold_examinations"])

    def test_budget_petition_uses_exact_compact_boolean_scope_variant(self) -> None:
        event_key = "tgp_decision_events.0101"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=408,
            date_raw=53248848,
            player=32904,
            scopes=[
                _scope("petitioner", "character", 29346),
                _scope("actors_movement", "situation_participant_group"),
                _scope("hegemon", "character", 32904),
                _scope("petition_recipient", "character", 32904),
                _scope("increase_budget_ministry", "boolean"),
            ],
            native_option_indices=(0, 1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53248848,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 408},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

        for sibling_scope in (
            "increase_budget_salary",
            "increase_budget_military",
            "increase_retirement_law",
            "decrease_retirement_law",
        ):
            with self.subTest(sibling_scope=sibling_scope):
                sibling = copy.deepcopy(context)
                sibling["saved_scopes"][4] = _scope(
                    sibling_scope, "boolean"
                )
                sibling_checks = production._known_interrupt_checks(
                    snapshot={
                        "date_raw": 53248848,
                        "active_event": {"option_count": 3},
                    },
                    event={"event_instance_id": 408},
                    context=sibling,
                    event_key=event_key,
                    contract=contract,
                )
                self.assertTrue(all(sibling_checks.values()), sibling_checks)

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

    def test_movement_rival_uses_non_hostile_non_religious_power_route(
        self,
    ) -> None:
        event_key = "tgp_movement_events.0060"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=343,
            date_raw=53219640,
            player=32904,
            scopes=[
                _scope("my_movement", "situation_participant_group"),
                _scope("rival_movement", "situation_participant_group"),
                _scope("rival", "character", 30340),
            ],
            native_option_indices=(1, 2, 3),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53219640,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 343},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

        wrong_projection = copy.deepcopy(context)
        wrong_projection["options"][0]["native_option_index"] = 0
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53219640,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 343},
            context=wrong_projection,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])


if __name__ == "__main__":
    unittest.main()
