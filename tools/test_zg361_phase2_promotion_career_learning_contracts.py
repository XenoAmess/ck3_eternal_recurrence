#!/usr/bin/env python3
"""Focused checks for player career-learning timeline contracts."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import zg361_phase2_promotion_source_production_entry as production  # noqa: E402


class CareerLearningTimelineContractTests(unittest.TestCase):
    def test_portfolio_digest_acknowledges_exact_live_scope_set(self) -> None:
        event_key = "zg361cl.390"
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            starting_date=53147016,
        )
        names = contract["saved_scope_name_sets"][0]
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": event_key,
            "current_event_instance_id": 342,
            "date_raw": 53221752,
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
                {
                    "name": name,
                    "scope": {"status": "available", "type_key": "unknown"},
                }
                for name in names
            ],
            "options": [
                {
                    "rendered_index": 0,
                    "native_option_index": 0,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
            ],
        }
        snapshot = {
            "date_raw": 53221752,
            "active_event": {"option_count": 1},
        }
        event = {"event_instance_id": 342}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["saved_scope_count"], 60)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        missing = copy.deepcopy(context)
        missing["saved_scopes"].pop()
        missing_checks = checks_for(missing)
        self.assertFalse(missing_checks["saved_scope_names_exact"])
        self.assertFalse(missing_checks["saved_scope_count"])

        extra = copy.deepcopy(context)
        extra["saved_scopes"].append(
            {
                "name": "unrelated_scope",
                "scope": {"status": "available", "type_key": "unknown"},
            }
        )
        extra_checks = checks_for(extra)
        self.assertFalse(extra_checks["saved_scope_names_exact"])
        self.assertFalse(extra_checks["saved_scope_count"])

        wrong_native = copy.deepcopy(context)
        wrong_native["options"][0]["native_option_index"] = 1
        self.assertFalse(checks_for(wrong_native)["authored_options_exact"])

    def test_relocation_response_uses_decline_and_exact_scope_set(self) -> None:
        contract = production._timeline_contract_for_window(
            production.KNOWN_TIMELINE_INTERRUPTS["zg361cl.314"],
            starting_date=53173584,
        )
        names = contract["saved_scope_name_sets"][0]
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "zg361cl.314",
            "current_event_instance_id": 136,
            "date_raw": 53173584,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 29037,
                },
            },
            "saved_scopes": [
                {
                    "name": name,
                    "scope": {"status": "available", "type_key": "unknown"},
                }
                for name in names
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
        snapshot = {"date_raw": 53173584, "active_event": {"option_count": 2}}
        event = {"event_instance_id": 136}

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot=snapshot,
                event=event,
                context=candidate,
                event_key="zg361cl.314",
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        extra = copy.deepcopy(context)
        extra["saved_scopes"].append(
            {
                "name": "unrelated_scope",
                "scope": {"status": "available", "type_key": "unknown"},
            }
        )
        self.assertFalse(checks_for(extra)["saved_scope_names_exact"])


if __name__ == "__main__":
    unittest.main()
