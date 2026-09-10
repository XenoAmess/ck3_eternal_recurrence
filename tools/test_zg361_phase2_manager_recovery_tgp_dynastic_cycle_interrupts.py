#!/usr/bin/env python3
"""Tests for the source-reviewed TGP dynastic-cycle interrupt contract."""

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
    _scope,
)


class ManagerRecoveryTgpDynasticCycleInterruptTests(unittest.TestCase):
    def test_advancement_event_accepts_exact_relation_fallthroughs(self) -> None:
        event_key = "tgp_dynastic_cycle_events.0001"
        contract = production._resolve_timeline_interrupt_contract(
            event_key,
            player=32904,
            starting_date=53760000,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(contract)
        assert contract is not None

        def checks_for(scopes: list[dict[str, object]]) -> dict[str, bool]:
            context = _context(
                event_key=event_key,
                instance_id=1074,
                date_raw=53767200,
                player=32904,
                scopes=scopes,
                native_option_indices=(1, 2, 3),
            )
            return production._known_interrupt_checks(
                snapshot={
                    "date_raw": 53767200,
                    "active_event": {"option_count": 4},
                },
                event={"event_instance_id": 1074},
                context=context,
                event_key=event_key,
                contract=contract,
            )

        common = [
            _scope("my_situation", "situation"),
            _scope("my_movement", "situation_participant_group"),
            _scope("servant", "character", 107353),
        ]
        for relation in (
            [_scope("potential_friend", "character", 49718)],
            [_scope("friend", "character", 49718)],
            [],
        ):
            with self.subTest(relation=relation):
                checks = checks_for(common + relation)
                self.assertTrue(all(checks.values()), checks)

        drifted = checks_for(common + [_scope("friend", "landed_title")])
        self.assertFalse(drifted["scope:friend:type"])

    def test_instability_event_uses_non_resource_third_option(self) -> None:
        event_key = "tgp_dynastic_cycle_events.0020"
        contract = production._resolve_timeline_interrupt_contract(
            event_key,
            player=32904,
            starting_date=53400000,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertEqual(contract["root_character_id"], 32904)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        context = _context(
            event_key=event_key,
            instance_id=777,
            date_raw=53450184,
            player=32904,
            scopes=[
                _scope("my_situation", "situation"),
                _scope("my_movement", "situation_participant_group"),
                _scope("marshal", "character", 36528),
                _scope("peasant_county", "landed_title"),
            ],
            native_option_indices=(1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53450184,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 777},
            context=context,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)

        focused_without_movement = _context(
            event_key=event_key,
            instance_id=778,
            date_raw=53450208,
            player=32904,
            scopes=[
                _scope("my_situation", "situation"),
                _scope("marshal", "character", 36528),
                _scope("peasant_county", "landed_title"),
            ],
            native_option_indices=(0, 1, 2),
        )
        variant_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53450208,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 778},
            context=focused_without_movement,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(variant_checks.values()), variant_checks)

        drifted = copy.deepcopy(context)
        drifted["options"][0]["native_option_index"] = 0
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53450184,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 777},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])


if __name__ == "__main__":
    unittest.main()
