from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from xar_autoplayer.vanilla_events import (  # noqa: E402
    DEFAULT_VANILLA_EVENT_ANALYSIS,
    DEFAULT_VANILLA_EVENT_OBSERVATIONS,
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_embedded import (  # noqa: E402
    EMBEDDED_VANILLA_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_epidemic import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_EPIDEMIC_ANALYSIS,
    VANILLA_EPIDEMIC_OBSERVATIONS,
    VANILLA_EPIDEMIC_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
import zg361_phase2_promotion_source_production_entry as production  # noqa: E402


EVENT_KEY = "epidemic_events.1064"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


def _scope(name: str, type_key: str) -> dict[str, object]:
    return {
        "name": name,
        "scope": {"status": "available", "type_key": type_key},
    }


class EpidemicEventRecordTests(unittest.TestCase):
    def test_contract_is_portable_and_selects_high_piety_duel(self) -> None:
        contract = VANILLA_EPIDEMIC_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["saved_scope_count"], 5)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["snapshot_option_count"], 3)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)

    def test_exact_analysis_separates_daily_maintenance_from_event_pulse(self) -> None:
        analysis = VANILLA_EPIDEMIC_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "2738-2914")
        self.assertIn("not a daily event", analysis["frequency_boundary"])
        self.assertIn("five-year cooldown", analysis["repeatability"])
        self.assertIn("ten rather than fifteen years", analysis["safe_option_rationale"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_live_observation_does_not_leak_campaign_ids_into_contract(self) -> None:
        exemplar = VANILLA_EPIDEMIC_OBSERVATIONS[EVENT_KEY]["exemplars"][0]
        contract_repr = repr(VANILLA_EPIDEMIC_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(exemplar["event_instance_id"], 867)
        self.assertEqual(exemplar["date_raw"], 53486160)
        self.assertEqual(exemplar["rendered_native_option_indices"], [0, 1, 2])
        self.assertFalse(exemplar["selection_attempted"])
        for field in (
            "artifact_sha256",
            "park_artifact_sha256",
            "driver_state_artifact_sha256",
        ):
            self.assertRegex(exemplar[field], SHA256_PATTERN)
        for observation_only in (867, 53486160, 32904, 28772):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_default_registry_mcp_and_production_runtime_include_record(self) -> None:
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS), 165)
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_ANALYSIS), 165)
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_OBSERVATIONS), 15)
        self.assertEqual(len(production.KNOWN_TIMELINE_INTERRUPTS), 304)
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            VANILLA_EPIDEMIC_TIMELINE_CONTRACTS[EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["root_character_id"], "$player")
        self.assertEqual(response["contract"]["native_option_indices"], [0, 1, 2])
        self.assertEqual(response["analysis"]["definition_lines"], "2738-2914")
        self.assertEqual(response["observations"]["exemplars"][0]["event_instance_id"], 867)
        json.dumps(response, allow_nan=False)

    def test_current_live_shape_passes_production_recovery_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            player=32904,
            event_key=EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53480000,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": EVENT_KEY,
            "current_event_instance_id": 867,
            "date_raw": 53486160,
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
                _scope("story", "story"),
                _scope("story_scope", "story"),
                _scope("epidemic_scope", "epidemic"),
                _scope("trait_blamed", "trait"),
                _scope("witch_trial_county", "landed_title"),
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
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53486160,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 867},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_repeat_sachet_contract_is_portable_and_source_backed(self) -> None:
        event_key = "epidemic_events.5009"
        contract = EMBEDDED_VANILLA_TIMELINE_CONTRACTS[event_key]
        analysis = DEFAULT_VANILLA_EVENT_ANALYSIS[event_key]
        exemplar = VANILLA_EPIDEMIC_OBSERVATIONS[event_key]["exemplars"][0]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertNotIn("max_occurrences", contract)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertEqual(len(contract["option_variants"]), 2)
        self.assertTrue(
            all(
                variant["selected_native_option_index"] == 3
                for variant in contract["option_variants"]
            )
        )
        self.assertEqual(analysis["definition_lines"], "7112-7329")
        self.assertIn("ten-year cooldown", analysis["repeatability"])
        self.assertEqual(exemplar["event_instance_id"], 871)
        self.assertEqual(exemplar["prior_green_occurrence"]["event_instance_id"], 612)
        self.assertEqual(exemplar["elapsed_days_since_prior_occurrence"], 3733)
        self.assertFalse(exemplar["selection_attempted"])


if __name__ == "__main__":
    unittest.main()
