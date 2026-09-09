#!/usr/bin/env python3
"""Focused tests for vanilla historical-character interrupt contracts."""

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
    "ACE7B285D613419B17F2EC52BC1CE81A2DAAA8515B7CC159E0DC1E34BA4ACC8B"
)
EFFECT_SOURCE_SHA256 = (
    "0742FC261C844979E9B6311B297502172400B8B5A6A70743122DDB30DE8B632D"
)


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


def _source(relative: str) -> Path | None:
    for root in (ROOT, ROOT.parent):
        candidate = root / "Crusader Kings III" / "game" / relative
        if candidate.is_file():
            return candidate
    return None


class VanillaHistoricalCharacterInterruptContractTests(unittest.TestCase):
    def test_li_qingzhao_variant_uses_non_mutating_decline(self) -> None:
        event_key = "historical_char_creation_events.1"
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
            "current_event_instance_id": 665,
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
                _scope("birth_location", "landed_title"),
                _character_scope("historical_character", 50405035),
                _character_scope("major", 50377335),
                _scope("county_scope", "landed_title"),
                _scope("background_terrain_scope", "landed_title"),
                _scope("background_market_scope", "province"),
                _scope("background_university_scope", "province"),
                _scope("holy_site_scope", "province"),
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
                for index in range(3)
            ],
        }

        def checks_for(candidate: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot={
                    "date_raw": 53436024,
                    "active_event": {"option_count": 3},
                },
                event={"event_instance_id": 665},
                context=candidate,
                event_key=event_key,
                contract=contract,
            )

        checks = checks_for(context)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

        missing_scope = copy.deepcopy(context)
        missing_scope["saved_scopes"].pop()
        self.assertFalse(checks_for(missing_scope)["saved_scope_count"])

        wrong_type = copy.deepcopy(context)
        wrong_type["saved_scopes"][4] = _scope(
            "background_terrain_scope", "province"
        )
        self.assertFalse(
            checks_for(wrong_type)["scope:background_terrain_scope:type"]
        )

        aliased_characters = copy.deepcopy(context)
        aliased_characters["saved_scopes"][2] = _character_scope(
            "major", 50405035
        )
        self.assertFalse(
            checks_for(aliased_characters)[
                "scope:historical_character:differs_from"
            ]
        )

        root_as_character = copy.deepcopy(context)
        root_as_character["saved_scopes"][1] = _character_scope(
            "historical_character", 32904
        )
        self.assertFalse(
            checks_for(root_as_character)[
                "scope:historical_character:unique_third_party"
            ]
        )

        wrong_option = copy.deepcopy(context)
        wrong_option["options"].pop()
        self.assertFalse(checks_for(wrong_option)["authored_options_exact"])

    def test_exact_build_sources_remain_frozen(self) -> None:
        sources = {
            "events/historical_character_events.txt": EVENT_SOURCE_SHA256,
            (
                "common/scripted_effects/"
                "00_historical_characters_scripted_effects.txt"
            ): EFFECT_SOURCE_SHA256,
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
