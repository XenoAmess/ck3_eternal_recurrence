#!/usr/bin/env python3
"""Focused tests for exact vanilla dynastic-cycle interrupt contracts."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

import zg361_phase2_promotion_source_production_entry as production


EVENT_SOURCE_SHA256 = (
    "C9904AAA01ABC8583E67D07866FAE8EF89274708BDA3929498DDDB2F24FC2153"
)
SITUATION_SOURCE_SHA256 = (
    "748F2AF8CBDF97E01182FEFADF0B975E62AECE57D09AB1515C02E112DB56FAEA"
)


def _scope(name: str, type_key: str) -> dict[str, object]:
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": type_key,
            "typed_identity": {
                "status": "unavailable",
                "reason": "generic_scope_payload_identity_not_closed",
            },
        },
    }


def _character_scope(name: str, character_id: int) -> dict[str, object]:
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": "character",
            "typed_identity": {
                "status": "available",
                "kind": "character",
                "character_id": character_id,
            },
        },
    }


def _source(relative: str) -> Path | None:
    for root in (ROOT, ROOT.parent):
        candidate = root / "Crusader Kings III" / "game" / relative
        if candidate.is_file():
            return candidate
    return None


class VanillaDynasticCycleInterruptContractTests(unittest.TestCase):
    def test_stability_notification_keeps_player_independent(self) -> None:
        event_key = "tgp_dynastic_cycle.0072"
        contract = production._resolve_timeline_interrupt_contract(
            event_key,
            player=32904,
            starting_date=53905680,
            absolute_end_date=54158880,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(contract)
        assert contract is not None
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 1101,
            "date_raw": 54044544,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 32904,
                },
            },
            "saved_scopes": [
                _scope("situation", "situation"),
                _scope("situation_sub_region", "situation_sub_region"),
                _character_scope("new_son_of_heaven", 110448),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot={
                    "date_raw": 54044544,
                    "active_event": {"option_count": 2},
                },
                event={"event_instance_id": 1101},
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        no_new_emperor = copy.deepcopy(context)
        no_new_emperor["saved_scopes"].pop()
        self.assertTrue(all(checks_for(no_new_emperor).values()))

        player_as_new_emperor = copy.deepcopy(context)
        player_as_new_emperor["saved_scopes"][2] = _character_scope(
            "new_son_of_heaven", 32904
        )
        self.assertFalse(
            checks_for(player_as_new_emperor)[
                "scope:new_son_of_heaven:unique_third_party"
            ]
        )

        wrong_option = copy.deepcopy(context)
        wrong_option["options"][0]["native_option_index"] = 1
        self.assertFalse(checks_for(wrong_option)["authored_options_exact"])

    def test_instability_transition_uses_exact_empty_acknowledgement(self) -> None:
        event_key = "tgp_dynastic_cycle.0091"
        contract = production._resolve_timeline_interrupt_contract(
            event_key,
            player=32904,
            starting_date=53383440,
            absolute_end_date=53635896,
            stop_at_clean_review_boundary=False,
            continue_to_pause_target=True,
        )
        self.assertIsNotNone(contract)
        assert contract is not None
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 666,
            "date_raw": 53436024,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 32904,
                },
            },
            "saved_scopes": [
                _scope("situation", "situation"),
                _scope("situation_sub_region", "situation_sub_region"),
            ],
            "options": [{
                "rendered_index": 0,
                "native_option_index": 0,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }],
        }

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot={
                    "date_raw": 53436024,
                    "active_event": {"option_count": 1},
                },
                event={"event_instance_id": 666},
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

        missing_scope = copy.deepcopy(context)
        missing_scope["saved_scopes"].pop()
        self.assertFalse(checks_for(missing_scope)["saved_scope_count"])

        wrong_type = copy.deepcopy(context)
        wrong_type["saved_scopes"][1] = _scope(
            "situation_sub_region", "situation"
        )
        self.assertFalse(
            checks_for(wrong_type)["scope:situation_sub_region:type"]
        )

        wrong_option = copy.deepcopy(context)
        wrong_option["options"][0]["native_option_index"] = 1
        self.assertFalse(checks_for(wrong_option)["authored_options_exact"])

    def test_exact_build_sources_remain_frozen(self) -> None:
        sources = {
            "events/dlc/tgp/tgp_dynastic_cycle_events.txt": EVENT_SOURCE_SHA256,
            "common/situation/situations/tgp_dynastic_cycle.txt": (
                SITUATION_SOURCE_SHA256
            ),
        }
        for relative, expected in sources.items():
            with self.subTest(relative=relative):
                path = _source(relative)
                if path is None:
                    continue
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest().upper(),
                    expected,
                )


if __name__ == "__main__":
    unittest.main()
